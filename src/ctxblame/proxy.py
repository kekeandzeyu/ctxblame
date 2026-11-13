"""Recording proxy for the Anthropic Messages API (and compatible endpoints).

Point a client at it with ``ANTHROPIC_BASE_URL=http://127.0.0.1:8787``. Every
request is forwarded unchanged to the upstream; each ``POST .../v1/messages``
exchange is also saved as one JSON file: the parsed request body, the response
body (or, for streams, every raw SSE event plus the reassembled message).

Credentials are forwarded but never recorded: auth-like headers are dropped
from the saved record.
"""

from __future__ import annotations

import argparse
import asyncio
import itertools
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from aiohttp import ClientSession, ClientTimeout, web

from .sse import SSEParser, assemble_message

RECORD_VERSION = 1
CLIENT_KEY = web.AppKey("client", ClientSession)

HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length",
    "accept-encoding", "content-encoding",
}
SECRET_EXACT = {"authorization", "x-api-key", "cookie", "set-cookie", "proxy-authorization"}
SECRET_PARTS = ("key", "token", "secret", "auth", "cookie", "session-ingress")


def is_secret_header(name: str) -> bool:
    n = name.lower()
    return n in SECRET_EXACT or any(p in n for p in SECRET_PARTS)


def redact_headers(headers) -> dict[str, str]:
    return {k: v for k, v in headers.items() if not is_secret_header(k)}


def forward_headers(headers) -> dict[str, str]:
    out = {k: v for k, v in headers.items() if k.lower() not in HOP_BY_HOP}
    out["Accept-Encoding"] = "identity"  # keep bytes plain so we can record them
    return out


def is_messages_call(method: str, path: str) -> bool:
    return method == "POST" and path.rstrip("/").endswith("/v1/messages")


class Recorder:
    def __init__(self, out_dir: Path) -> None:
        self.out_dir = out_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self._seq = itertools.count(1)

    def save(self, record: dict) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        path = self.out_dir / f"{stamp}-{next(self._seq):04d}-{record['id'][:8]}.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(record, ensure_ascii=False, indent=1))
        tmp.replace(path)
        return path


def make_app(upstream: str, out_dir: Path, quiet: bool = False) -> web.Application:
    upstream = upstream.rstrip("/")
    recorder = Recorder(out_dir)
    app = web.Application(client_max_size=256 * 1024**2)

    async def on_startup(app: web.Application) -> None:
        app[CLIENT_KEY] = ClientSession(
            timeout=ClientTimeout(total=None, sock_connect=30, sock_read=900),
            auto_decompress=False,
        )

    async def on_cleanup(app: web.Application) -> None:
        await app[CLIENT_KEY].close()

    async def handle(request: web.Request) -> web.StreamResponse:
        body = await request.read()
        url = upstream + request.path_qs
        record_it = is_messages_call(request.method, request.path)
        t0 = time.time()
        rec: dict | None = None
        if record_it:
            try:
                req_json = json.loads(body) if body else None
            except json.JSONDecodeError:
                req_json = None
            rec = {
                "version": RECORD_VERSION,
                "id": uuid.uuid4().hex,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "upstream": upstream,
                "request": {
                    "method": request.method,
                    "path": request.path_qs,
                    "headers": redact_headers(request.headers),
                    "body": req_json,
                    "body_text": None if req_json is not None else body.decode("utf-8", "replace"),
                },
            }

        client = request.app[CLIENT_KEY]
        try:
            up = await client.request(
                request.method, url, data=body, headers=forward_headers(request.headers)
            )
        except Exception as e:  # upstream unreachable
            if rec is not None:
                rec["error"] = f"upstream request failed: {e!r}"
                recorder.save(rec)
            return web.Response(status=502, text=f"ctxblame proxy: upstream error: {e}")

        resp_headers = {k: v for k, v in up.headers.items() if k.lower() not in HOP_BY_HOP}
        ctype = up.headers.get("Content-Type", "")
        streaming = ctype.startswith("text/event-stream")
        resp = web.StreamResponse(status=up.status, headers=resp_headers)
        await resp.prepare(request)

        parser = SSEParser() if (streaming and rec is not None) else None
        events: list[dict] = []
        chunks: list[bytes] = []
        try:
            async for chunk in up.content.iter_any():
                await resp.write(chunk)
                if rec is None:
                    continue
                if parser is not None:
                    events.extend(e.to_json() for e in parser.feed(chunk))
                else:
                    chunks.append(chunk)
            if parser is not None:
                events.extend(e.to_json() for e in parser.flush())
        except (ConnectionResetError, asyncio.CancelledError) as e:
            if rec is not None:
                rec["error"] = f"stream interrupted: {e!r}"
            raise
        finally:
            up.release()
            if rec is not None:
                rec["duration_s"] = round(time.time() - t0, 3)
                rec["response"] = {
                    "status": up.status,
                    "headers": redact_headers(up.headers),
                    "streamed": streaming,
                }
                if streaming:
                    rec["response"]["events"] = events
                    rec["response"]["message"] = assemble_message(events)
                else:
                    raw = b"".join(chunks)
                    try:
                        rec["response"]["body"] = json.loads(raw)
                    except json.JSONDecodeError:
                        rec["response"]["body_text"] = raw.decode("utf-8", "replace")
                path = recorder.save(rec)
                if not quiet:
                    print(f"recorded {request.path} -> {up.status} "
                          f"{'stream' if streaming else 'json'} {path}", flush=True)

        await resp.write_eof()
        return resp

    app.router.add_route("*", "/{tail:.*}", handle)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Record Anthropic Messages API traffic.")
    ap.add_argument("--upstream", default=os.environ.get("CTXBLAME_UPSTREAM", "https://api.anthropic.com"),
                    help="e.g. https://api.anthropic.com or https://api.deepseek.com/anthropic")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--out", type=Path, default=Path("traces"))
    args = ap.parse_args(argv)
    print(f"ctxblame proxy: http://{args.host}:{args.port} -> {args.upstream}, saving to {args.out}/")
    web.run_app(make_app(args.upstream, args.out), host=args.host, port=args.port, print=None)


if __name__ == "__main__":
    main()
