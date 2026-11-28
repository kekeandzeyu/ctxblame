import asyncio
import json
import sys
from pathlib import Path

from aiohttp import web
from aiohttp.test_utils import TestServer

from ctxblame.trace import load_trace
from ctxblame.wrap import ANTHROPIC_DEFAULT, OPENAI_DEFAULT, child_env, upstreams, wrap

KEY = "sk-wrap-DO-NOT-RECORD"
SEEN = web.AppKey("seen", list)

# The wrapped "agent": one call in each wire format, through the injected base URLs.
CHILD = r'''
import json, os, sys, urllib.request
def post(url, body, hdrs):
    req = urllib.request.Request(url, json.dumps(body).encode(), {"content-type": "application/json", **hdrs})
    return json.load(urllib.request.urlopen(req))
a = post(os.environ["ANTHROPIC_BASE_URL"] + "/v1/messages?beta=true",
         {"model": "m", "max_tokens": 9, "messages": [{"role": "user", "content": "hi"}]}, {"x-api-key": sys.argv[1]})
o = post(os.environ["OPENAI_BASE_URL"] + "/chat/completions",
         {"model": "m", "messages": [{"role": "user", "content": "hi"}]}, {"Authorization": "Bearer " + sys.argv[1]})
assert os.environ["OPENAI_API_BASE"] == os.environ["OPENAI_BASE_URL"]
print(a["content"][0]["text"], o["choices"][0]["message"]["content"], os.environ["CTXBLAME_TRACE"])
sys.exit(3)
'''


def fake_upstream() -> web.Application:
    app = web.Application()
    app[SEEN] = []

    async def messages(request):
        app[SEEN].append(request.path)
        return web.json_response({"id": "m1", "type": "message", "role": "assistant", "model": "m",
                                  "content": [{"type": "text", "text": "A"}], "stop_reason": "end_turn",
                                  "usage": {"input_tokens": 3, "output_tokens": 1}})

    async def chat(request):
        app[SEEN].append(request.path)
        return web.json_response({"id": "c1", "object": "chat.completion", "model": "m",
                                  "choices": [{"index": 0, "finish_reason": "stop",
                                               "message": {"role": "assistant", "content": "O"}}],
                                  "usage": {"prompt_tokens": 3, "completion_tokens": 1}})

    app.router.add_post("/anthropic/v1/messages", messages)  # like https://api.deepseek.com/anthropic
    app.router.add_post("/v1/chat/completions", chat)
    return app


async def _run(tmp: Path, cmd: list[str]):
    app = fake_upstream()
    async with TestServer(app) as up:
        rc = await wrap(cmd, tmp / "t.jsonl", str(up.make_url("/anthropic")), str(up.make_url("/v1")),
                        env={"PATH": "/usr/bin:/bin"}, quiet=True)
    return rc, app[SEEN]


def test_wrap_records_both_formats_and_passes_the_exit_code(tmp_path, capfd):
    rc, seen = asyncio.run(_run(tmp_path, [sys.executable, "-c", CHILD, KEY]))
    assert rc == 3
    assert seen == ["/anthropic/v1/messages", "/v1/chat/completions"]
    assert capfd.readouterr().out.split() == ["A", "O", str(tmp_path / "t.jsonl")]
    text = (tmp_path / "t.jsonl").read_text()
    assert KEY not in text
    steps = load_trace(tmp_path / "t.jsonl")
    assert [(s.step, s.fmt) for s in steps] == [(1, "anthropic"), (2, "openai")]
    assert steps[0].record["upstream"].endswith("/anthropic")
    assert steps[1].record["request"]["path"] == "/chat/completions"


def test_wrap_reports_a_missing_command(tmp_path):
    rc, seen = asyncio.run(_run(tmp_path, ["ctxblame-no-such-command"]))
    assert rc == 127 and seen == []


def test_wrap_reports_death_by_signal_like_a_shell(tmp_path):
    rc, _ = asyncio.run(_run(tmp_path, [sys.executable, "-c", "import os, signal; os.kill(os.getpid(), signal.SIGTERM)"]))
    assert rc == 128 + 15


def test_upstreams_keep_the_base_urls_the_command_would_have_used():
    assert upstreams({}) == (ANTHROPIC_DEFAULT, OPENAI_DEFAULT)
    env = {"ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic/", "OPENAI_API_BASE": "http://127.0.0.1:8000/v1"}
    assert upstreams(env) == ("https://api.deepseek.com/anthropic", "http://127.0.0.1:8000/v1")
    assert upstreams(env, openai="https://x/v1")[1] == "https://x/v1"
    e = child_env({"HOME": "/h", "OPENAI_BASE_URL": "old"}, "http://a", "http://o", Path("t.jsonl"))
    assert e == {"HOME": "/h", "ANTHROPIC_BASE_URL": "http://a", "OPENAI_BASE_URL": "http://o",
                 "OPENAI_API_BASE": "http://o", "CTXBLAME_TRACE": "t.jsonl"}
