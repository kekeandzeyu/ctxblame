# Phase 3 benchmark summary: `llama3.1-8b`

46 oracle-valid cases x 3 seed(s) (seed0, seed1, seed2). Means over case x seed; F1 CI = 95% bootstrap over cases. Sim. uncached chars = what a per-run provider prefix cache would bill once per distinct request body (live vLLM hit rates are shared across concurrent runs, so not comparable).

| Method | Recall | Precision | F1 [95% CI] | Precond. separated | Precond. blamed as cause | Negatives correct | Replays/case | Distinct requests/case | Sim. uncached chars/case | Secs/case |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 89% | 84% | 85% [76%, 93%] | 76% | 15% | 100% | 271 | 33 | 89,829 | 89 |
| ctxblame_uncond | 81% | 73% | 77% [67%, 86%] | 0% | 94% | 100% | 226 | 26 | 30,743 | 69 |
| loo | 40% | 35% | 36% [23%, 52%] | 0% | 100% | 100% | 63 | 9 | 18,409 | 19 |
| self_explain | 67% | 76% | 67% [60%, 74%] | 0% | 6% | 7% | 1 | 0 | 0 | 2 |
| contextcite | 95% | 80% | 84% [79%, 89%] | 0% | 91% | 0% | 64 | 0 | 0 | 6 |

## F1 by case category (negatives: share correct)

| Method | single (n=10) | precondition_or (n=11) | tail_long_ctx (n=1) | or_redundant (n=15) | negative (n=9) |
|---|---:|---:|---:|---:|---:|
| ctxblame | 91% | 72% | 100% | 91% | 100% |
| ctxblame_uncond | 86% | 49% | 100% | 89% | 100% |
| loo | 95% | 24% | 100% | 4% | 100% |
| self_explain | 73% | 58% | 56% | 71% | 7% |
| contextcite | 93% | 72% | 100% | 85% | 0% |

## Recall by carrier kind (generated cases)

| Method | system | tooldesc | doc | user | history |
|---|---:|---:|---:|---:|---:|
| ctxblame | 92% (n=66) | 76% (n=42) | 81% (n=36) | 95% (n=42) | 100% (n=6) |
| ctxblame_uncond | 86% (n=66) | 64% (n=42) | 72% (n=36) | 95% (n=42) | 100% (n=6) |
| loo | 27% (n=66) | 12% (n=42) | 22% (n=36) | 7% (n=42) | 50% (n=6) |
| self_explain | 68% (n=66) | 48% (n=42) | 50% (n=36) | 93% (n=42) | 33% (n=6) |
| contextcite | 94% (n=66) | 88% (n=42) | 97% (n=36) | 88% (n=42) | 100% (n=6) |

## Recall by redundancy (number of planted carriers)

| Method | 1 carrier | 2 carriers | 3 carriers |
|---|---:|---:|---:|
| ctxblame | 98% | 89% | 78% |
| ctxblame_uncond | 89% | 77% | 75% |
| loo | 96% | 5% | 0% |
| self_explain | 71% | 65% | 62% |
| contextcite | 100% | 94% | 89% |
