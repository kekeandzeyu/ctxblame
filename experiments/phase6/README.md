# Phase 6 — ground truth independent of the method

Plan and exit gate: [docs/ROADMAP.md](../../docs/ROADMAP.md#phase-6--ground-truth-independent-of-the-method-tier-1-0).

| Item | Status | Where |
|---|---|---|
| 6.1 exhaustive coalition tables | code done, tested offline with a simulated model | `cases6.py`, `tables.py`, `truth.py` |
| 6.2 pilot (10 cases, Qwen3-14B) | waiting for the GPU | `run_p6.sh` with `LIMIT=10` |
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

## Running

On a GPU box with vLLM 0.34.0:

```sh
# 6.2 pilot: 10 cases, tables only, to measure throughput
MODEL=/models/Qwen3-14B-FP8 NAME=Qwen3-14B TAG=pilot-qwen3-14b LIMIT=10 SEEDS= \
  PY=.venv/bin/python VLLM=.venv/bin/vllm experiments/phase6/run_p6.sh
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
