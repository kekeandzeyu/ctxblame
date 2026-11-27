# Phase 3 benchmark summary: `p5-gen-qwen3-14b`

48 oracle-valid cases x 3 seed(s) (seed0, seed1, seed2). Means over case x seed; F1 CI = 95% bootstrap over cases. Sim. uncached chars = what a per-run provider prefix cache would bill once per distinct request body (live vLLM hit rates are shared across concurrent runs, so not comparable).

| Method | Recall | Precision | F1 [95% CI] | Precond. separated | Precond. blamed as cause | Negatives correct | Replays/case | Distinct requests/case | Sim. uncached chars/case | Secs/case |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 90% | 90% | 90% [80%, 98%] | 93% | 2% | 97% | 230 | 25 | 28,080 | 62 |
| ctxblame_uncond | 82% | 73% | 76% [64%, 87%] | 0% | 100% | 100% | 205 | 23 | 25,803 | 56 |

## F1 by case category (negatives: share correct)

| Method | single (n=11) | precondition_or (n=15) | tail_long_ctx (n=1) | or_redundant (n=11) | negative (n=10) |
|---|---:|---:|---:|---:|---:|
| ctxblame | 91% | 93% | 100% | 85% | 97% |
| ctxblame_uncond | 94% | 45% | 100% | 100% | 100% |

## Recall by carrier kind (generated cases)

| Method | system | tooldesc | doc | user | history |
|---|---:|---:|---:|---:|---:|
| ctxblame | 100% (n=51) | 93% (n=30) | 83% (n=30) | 93% (n=45) | 100% (n=9) |
| ctxblame_uncond | 76% (n=51) | 80% (n=30) | 90% (n=30) | 87% (n=45) | 100% (n=9) |

## Recall by redundancy (number of planted carriers)

| Method | 1 carrier | 2 carriers | 3 carriers |
|---|---:|---:|---:|
| ctxblame | 94% | 78% | 100% |
| ctxblame_uncond | 91% | 83% | 62% |
