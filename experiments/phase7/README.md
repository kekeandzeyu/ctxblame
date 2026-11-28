# Phase 7 — Steelmanned baselines

Status: **7.1 code ready, offline-tested; the GPU run is pending.** The plan and the
gate are in [docs/ROADMAP.md](../../docs/ROADMAP.md#phase-7--steelmanned-baselines-and-theory-0).

## 7.1 Baselines at matched replay budgets

The question: does a tuned **non-adaptive** design find what ctxblame finds, for the
same number of replays? If it does on choice carriers, ctxblame's contribution is the
handling of the precondition gate, not the search.

**Same cases, same truth, same scorer.**
- Cases: the 250 Phase 6 cases.
- Truth: the coalition tables, read with E forced where 6.4 measured it (choice sets).
- Scoring: `score6.score_case`, the scorer ctxblame's 6.4 run (`p64c-<model>`) was
  scored with. Nothing is dropped.

**Same units.** Each baseline can remove exactly what ctxblame can: every line, and
each tool-call pair as one unit. A pair can only be removed whole, and 196 of the
planted elements are pairs (most preconditions and many probes). About 32 units per
case (21–45).

**Budgets.** M ∈ {64, 128, 256, 512} replays per case. ctxblame spends a median of
about 295 (mean 320, 90th percentile 500–630), so 512 is above it. Each design is
recorded once at 512 rows, and a budget M is its first M rows. The first 10 rows
remove nothing; they set up A and E and count towards M, as ctxblame's 10 baseline
replays do. They are left out of the estimators: kept in, they make every unit look
harmful to remove, and a permutation null cannot detect it.

**Designs** (`baselines.py`). In row t, each unit is removed with probability 1 − q,
and the request is replayed once.
- `q0.25`, `q0.5`, `q0.75`, `q0.9`: the keep-probability sweep. A small q removes OR
  backups together but loses E behind a precondition (rows in E ≈ q^m with m
  necessary preconditions). A large q keeps E but rarely removes every backup. The
  roadmap's {1/2, 1/4, 1/k} lies inside this range: with k ≤ 3 carriers, 1/k as a keep
  probability is about 0.33, and as a removal probability about 0.67.
- `fq0.5`: the same design with E forced by `tool_choice`. Every row is then in E, but
  this design cannot see preconditions. `<est>:fq0.5+q0.5` spends M/2 rows on each.
  This is the strongest non-adaptive opponent: it uses the 6.4 intervention without
  the adaptive search.

**Estimators** (`estimate.py`, offline). The same rows feed all three:
- `banzhaf`: mean(bad | removed) − mean(bad | kept).
- `lasso`: a linear probability model.
- `gt`: a noisy group-testing decoder for OR-of-AND causes. It tests every set of up to
  3 units among the top 8 and keeps the minimal sets that pass.

"Bad" means "not A" among the rows in E (choice carriers), or "not E" among all rows
(preconditions). A unit is reported when its statistic beats the 95th percentile of the
largest statistic under permuted outcomes. The family-wise error is then 5%, and every
estimator can answer "nothing".

**Other baselines.**
- `cc`, contrastive ContextCite: 512 masks at q = 1/2, each scored with one prefill.
  The choice part is log p(tokens after the tool name | prefix). Lasso with the same
  null; the E prefix gives preconditions.
- `self_explain_full`: every unit in full (no truncation), A and E stated. The model
  lists the units that decided the choice and the ones that made it act at all.

**Reported** (`score7.py` → `summary.md`):
1. The best design of each estimator at each M, chosen on these same cases (this
   favours the baselines), next to ctxblame.
2. ctxblame minus the best baseline at each M, paired over cases, with a 95%
   bootstrap interval.
3. Every method.
4. The gate: the share of rows in E by q and m, next to q^m (7.2, proposition 2).

**Cost.** Per case: 5 designs × 512 replays + 512 prefills + 1 call, or about 2,560
sampled replays. That is about 640k replays per model for one seed. At the 6.x rate
(75–90/s) that's roughly 2–2.5 h per model, run in parallel on two GPUs. The 10-case
pilot measures the real rate first.

### Commands

```sh
# pilot: 10 cases, throughput (one GPU per model, as in AGENTS.md)
CUDA_VISIBLE_DEVICES=0 PORT=8000 MODEL=/root/autodl-tmp/models/Qwen3-14B-FP8 NAME=Qwen3-14B FROM=qwen3-14b \
  TAG=p71pilot-qwen3-14b LIMIT=10 experiments/phase7/run_p7.sh
# full suite
CUDA_VISIBLE_DEVICES=0 PORT=8000 SKIP_SERVE=1 MODEL=/root/autodl-tmp/models/Qwen3-14B-FP8 NAME=Qwen3-14B \
  FROM=qwen3-14b TAG=p71-qwen3-14b experiments/phase7/run_p7.sh
# Llama the same on GPU 1 / port 8001 with FROM=llama3.1-8b and
#   TOOL_PARSER=llama3_json SERVE_ARGS="--chat-template experiments/phase6/llama31_tool_template.jinja"
#   EXTRA_BODY='{"temperature": 0.6, "top_p": 0.9}'
# progress
PORT=8000 experiments/phase3/vm_status.sh p71
# offline, after copying results back: re-estimate (other estimators need no GPU) and re-score
uv run python experiments/phase7/estimate.py experiments/phase7/results/p71-qwen3-14b/seed0
uv run python experiments/phase7/score7.py experiments/phase7/results/p71-qwen3-14b/seed* \
  --tables experiments/phase6/results/qwen3-14b/tables --forced experiments/phase6/results/p64c-qwen3-14b/forced \
  --ctxblame experiments/phase6/results/p64c-qwen3-14b/seed*/benchmark.json
```

Tests: `tests/test_phase7.py`. It covers the designs and units, and checks the
estimators on simulated single, OR, precondition and noise cases. It also runs the
whole collector against a fake vLLM server (chat, `/tokenize`, `/detokenize`,
prompt logprobs) on a real Phase 6 case.
