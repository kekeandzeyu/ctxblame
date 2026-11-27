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

The fix: after a stabilizer, the choice search runs over the whole rest as one
region, so it starts from the removal the stabilizer showed keeps E, and ddmin
counts partial removals that stop E as "not flipped". The report now says
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
