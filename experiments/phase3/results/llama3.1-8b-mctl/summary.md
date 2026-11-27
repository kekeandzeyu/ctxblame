# Phase 3 benchmark summary: `llama3.1-8b-mctl`

46 oracle-valid cases x 3 seed(s) (seed0, seed1, seed2). Means over case x seed; F1 CI = 95% bootstrap over cases. Sim. uncached chars = what a per-run provider prefix cache would bill once per distinct request body (live vLLM hit rates are shared across concurrent runs, so not comparable).

| Method | Recall | Precision | F1 [95% CI] | Precond. separated | Precond. blamed as cause | Negatives correct | Replays/case | Distinct requests/case | Sim. uncached chars/case | Secs/case |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 89% | 86% | 87% [78%, 94%] | 76% | 12% | 100% | 311 | 37 | 90,436 | 84 |

## F1 by case category (negatives: share correct)

| Method | single (n=10) | precondition_or (n=11) | tail_long_ctx (n=1) | or_redundant (n=15) | negative (n=9) |
|---|---:|---:|---:|---:|---:|
| ctxblame | 88% | 77% | 100% | 92% | 100% |

## Recall by carrier kind (generated cases)

| Method | system | tooldesc | doc | user | history |
|---|---:|---:|---:|---:|---:|
| ctxblame | 92% (n=66) | 76% (n=42) | 83% (n=36) | 95% (n=42) | 100% (n=6) |

## Recall by redundancy (number of planted carriers)

| Method | 1 carrier | 2 carriers | 3 carriers |
|---|---:|---:|---:|
| ctxblame | 96% | 89% | 79% |
