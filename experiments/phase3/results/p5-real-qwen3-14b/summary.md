# Phase 3 benchmark summary: `p5-real-qwen3-14b`

13 oracle-valid cases x 3 seed(s) (seed0, seed1, seed2). Means over case x seed; F1 CI = 95% bootstrap over cases. Sim. uncached chars = what a per-run provider prefix cache would bill once per distinct request body (live vLLM hit rates are shared across concurrent runs, so not comparable).

| Method | Recall | Precision | F1 [95% CI] | Precond. separated | Precond. blamed as cause | Negatives correct | Replays/case | Distinct requests/case | Sim. uncached chars/case | Secs/case |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 95% | 95% | 95% [85%, 100%] | 100% | 0% | - | 722 | 77 | 602,216 | 474 |
| ctxblame_uncond | 69% | 52% | 60% [40%, 79%] | 0% | 100% | - | 544 | 63 | 485,879 | 376 |

## F1 by case category (negatives: share correct)

| Method | precondition_or (n=12) | or_redundant (n=1) |
|---|---:|---:|
| ctxblame | 100% | 33% |
| ctxblame_uncond | 65% | 0% |

## Recall by carrier kind (generated cases)

| Method | system | tooldesc | doc | user | history |
|---|---:|---:|---:|---:|---:|
| ctxblame | - (n=0) | - (n=0) | - (n=0) | - (n=0) | - (n=0) |
| ctxblame_uncond | - (n=0) | - (n=0) | - (n=0) | - (n=0) | - (n=0) |

## Recall by redundancy (number of planted carriers)

| Method | 3 carriers | 4 carriers | 5 carriers |
|---|---:|---:|---:|
| ctxblame | 93% | 100% | 100% |
| ctxblame_uncond | 89% | 33% | 0% |
