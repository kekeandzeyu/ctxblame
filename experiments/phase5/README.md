# Phase 5 — engine correctness and valid statistics

Plan and exit gate: [docs/ROADMAP.md](../../docs/ROADMAP.md#phase-5--engine-correctness-and-valid-statistics-0-offline--one-re-run).

| Item | Status | Where |
|---|---|---|
| 5.1 injected `<system-reminder>` blocks are chunks; only the user's own text is the task | done, offline | `blame.py:chunk_request`, `tests/test_blame.py` |
| 5.2 stabilizer instead of stopping when preconditions run out or are diffuse | done offline; real-case acceptance in 5.5 | `blame.py:_stabilizer`, `search` |
| 5.3 search/audit split with FWER control | done, null simulation below | `blame.py:Tester.audit`, `audit_findings`, `stats.py`, `null_sim.py` |
| 5.4 Anthropic `cache_control` pinning | done, offline | `ablate.py:pin_cache_breakpoints` |
| 5.5 GPU re-run of Qwen3-14B | repro passes; `real`, `gen` running | `run_p5.sh` |

## 5.1: chunking is unchanged on every existing case

Chunk ids, spans, units, children and texts are byte-identical to `v0.2` for all
5,090 chunks of the `core`, `gen`, `gen-open`, `gen-long` and `real` suites, so
5.1 cannot move any `v0.2` number; it changes only requests that contain
injected blocks (Claude Code, Cline).

## 5.2: what actually stopped `real/run4/step21`

The `v0.2` reports show the stratified search never reached the diffuse
`break`: in all 3 seeds it isolated three one-line preconditions in `read_file`
outputs (removing any of several scattered lines stops the agent from testing),
hit `max_preconditions = 3`, and stopped before the choice search. The fix
covers both exits.

**5.2b, found by the GPU run** (`p5-real-qwen3-14b`, seed 0). The stabilizer
worked: it kept 9 `read_file` lines, and with them kept, removing the other 41
chunks left E intact and flipped the choice (0 of 8 calls kept `--tb=line`). The
loop then restarted its suffix-tier probe. Removing only the last 14-chunk tier
**stopped** E, because E is non-monotone in what is removed (a late output
without the history that explains it). With the stabilizer already used, the
search stopped before any choice test, and the audit then correctly rejected all
three noisy preconditions (p = 0.59 to 0.99).

A first fix (a5f5461) searched the whole rest as one region after a stabilizer.
On the GPU (`p5b-real`, seed 0, stopped after one seed) it failed. Most partial
removals of this trace's history stop E, so plain ddmin could not shrink below
38 chunks ("diffuse"), at 3,710 replays.

The fix that replaces it keeps the stratified tiers (tool schemas, system prompt,
early and late history), which is what separated the carriers in the one seed the
pre-fix engine solved. After a stabilizer, the suffix probe only changes its
stopping rule: it widens past tiers whose removal stops E and stops at the first
flip. Removing all of the rest is known to flip, so it always reaches one. The
stratified ddmin counts collapses as "not flipped". `p5c-real` and `p5c-gen` run
this final engine.

**Result on `real/run4/step21` with the final engine** (`p5c-real`). The stabilizer now
always hands over to the choice search, and the case is still unsolved in all 3
seeds:

| seed | stabilizer kept | outcome | replays |
|---|---|---|---:|
| 0 | 3 chunks | diffuse: the smallest flipping removal has 10 chunks | 3,040 |
| 1 | 2 chunks | diffuse: 6 chunks | 3,455 |
| 2 | the `bash` tool description | removing all the rest keeps the choice | 820 |

Seed 2 shows the cause. The tool description both enables the action (without it
the agent does not use `bash`) and holds one of the three carriers (the
``e.g. `python -m pytest -q -x --tb=line` `` example). This is the positivity
violation AGENTS.md calls `triggers_and_steers`: a chunk that is a precondition
and a carrier at once. In seeds 0 and 1 the same coupling runs through the
history, so flipping the choice while E survives needs extra removals. The
pre-fix engine's single success (seed 1) was replay luck. Two possible
follow-ups, deliberately not done in Phase 5 to avoid tuning the engine on one
case:
- stabilize at line level, so the example line can separate from the rest of
  the description;
- report `triggers_and_steers` explicitly when the stabilizer contains a
  recorded carrier. The report now says
`none_found` rather than `not_in_context` when removing everything stopped E
instead of keeping the decision. Regression test:
`test_search_after_stabilizer_searches_the_whole_rest_for_the_choice`.
`p5-real` and `p5-gen` ran the pre-fix engine. `p5b-real-qwen3-14b` re-runs
`real` with the fix.

## 5.3: type-I error under least-favourable nulls

`null_sim.py` runs the real `search` and `Tester` (sequential tests,
`apply_chunks`, audit) against a simulated model (baseline 0.9, threshold 0.45).
500 runs per row, seed 0
([results/null-sim-v1/null_sim.json](results/null-sim-v1/null_sim.json)):

| scenario | audit | P(any false cause) [95% CI] | power | replays/run |
|---|---|---:|---:|---:|
| single cause at the boundary | off (v0.2) | 0.4% [0.1, 1.4] | – | 40 |
| single cause at the boundary | n=20, α=0.05 | 0.0% [0.0, 0.8] | – | 41 |
| bundle with a member at the boundary | off (v0.2) | **93.0%** [90.4, 94.9] | – | 160 |
| bundle with a member at the boundary | n=20, α=0.05 | **1.6%** [0.8, 3.1] | – | 234 |
| true 2-way OR bundle | off (v0.2) | 0.0% | 100% | 79 |
| true 2-way OR bundle | n=20, α=0.05 | 0.0% | 99% | 139 |

The `v0.2` failure is not sample reuse but a definition: its leave-one-in check
counts "removing the others does not clearly flip it" as "this member restores
the decision", so a member whose presence brings the rate back only to the
threshold passes. The audit tests restoration itself (rate above the threshold).
The guarantee is conditional on the baseline replays, which set the threshold
and are not reused.

```sh
uv run python experiments/phase5/null_sim.py --runs 500 --out experiments/phase5/results/<tag>/null_sim.json
```

### Two-stage audit (found by `p5-gen` seed 0)

On `gen`, the one-stage audit rejected two bundles that held a true carrier plus a
hitchhiker the search had not pruned (`p0/tool_result_sentence_config`,
`gen/0-013/ruff/doc+user`; both found by `v0.2`). Keeping the hitchhiker alone
cannot restore the choice (p = 1), so the whole bundle failed, and the true
carrier was lost with it.

The audit now runs in two stages:
- **Stage 1:** when a bundle's removal flips but some members do not restore,
  those members are dropped.
- **Stage 2:** the smaller bundle is audited on new fresh replays, and only
  stage 2 gives its p-value.

Stage 1 only chooses the hypothesis, so this is sample splitting and Holm still
covers one final hypothesis per finding.
[results/null-sim-v2](results/null-sim-v2/null_sim.json), 500 runs, seed 0, adds
a `hitchhiker` scenario:

| scenario | audit | P(any false cause) [95% CI] | power | replays/run |
|---|---|---:|---:|---:|
| bundle with a member at the boundary | one-stage (v1) | 1.6% [0.8, 3.1] | – | 234 |
| bundle with a member at the boundary | two-stage | 3.0% [1.8, 4.9] | – | 286 |
| true 2-way OR bundle | two-stage | 0.0% | 99% | 139 |
| carrier + weak line (hitchhiker) | off (v0.2) | 0.4% [0.1, 1.4] | 97% | 111 |
| carrier + weak line (hitchhiker) | two-stage | 0.0% [0.0, 0.8] | 97% | 130 |

The false-cause rate rises in the boundary scenario but stays below α, as theory
predicts. When stage 1 drops the boundary member, stage 2 tests {X, Y}, which
sits exactly on its null boundary and is rejected at most α of the time. The
simulated search rarely leaves the weak line in a bundle (real hitchhikers come
from replay noise), so the hitchhiker scenario does not stress the fix.
`test_audit_drops_a_hitchhiker_and_certifies_the_rest_on_new_replays` covers the
mechanism deterministically.

## 5.5: GPU re-run

On a GPU box with vLLM (48 GB is enough for Qwen3-14B-FP8):

```sh
MODEL=/models/Qwen3-14B-FP8 PY=.venv/bin/python VLLM=/path/to/vllm experiments/phase5/run_p5.sh
uv run --with numpy python experiments/phase3/analyze.py experiments/phase3/results/p5-real-qwen3-14b
```

`repro` must reproduce `v0.2` (`real`: 92% F1 [77, 100]) before the Phase 5 runs
are compared with it.

**Environment check passed**
([p5-repro-real-qwen3-14b](../phase3/results/p5-repro-real-qwen3-14b/summary.md)).
The box was an RTX 4090 48 GB running vLLM 0.34.0, with the official Qwen3-14B-FP8
weights (sha256 verified). It used the `v0.2` behaviour (`--audit-n 0 --no-stabilize`)
on the same 13 oracle-valid `real` cases with 3 seeds.

| | Recall | Precision | F1 [95% CI] | Precond. separated | Precond. blamed | Replays/case |
|---|---:|---:|---:|---:|---:|---:|
| `v0.2` (real-qwen3-14b) | 92% | 92% | 92% [77, 100] | 100% | 0% | 545 |
| repro (p5-repro-real-qwen3-14b) | 92% | 92% | 92% [77, 100] | 100% | 0% | 531 |

Every seed matches `v0.2` (seed F1 92 / 92 / 92).

### `real` with the Phase 5 engine (pre-5.2b code, 6bf5394)

[p5-real-qwen3-14b](../phase3/results/p5-real-qwen3-14b/summary.md): defaults
(`--audit-n 20 --alpha 0.05`, stabilizer on), same 13 cases, 3 seeds.

| | F1 [95% CI] | precondition_or (n=12) | or_redundant (`run4/step21`) | Precond. blamed | Replays/case |
|---|---:|---:|---:|---:|---:|
| `v0.2` | 92% [77, 100] | 100% | 0% | 0% | 545 |
| Phase 5 | **95% [85, 100]** | 100% | 33% (1 of 3 seeds) | 0% | 722 (+32%) |

- **The audit cost nothing on the 12 clean cases.** Every finding there was
  certified (24–26 per seed). All 7 uncertified findings are noisy preconditions
  in `run4/step21` (p = 0.13 to 0.99).
- **`run4/step21` per seed:**
  - seed 1: all 3 carriers found and certified as one bundle (Holm p < 1e-4).
  - seeds 0 and 2: the search stopped right after the stabilizer (the 5.2b bug
    above).
  - The case costs 1,270–2,460 replays (v0.2: about 600).

### `gen` with the Phase 5 engine (pre-fix code, one-stage audit)

[p5-gen-qwen3-14b](../phase3/results/p5-gen-qwen3-14b/summary.md): 48 oracle-valid
`core` + generated cases (same as `v0.2`'s `qwen3-14b-fp8`), 3 seeds.

| | F1 [95% CI] | Precond. blamed | Negatives correct | Replays/case |
|---|---:|---:|---:|---:|
| `v0.2` | 95% [87, 99] | 4% | 100% | 189 |
| Phase 5, one-stage audit | **90% [80, 98]** | 2% | 97% | 230 |

**A regression, and what causes it.** In every seed, two of the misses are bundles
the one-stage audit rejected whole, each holding a true carrier plus a hitchhiker
(`p0/tool_result_sentence_config`, `gen/0-013/ruff/doc+user`). The two-stage
audit above targets these; `p5b-gen` measures it.
`gen/0-037/ruff/tooldesc+doc` is threshold-sensitive, not a regression: the
search is identical to `v0.2`'s, but removing the bundle keeps E only about half
the time (15/30 and 13/30 here; 23/40 and 20/20 in `v0.2`), right at the 0.5
threshold for E. One negative (`gen/0-052/uv/neg`) reports a precondition, which
the scoring counts as wrong even though no cause is blamed.
