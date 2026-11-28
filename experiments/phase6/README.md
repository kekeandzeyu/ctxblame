# Phase 6 — ground truth independent of the method

Plan and exit gate: [docs/ROADMAP.md](../../docs/ROADMAP.md#phase-6--ground-truth-independent-of-the-method-tier-1-0).

| Item | Status | Where |
|---|---|---|
| 6.1 exhaustive coalition tables | **done**: 250 cases × 2 models, scored per regime | [results/qwen3-14b](results/qwen3-14b/summary.md), [results/llama3.1-8b](results/llama3.1-8b/summary.md) |
| 6.2 pilot (10 cases, Qwen3-14B and Llama-3.1-8B) | **done**: about 1 h of tables per model for 250 cases | [results/pilot-qwen3-14b](results/pilot-qwen3-14b/summary.md), [results/pilot-llama3.1-8b](results/pilot-llama3.1-8b/summary.md) |
| 6.3 Llama's neutral lines | **answered**: real interactions (a probe is a carrier in 14% of cases), ctxblame blames table-neutral probes in 1% of rows | `score6.py` (`neutral probe blamed`, regime `probe_interaction`) |
| 6.4 E-coupled cases | **done**: E forced by `tool_choice` in the engine and the truth; `e_coupled` F1 +8.7 pp (Qwen) and +10.2 pp (Llama) over the 5.6 engine, both intervals above 0 | [results/p64c-qwen3-14b](results/p64c-qwen3-14b/summary_choice_sets.md), [results/p64c-llama3.1-8b](results/p64c-llama3.1-8b/summary_choice_sets.md) |

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
  `tool_choice` intervention is 6.4 (below).

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

## 6.4: E forced by `tool_choice` (2026-11-28)

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

**Engine** (`blame.py`, default on, `--no-force` for v0.2.1 behaviour):
- **When E can be forced.** Only when E is a tool name among the request's tools,
  and not on Anthropic with extended thinking. Otherwise the report says why.
  vLLM 0.34 honours a named `tool_choice` with the `hermes` (Qwen) and `llama3_json`
  (Llama) parsers.
- **Forced baseline.** P(A | do(E)) is measured once (`max_n` replays). Forced
  tests use half of it as their threshold, never the unforced P(A | E). If forcing
  changes the choice even with the whole context (below 0.5), or the provider
  ignores `tool_choice`, nothing is forced.
- **Preconditions.** Each confirmed precondition is replayed with E forced. A flip
  makes it a cause *with E forced* (`Cause.forced`), audited on fresh forced replays
  (`forced_flip` / `forced_restore`, in the same Holm family). If that cause is
  certified, the precondition is `steers: true` (`triggers_and_steers`); if the
  forced choice is kept, `steers: false`.
- **`coupled` members.** A member whose leave-one-in test stops E gets its
  restoration tested with E forced. If it restores, stage 2 tests that. If the
  choice clearly does not come back, it is dropped, and when every dropped member
  went this way the rest of the bundle is audited as a forced claim (below).
  Otherwise the 5.6 collapse test is kept.
- **Stabilizers.** A forced removal that flips starts a forced search for the
  steering lines (the `run4/step21` tool description).
- **What replaces A.** Every forced outcome lists what the replies in E did instead
  (`dist`, as intents), and the report prints it: `instead: run git status 12`.

**Truth** (`tables.py --forced --base-tables <finished tables/>`, a new results dir):
- Every removal of each gated case (a case with a precondition set) is replayed with
  E forced, recording [A?, intent, count] per cell.
- *Steer sets* are the minimal removals whose forced cell flips (threshold: half the
  forced base). Forced cells are not used if the forced base is below 0.5 or has
  fewer than 10 replies in E.
- **Choice sets** (6.4b) are the minimal sets among the unforced flips (E intact)
  and the forced flips together. A precondition element in a choice set is
  `triggers_and_steers`.
- Without forced cells, relabelling all 520 committed tables reproduces them
  exactly.

### Results (Qwen3-14B-FP8 and Llama-3.1-8B, vLLM 0.34.0, one RTX 5090 each)

**Forced tables.**
- Qwen: 99 gated cases, 111,200 replays, 26 min. Llama: 61 cases, 76,400 replays, 14 min.
- Run twice, the second time also recording reply intents ([p64-*](results/p64-qwen3-14b),
  [p64b-*](results/p64b-qwen3-14b)). Element roles agree in 426 of 431 (Qwen) and
  273 of 277 (Llama). Every disagreement swaps `precondition` and
  `triggers_and_steers`.
- Forcing relabels many E-collapsing elements as `triggers_and_steers`:
  - Qwen: 37 of 51 planted carriers that looked like preconditions, and 26 of 50
    planted edit preconditions.
  - Llama: 30 of 50 planted edit preconditions.
  - These are counted on the `p64b` tables with choice sets.

**What replaces A** ([forced_alts.md](results/p64b-qwen3-14b/forced_alts.md), a
heuristic over the recorded intents). Removing a planted edit and forcing `bash`
mostly moves the model to another step:
- Llama `0-1042`: `make check` → `git status` / `git diff`.
- Qwen `0-1043`: `pnpm install --frozen-lockfile` → `pnpm add zod`, the same
  package manager.

Removing a planted carrier gives a competing tool (`flake8` for `ruff check --fix`,
`eslint --fix`, `pip install` for `uv sync`) or, for Qwen as often, `git status`.

Both are a flip of A among `bash` calls. That is the estimand the unforced carrier
truth has always used: removing two carriers in `0-1002` also gives
`git status` 50 times out of 50. So a planted edit that makes the model verify
rather than inspect does steer A, and the table says so. The `instead` line lets a
user tell "decides what to do next" from "decides how".

**ctxblame**: 3 seeds on all 250 cases, the 6.4 engine at `570ea68`
([p64c-qwen3-14b](results/p64c-qwen3-14b), [p64c-llama3.1-8b](results/p64c-llama3.1-8b)).
- The comparison is the committed 5.6 engine (`results/<model>/seed*`), scored on
  the same truth.
- The difference is paired over cases (seeds averaged inside a case), with a 95%
  bootstrap interval (`compare6.py`). Negatives are scored apart.

| F1, 6.4 − 5.6 | Qwen, as-run forced truth | Qwen, choice sets | Llama, as-run forced truth | Llama, choice sets |
|---|---:|---:|---:|---:|
| all | +0.9 [−1.2, +2.9] | +2.2 [−0.1, +4.5] | +1.9 [−0.5, +4.3] | +2.0 [−0.4, +4.3] |
| oracle-valid | **+2.2 [+0.5, +4.1]** | **+2.2 [+0.5, +4.1]** | **+3.1 [+1.1, +5.3]** | **+3.2 [+1.2, +5.4]** |
| `e_coupled` | +5.0 [−0.8, +10.4] | **+8.7 [+2.6, +15.0]** | **+10.1 [+4.7, +15.7]** | **+10.2 [+5.0, +15.7]** |
| `non_monotone` | −0.8 [−10.0, +9.0] | +8.6 [−3.7, +21.4] | **+10.5 [+4.3, +18.2]** | **+10.5 [+4.3, +18.1]** |
| `precondition_gated` | −1.0 [−2.9, 0.0] | −1.0 [−2.9, 0.0] | +2.5 [0.0, +6.2] | +2.5 [0.0, +6.2] |

(percentage points; bold: the interval excludes 0)

- `e_coupled` F1 on choice sets, 5.6 → 6.4: Qwen 53% → **62%**, Llama 46% → **56%**.
  On Qwen `e_coupled`, the new engine also blames fewer table-neutral probes (3% vs 8%
  of rows) and fewer unplanted lines (0.16 vs 0.26 per row).
- Negatives are unchanged: correct in 80% / 80% (Qwen) and 95% / 94% (Llama) of rows.
- Scored on the *unforced* truth, the same engine "blames a precondition" in 10%
  (Qwen) and 6% (Llama) of rows. Those are the preconditions the forced tables show
  steering, so an unforced truth would count the improvement as an error.

**Two caveats.**
- **The choice-set rule came after the result.** It was found by reading where the
  engines disagree: `0-1179` and `0-1223` lost an OR carrier `p1` that is minimal
  only because removing `c1` alone collapses E. It follows from the same positivity
  argument as the rest of 6.4, and both engines are rescored on it. But Qwen's
  `e_coupled` gain is significant only under it, so both truths are reported:
  `summary.md` (as run) and `summary_choice_sets.md`.
- **Two audit bugs were found in this run.**
  - The first: after dropping a member that only looked coupled, stage 2 re-audited
    the rest unforced. There, removing it stops E, so nothing could be certified,
    and single-carrier `e_coupled` cases reported nothing (`0-1187`). The fix is
    `570ea68`; the buggy engine's seed 0 is kept in `p64b-*`.
  - The second: the same with two members dropped (`0-1085`). The fix is in
    `4404d8f`, after this run; it affects that one case. Re-run on it alone (3 seeds,
    [p64d-qwen3-14b](results/p64d-qwen3-14b)), the rule is certified as a forced cause
    in every seed, and F1 goes from 0% to 100%.

**Regression on the `v0.2` cases** (Qwen3-14B, 3 seeds, the same oracle-valid cases as
`p5d`; [p64-real](../phase3/results/p64-real-qwen3-14b/summary.md),
[p64-gen](../phase3/results/p64-gen-qwen3-14b/summary.md)):

| F1 [95% CI] | `v0.2` | `p5d` (5.6) | 6.4, as run | 6.4, forced causes set aside |
|---|---:|---:|---:|---:|
| real (13 cases) | 92% [77, 100] | 92% [77, 100] | **92% [77, 100]** | 92% [77, 100] |
| generated + core (48) | 95% [87, 99] | 97% [92, 100] | **92% [85, 97]** | 95% [87, 100] |

- **Real traces.** Nothing is forced there: E is intent-level (`run pytest`), so the
  engine says so and runs as 5.6. `run4/step21` is still `preconditions_only`.
- **Generated cases.**
  - The v0.2 oracle labels each planted edit a pure precondition. With E forced, the
    engine reports 14 of them, over 15 case × seed rows, as "with E forced,
    removing it flips the choice". The forced replies mostly do another step
    (`instead: run git status 20`), the pattern the forced tables measure. So
    "precondition blamed as cause" goes from 7% to 38%, and F1 to 92%, still
    inside the `v0.2` interval.
  - With forced causes set aside, which is the like-for-like v0.2 score (the oracle
    has no forced truth), it is 95% with 7% blamed, as `p5d`
    (`experiments/phase5/rescore_forced.py`; on `p5d` itself it reproduces the
    committed summary exactly).

**Still open after 6.4.**
- Qwen `e_coupled` is at 62%, and `non_monotone` / `probe_interaction` are at 41–50%.
  The remaining misses are mostly searches that stop as "diffuse" (bundles over
  `max_members`) and borderline line-level bundles that fail the fresh audit
  (`0-1135`, `0-1159`).
- An intent-level E (a command family) still cannot be forced.

**Commands** (as run; launched as in `AGENTS.md`, one GPU per model, servers reused with `SKIP_SERVE=1`):

```sh
# forced tables with reply intents (tables only), then ctxblame on all 250 + scores
CUDA_VISIBLE_DEVICES=0 PORT=8000 SKIP_SERVE=1 SEEDS= FORCED_FROM=qwen3-14b MODEL=/root/autodl-tmp/models/Qwen3-14B-FP8 \
  NAME=Qwen3-14B TAG=p64b-qwen3-14b experiments/phase6/run_p6.sh
# p64c-<model>/forced = a copy of p64b-<model>/forced (tables.py skips finished cases)
CUDA_VISIBLE_DEVICES=0 PORT=8000 SKIP_SERVE=1 FORCED_FROM=qwen3-14b MODEL=/root/autodl-tmp/models/Qwen3-14B-FP8 \
  NAME=Qwen3-14B TAG=p64c-qwen3-14b experiments/phase6/run_p6.sh
# Llama the same on GPU 1 / port 8001, with
#   TOOL_PARSER=llama3_json SERVE_ARGS="--chat-template experiments/phase6/llama31_tool_template.jinja"
#   EXTRA_BODY='{"temperature": 0.6, "top_p": 0.9}'
# the v0.2 cases with forcing on (regression against p5d)
SKIP_SERVE=1 MODEL=/root/autodl-tmp/models/Qwen3-14B-FP8 RUNS="real64 gen64" experiments/phase5/run_p5.sh
# offline: rescore on choice sets, compare, alternatives
python experiments/phase6/score6.py results/qwen3-14b/tables results/p64c-qwen3-14b/seed*/benchmark.json \
  --forced results/p64c-qwen3-14b/forced --out score_choice_sets.json
python experiments/phase6/compare6.py <5.6 score.json> <6.4 score.json> --names 5.6 6.4
python experiments/phase6/forced_alts.py results/p64b-qwen3-14b
```

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

The unforced rows reproduce v3 exactly. Re-run after both audit fixes (200 runs),
the forced rows are unchanged within noise (`boundary_coupled_forced` 3.5% [1.7, 7.0]).
The forced claim after a coupled drop is an exact binomial test on fresh forced
replays like every other forced finding. It is covered by unit tests
(`tests/test_stats.py`); no simulated scenario reaches it.

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
