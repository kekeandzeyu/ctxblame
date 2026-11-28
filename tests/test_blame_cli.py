"""`ctxblame why` end to end against a fake model that follows one planted sentence."""
import json

from aiohttp import web

from ctxblame import cli

from test_replay import ServerThread, anthropic_resp, openai_resp

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


def _make_step5_like_model():
    """Simulates the Phase 2 step5/step7 bug on an OpenAI-compatible local server:
    - Removing edit_file makes the agent re-edit src/ctxblame/formats.py (precondition collapse).
    - With edit_file present, any of the 3 pytest style carriers keeps `python -m pytest -q`.
    - With all 3 style carriers removed (edit_file kept), the agent runs `uv run pytest` (choice flip).
    """
    async def handler(request):
        body = await request.json()
        raw = json.dumps(body)
        if "edited src/ctxblame/formats.py" not in raw:
            resp = openai_resp("edit_file", "")
            resp["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = json.dumps(
                {"path": "src/ctxblame/formats.py", "old_string": "a", "new_string": "b"})
            resp["model"] = body["model"]
            return web.json_response(resp)
        has_carrier = (
            "python -m pytest -q" in raw
        )
        cmd = "python -m pytest -q" if has_carrier else "uv run pytest"
        resp = openai_resp("bash", cmd)
        resp["model"] = body["model"]
        return web.json_response(resp)

    app = web.Application()
    app.router.add_post("/v1/chat/completions", handler)
    return app


def _step5_trace(tmp_path, base):
    body = {
        "model": "deepseek-v4-pro",
        "tools": [
            {"type": "function", "function": {
                "name": "bash",
                "description": "Run one shell command.",
                "parameters": {"type": "object", "properties": {
                    "command": {"type": "string", "description": "the command line, e.g. `python -m pytest -q`"},
                }},
            }},
            {"type": "function", "function": {
                "name": "edit_file",
                "description": "Edit a file.",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}},
            }},
        ],
        "messages": [
            {"role": "system", "content": (
                "You are a coding agent.\n\n"
                "## Workflow\n"
                "- Keep fixes minimal.\n"
                "- Run the test suite with `python -m pytest -q`.\n"
                "- Do not reformat unrelated code.\n"
            )},
            {"role": "user", "content": "Fix the failing test in tests/test_formats.py and verify the suite passes."},
            {"role": "assistant", "content": None, "tool_calls": [
                {"id": "call_1", "type": "function",
                 "function": {"name": "bash", "arguments": json.dumps({"command": "python -m pytest -q"})}}]},
            {"role": "tool", "tool_call_id": "call_1", "content": "1 failed in tests/test_formats.py"},
            {"role": "assistant", "content": None, "tool_calls": [
                {"id": "call_2", "type": "function",
                 "function": {"name": "edit_file", "arguments": json.dumps({"path": "src/ctxblame/formats.py"})}}]},
            {"role": "tool", "tool_call_id": "call_2", "content": "edited src/ctxblame/formats.py"},
        ],
    }
    rec = {"format": "openai", "upstream": base + "/v1",
           "request": {"path": "/chat/completions", "headers": {}, "body": body},
           "response": {"streamed": False, "body": openai_resp("bash", "python -m pytest -q")}}
    p = tmp_path / "step5.json"
    p.write_text(json.dumps(rec))
    return p


def test_why_conditional_separates_precondition_from_redundant_carriers_on_free_local_model(
        tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with ServerThread(_make_step5_like_model()) as base:
        p = _step5_trace(tmp_path, base)
        rc = cli.main(["why", str(p), "--key-arg", r"command~^python -m pytest",
                       "--model", "Qwen/Qwen3-14B", "--free",
                       "--controls", "0",
                       "--ledger", str(tmp_path / "spend.jsonl"), "--out", str(tmp_path / "runs")])
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "Given:     run pytest" in out
    assert "Precondition 1" in out
    assert "Cause 1 (redundant:" in out
    rep = json.loads(next((tmp_path / "runs").glob("*.why.json")).read_text())
    assert rep["cost"] == 0.0
    assert rep["given"]["target"] == "run pytest"
    # Precondition is edit_file (call_2), NOT reported as a choice cause
    pre_ids = [m["id"] for pre in rep["preconditions"] for m in pre["members"]]
    assert pre_ids == ["pair:call_2"]
    assert rep["preconditions"][0]["relation"] == "and_precondition"
    cause_ids = sorted(m["id"] for c in rep["causes"] for m in c["members"])
    assert len(cause_ids) == 3
    assert "pair:call_1" in cause_ids  # earlier pytest call
    assert any(cid.startswith("tooldesc:bash") for cid in cause_ids)
    assert any(cid.startswith("sys@msg0.") for cid in cause_ids)
    assert "pair:call_2" not in cause_ids
    assert rep["causes"][0]["relation"] == "or_carriers"
    assert sorted(rep["causes"][0]["restored"]) == cause_ids
    assert "cache_stats" in rep and rep["cache_stats"]["input_uncached"] > 0
    # audit stage: the bundle flip and each leave-one-in restore on 20 fresh replays, then Holm
    c, pre = rep["causes"][0], rep["preconditions"][0]
    assert c["certified"] is True and pre["certified"] is True and rep["uncertified"] == []
    stage2 = sorted(cause_ids + ["together"])  # a bundle is audited twice: stage 1 picks, stage 2 decides
    assert sorted(c["audit"]) == sorted(stage2 + [f"stage1:{k}" for k in stage2])
    assert c["audit"]["together"]["n_total"] == 20
    assert c["p_adjusted"] <= 0.05 and "certified on fresh replays" in out
    assert sum(1 for t in rep["tests"] if t.get("audit")) == 2 * (1 + 3) + 1


def test_why_given_none_preserves_unconditional_behavior(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with ServerThread(_make_step5_like_model()) as base:
        p = _step5_trace(tmp_path, base)
        rc = cli.main(["why", str(p), "--key-arg", r"command~^python -m pytest",
                       "--given", "none", "--model", "Qwen/Qwen3-14B", "--free",
                       "--controls", "0", "--json",
                       "--ledger", str(tmp_path / "spend.jsonl"), "--out", str(tmp_path / "runs")])
    assert rc == 0
    rep = json.loads(next((tmp_path / "runs").glob("*.why.json")).read_text())
    assert "given" not in rep
    assert rep["preconditions"] == []
    # Without conditioning, unconditional ddmin locks onto edit_file (pair:call_2)
    assert [m["id"] for m in rep["causes"][0]["members"]] == ["pair:call_2"]


def _make_pnpm_model():
    """p3/precond_2or_pnpm as measured on Qwen3-14B (Phase 5.6): without the package.json
    edit the agent redoes the edit, and if it is made to run bash anyway (tool_choice) it
    runs `pnpm add zod` instead of `pnpm install`; the pnpm rule picks pnpm over npm."""
    async def handler(request):
        body = await request.json()
        raw = json.dumps(body)
        forced = (body.get("tool_choice") or {}).get("function", {}).get("name") == "bash"
        if "edited package.json" not in raw and not forced:
            resp = openai_resp("edit_file", "")
            resp["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = json.dumps(
                {"path": "package.json"})
        else:
            pm = "pnpm" if "Always install dependencies with pnpm" in raw else "npm"
            cmd = f"{pm} install --frozen-lockfile" if "edited package.json" in raw else f"{pm} add zod"
            resp = openai_resp("bash", cmd)
        resp["model"] = body["model"]
        return web.json_response(resp)
    app = web.Application()
    app.router.add_post("/v1/chat/completions", handler)
    return app


def test_why_forces_E_and_reports_a_precondition_that_also_steers(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    tools = [{"type": "function", "function": {"name": n, "description": d, "parameters": {"type": "object"}}}
             for n, d in (("bash", "Run one shell command."), ("edit_file", "Edit a file."))]
    body = {"model": "m", "tools": tools, "messages": [
        {"role": "system", "content": "You are a coding agent.\n\n## Rules\n- Keep diffs small.\n"
                                      "- Always install dependencies with pnpm; never npm.\n"},
        {"role": "user", "content": "Add zod to package.json and install dependencies."},
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": "call_edit", "type": "function",
             "function": {"name": "edit_file", "arguments": json.dumps({"path": "package.json"})}}]},
        {"role": "tool", "tool_call_id": "call_edit", "content": "edited package.json"}]}
    with ServerThread(_make_pnpm_model()) as base:
        rec = {"format": "openai", "upstream": base + "/v1",
               "request": {"path": "/chat/completions", "headers": {}, "body": body},
               "response": {"streamed": False, "body": openai_resp("bash", "pnpm install --frozen-lockfile")}}
        p = tmp_path / "pnpm.json"
        p.write_text(json.dumps(rec))
        args = ["why", str(p), "--key-arg", r"command~^pnpm install", "--given", "bash", "--free",
                "--controls", "0", "--ledger", str(tmp_path / "spend.jsonl"), "--out", str(tmp_path / "runs")]
        rc = cli.main(args)
        out = capsys.readouterr().out
        assert rc == 0, out
        rep = json.loads(next((tmp_path / "runs").glob("*.why.json")).read_text())
        assert rep["forcing"]["tool"] == "bash" and rep["forcing"]["threshold"] == 0.5
        pre = rep["preconditions"][0]
        assert [m["id"] for m in pre["members"]] == ["pair:call_edit"] and pre["steers"] is True
        forced = [c for c in rep["causes"] if c["forced"]]
        assert [[m["id"] for m in c["members"]] for c in forced] == [["pair:call_edit"]]
        assert forced[0]["certified"] is True and forced[0]["audit"]["together"]["k"] == 0
        assert "triggers and steers" in out and "with bash forced" in out
        # the rule is an ordinary choice carrier (pnpm vs npm), unforced
        plain = [m["id"] for c in rep["causes"] if not c["forced"] for m in c["members"]]
        assert any(i.startswith("sys@msg0.") for i in plain)
        # --no-force: the v0.2.1 report, the edit only a precondition
        rc = cli.main(args + ["--no-force", "--out", str(tmp_path / "runs2")])
        capsys.readouterr()
        rep2 = json.loads(next((tmp_path / "runs2").glob("*.why.json")).read_text())
        assert rc == 0 and rep2["preconditions"][0]["steers"] is None
        assert not any(c["forced"] for c in rep2["causes"]) and rep2["forcing"]["unavailable"] == "--no-force"
