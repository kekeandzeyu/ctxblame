# Phase 6 — ground truth independent of the method

Plan and exit gate: [docs/ROADMAP.md](../../docs/ROADMAP.md#phase-6--ground-truth-independent-of-the-method-tier-1-0).

| Item | Status | Where |
|---|---|---|
| 6.1 exhaustive coalition tables | code done, tested offline with a simulated model | `cases6.py`, `tables.py`, `truth.py` |
| 6.2 pilot (10 cases, Qwen3-14B and Llama-3.1-8B) | **done**: about 1 h of tables per model for 250 cases | [results/pilot-qwen3-14b](results/pilot-qwen3-14b/summary.md), [results/pilot-llama3.1-8b](results/pilot-llama3.1-8b/summary.md) |
| 6.3 Llama's neutral lines | probes in every case; needs the Llama run | `score6.py` (`neutral probe blamed`, regime `probe_interaction`) |
| 6.4 E-coupled cases | `e_coupled` design cases and `triggers_and_steers` roles in the truth | `truth.py` |

## Method

Each case plants m ≤ 5 **elements**: the choice carriers, a workflow
precondition if any, and 1–3 neutral **probes**. A probe is a line already in the
case (a filler repository rule, a filler line of CONTRIBUTING.md, a distractor
tool call), so no new text is added to make it neutral.

`tables.py` replays all 2^m removals of the elements, with a fixed N = 50
replays each, no adaptive stopping, and every request of a case in flight
together. `truth.py` reads the Boolean functions of P(E) and P(A | E) off the
table at the engine's thresholds (half the base rates, 95% Wilson intervals;
straddling cells are `ambiguous`). From them it derives:
- minimal carrier sets and minimal precondition sets;
- a role for each element: carrier, precondition, `triggers_and_steers`
  (both) or neutral;
- the regimes: negative, single, or, and, mixed, precondition_gated, e_coupled,
  non_monotone, probe_interaction.

Nothing is dropped. The Phase 3 oracle's validity rule is recomputed from each
table (`score6.oracle_valid`), so the subset `v0.2` would have kept is scored
separately.

The case designs, which are only used to stratify the suite (`cases6.py`, 250
cases): single/or 40%, precondition-gated 20%, and 12%, e_coupled ("open" style)
10%, conflict (a stale doc line names another command) 10%, habit-negative 8%.

## 6.2 pilot (2026-11-28)

The first 10 cases of the suite, tables only (N = 50, concurrency 128).
- Box: one RTX 5090 per model.
- vLLM 0.34.0, without FlashInfer or DeepGEMM kernels on this box (no `flashinfer-cubin`, nvcc 12.8).
- Sampling as in `v0.2`.

| model | replays | wall | replays/s | ambiguous cells/case | oracle-valid | est. tables for 250 cases |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3-14B-FP8 | 10,800 | 142 s | 76 | 0.1 | 6/10 | 1.0 h |
| Llama-3.1-8B | 10,800 | 115 s | 94 | 1.8 | 5/10 | 0.8 h |

Sizing:
- Tables are cheap, so the suite stays at 250 cases with N = 50.
- The ctxblame seeds dominate the run time: about 35 min per seed at `p5c`'s 68 s/case and 8 cases in parallel.
- A full model is about 3 h. Qwen and Llama run side by side, one per GPU (`CUDA_VISIBLE_DEVICES`, `PORT`).

What the 10 tables already show (to be confirmed on 250):
- 4 of 10 Qwen cases and 5 of 10 Llama cases fail the Phase 3 oracle's validity rule. `v0.2` would have dropped them.
- The tables do not always match the case designs:
  - `0-1004` (system+tooldesc+user): the tool-description line is not a carrier for Qwen.
  - `0-1007` (one user carrier): Qwen needs a neutral probe together with the carrier (`and`, `probe_interaction`); for Llama it is a habit (negative).
- **6.3, early signal.** Llama has `probe_interaction` in 2 of 10 cases (`0-1002`, `0-1004`: a probe in a minimal carrier set) and Qwen in 1. So some of Llama's "neutral" lines are real interactions, not only ctxblame false positives.

## Running

On a GPU box with vLLM 0.34.0:

```sh
# 6.2 pilot: 10 cases, tables only, to measure throughput. Writes summary.md with the
# regimes, replays/s and the estimated hours for the CASES-case suite (score6.py, no benchmark.json)
MODEL=/models/Qwen3-14B-FP8 NAME=Qwen3-14B TAG=pilot-qwen3-14b LIMIT=10 SEEDS= \
  PY=.venv/bin/python VLLM=.venv/bin/vllm experiments/phase6/run_p6.sh
# on a 2-GPU box, a second run side by side: its own GPU and port
CUDA_VISIBLE_DEVICES=1 PORT=8001 MODEL=... TAG=... experiments/phase6/run_p6.sh
# full suite: tables, ctxblame (3 seeds) on the same cases, score
MODEL=... NAME=Qwen3-14B TAG=qwen3-14b experiments/phase6/run_p6.sh
uv run python experiments/phase6/score6.py experiments/phase6/results/qwen3-14b/tables \
  experiments/phase6/results/qwen3-14b/seed*/benchmark.json
# Llama-3.1-8B (6.3): llama3_json parser, the committed patched template, v0.2 sampling
MODEL=/models/Llama-3.1-8B-Instruct NAME=Llama-3.1-8B TAG=llama3.1-8b TOOL_PARSER=llama3_json \
  SERVE_ARGS="--chat-template experiments/phase6/llama31_tool_template.jinja" \
  EXTRA_BODY='{"temperature": 0.6, "top_p": 0.9}' experiments/phase6/run_p6.sh
```

`llama31_tool_template.jinja` is vLLM v0.34.0's Llama 3.1 JSON tool template.
The only change is that a history turn with several tool calls is rendered as
`; `-separated calls instead of raising. The Phase 3 Llama run used a patched
template that was not committed. This one is committed so the run can be
reproduced; Phase 6 cases have no parallel calls, so the patch does not touch
them.
