# Phase 3 benchmark summary: `qwen3-14b-fp8`

48 oracle-valid cases x 3 seed(s) (seed0, seed1, seed2). Means over case x seed; F1 CI = 95% bootstrap over cases. Sim. uncached chars = what a per-run provider prefix cache would bill once per distinct request body (live vLLM hit rates are shared across concurrent runs, so not comparable).

| Method | Recall | Precision | F1 [95% CI] | Precond. separated | Precond. blamed as cause | Negatives correct | Replays/case | Distinct requests/case | Sim. uncached chars/case | Secs/case |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 96% | 94% | 95% [87%, 99%] | 93% | 4% | 100% | 189 | 25 | 28,785 | 87 |
| ctxblame_uncond | 82% | 72% | 76% [64%, 86%] | 0% | 100% | 93% | 173 | 23 | 26,257 | 78 |
| loo | 45% | 36% | 39% [25%, 53%] | 0% | 100% | 100% | 60 | 9 | 19,143 | 28 |
| self_explain | 58% | 65% | 60% [46%, 74%] | 0% | 0% | 0% | 1 | 0 | 0 | 3 |
| contextcite | 96% | 77% | 84% [79%, 89%] | 0% | 93% | 0% | 64 | 0 | 0 | 11 |

## F1 by case category (negatives: share correct)

| Method | single (n=11) | precondition_or (n=15) | tail_long_ctx (n=1) | or_redundant (n=11) | negative (n=10) |
|---|---:|---:|---:|---:|---:|
| ctxblame | 100% | 90% | 100% | 95% | 100% |
| ctxblame_uncond | 94% | 43% | 100% | 100% | 93% |
| loo | 91% | 25% | 100% | 0% | 100% |
| self_explain | 79% | 67% | 100% | 26% | 0% |
| contextcite | 90% | 71% | 100% | 93% | 0% |

## Recall by carrier kind (generated cases)

| Method | system | tooldesc | doc | user | history |
|---|---:|---:|---:|---:|---:|
| ctxblame | 100% (n=51) | 97% (n=30) | 97% (n=30) | 100% (n=45) | 100% (n=9) |
| ctxblame_uncond | 76% (n=51) | 80% (n=30) | 90% (n=30) | 87% (n=45) | 100% (n=9) |
| loo | 35% (n=51) | 10% (n=30) | 30% (n=30) | 20% (n=45) | 33% (n=9) |
| self_explain | 43% (n=51) | 20% (n=30) | 73% (n=30) | 51% (n=45) | 67% (n=9) |
| contextcite | 98% (n=51) | 90% (n=30) | 100% (n=30) | 91% (n=45) | 100% (n=9) |

## Recall by redundancy (number of planted carriers)

| Method | 1 carrier | 2 carriers | 3 carriers |
|---|---:|---:|---:|
| ctxblame | 100% | 89% | 100% |
| ctxblame_uncond | 91% | 83% | 62% |
| loo | 94% | 0% | 0% |
| self_explain | 83% | 28% | 44% |
| contextcite | 100% | 100% | 83% |
