# Phase 3 benchmark summary: `p5c-real-qwen3-14b`

13 oracle-valid cases x 3 seed(s) (seed0, seed1, seed2). Means over case x seed; F1 CI = 95% bootstrap over cases. Sim. uncached chars = what a per-run provider prefix cache would bill once per distinct request body (live vLLM hit rates are shared across concurrent runs, so not comparable).

| Method | Recall | Precision | F1 [95% CI] | Precond. separated | Precond. blamed as cause | Negatives correct | Replays/case | Distinct requests/case | Sim. uncached chars/case | Secs/case |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 92% | 92% | 92% [77%, 100%] | 100% | 0% | - | 762 | 81 | 615,898 | 477 |

## F1 by case category (negatives: share correct)

| Method | precondition_or (n=12) | or_redundant (n=1) |
|---|---:|---:|
| ctxblame | 100% | 0% |

## Recall by carrier kind (generated cases)

| Method | system | tooldesc | doc | user | history |
|---|---:|---:|---:|---:|---:|
| ctxblame | - (n=0) | - (n=0) | - (n=0) | - (n=0) | - (n=0) |

## Recall by redundancy (number of planted carriers)

| Method | 3 carriers | 4 carriers | 5 carriers |
|---|---:|---:|---:|
| ctxblame | 89% | 100% | 100% |
