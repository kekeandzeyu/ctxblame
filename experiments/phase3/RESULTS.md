# Attribution benchmark results (Phases 3–4, open models, $0)

All runs: vLLM with prefix caching on one RTX 4090 48GB, 3 seeds, thinking
off unless noted. Only **oracle-valid** cases are scored: `oracle.py` first checks on
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

| Method | Qwen3-8B gen (53 cases) | Qwen3-14B gen (48) | Qwen3-14B thinking on, gen (55) | Qwen3-14B real (13) | Qwen3-14B gen-long (38) |
|---|---:|---:|---:|---:|---:|
| **ctxblame** | **94%** [88, 99] | **95%** [87, 99] | **95%** [89, 99] | **92%** [77, 100] | **95%** [89, 99] |
| ctxblame `--given none` | 79% | 76% | 81% | 60% | – |
| ctxblame `--no-stratify` (flat search) | 95% | – | – | 92% | 90% |
| ContextCite (Lasso on prompt logprobs) | 71% | 84% | 83% | 29% | – |
| self-explanation | 73% | 60% | 80% | 46% | – |
| leave-one-out | 34% | 39% | 34% | 0% | – |

Preconditions kept apart from causes: ctxblame 93% / 93% / 94% / 100% / 94%; every
baseline 0% (leave-one-out, ContextCite and unconditional ctxblame report the
edit as a cause in 92–100% of precondition cases). Negatives (nothing in the
context drives the decision) correct: ctxblame 97–100%; ContextCite 0% and
self-explanation 0–27% (they almost always name something).

With thinking on, replays take ~5× longer (549 vs ~90 s per case) but the
number of replays is unchanged (~190). Self-explanation gains the most from
thinking (60% → 80%) yet still invents a cause for 73% of negatives; the
hardest carrier for ctxblame is the tool description (75% recall).

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
