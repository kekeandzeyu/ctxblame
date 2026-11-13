"""End-to-end replay against a fake upstream that speaks both formats."""

import asyncio
import itertools
import json
import threading

import pytest
from aiohttp import web

from ctxblame import replay

FAKE_KEY = "sk-fake-replay-key"
CALLS = web.AppKey("calls", list)


def anthropic_resp(name, command):
    return {"id": "m", "type": "message", "role": "assistant", "model": "deepseek-flash",
            "content": [{"type": "tool_use", "id": "t1", "name": name, "input": {"command": command}}],
            "stop_reason": "tool_use", "usage": {"input_tokens": 1000, "output_tokens": 100}}


def openai_resp(name, command):
    return {"id": "c", "object": "chat.completion", "model": "deepseek-flash",
            "choices": [{"index": 0, "finish_reason": "tool_calls", "message": {
                "role": "assistant", "content": None,
                "tool_calls": [{"id": "x", "type": "function",
                                "function": {"name": name, "arguments": json.dumps({"command": command})}}]}}],
            "usage": {"prompt_tokens": 1000, "completion_tokens": 100,
                      "prompt_cache_hit_tokens": 0, "prompt_cache_miss_tokens": 1000}}


def sse(events):
    return "".join(f"event: {e['type']}\ndata: {json.dumps(e)}\n\n" for e in events)


def anthropic_stream(name, command):
    r = anthropic_resp(name, command)
    return sse([
        {"type": "message_start", "message": {**r, "content": [], "stop_reason": None,
                                              "usage": {"input_tokens": 1000, "output_tokens": 1}}},
        {"type": "content_block_start", "index": 0,
         "content_block": {"type": "tool_use", "id": "t1", "name": name, "input": {}}},
        {"type": "content_block_delta", "index": 0,
         "delta": {"type": "input_json_delta", "partial_json": json.dumps({"command": command})}},
        {"type": "content_block_stop", "index": 0},
        {"type": "message_delta", "delta": {"stop_reason": "tool_use"}, "usage": {"output_tokens": 100}},
        {"type": "message_stop"},
    ])


# 7 of every 10 replies repeat the decision; 3 do something else
SCRIPT = [("Bash", "ls -la")] * 7 + [("Bash", "ls"), ("Read", "README.md"), ("Bash", "ls -la /tmp")]


def make_upstream(fail_first_with=None):
    counter = itertools.count()
    calls = []

    async def handler(request):
        body = await request.json()
        calls.append({"headers": dict(request.headers), "body": body})
        i = next(counter)
        if fail_first_with and i == 0:
            return web.json_response({"error": "nope"}, status=fail_first_with)
        name, cmd = SCRIPT[i % len(SCRIPT)]
        if request.path.endswith("/v1/messages"):
            if body.get("stream"):
                return web.Response(text=anthropic_stream(name, cmd), content_type="text/event-stream")
            return web.json_response(anthropic_resp(name, cmd))
        return web.json_response(openai_resp(name, cmd))

    app = web.Application()
    app[CALLS] = calls
    app.router.add_post("/anthropic/v1/messages", handler)
    app.router.add_post("/chat/completions", handler)
    return app


class ServerThread:
    """Run an aiohttp app on its own loop so replay.main() can asyncio.run()."""

    def __init__(self, app):
        self.app, self.loop = app, asyncio.new_event_loop()
        self.ready = threading.Event()

    def __enter__(self):
        def run():
            asyncio.set_event_loop(self.loop)
            self.runner = web.AppRunner(self.app)
            self.loop.run_until_complete(self.runner.setup())
            site = web.TCPSite(self.runner, "127.0.0.1", 0)
            self.loop.run_until_complete(site.start())
            self.port = site._server.sockets[0].getsockname()[1]
            self.ready.set()
            self.loop.run_forever()
        self.t = threading.Thread(target=run, daemon=True)
        self.t.start()
        self.ready.wait(5)
        return f"http://127.0.0.1:{self.port}"

    def __exit__(self, *exc):
        asyncio.run_coroutine_threadsafe(self.runner.cleanup(), self.loop).result(5)
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.t.join(5)


def write_record(tmp_path, fmt, upstream, stream=False):
    if fmt == "anthropic":
        body = {"model": "deepseek-flash", "max_tokens": 1000, "stream": stream,
                "tools": [{"name": "Bash", "input_schema": {"type": "object"}}],
                "messages": [{"role": "user", "content": "list files"}]}
        rec = {"format": fmt, "upstream": upstream + "/anthropic",
               "request": {"path": "/v1/messages", "headers": {"anthropic-version": "2023-06-01"}, "body": body},
               "response": {"streamed": False, "body": anthropic_resp("Bash", "ls -la")}}
    else:
        body = {"model": "deepseek-flash", "messages": [{"role": "user", "content": "list files"}],
                "tools": [{"type": "function", "function": {"name": "Bash", "parameters": {"type": "object"}}}]}
        rec = {"format": fmt, "upstream": upstream,
               "request": {"path": "/chat/completions", "headers": {}, "body": body},
               "response": {"streamed": False, "body": openai_resp("Bash", "ls -la")}}
    p = tmp_path / f"{fmt}.json"
    p.write_text(json.dumps(rec))
    return p


@pytest.mark.parametrize("fmt,stream", [("anthropic", False), ("anthropic", True), ("openai", False)])
def test_replay_measures_reproduce_rate(tmp_path, monkeypatch, capsys, fmt, stream):
    monkeypatch.setenv("DEEPSEEK_API_KEY", FAKE_KEY)
    app = make_upstream()
    with ServerThread(app) as base:
        rec = write_record(tmp_path, fmt, base, stream)
        # base url contains no "deepseek", so name the key env explicitly
        rc = replay.main([str(rec), "-n", "10", "--api-key-env", "DEEPSEEK_API_KEY",
                          "--ledger", str(tmp_path / "spend.jsonl"), "--out", str(tmp_path / "runs")])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Same decision:  7/10 = 70%" in out
    assert "Same tool name: 9/10" in out

    run = json.loads(next((tmp_path / "runs").glob("*.json")).read_text())
    s = run["summary"]
    assert (s["n_ok"], s["same_decision"], s["n_error"]) == (10, 7, 0)
    # 10 calls x (1000 in + 100 out) on deepseek-flash, peak or off-peak
    assert s["cost"] in (pytest.approx(10 * (1000 * .30 + 100 * 1.2) / 1e6),
                         pytest.approx(10 * (1000 * .15 + 100 * .6) / 1e6))
    assert len(app[CALLS]) == 10
    sent = app[CALLS][0]
    assert sent["body"] == json.loads(rec.read_text())["request"]["body"]  # exact body re-sent
    if fmt == "anthropic":
        assert sent["headers"]["x-api-key"] == FAKE_KEY
    else:
        assert sent["headers"]["Authorization"] == f"Bearer {FAKE_KEY}"
    for f in tmp_path.rglob("*.json*"):
        assert FAKE_KEY not in f.read_text()


def test_retries_rate_limit(tmp_path, monkeypatch):
    monkeypatch.setenv("K", FAKE_KEY)
    monkeypatch.setattr(replay.random, "random", lambda: 0.0)
    app = make_upstream(fail_first_with=429)
    with ServerThread(app) as base:
        rec = write_record(tmp_path, "openai", base)
        rc = replay.main([str(rec), "-n", "2", "--api-key-env", "K", "--concurrency", "1",
                          "--ledger", str(tmp_path / "s.jsonl"), "--out", str(tmp_path / "runs")])
    assert rc == 0 and len(app[CALLS]) == 3


def test_auth_error_aborts_without_spending(tmp_path, monkeypatch):
    monkeypatch.setenv("K", FAKE_KEY)
    app = make_upstream(fail_first_with=401)
    with ServerThread(app) as base:
        rec = write_record(tmp_path, "openai", base)
        rc = replay.main([str(rec), "-n", "5", "--api-key-env", "K", "--concurrency", "1",
                          "--ledger", str(tmp_path / "s.jsonl"), "--out", str(tmp_path / "runs")])
    assert rc == 4 and len(app[CALLS]) == 1
    assert not (tmp_path / "s.jsonl").exists()


def test_budget_stops_new_calls(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("K", FAKE_KEY)
    app = make_upstream()
    with ServerThread(app) as base:
        rec = write_record(tmp_path, "openai", base)
        # each call costs at most ~$0.00042 (peak); estimate is 1.5x that
        rc = replay.main([str(rec), "-n", "10", "--api-key-env", "K", "--concurrency", "1",
                          "--budget", "0.002", "--ledger", str(tmp_path / "s.jsonl"),
                          "--out", str(tmp_path / "runs")])
    assert rc == 0
    assert 1 <= len(app[CALLS]) < 10
    total = sum(json.loads(l)["cost"] for l in (tmp_path / "s.jsonl").read_text().splitlines())
    assert total <= 0.002
    assert "skipped because of the budget" in capsys.readouterr().err


def test_missing_key_env(tmp_path, monkeypatch):
    monkeypatch.delenv("NOPE", raising=False)
    rec = write_record(tmp_path, "openai", "http://127.0.0.1:9")
    assert replay.main([str(rec), "--api-key-env", "NOPE"]) == 2


def test_cli_ablation_sends_ablated_body(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("K", FAKE_KEY)
    app = make_upstream()
    with ServerThread(app) as base:
        rec = write_record(tmp_path, "openai", base)
        rc = replay.main([str(rec), "-n", "2", "--api-key-env", "K", "--remove-text", "list ",
                          "--key-arg", "command~^ls", "--ledger", str(tmp_path / "s.jsonl"),
                          "--out", str(tmp_path / "runs")])
    assert rc == 0
    assert app[CALLS][0]["body"]["messages"][0]["content"] == "files"
    assert "Ablation: removed text 'list '" in capsys.readouterr().out
    run = json.loads(next((tmp_path / "runs").glob("*.json")).read_text())
    assert run["ablation"] == ["removed text 'list '"]
    assert run["samples"][0]["call"] == {"name": "Bash", "args": {"command": "ls -la"}}


def test_cli_list_units_needs_no_key(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    rec = write_record(tmp_path, "anthropic", "http://127.0.0.1:9")
    assert replay.main([str(rec), "--list-units"]) == 0
    assert "msg[0]" in capsys.readouterr().out
