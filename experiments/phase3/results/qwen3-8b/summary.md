# Phase 3 benchmark summary: `qwen3-8b`

53 oracle-valid cases x 3 seed(s) (seed0, seed1, seed2). Means over case x seed; F1 CI = 95% bootstrap over cases. Sim. uncached chars = what a per-run provider prefix cache would bill once per distinct request body (live vLLM hit rates are shared across concurrent runs, so not comparable).

| Method | Recall | Precision | F1 [95% CI] | Precond. separated | Precond. blamed as cause | Negatives correct | Replays/case | Distinct requests/case | Sim. uncached chars/case | Secs/case |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 95% | 94% | 94% [88%, 99%] | 93% | 7% | 97% | 204 | 26 | 27,947 | 107 |
| ctxblame_uncond | 85% | 76% | 79% [68%, 89%] | 0% | 100% | 100% | 173 | 23 | 25,507 | 67 |
| loo | 39% | 32% | 34% [21%, 46%] | 0% | 100% | 100% | 60 | 3 | 18,449 | 15 |
| self_explain | 71% | 88% | 73% [67%, 80%] | 0% | 0% | 0% | 1 | 0 | 0 | 2 |
| contextcite | 88% | 64% | 71% [65%, 76%] | 0% | 100% | 0% | 64 | 0 | 0 | 5 |
| ctxblame_flat | 96% | 95% | 95% [90%, 99%] | 93% | 7% | 100% | 193 | 24 | 27,833 | 65 |

## F1 by case category (negatives: share correct)

| Method | single (n=10) | precondition_or (n=14) | tail_long_ctx (n=1) | or_redundant (n=17) | negative (n=11) |
|---|---:|---:|---:|---:|---:|
| ctxblame | 92% | 96% | 100% | 95% | 97% |
| ctxblame_uncond | 92% | 48% | 100% | 96% | 100% |
| loo | 92% | 24% | 100% | 4% | 100% |
| self_explain | 76% | 70% | 100% | 73% | 0% |
| contextcite | 68% | 60% | 67% | 81% | 0% |
| ctxblame_flat | 100% | 96% | 100% | 92% | 100% |

## Recall by carrier kind (generated cases)

| Method | system | tooldesc | doc | user | history |
|---|---:|---:|---:|---:|---:|
| ctxblame | 100% (n=66) | 93% (n=45) | 100% (n=36) | 100% (n=45) | 100% (n=12) |
| ctxblame_uncond | 86% (n=66) | 80% (n=45) | 92% (n=36) | 87% (n=45) | 100% (n=12) |
| loo | 23% (n=66) | 20% (n=45) | 17% (n=36) | 13% (n=45) | 50% (n=12) |
| self_explain | 95% (n=66) | 27% (n=45) | 50% (n=36) | 80% (n=45) | 50% (n=12) |
| contextcite | 79% (n=66) | 93% (n=45) | 94% (n=36) | 64% (n=45) | 100% (n=12) |
| ctxblame_flat | 98% (n=66) | 96% (n=45) | 97% (n=36) | 100% (n=45) | 100% (n=12) |

## Recall by redundancy (number of planted carriers)

| Method | 1 carrier | 2 carriers | 3 carriers |
|---|---:|---:|---:|
| ctxblame | 96% | 92% | 100% |
| ctxblame_uncond | 96% | 84% | 70% |
| loo | 100% | 3% | 0% |
| self_explain | 94% | 62% | 50% |
| contextcite | 100% | 93% | 63% |
| ctxblame_flat | 100% | 89% | 100% |
