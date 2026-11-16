import asyncio
import json
from pathlib import Path

from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer

from ctxblame.proxy import make_app
from ctxblame.trace import load_trace

from test_sse import TOOL_STREAM

SEEN = web.AppKey("seen", list)
FAKE_KEY = "sk-test-DO-NOT-RECORD-123"


def fake_upstream() -> web.Application:
    seen: list[dict] = []

    async def messages(request: web.Request):
        body = await request.json()
        seen.append({"path": request.path, "headers": dict(request.headers), "body": body})
        if body.get("stream"):
            resp = web.StreamResponse(headers={"Content-Type": "text/event-stream", "request-id": "req_1"})
            await resp.prepare(request)
            data = TOOL_STREAM.encode()
            for i in range(0, len(data), 50):  # deliver in odd-sized chunks
                await resp.write(data[i:i + 50])
                await asyncio.sleep(0)
            await resp.write_eof()
            return resp
        return web.json_response({"id": "msg_2", "type": "message", "role": "assistant",
                                  "content": [{"type": "text", "text": "hi"}],
                                  "stop_reason": "end_turn",
                                  "usage": {"input_tokens": 5, "output_tokens": 1}})

    async def count(request: web.Request):
        return web.json_response({"input_tokens": 5})

    app = web.Application()
    app[SEEN] = seen
    # upstream with a path prefix, like https://api.deepseek.com/anthropic
    app.router.add_post("/anthropic/v1/messages", messages)
    app.router.add_post("/anthropic/v1/messages/count_tokens", count)
    return app


async def _run(tmp: Path):
    up_app = fake_upstream()
    async with TestServer(up_app) as up:
        proxy_app = make_app(str(up.make_url("/anthropic")), tmp / "t.jsonl", quiet=True)
        async with TestServer(proxy_app) as px, ClientSession() as s:
            hdrs = {"x-api-key": FAKE_KEY, "Authorization": f"Bearer {FAKE_KEY}",
                    "anthropic-version": "2023-06-01", "content-type": "application/json"}
            req = {"model": "m", "max_tokens": 100, "system": "sys",
                   "tools": [{"name": "Bash", "input_schema": {"type": "object"}}],
                   "messages": [{"role": "user", "content": "list files"}]}

            async with s.post(px.make_url("/v1/messages"), json={**req, "stream": True}, headers=hdrs) as r:
                streamed_bytes = await r.read()
                assert r.status == 200
            async with s.post(px.make_url("/v1/messages"), json=req, headers=hdrs) as r:
                plain = await r.json()
            async with s.post(px.make_url("/v1/messages/count_tokens"), json=req, headers=hdrs) as r:
                assert (await r.json()) == {"input_tokens": 5}
    return up_app[SEEN], streamed_bytes, plain


def test_proxy_forwards_and_records(tmp_path):
    seen, streamed_bytes, plain = asyncio.run(_run(tmp_path))

    # client got the upstream bytes unchanged; upstream got the key
    assert streamed_bytes.decode() == TOOL_STREAM
    assert plain["content"][0]["text"] == "hi"
    assert seen[0]["headers"]["x-api-key"] == FAKE_KEY
    assert seen[0]["path"] == "/anthropic/v1/messages"

    trace = (tmp_path / "t.jsonl").read_text()
    assert FAKE_KEY not in trace
    recs = [json.loads(l) for l in trace.splitlines()]
    assert len(recs) == 2  # count_tokens is passed through, not recorded
    assert [r["step"] for r in recs] == [1, 2]
    assert [s.step for s in load_trace(tmp_path / "t.jsonl")] == [1, 2]
    stream_rec = next(r for r in recs if r["response"]["streamed"])
    plain_rec = next(r for r in recs if not r["response"]["streamed"])

    assert stream_rec["request"]["body"]["system"] == "sys"
    assert stream_rec["request"]["body"]["tools"][0]["name"] == "Bash"
    assert "x-api-key" not in stream_rec["request"]["headers"]
    assert "authorization" not in {k.lower() for k in stream_rec["request"]["headers"]}
    msg = stream_rec["response"]["message"]
    assert msg["_stream_complete"] and msg["content"][2]["input"] == {"command": "ls -la"}
    assert len(stream_rec["response"]["events"]) == 18  # every event, ping included
    assert plain_rec["response"]["body"]["content"][0]["text"] == "hi"
