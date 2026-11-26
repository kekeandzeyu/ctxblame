# Phase 3 benchmark summary: `genlong-qwen3-14b`

38 oracle-valid cases x 3 seed(s) (seed0, seed1, seed2). Means over case x seed; F1 CI = 95% bootstrap over cases. Sim. uncached chars = what a per-run provider prefix cache would bill once per distinct request body (live vLLM hit rates are shared across concurrent runs, so not comparable).

| Method | Recall | Precision | F1 [95% CI] | Precond. separated | Precond. blamed as cause | Negatives correct | Replays/case | Distinct requests/case | Sim. uncached chars/case | Secs/case |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 98% | 93% | 95% [89%, 99%] | 94% | 6% | 100% | 275 | 33 | 220,595 | 220 |
| ctxblame_flat | 92% | 89% | 90% [80%, 98%] | 72% | 3% | 100% | 376 | 42 | 331,774 | 304 |

## F1 by case category (negatives: share correct)

| Method | single (n=8) | or_redundant (n=11) | precondition_or (n=12) | negative (n=7) |
|---|---:|---:|---:|---:|
| ctxblame | 96% | 96% | 92% | 100% |
| ctxblame_flat | 100% | 76% | 95% | 100% |

## Recall by carrier kind (generated cases)

| Method | system | tooldesc | doc | user | history |
|---|---:|---:|---:|---:|---:|
| ctxblame | 98% (n=60) | 90% (n=30) | 100% (n=30) | 100% (n=42) | 100% (n=6) |
| ctxblame_flat | 90% (n=60) | 70% (n=30) | 100% (n=30) | 88% (n=42) | 100% (n=6) |

## Recall by redundancy (number of planted carriers)

| Method | 1 carrier | 2 carriers | 3 carriers |
|---|---:|---:|---:|
| ctxblame | 98% | 100% | 96% |
| ctxblame_flat | 100% | 93% | 78% |
