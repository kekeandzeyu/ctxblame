# AGENTS.md

Instructions for coding and research agents working in `ctxblame`.

## Overview

`ctxblame` is a black-box counterfactual attribution engine ("`git blame` for LLM agent decisions") over standard Anthropic Messages (`/v1/messages`) and OpenAI Chat Completions (`/chat/completions`) wire protocols. It needs no token logprobs or model weights.

### Module Map (`src/ctxblame/`)

- `proxy.py`, `sse.py`: Local HTTP recording proxy (`ctxblame record`). Reassembles streamed SSE replies and strips auth headers before writing `traces/*.jsonl`.
- `formats.py`: Wire-format detection (`anthropic` vs. `openai`), `Decision` / `ToolCall` extraction, and `Usage` accounting (for OpenAI responses, `prompt_tokens` includes `cached_tokens`; subtract `cached_tokens` to get `input_uncached`).
- `match.py`: Discrete action equivalence classes (`intent`, `exact`, `args`, `name`, `--key-arg <arg~regex>`, and `--any-call` parallel call matching).
- `ablate.py`: Structure-preserving JSON context ablation. Pairs `tool_use` + `tool_result` (and `tool_calls` + `role: tool`), drops empty turns, merges adjacent same-role messages, rotates `tool_use` IDs when stripping `thinking` blocks (preventing server-side reasoning caches from restoring removed thoughts), validates the resulting request, and pins Anthropic `cache_control` breakpoints at the frozen prefix (`pin_cache_breakpoints`).
- `blame.py`: Coarse/line chunking (`chunk_request`, harness-injected `<system-reminder>` blocks as `injected` chunks), sequential `Tester`, conditional blame $P(A \mid E)$ (`--given`, `decide_conditional`), KV-cache-stratified suffix-first `ddmin`, leave-one-in hitchhiker pruning (`_prune_bundle`), diffuse-precondition stabilizer (`_stabilizer`), random same-size controls, and the fresh-replay audit stage (`Tester.audit`, `audit_findings`).
- `stats.py`: Exact binomial tails and Holm adjustment for the audit.
- `replay.py`, `pricing.py`: Async HTTP replay runner, Wilson intervals, model pricing table, and persistent hard USD spend cap (`Ledger` at `.ctxblame/spend.jsonl`).
- `trace.py`, `cli.py`: Trace reader and CLI subcommands (`record`, `steps`, `replay`, `why`).

## Commands & Zero-Cost Verification

- **Python & packaging:** Python `>=3.12`, managed via `uv`. Runtime dependencies in `pyproject.toml` are intentionally minimal (`aiohttp` only). **Do not add new runtime dependencies** without explicit approval (`numpy` in `experiments/phase3/analyze.py` is invoked via `uv run --with numpy`).
- **Run unit tests (`$0`, offline, ~1.5s):**
  ```sh
  uv run pytest -q
  ```
- **Validate benchmark cases & chunking offline (`$0`, no server required):**
  ```sh
  uv run python experiments/phase3/benchmark.py --dry-run
  ```
- **Run against a local or Colab `vLLM` server (`$0`):**
  Pass `--base-url http://127.0.0.1:8000/v1 --free --no-thinking-param` (see `experiments/phase3/serve_vllm.sh` and `experiments/phase3/run_model.sh`).

## Hard Guardrails

1. **Spend & Credential Safety:**
   - Never bypass `Ledger` (`--budget`, default `$5.00`) or launch paid frontier API replays (`DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) without user confirmation.
   - Never commit `traces/`, `runs/`, `.ctxblame/`, `dist/`, or any prompt dump containing credentials.
2. **Experimental & Benchmark Integrity:**
   - Committed artifacts under `experiments/*/results/` and `experiments/*/results/traces/` are immutable provenance backing [docs/WRITEUP.md](docs/WRITEUP.md) and [experiments/phase3/RESULTS.md](experiments/phase3/RESULTS.md). Do not overwrite existing result directories; write new runs under a fresh `<tag>/` directory.
   - Quantitative benchmark traces **must** come from wire-exact proxy capture (`ctxblame record` / `wrap`), never from lossy reconstructed local CLI transcripts.
   - Keep adaptive search draws strictly separate from confirmation/audit draws when implementing statistical guarantees, and keep workflow preconditions ($P(E)$ collapse) distinct from choice carriers ($P(A \mid E)$ flip) and positivity-violating coupled causes (`triggers_and_steers`).
3. **Code & Documentation Hygiene:**
   - Keep changes minimal, typed, and covered by offline tests under `tests/`.
   - Maintain a **single canonical roadmap** in [docs/ROADMAP.md](docs/ROADMAP.md):
     - [README.md](README.md) — user-facing CLI quickstart and concise next-step summary.
     - [docs/WRITEUP.md](docs/WRITEUP.md) — `v0.2` technical writeup and empirical findings.
     - [docs/ROADMAP.md](docs/ROADMAP.md) — next-stage research, benchmark, and `v0.3` engineering plan (do not create duplicate `PLAN.md` or `PEER_REVIEW.md` files).
     - [experiments/phase3/RESULTS.md](experiments/phase3/RESULTS.md) — Phase 3–4 benchmark tables and reproduction commands.
