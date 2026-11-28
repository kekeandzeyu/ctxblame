# Attribution benchmark results (Phases 3–4, open models, $0)

All runs: vLLM with prefix caching on one RTX 4090 48GB, 3 seeds, thinking
off unless noted. Sampling: temperature 0.7 (Qwen, thinking off) or 0.6 (Qwen
thinking on, Llama); the exact `extra_body` of each run is in
`results/<tag>/oracle_all.json`. Only **oracle-valid** cases are scored: `oracle.py` first checks on
the model under test that the base decision is stable, removing all planted
carriers flips it, each carrier alone restores it, and removing the
precondition collapses the action family `E`. F1 = mean over case × seed with
a 95% bootstrap CI over cases. Per-suite tables (by category, carrier kind and
redundancy) are in each `results/<tag>/summary.md`.

## Suites

| Suite | Cases | What it is |
|---|---|---|
| `core` + `gen` | 12 hand-written + generated | 8 tool conventions (tox, hatch, make, pnpm, uv, ruff, cargo, script) planted in 5 places (system prompt, tool description, read doc, user message, earlier tool calls), 1–3 redundant carriers, optional edit precondition, negatives (decision not driven by context) |
| `gen-long` | generated | the same with a ~30k-char agent manual before the repository rules |
| `real` | 15 steps from 15 runs | real runs of `experiments/phase1/agent.py` driven by Qwen3-14B fixing a planted bug ([phase4/results/traces](../phase4/results/traces)); carriers = AGENTS.md rule, the bash tool's example, the agent's earlier test runs; precondition = the edits since the last run |

## Accuracy (F1)

| Method | Qwen3-8B gen (53 cases) | Qwen3-14B gen (48) | Qwen3-14B thinking on, gen (55) | Llama-3.1-8B gen (46) | Qwen3-14B real (13) | Qwen3-14B gen-long (38) |
|---|---:|---:|---:|---:|---:|---:|
| **ctxblame** | **94%** [88, 99] | **95%** [87, 99] | **95%** [89, 99] | **85%** [76, 93] | **92%** [77, 100] | **95%** [89, 99] |
| ctxblame `--given none` | 79% | 76% | 81% | 77% | 60% | – |
| ctxblame `--no-stratify` (flat search) | 95% | – | – | – | 92% | 90% |
| ContextCite (Lasso on prompt logprobs) | 71% | 84% | 83% | 84% | 29% | – |
| self-explanation | 73% | 60% | 80% | 67% | 46% | – |
| leave-one-out | 34% | 39% | 34% | 36% | 0% | – |

Preconditions kept apart from causes: ctxblame 93% / 93% / 94% / 76% / 100% / 94%; every
baseline 0% (leave-one-out, ContextCite and unconditional ctxblame report the
edit as a cause in 92–100% of precondition cases). Negatives (nothing in the
context drives the decision) correct: ctxblame 97–100%; ContextCite 0% and
self-explanation 0–27% (they almost always name something).

With thinking on, replays take ~5× longer (549 vs ~90 s per case) but the
number of replays is unchanged (~190). Self-explanation gains the most from
thinking (60% → 80%) yet still invents a cause for 73% of negatives; the
hardest carrier for ctxblame is the tool description (75% recall).

### Llama-3.1-8B: a harder, noisier model

Run with vLLM's `llama3_json` parser and a patched copy of its chat template
(the stock one refuses a history with parallel tool calls). Fewer cases pass
the oracle (46/76), and ctxblame drops to 85% F1, statistically tied with
ContextCite (84%). It still is the only method that separates preconditions
(76%, everyone else 0%) and answers every negative correctly (100%; ContextCite
0%, self-explanation 7%). The drop has one cause: Llama's decision also moves
when *unrelated* lines are removed. ctxblame's random-removal controls catch
part of this and withhold the finding as "not specific" (e.g. removing "You
are a careful coding agent" flips `hatch run test:all` 11/13 times), and the
rest shows up as OR bundles padded with neutral lines ("Hi!", "Understood.")
that pass the leave-one-in check by chance. Recall with 3 redundant carriers
falls to 78% (Qwen: 93–96%).

#### Vetting bundle members does not close the gap

If neutral lines only pass the leave-one-in check by noise, or by being "some
context", two stricter checks should drop them: `--strict-restore` (keeping the
line alone must clearly restore the decision, confirmed with more replays) and
`--member-controls 2` (it must still restore it when a random same-size run of
other lines is removed too). Measured, ctxblame only, 3 seeds:

| ctxblame F1 | default | both checks | `--member-controls 2` only |
|---|---:|---:|---:|
| Llama-3.1-8B gen (46) | 85% [76, 93] | 85% [76, 92] | 87% [78, 94] |
| Qwen3-14B gen (48) | 95% [87, 99] | 95% [88, 99] | – |
| Qwen3-14B real (13) | 92% [77, 100] | 92% [77, 100] | – |

No change beyond noise, at 10–17% more replays, so both stay off by default.
The neutral lines that end up in Llama's bundles pass both checks: removing
them together with the planted carriers really does flip the decision, and
not because of how much text is removed. They are genuine interactions in
this model (e.g. a rule in a read doc that Llama follows only while the
conversation still has an assistant turn), which a planted-carrier ground
truth counts as false positives.

## Cost: suffix-first vs flat search

Simulated uncached input = what a per-run provider prefix cache bills once per
distinct request body (live vLLM hit rates are shared across concurrent runs).

| Suite | Request size | Replays/case (stratified / flat) | Uncached chars/case (stratified / flat) | Saving |
|---|---|---:|---:|---:|
| gen (Qwen3-8B) | 2–6k chars | 204 / 193 | 27,947 / 27,833 | none |
| real (Qwen3-14B) | 14–26k chars | 545 / 707 | 575,985 / 934,908 | −38% |
| gen-long (Qwen3-14B) | ~35k chars | 275 / 376 | 220,595 / 331,774 | −34% |

On short prompts the tiers buy nothing; on long ones they cut replays by a
quarter and uncached input by a third, and on gen-long they are also more
accurate (F1 95% vs 90%; recall with 3 carriers 96% vs 78%), because removals
stay small and carriers are not tested in one big block.

## Findings that changed the plan

- **ContextCite does not give redundant carriers ~0 weight.** Its random
  multi-chunk ablations remove backups together, so it recalls carriers
  (88–96% recall on gen). Its failures are elsewhere: it always blames the
  precondition, never answers "nothing in the context", needs prompt
  logprobs, and on real traces precision drops to 23%. Leave-one-out is the
  method that collapses on redundancy (0% on real traces).
- **Milestone 1 on an open model.** Phase 1's step5/step7 cannot be re-run on
  Qwen (`python -m pytest` is the model's habit, so the carriers don't drive
  it); the real Qwen3-14B traces replace that check. ctxblame finds every
  carrier with 100% precision on all 12 real cases with an edit precondition.
- **Known failure:** `real/run4/step21`, the one real case without an edit
  since the last test run. Whether the agent tests at all there depends on
  scattered `read_file` output; ctxblame reports it as a precondition and
  finds no carriers (the flat search reports a diffuse 24–31-chunk removal).

## Reproduce

```sh
# on a GPU box with vLLM; see run_model.sh for the environment variables
TAG=qwen3-14b MODEL=/path/to/Qwen3-14B-FP8 SUITE=all SEEDS="0 1 2" experiments/phase3/run_model.sh
uv run --with numpy python experiments/phase3/analyze.py experiments/phase3/results/qwen3-14b
```
