# Phase 6 — ground truth independent of the method

Plan and exit gate: [docs/ROADMAP.md](../../docs/ROADMAP.md#phase-6--ground-truth-independent-of-the-method-tier-1-0).

| Item | Status | Where |
|---|---|---|
| 6.1 exhaustive coalition tables | **done**: 250 cases × 2 models, scored per regime | [results/qwen3-14b](results/qwen3-14b/summary.md), [results/llama3.1-8b](results/llama3.1-8b/summary.md) |
| 6.2 pilot (10 cases, Qwen3-14B and Llama-3.1-8B) | **done**: about 1 h of tables per model for 250 cases | [results/pilot-qwen3-14b](results/pilot-qwen3-14b/summary.md), [results/pilot-llama3.1-8b](results/pilot-llama3.1-8b/summary.md) |
| 6.3 Llama's neutral lines | **answered**: real interactions (a probe is a carrier in 14% of cases), ctxblame blames table-neutral probes in 1% of rows | `score6.py` (`neutral probe blamed`, regime `probe_interaction`) |
| 6.4 E-coupled cases | **offline done, GPU scoring pending**: E forced by `tool_choice` in the engine and in the truth (below) | `blame.py` (`force_tool_choice`, `Cause.steers`), `tables.py --forced`, `truth.py` |

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

## 6.1 / 6.3: the full suite (2026-11-28)

Setup:
- 250 cases, all 2^m removals, N = 50 replays per cell: 234,000 replays per model, nothing dropped.
- Then ctxblame (defaults, the 5.6 engine) with 3 seeds on the same cases, no oracle filter.
- One RTX 5090 per model, vLLM 0.34.0, sampling as in `v0.2`.

| | Qwen3-14B-FP8 | Llama-3.1-8B |
|---|---:|---:|
| tables (wall, replays/s) | 53 min, 74/s | 42 min, 93/s |
| ctxblame, per seed | 23 min | 22 min |
| ambiguous cells per case (of 18.7) | 1.2 | 2.0 |
| cases the Phase 3 oracle would keep | 146 / 250 | 114 / 250 |

**ctxblame against the tables** (case × seed rows; F1 over planted elements):

| group | Qwen3-14B F1 | Llama-3.1-8B F1 | `v0.2` (oracle-filtered) |
|---|---:|---:|---:|
| oracle-valid | **95%** (146 cases) | **85%** (114) | 95% / 85% |
| oracle-dropped | 71% (104) | 44% (136) | not measured |
| all 250 | 87% | 66% | – |

Other columns, Qwen / Llama:
- Preconditions separated: 54% / 67% overall, 95% / 79% on oracle-valid cases.
- Preconditions blamed as causes: 5% / 1%.
- Table-neutral probes blamed: 3% / 1%.
- Negatives correct: 80% / 94%.

| regime (cases, Qwen / Llama) | Qwen3-14B F1 | Llama-3.1-8B F1 |
|---|---:|---:|
| single (85 / 87) | 97% | 80% |
| precondition_gated (49 / 52) | 94% | 74% |
| or (100 / 75) | 81% | 65% |
| and (4 / 19) | 83% | 55% |
| e_coupled (50 / 9) | 46% | 14% |
| non_monotone (30 / 25) | 45% | 34% |
| probe_interaction (34 / 35) | 46% | 31% |
| mixed (4 / 28) | 45% | 34% |

A case can be in several regimes. Full tables:
[qwen3-14b/summary.md](results/qwen3-14b/summary.md) and
[llama3.1-8b/summary.md](results/llama3.1-8b/summary.md).

What this shows:
- **On the cases `v0.2` could validate, the numbers hold under independent truth:**
  95% and 85%, the same as `v0.2`. The oracle's selection did not inflate them.
- **The oracle dropped the hard part of the problem.** 42% (Qwen) and 54% (Llama)
  of cases fail its validity rule. On them, F1 falls to 71% and 44%. The failures
  concentrate where monotone search assumptions break: `e_coupled`,
  `non_monotone`, `probe_interaction`, `mixed`.
- **6.3, Llama's neutral lines are real.** A planted probe is in a minimal carrier
  set in 35 of 250 Llama cases (14%; Qwen 34). Probes the table calls neutral are
  blamed in 1% of Llama rows. So `v0.2`'s Llama gap was not ctxblame blaming
  neutral lines. Llama's choices really do depend on them, and ctxblame mostly
  *misses* those interactions (recall 24% on `probe_interaction`).
- **6.4 is the main open problem on Qwen.** 50 of 250 Qwen cases (20%, against
  10% by design) have a `triggers_and_steers` element. There ctxblame separates
  preconditions in only 10% of rows and blames a pure precondition as a cause in
  23%, and F1 is 46%. The matched
  `tool_choice` intervention is next.

**Scoring correction before commit.** The as-run `summary.md` reported
negatives correct 26% (Qwen) and 90% (Llama). The scorer counted any reported
cause as a failure on a truth-negative case. But the tables judge only the
planted elements, as the scorer's own docstring says for precision.
- On Qwen, 45 of 48 `habit_negative` rows blamed one unplanted line, "You are a
  careful coding agent working in a Python repository."
- Direct replays (`p6/0-092`, N = 40, diagnostic) show it is a real cause: 40×
  `pytest` with the line, 40× `npm test` without it.

`negative_ok` now counts planted elements only (test added). The unplanted
members stay in their own column, and every other column is unchanged. So the
`habit_negative` design is not a habit for Qwen: the role line carries the
choice, and Phase 7 cases should plant it as an element.

## 6.4: E forced by `tool_choice` (offline done; GPU scoring pending)

**Why.** On the 250-case tables, ctxblame scores 46% (Qwen) and 14% (Llama) F1 on
`e_coupled` cases. Reading the rows:
- **About half of Qwen's `e_coupled` rows have no carrier in the truth.** The planted
  rule is only in a precondition set. Removing it stops E, so the unforced table
  cannot say whether it also steers the choice. ctxblame mostly reports it as a
  cause there. Neither side is measured: the truth needs forcing as much as the engine.
- **The 5.6 `coupled` flag does not hold up against the tables.** Of the 23 coupled
  members that map to a planted element, 11 are carriers, 9 are table-neutral and
  3 are preconditions (43 more are unplanted). `triggers_and_steers suspected`
  never fired on the suite.
- **Other misses are outside 6.4.** For example, `0-1026`'s 3-way OR bundle needs 6
  chunks, more than `max_members`, so the search stops as "diffuse".

**Feasibility, on the GPU (2026-11-28).** vLLM 0.34 honours a named `tool_choice` with
both the `hermes` (Qwen) and `llama3_json` parsers. On `0-1002` with `c1`+`c2`
removed:
- Qwen unforced: 15× `bash git status`, 5× `read_file`.
- Qwen forced: 20× `bash git status`, so P(A | do(E), do(-S)) = 0/20 against a
  forced baseline of 20/20.

**Engine** (`blame.py`, default on, `--no-force` for v0.2.1 behaviour):
- **When E can be forced.** Only when E is a tool name among the request's tools,
  and not on Anthropic with extended thinking. Otherwise the report says why.
- **Forced baseline.** P(A | do(E)) is measured once (`max_n` replays). Forced
  tests use half of it as their threshold. If forcing changes the choice even with
  the whole context (below 0.5), or the provider ignores `tool_choice`, nothing is
  forced.
- **Preconditions.** Each confirmed precondition is replayed with E forced. A flip
  makes it a cause *with E forced* (`Cause.forced`), audited on fresh forced replays
  (`forced_flip` / `forced_restore` tests, in the same Holm family). If that cause
  survives the audit, the precondition is `steers: true` (`triggers_and_steers`);
  if the forced choice is kept, `steers: false`.
- **`coupled` members.** A member whose leave-one-in test stops E gets its
  restoration tested with E forced. If it restores, stage 2 tests that; if the
  choice clearly does not come back, it is dropped. Otherwise the 5.6 collapse
  test is kept.
- **Stabilizers.** A forced removal that flips starts a forced search for the
  steering lines. This is the `run4/step21` tool description.

**Truth** (`tables.py --forced --base-tables <finished tables/>`, written to a
**new** results dir, `<tag>/forced/`):
- Every removal of each gated case (a case with a precondition set) is replayed with
  E forced.
- `truth.label(forced=…)` marks a precondition element `triggers_and_steers` if it
  is in a minimal *steer set* (a minimal removal whose forced cell flips).
- Carriers outside every precondition set keep their unforced definition.
- Forced cells are not used if the forced base is below 0.5 or has fewer than 10
  replies in E.
- Relabelling all 520 committed tables without forced cells reproduces them
  exactly.

**Null simulation v4**
([results/null-sim-v4](../phase5/results/null-sim-v4/null_sim.json), 500 runs, the
real `Tester` and `search` with a simulated model that honours `tool_choice`):

| scenario | audit off | audit on (n=20, α=0.05) | replays/run |
|---|---:|---:|---:|
| `tas_power` (X triggers and steers), power | 100% | **100%** | 120 → 160 |
| `pure_precondition`, any false cause | 0.0% | **0.0%** | 107 → 127 |
| `boundary_tas` (forced choice at the threshold), any false cause | 3.2% | **0.2%** [0.0, 1.1] | 122 → 143 |
| `coupled_power`, power (unforced, as v3) | 100% | 97% | 90 → 210 |
| `coupled_forced`, power | 100% | **97%** | 90 → 244 |
| `boundary_coupled`, any false cause (unforced, as v3) | 98.2% | 3.8% | 187 → 334 |
| `boundary_coupled_forced`, any false cause | 98.2% | **3.8%** [2.4, 5.9] | 187 → 335 |

The unforced rows reproduce v3 exactly, so the default path without a tool-level E
is unchanged.

On these two coupled scenarios, forcing neither gains nor loses on power or error:
the simulated coupled member restores the choice with E forced. Its purpose is the
other case, a member that only looks coupled (like the 9 table-neutral ones). There
the forced test drops it (`tests/test_stats.py`). Whether that happens on real
models is what the GPU run measures.

**GPU runs, about 2 h on the 2 × 5090 box.** Each driver line below is launched as in
`AGENTS.md`.

```sh
# GPU 0 and GPU 1 side by side: forced tables of the gated cases, ctxblame on all 250, scores
CUDA_VISIBLE_DEVICES=0 PORT=8000 FORCED_FROM=qwen3-14b MODEL=/root/autodl-tmp/models/Qwen3-14B-FP8 \
  NAME=Qwen3-14B TAG=p64-qwen3-14b experiments/phase6/run_p6.sh
CUDA_VISIBLE_DEVICES=1 PORT=8001 FORCED_FROM=llama3.1-8b MODEL=/root/autodl-tmp/models/Llama-3.1-8B-Instruct \
  NAME=Llama-3.1-8B TAG=p64-llama3.1-8b TOOL_PARSER=llama3_json \
  SERVE_ARGS="--chat-template experiments/phase6/llama31_tool_template.jinja" \
  EXTRA_BODY='{"temperature": 0.6, "top_p": 0.9}' experiments/phase6/run_p6.sh
# then on GPU 0: the v0.2 cases with forcing on (regression against p5d)
SKIP_SERVE=1 MODEL=/root/autodl-tmp/models/Qwen3-14B-FP8 RUNS="real64 gen64" experiments/phase5/run_p5.sh
```

The Phase 6 runs write three summaries:
- `summary.md`: the new engine on the forced truth.
- `summary_<base>_engine.md`: the committed 5.6 engine on the forced truth.
- `summary_unforced_truth.md`: the new engine on the unforced truth.

So the change in F1 can be split into the part that comes from the engine and the
part that comes from the truth.

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
