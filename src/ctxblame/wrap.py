"""``ctxblame wrap -- <cmd>``: record an agent run without configuring a proxy.

Starts two recording proxies on free loopback ports, one for Anthropic-format
clients and one for OpenAI-format ones, both appending to one trace. Then runs
``<cmd>`` with ``ANTHROPIC_BASE_URL`` and ``OPENAI_BASE_URL`` (and the older
``OPENAI_API_BASE``) pointing at them. Base URLs already in the environment
become the upstreams, so a harness already pointed at DeepSeek or a local vLLM
server keeps talking to it. The proxies stop when the command exits, and
``wrap`` exits with the command's code.

Only ``/v1/messages`` and ``/chat/completions`` calls are recorded. Others
(e.g. the OpenAI Responses API) are forwarded but not recorded, the same as
``ctxblame record``.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import signal
import sys
from pathlib import Path

from aiohttp import web

from .proxy import default_trace_path, make_app
from .trace import TraceWriter

ANTHROPIC_DEFAULT = "https://api.anthropic.com"
OPENAI_DEFAULT = "https://api.openai.com/v1"


def upstreams(env: dict[str, str], anthropic: str | None = None,
              openai: str | None = None) -> tuple[str, str]:
    """Where the proxies forward to: the flag, else the base URL the command would
    have used (``ANTHROPIC_BASE_URL``, ``OPENAI_BASE_URL`` / ``OPENAI_API_BASE``),
    else the provider's own API."""
    a = anthropic or env.get("ANTHROPIC_BASE_URL") or ANTHROPIC_DEFAULT
    o = openai or env.get("OPENAI_BASE_URL") or env.get("OPENAI_API_BASE") or OPENAI_DEFAULT
    return a.rstrip("/"), o.rstrip("/")


def child_env(env: dict[str, str], anthropic_url: str, openai_url: str, trace: Path) -> dict[str, str]:
    return {**env, "ANTHROPIC_BASE_URL": anthropic_url, "OPENAI_BASE_URL": openai_url,
            "OPENAI_API_BASE": openai_url, "CTXBLAME_TRACE": str(trace)}


def _exit_code(rc: int) -> int:
    return 128 - rc if rc < 0 else rc  # killed by signal N -> 128 + N, as a shell reports it


def _count(trace: Path) -> int:
    try:
        return sum(1 for line in trace.read_text().splitlines() if line.strip())
    except OSError:
        return 0


async def wrap(cmd: list[str], trace: Path, anthropic_upstream: str, openai_upstream: str,
               host: str = "127.0.0.1", env: dict[str, str] | None = None, quiet: bool = False) -> int:
    """Run ``cmd`` behind the two proxies; return its exit code (127 if it cannot start)."""
    say = (lambda *a: None) if quiet else (lambda *a: print("ctxblame wrap:", *a, file=sys.stderr, flush=True))
    before = _count(trace)
    recorder = TraceWriter(trace)
    runners: list[web.AppRunner] = []
    try:
        urls = []
        for up in (anthropic_upstream, openai_upstream):
            r = web.AppRunner(make_app(up, trace, quiet=True, recorder=recorder),
                              handle_signals=False, access_log=None)
            runners.append(r)
            await r.setup()
            await web.TCPSite(r, host, 0).start()
            urls.append(f"http://{host}:{r.addresses[0][1]}")
        say(f"{urls[0]} -> {anthropic_upstream} (Anthropic), {urls[1]} -> {openai_upstream} (OpenAI)")
        say(f"trace: {trace}")
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, env=child_env(dict(os.environ if env is None else env), urls[0], urls[1], trace))
        except OSError as e:
            print(f"ctxblame wrap: cannot run {cmd[0]!r}: {e}", file=sys.stderr)
            return 127
        loop = asyncio.get_running_loop()
        # Ctrl-C reaches the command through the terminal; keep the proxies up until
        # it exits. A SIGTERM / SIGHUP sent to wrap alone is passed on to it.
        handlers = {signal.SIGINT: lambda: None}
        for sig in (signal.SIGTERM, signal.SIGHUP):
            handlers[sig] = lambda s=sig: proc.returncode is None and proc.send_signal(s)
        for sig, h in handlers.items():
            try:
                loop.add_signal_handler(sig, h)
            except (NotImplementedError, RuntimeError):  # Windows, or not the main thread
                pass
        try:
            rc = await proc.wait()
        finally:
            for sig in handlers:
                try:
                    loop.remove_signal_handler(sig)
                except (NotImplementedError, RuntimeError):
                    pass
        n = _count(trace) - before
        say(f"recorded {n} step{'s' * (n != 1)} to {trace}" + (f"\n  next: ctxblame steps {trace}" if n else ""))
        return _exit_code(rc)
    finally:
        for r in runners:
            await r.cleanup()


def add_args(ap: argparse.ArgumentParser) -> None:
    ap.add_argument("--trace", type=Path, default=None, help="trace file to append to (default: a new file in --out)")
    ap.add_argument("--out", type=Path, default=Path("traces"))
    ap.add_argument("--anthropic-upstream", default=None,
                    help=f"default: $ANTHROPIC_BASE_URL, else {ANTHROPIC_DEFAULT}")
    ap.add_argument("--openai-upstream", default=None,
                    help=f"default: $OPENAI_BASE_URL or $OPENAI_API_BASE, else {OPENAI_DEFAULT}")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("-q", "--quiet", action="store_true", help="no messages on stderr")
    ap.add_argument("cmd", nargs=argparse.REMAINDER, help="the command to run, after --")


def run_cli(args) -> int:
    cmd = args.cmd[1:] if args.cmd[:1] == ["--"] else args.cmd
    if not cmd:
        print("usage: ctxblame wrap [options] -- <cmd> [args...]", file=sys.stderr)
        return 2
    a, o = upstreams(dict(os.environ), args.anthropic_upstream, args.openai_upstream)
    trace = args.trace or default_trace_path(args.out)
    return asyncio.run(wrap(cmd, trace, a, o, host=args.host, quiet=args.quiet))
