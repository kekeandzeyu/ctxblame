# Phase 3 benchmark summary: `qwen3-14b-think`

55 oracle-valid cases x 3 seed(s) (seed0, seed1, seed2). Means over case x seed; F1 CI = 95% bootstrap over cases. Sim. uncached chars = what a per-run provider prefix cache would bill once per distinct request body (live vLLM hit rates are shared across concurrent runs, so not comparable).

| Method | Recall | Precision | F1 [95% CI] | Precond. separated | Precond. blamed as cause | Negatives correct | Replays/case | Distinct requests/case | Sim. uncached chars/case | Secs/case |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 94% | 95% | 95% [89%, 99%] | 94% | 6% | 100% | 188 | 24 | 24,995 | 549 |
| ctxblame_uncond | 84% | 79% | 81% [70%, 90%] | 0% | 97% | 100% | 176 | 22 | 23,173 | 493 |
| loo | 38% | 33% | 34% [22%, 48%] | 0% | 94% | 100% | 61 | 9 | 18,238 | 141 |
| self_explain | 76% | 91% | 80% [74%, 86%] | 0% | 6% | 27% | 1 | 0 | 0 | 23 |
| contextcite | 95% | 78% | 83% [78%, 87%] | 0% | 100% | 0% | 64 | 0 | 0 | 10 |

## F1 by case category (negatives: share correct)

| Method | single (n=13) | precondition_or (n=12) | tail_long_ctx (n=1) | or_redundant (n=19) | negative (n=10) |
|---|---:|---:|---:|---:|---:|
| ctxblame | 96% | 94% | 100% | 94% | 100% |
| ctxblame_uncond | 99% | 38% | 100% | 95% | 100% |
| loo | 89% | 21% | 100% | 4% | 100% |
| self_explain | 94% | 75% | 100% | 71% | 27% |
| contextcite | 88% | 69% | 100% | 88% | 0% |

## Recall by carrier kind (generated cases)

| Method | system | tooldesc | doc | user | history |
|---|---:|---:|---:|---:|---:|
| ctxblame | 99% (n=75) | 75% (n=36) | 100% (n=48) | 100% (n=51) | 100% (n=3) |
| ctxblame_uncond | 81% (n=75) | 67% (n=36) | 94% (n=48) | 88% (n=51) | 100% (n=3) |
| loo | 28% (n=75) | 8% (n=36) | 25% (n=48) | 18% (n=51) | 0% (n=3) |
| self_explain | 93% (n=75) | 25% (n=36) | 83% (n=48) | 43% (n=51) | 0% (n=3) |
| contextcite | 95% (n=75) | 92% (n=36) | 96% (n=48) | 90% (n=51) | 100% (n=3) |

## Recall by redundancy (number of planted carriers)

| Method | 1 carrier | 2 carriers | 3 carriers |
|---|---:|---:|---:|
| ctxblame | 94% | 91% | 97% |
| ctxblame_uncond | 94% | 83% | 67% |
| loo | 93% | 3% | 0% |
| self_explain | 100% | 68% | 46% |
| contextcite | 100% | 96% | 84% |
