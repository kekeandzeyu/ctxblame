# Phase 3 benchmark summary: `qwen3-14b-vet`

48 oracle-valid cases x 3 seed(s) (seed0, seed1, seed2). Means over case x seed; F1 CI = 95% bootstrap over cases. Sim. uncached chars = what a per-run provider prefix cache would bill once per distinct request body (live vLLM hit rates are shared across concurrent runs, so not comparable).

| Method | Recall | Precision | F1 [95% CI] | Precond. separated | Precond. blamed as cause | Negatives correct | Replays/case | Distinct requests/case | Sim. uncached chars/case | Secs/case |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 96% | 94% | 95% [88%, 99%] | 93% | 2% | 87% | 213 | 27 | 31,923 | 68 |

## F1 by case category (negatives: share correct)

| Method | single (n=11) | precondition_or (n=15) | tail_long_ctx (n=1) | or_redundant (n=11) | negative (n=10) |
|---|---:|---:|---:|---:|---:|
| ctxblame | 100% | 91% | 100% | 94% | 87% |

## Recall by carrier kind (generated cases)

| Method | system | tooldesc | doc | user | history |
|---|---:|---:|---:|---:|---:|
| ctxblame | 100% (n=51) | 97% (n=30) | 93% (n=30) | 98% (n=45) | 100% (n=9) |

## Recall by redundancy (number of planted carriers)

| Method | 1 carrier | 2 carriers | 3 carriers |
|---|---:|---:|---:|
| ctxblame | 100% | 86% | 100% |
