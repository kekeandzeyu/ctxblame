@AGENTS.md

## Claude Code Notes

- Follow all architecture, testing, cost-cap, and benchmark-integrity rules in `AGENTS.md` above (keep `AGENTS.md` as the single source of truth rather than duplicating rules here).
- Run `uv run pytest -q` and `uv run python experiments/phase3/benchmark.py --dry-run` before finishing any code or benchmark change.
- When working on request chunking (`src/ctxblame/blame.py:chunk_request`), remember that Claude Code and similar harnesses inject `<system-reminder>` blocks inside `role: "user"` messages alongside `tool_result` blocks—always test both Anthropic `/v1/messages` and OpenAI `/chat/completions` wire formats.
