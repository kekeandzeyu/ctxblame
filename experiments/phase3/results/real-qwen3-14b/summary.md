# Phase 3 benchmark summary: `real-qwen3-14b`

13 oracle-valid cases x 3 seed(s) (seed0, seed1, seed2). Means over case x seed; F1 CI = 95% bootstrap over cases. Sim. uncached chars = what a per-run provider prefix cache would bill once per distinct request body (live vLLM hit rates are shared across concurrent runs, so not comparable).

| Method | Recall | Precision | F1 [95% CI] | Precond. separated | Precond. blamed as cause | Negatives correct | Replays/case | Distinct requests/case | Sim. uncached chars/case | Secs/case |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 92% | 92% | 92% [77%, 100%] | 100% | 0% | - | 545 | 71 | 575,985 | 585 |
| ctxblame_uncond | 69% | 52% | 60% [40%, 79%] | 0% | 100% | - | 461 | 62 | 485,341 | 491 |
| ctxblame_flat | 92% | 92% | 92% [77%, 100%] | 100% | 0% | - | 707 | 95 | 934,908 | 672 |
| loo | 0% | 0% | 0% [0%, 0%] | 0% | 100% | - | 204 | 35 | 427,445 | 231 |
| self_explain | 50% | 53% | 46% [34%, 57%] | 0% | 11% | - | 1 | 0 | 0 | 24 |
| contextcite | 44% | 23% | 29% [19%, 41%] | 0% | 92% | - | 64 | 0 | 0 | 46 |

## F1 by case category (negatives: share correct)

| Method | precondition_or (n=12) | or_redundant (n=1) |
|---|---:|---:|
| ctxblame | 100% | 0% |
| ctxblame_uncond | 65% | 0% |
| ctxblame_flat | 100% | 0% |
| loo | 0% | 0% |
| self_explain | 49% | 0% |
| contextcite | 27% | 50% |

## Recall by carrier kind (generated cases)

| Method | system | tooldesc | doc | user | history |
|---|---:|---:|---:|---:|---:|
| ctxblame | - (n=0) | - (n=0) | - (n=0) | - (n=0) | - (n=0) |
| ctxblame_uncond | - (n=0) | - (n=0) | - (n=0) | - (n=0) | - (n=0) |
| ctxblame_flat | - (n=0) | - (n=0) | - (n=0) | - (n=0) | - (n=0) |
| loo | - (n=0) | - (n=0) | - (n=0) | - (n=0) | - (n=0) |
| self_explain | - (n=0) | - (n=0) | - (n=0) | - (n=0) | - (n=0) |
| contextcite | - (n=0) | - (n=0) | - (n=0) | - (n=0) | - (n=0) |

## Recall by redundancy (number of planted carriers)

| Method | 3 carriers | 4 carriers | 5 carriers |
|---|---:|---:|---:|
| ctxblame | 89% | 100% | 100% |
| ctxblame_uncond | 89% | 33% | 0% |
| ctxblame_flat | 89% | 100% | 100% |
| loo | 0% | 0% | 0% |
| self_explain | 52% | 56% | 20% |
| contextcite | 35% | 61% | 73% |
