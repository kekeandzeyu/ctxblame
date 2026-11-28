# AGENTS.md

Instructions for coding and research agents working in `ctxblame`.

## Overview

`ctxblame` is a black-box counterfactual attribution engine ("`git blame` for LLM agent decisions") over standard Anthropic Messages (`/v1/messages`) and OpenAI Chat Completions (`/chat/completions`) wire protocols. It needs no token logprobs or model weights.

### Module Map (`src/ctxblame/`)

- `proxy.py`, `sse.py`: Local HTTP recording proxy (`ctxblame record`). Reassembles streamed SSE replies and strips auth headers before writing `traces/*.jsonl`.
- `formats.py`: Wire-format detection (`anthropic` vs. `openai`), `Decision` / `ToolCall` extraction, and `Usage` accounting (for OpenAI responses, `prompt_tokens` includes `cached_tokens`; subtract `cached_tokens` to get `input_uncached`).
- `match.py`: Discrete action equivalence classes (`intent`, `exact`, `args`, `name`, `--key-arg <arg~regex>`, and `--any-call` parallel call matching).
- `ablate.py`: Structure-preserving JSON context ablation. Pairs `tool_use` + `tool_result` (and `tool_calls` + `role: tool`), drops empty turns, merges adjacent same-role messages, rotates `tool_use` IDs when stripping `thinking` blocks (preventing server-side reasoning caches from restoring removed thoughts), validates the resulting request, and pins Anthropic `cache_control` breakpoints at the frozen prefix (`pin_cache_breakpoints`).
- `blame.py`: Coarse/line chunking (`chunk_request`, harness-injected `<system-reminder>` blocks as `injected` chunks), sequential `Tester`, conditional blame $P(A \mid E)$ (`--given`, `decide_conditional`), KV-cache-stratified suffix-first `ddmin`, leave-one-in hitchhiker pruning (`_prune_bundle`), diffuse-precondition stabilizer (`_stabilizer`), random same-size controls, the fresh-replay audit stage (`Tester.audit`, `audit_findings`), and forced-E tests (6.4: `force_tool_choice`, `Tester(force_tool=…)`, `Cause.forced` / `Cause.steers`; `--no-force`).
- `stats.py`: Exact binomial tails and Holm adjustment for the audit.
- `replay.py`, `pricing.py`: Async HTTP replay runner, Wilson intervals, model pricing table, and persistent hard USD spend cap (`Ledger` at `.ctxblame/spend.jsonl`).
- `wrap.py`: `ctxblame wrap -- <cmd>`: two recording proxies on ephemeral ports sharing one trace, with `ANTHROPIC_BASE_URL` / `OPENAI_BASE_URL` injected into the command (existing values become the upstreams).
- `trace.py`, `cli.py`: Trace reader and CLI subcommands (`record`, `wrap`, `steps`, `replay`, `why`).

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

### Remote GPU Runs (launching and watching a VM)

Host, port, and password are given per session by the user. Never write them into the repo, commits, or memory.

- **Launch detached:** `cd <repo> && setsid nohup <driver, e.g. experiments/phase5/run_p5.sh> > ../logs/<run>.log 2>&1 < /dev/null & disown`. Logs go to `<repo>/../logs/`, the `LOGS` default in `run_model.sh`. If a local ssh/expect call stays open after the launch, stop the local call; the remote job survives.
- **Check the first minute, not just the end.** Run the status check about 60 s after launch and confirm `bench=up` and that `cases_started` is rising. In Phase 5.5 a `set -e` failure killed the driver 30 s in, and the GPU sat idle for hours.
- **Status check** (on the VM, over ssh): `experiments/phase3/vm_status.sh [tag-prefix]`.
  - The first line is machine-readable: `job= bench= vllm= gpu=util%,MiB[;…per GPU] benchErr= vllmErr=`.
  - Then it prints seeds finished per tag (`seed*/benchmark.json`, plus `summary` when done), `cases_started` per `bench_*.log`, and driver log tails.
  - It exits 1 when something needs attention: errors or tracebacks in `bench_*`, `oracle_*` or `vllm_*` logs; vLLM down while a benchmark runs; or the driver gone while a tag it started has no `summary.md`.
- **Watching:** poll `vm_status.sh` every few minutes from a background task. Wake on exit 1 (inspect the `-- errors` tail before restarting anything) and on each new driver-log line (seed or run finished). After a wake, re-arm the watcher until the last run's `summary.md` exists. The watcher must retry until its baseline milestone count is a number. A failed first ssh read once left it comparing against an empty baseline, and it slept for hours past the end of the run.
- **Restarting:** `run_model.sh` skips seeds whose `benchmark.json` exists. Relaunch the same driver with `SKIP_SERVE=1` to reuse a live vLLM server on `:8000`. Never delete or overwrite a finished tag.
- **Two GPUs:** run one server per GPU with `CUDA_VISIBLE_DEVICES=<i> PORT=<800i>` on `run_model.sh` / `run_p6.sh`. Each driver only kills the server on its own port and writes `$LOGS/driver_<tag>.pid`. Check each run with `PORT=<port> vm_status.sh <tag-prefix>`, which reports a driver as gone by its pid even while the other run keeps `job=up`.
- **Never overwrite a script a driver is executing.** Bash reads scripts as it runs them, so an in-place copy (`scp`) can corrupt a live run. Deploy by writing a temp file and renaming it over the old one (`mv`), and leave a running driver's scripts alone until it finishes.
- **Model weights in China-hosted VMs:** HF through the cluster proxy is slow. Fetch shards from ModelScope (`curl --noproxy "*"`, shards in parallel) and verify each against the HF LFS sha256 (`huggingface.co/api/models/<repo>/tree/main`) before serving.
- **Provenance:** confirm the vLLM version matches the run being reproduced (the traces' `system_fingerprint`; `v0.2` = `vllm-0.34.0`). Copy results back into a fresh `experiments/phase3/results/<tag>/`.

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
