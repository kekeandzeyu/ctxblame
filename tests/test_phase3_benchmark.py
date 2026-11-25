"""Tests for the Phase 3 attribution benchmark (cases, dry-run, and all 4 methods)."""

import json
import sys
from pathlib import Path

from aiohttp import web

from test_replay import ServerThread, openai_resp

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "experiments" / "phase3"))

import benchmark  # noqa: E402
from cases import all_cases  # noqa: E402


def test_phase3_dry_run_validates_all_cases(capsys):
    cases = all_cases()
    assert len(cases) >= 9
    assert benchmark.dry_run(cases) == 0
    out = capsys.readouterr().out
    assert "FAIL" not in out
    assert "p3/precond_2or_pnpm" in out
    assert "p3/negative_habit_only" in out


def _make_bench_server():
    """Fake OpenAI server that handles both tool-call replays and self-explanation prompts."""
    async def handler(request):
        body = await request.json()
        raw = json.dumps(body)
        # Self-explanation prompt has no tools
        if not body.get("tools"):
            # Deliberately hallucinates a chunk on negative control, gets partial ID on pnpm
            if "git status" in raw:
                content = '{"chunk_ids": ["sys@msg0.p2"]}'
            else:
                content = '<think>thinking...</think>```json\n{"chunk_ids": ["sys@msg0.p2"]}\n```'
            return web.json_response({
                "id": "c", "object": "chat.completion", "model": body["model"],
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": content}}],
                "usage": {"prompt_tokens": 500, "completion_tokens": 20},
            })

        # Replay for p3/precond_2or_pnpm
        if "package.json" in raw:
            if "edited package.json" not in raw:
                resp = openai_resp("edit_file", "")
                resp["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = json.dumps(
                    {"path": "package.json", "old_string": "a", "new_string": "b"})
            elif "pnpm install --frozen-lockfile" in raw:
                resp = openai_resp("bash", "pnpm install --frozen-lockfile")
            else:
                resp = openai_resp("bash", "npm install")
            resp["model"] = body["model"]
            return web.json_response(resp)

        # Replay for p3/negative_habit_only
        resp = openai_resp("bash", "git status")
        resp["model"] = body["model"]
        return web.json_response(resp)

    app = web.Application()
    app.router.add_post("/v1/chat/completions", handler)
    return app


def test_phase3_benchmark_end_to_end_all_four_methods(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with ServerThread(_make_bench_server()) as base:
        rc = benchmark.main([
            "--base-url", base + "/v1",
            "--model", "Qwen/Qwen3-8B",
            "--free",
            "--no-thinking-param",
            "--only", "precond_2or_pnpm", "negative_habit_only",
            "--controls", "0",
            "--ledger", str(tmp_path / "spend.jsonl"),
            "--out-dir", str(tmp_path / "out"),
        ])
    assert rc == 0
    md = (tmp_path / "out" / "benchmark.md").read_text()
    rows = json.loads((tmp_path / "out" / "benchmark.json").read_text())
    by_key = {(r["case"], r["method"]): r["score"] for r in rows}

    # On precond_2or_pnpm:
    # - ctxblame recovers 2/2 redundant carriers with 100% precision and separates edit_file precondition
    s_cb = by_key[("p3/precond_2or_pnpm", "ctxblame")]
    assert s_cb["recall"] == 1.0 and s_cb["precision"] == 1.0
    assert s_cb["precond_found"] is True and s_cb["precond_fp"] is False
    assert s_cb["cost"] == 0.0

    # - ctxblame_uncond and loo get confounded by edit_file (precond_fp=True, 0% carrier recall)
    assert by_key[("p3/precond_2or_pnpm", "ctxblame_uncond")]["precond_fp"] is True
    assert by_key[("p3/precond_2or_pnpm", "loo")]["recall"] == 0.0
    assert by_key[("p3/precond_2or_pnpm", "loo")]["precond_fp"] is True

    # - self_explain misses the second carrier (50% recall) and hallucinates on the negative control
    assert by_key[("p3/precond_2or_pnpm", "self_explain")]["recall"] == 0.5
    assert by_key[("p3/negative_habit_only", "self_explain")]["neg_correct"] is False
    assert by_key[("p3/negative_habit_only", "ctxblame")]["neg_correct"] is True
    assert "## Summary by Method" in md and "| ctxblame |" in md
