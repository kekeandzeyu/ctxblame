"""`ctxblame why` end to end against a fake model that follows one planted sentence."""
import json

from aiohttp import web

from ctxblame import cli

from test_replay import ServerThread, anthropic_resp

PLANT = "We use pnpm in this repo, never npm."


def make_model():
    async def handler(request):
        body = await request.json()
        cmd = "pnpm add lodash" if PLANT in json.dumps(body) else "npm install lodash"
        return web.json_response(anthropic_resp("Bash", cmd))
    app = web.Application()
    app.router.add_post("/anthropic/v1/messages", handler)
    return app


def test_why_finds_the_planted_line(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")
    with ServerThread(make_model()) as base:
        body = {"model": "deepseek-flash", "max_tokens": 100,
                "system": "You are a coding agent.\n\n## Style\n- Be brief.\n- Use tools.\n\nThat is all.",
                "tools": [{"name": "Bash", "description": "Run a command.", "input_schema": {"type": "object"}}],
                "messages": [
                    {"role": "user", "content": f"Hi. This is our web shop. {PLANT} The app is in apps/web."},
                    {"role": "assistant", "content": "Thanks, what should I do?"},
                    {"role": "user", "content": "Add lodash."}]}
        rec = {"format": "anthropic", "upstream": base + "/anthropic",
               "request": {"path": "/v1/messages", "headers": {"anthropic-version": "2023-06-01"}, "body": body},
               "response": {"streamed": False, "body": anthropic_resp("Bash", "pnpm add lodash")}}
        p = tmp_path / "t.json"
        p.write_text(json.dumps(rec))
        rc = cli.main(["why", str(p), "--key-arg", r"command~\bpnpm\b", "--budget", "1",
                       "--ledger", str(tmp_path / "spend.jsonl"), "--out", str(tmp_path / "runs")])
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "Baseline:  10/10" in out and "Cause 1 (removing it flips the decision" in out
    assert PLANT in out and "Context it needs" not in out
    rep = json.loads(next((tmp_path / "runs").glob("*.why.json")).read_text())
    assert rep["result"] == "causes" and [m["text"] for m in rep["causes"][0]["members"]] == [PLANT]
    assert rep["causes"][0]["specific"] is True
