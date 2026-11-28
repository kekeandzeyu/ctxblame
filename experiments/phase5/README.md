# Phase 5 — engine correctness and valid statistics

Plan and exit gate: [docs/ROADMAP.md](../../docs/ROADMAP.md#phase-5--engine-correctness-and-valid-statistics-0-offline--one-re-run).

| Item | Status | Where |
|---|---|---|
| 5.1 injected `<system-reminder>` blocks are chunks; only the user's own text is the task | done, offline | `blame.py:chunk_request`, `tests/test_blame.py` |
| 5.2 stabilizer instead of stopping when preconditions run out or are diffuse | done offline; real-case acceptance in 5.5 | `blame.py:_stabilizer`, `search` |
| 5.3 search/audit split with FWER control | done, null simulation below | `blame.py:Tester.audit`, `audit_findings`, `stats.py`, `null_sim.py` |
| 5.4 Anthropic `cache_control` pinning | done, offline | `ablate.py:pin_cache_breakpoints` |
| 5.5 GPU re-run of Qwen3-14B | done: gate met (final table below) | `run_p5.sh`, `p5c-*` results |
| 5.6 audit: coupled members kept, every bundle re-audited | done offline (null-sim-v3); GPU run `p5d-*` queued | `blame.py:audit_findings`, `null_sim.py` |

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
  recorded carrier.

The report now says `none_found` rather than `not_in_context` when removing
everything stopped E instead of keeping the decision. Regression test:
`test_search_after_stabilizer_searches_the_whole_rest_for_the_choice`.
`p5-real` and `p5-gen` ran the pre-fix engine; `p5b-real` (seed 0) the replaced
first fix; `p5c-*` the final engine.

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

The false-cause rate rises in the boundary scenario but stays below α. *Correction
(5.6):* the reason given here first, that stage 2 alone decides, was wrong for
this design. Stage 2 ran only when stage 1 dropped a member; otherwise stage 1's
own replays certified the bundle, so a false bundle had two chances and the bound
was about 2α, not α. 5.6 removes the second chance. The
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
audit above targets these; `p5c-gen` below measures it.
`gen/0-037/ruff/tooldesc+doc` is threshold-sensitive, not a regression: the
search is identical to `v0.2`'s, but removing the bundle keeps E only about half
the time (15/30 and 13/30 here; 23/40 and 20/20 in `v0.2`), right at the 0.5
threshold for E. One negative (`gen/0-052/uv/neg`) reports a precondition, which
the scoring counts as wrong even though no cause is blamed.

### `gen` with the final engine (two-stage audit, c2c0a96)

[p5c-gen-qwen3-14b](../phase3/results/p5c-gen-qwen3-14b/summary.md): same 48
cases, 3 seeds (seed F1 92 / 95 / 92; `v0.2` 95 / 96 / 93).

| | F1 [95% CI] | Precond. blamed | Negatives correct | Replays/case |
|---|---:|---:|---:|---:|
| `v0.2` | 95% [87, 99] | 4% | 100% | 189 |
| Phase 5, one-stage audit (`p5-gen`) | 90% [80, 98] | 2% | 97% | 230 |
| Phase 5, final engine (`p5c-gen`) | **93% [84, 100]** | 7% | 97% | 237 |

Only six cases differ between the three runs (F1 per seed):

| case | `v0.2` | `p5-gen` | `p5c-gen` |
|---|---|---|---|
| `p0/tool_result_sentence_config` | 1 / 1 / 1 | 0 / 0 / 0 | 0 / 0 / 0 |
| `gen/0-013/ruff/doc+user` | .67 / .8 / .8 | 0 / 0 / 0 | 0 / **1** / 0 |
| `gen/0-037/ruff/tooldesc+doc` | 1 / 1 / 0 | 0 / 0 / 1 | 1 / 1 / 1 |
| `gen/0-045/ruff/history+pre/long` | .5 / .5 / .5 | 1 / 1 / 1 | 1 / 1 / 1 |
| `p3/precond_2or_pnpm` (precondition blamed) | 2 of 3 seeds | 1 of 3 | 3 of 3 |
| `gen/0-052/uv/neg` (negative correct) | 3 of 3 | 2 of 3 | 2 of 3 |

`gen/0-037` came back as predicted (threshold noise). The two-stage audit
recovered `gen/0-013` in one seed only, and `p0` in none. Both misses have the
same cause, and it is not a hitchhiker.

**The stage-1 drop acts on uninformative tests.** In `p0`, the bundle is the
`ls` output line `server.yaml` (`toolu_21.8`) plus the true carrier, the
`server.yaml` read whose result says "this file is no longer read"
(`toolu_22`). Removing both flips the choice with E intact (0/20). The restore
test for `toolu_22` removes only `toolu_21.8`, and that **stops E** (0 of 20
replays still call `Read`), so it says nothing about restoration. Stage 1 counted
it as "does not restore" (p = 1), dropped the true carrier, and re-audited the
`ls` line alone, whose removal alone also stops E. `gen/0-013` seed 2 is the
same: after dropping the file listing `call_13_2` (restore test E-collapsed),
removing just the two carriers kept E in only 3 of 20 replays (p = 0.125). In
`p3/precond_2or_pnpm`, stage 1 dropped `read_pkg` on an E-collapsed test and
certified `edit_pkg`, which the case labels a precondition: this is the whole
rise from 4% to 7%.

These are E-coupled bundles: leave-one-in cannot separate their members,
because removing one member without the other changes E itself. `v0.2`
"found" `p0` only through the lax check that the null simulation showed gives a
93% false-bundle rate. The validity guarantee is unaffected (stage 2 always tests
on new replays). A rule that drops a member only when its restore test keeps E
and fails would revert `p3` and leave `p0` rejected rather than certifying its
wrong member. It would probably also lose `gen/0-013` seed 1. Such bundles
should be reported as coupled (`triggers_and_steers`, Phase 6.4), not certified
or silently dropped. 5.6 below does this. It sets no threshold, only the rule
that a test which cannot see the choice is not evidence against a member. The
coalition tables in Phase 6 check it against independent ground truth.

### 5.6: coupled members and a strict sample split (offline; GPU run queued)

Two changes to `audit_findings`, both from the `p5c-gen` diagnosis above:

1. **Stage 1 sorts the members of a choice bundle by what their leave-one-in test
   showed**, instead of dropping every member whose test fails:
   - restores: the choice comes back. Stage 2 tests restoration.
   - hitchhiker: E is clearly intact and the choice does not come back. Dropped.
   - coupled: E itself stops (collapse test at α). Kept; stage 2 tests the
     collapse, and the report marks the member `coupled` (the certified claim
     for it is "keeping it while removing the others stops E").
   - undetermined: E is neither intact nor clearly stopped. Kept and tested as
     restoring, so a member is never dropped on a test that says nothing about it.
2. **Every bundle is re-audited on new replays**, even when stage 1 changes
   nothing, so stage 1 is never evidence and P(false certificate) ≤ α by sample
   splitting. A one-member finding has nothing to choose and is audited once.

The search also notes `triggers_and_steers suspected` (and the report sets
`triggers_and_steers_suspected`) when, with a stabilizer kept, removing all the
rest keeps the choice: `real/run4/step21` seed 2's outcome.

**Null simulation**
([results/null-sim-v3](results/null-sim-v3/null_sim.json), 500 runs, seed 0).
The unaudited rows and `boundary_single` / `hitchhiker` are unchanged from v2.
Two new conditional scenarios have an action family E (P(E) = 0.95 at baseline):
`coupled_power` is the `p0` shape and `boundary_coupled` is its least-favourable
null.

| scenario | v2 audit | 5.6 audit | replays/run (v2 → 5.6) |
|---|---:|---:|---:|
| bundle with a member at the boundary, P(false) | 3.0% [1.8, 4.9] | **1.4%** [0.7, 2.9] | 286 → 287 |
| true 2-way OR bundle, power | 99% | 97% | 139 → 198 |
| carrier + weak line, power | 97% | 97% | 130 → 130 |
| coupled OR bundle (`p0` shape), power | **0%**¹ | **97%** | 170¹ → 210 |
| coupled member at the boundary, P(false) | – | 3.8% [2.4, 5.9] | – → 334 |

¹ 40 runs with the v2 audit code. It drops the coupled carrier, as on the GPU.
Without any audit, the same null gives a false cause in 98.2% of runs.

**Predicted effect on the GPU runs.** Applying the stage-1 rule to the recorded
`p5c` audits, without new replays:
- `p0/tool_result_sentence_config`: `toolu_22` is coupled in all 3 seeds, so
  the bundle is kept rather than losing its true carrier.
- `p3/precond_2or_pnpm`: `read_pkg` is undetermined in all 3, so the bundle
  goes uncertified and the precondition is no longer blamed.
- `gen/0-013` seed 1: `call_13_2` is coupled (bundle F1 0.8 instead of 1).
  Seed 2: undetermined.
- `gen/0-037` seed 1: one member is undetermined (E at its threshold), which
  would lose a hit.
- `real`: no bundle reached stage 1 with a failing member, so nothing changes.

Whether the stage-2 replays then certify these bundles is what `p5d-gen` and
`p5d-real` measure (`RUNS="real5d gen5d" run_p5.sh`). They need a GPU box; the
Phase 5 VM has been released.

### Phase 5.5 summary

| run | engine | suite | F1 [95% CI] | `v0.2` |
|---|---|---|---:|---:|
| `p5-repro-real` | `v0.2` behaviour | real (13) | 92% [77, 100] | 92% [77, 100] |
| `p5-real` | Phase 5, pre-5.2b | real (13) | 95% [85, 100] | 92% |
| `p5c-real` | final | real (13) | 92% [77, 100] | 92% |
| `p5-gen` | Phase 5, one-stage audit | core + gen (48) | 90% [80, 98] | 95% [87, 99] |
| `p5c-gen` | final | core + gen (48) | 93% [84, 100] | 95% [87, 99] |

**Gate:** offline suite green; type-I error 3.0% [1.8, 4.9] ≤ α under the
least-favourable null; final-engine F1 inside the `v0.2` CI on both suites, now
with audited findings (Holm, α = 0.05) at +25–40% replays; on `run4/step21` the
search continues after the stabilizer in every seed (it stays unsolved, a
`triggers_and_steers` coupling).
