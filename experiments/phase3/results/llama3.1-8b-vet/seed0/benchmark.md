# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 83% | 82% | 82% | 18% | 100% | 332.3 | 91% | 89.5s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| p0/system_section_deploy_freeze | single | ctxblame | causes | 1/1 | 100% | 50% | - | 185 | 90% | 38.3s | $0.000 |
| p3/precond_2or_pnpm | precondition_or | ctxblame | causes | 0/2 | 0% | 0% | FP | 155 | 90% | 41.2s | $0.000 |
| p3/tail_carrier_long_ctx | tail_long_ctx | ctxblame | causes | 1/1 | 100% | 100% | - | 1985 | 84% | 632.6s | $0.000 |
| p3/two_carrier_ruff | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 270 | 87% | 184.1s | $0.000 |
| p3/negative_habit_only | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 86% | 7.6s | $0.000 |
| gen/0-000/tox/user/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 94% | 29.1s | $0.000 |
| gen/0-001/hatch/tooldesc+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 335 | 92% | 83.5s | $0.000 |
| gen/0-002/make/system+tooldesc+doc+pre | precondition_or | ctxblame | causes | 2/3 | 67% | 67% | YES | 890 | 90% | 247.2s | $0.000 |
| gen/0-003/pnpm/history+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 50% | FP | 195 | 93% | 39.0s | $0.000 |
| gen/0-005/ruff/system+doc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 370 | 92% | 118.5s | $0.000 |
| gen/0-006/cargo/tooldesc | single | ctxblame | causes | 1/1 | 100% | 100% | - | 690 | 91% | 161.9s | $0.000 |
| gen/0-008/tox/system+doc+user+pre | precondition_or | ctxblame | none_found | 0/3 | 0% | 0% | YES | 1175 | 93% | 314.1s | $0.000 |
| gen/0-009/hatch/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 170 | 93% | 43.1s | $0.000 |
| gen/0-010/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 7.8s | $0.000 |
| gen/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 430 | 92% | 119.1s | $0.000 |
| gen/0-013/ruff/doc+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 290 | 93% | 138.2s | $0.000 |
| gen/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 460 | 90% | 169.8s | $0.000 |
| gen/0-019/pnpm/system+tooldesc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 245 | 87% | 61.8s | $0.000 |
| gen/0-021/ruff/doc/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 110 | 94% | 38.1s | $0.000 |
| gen/0-022/cargo/system+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 240 | 91% | 56.9s | $0.000 |
| gen/0-025/hatch/system+user/long | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 225 | 92% | 64.4s | $0.000 |
| gen/0-026/make/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 415 | 91% | 102.7s | $0.000 |
| gen/0-027/pnpm/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | no | 460 | 92% | 146.6s | $0.000 |
| gen/0-029/ruff/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 11.3s | $0.000 |
| gen/0-030/cargo/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 110 | 88% | 26.1s | $0.000 |
| gen/0-031/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 90% | 9.4s | $0.000 |
| gen/0-032/tox/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 90% | 11.9s | $0.000 |
| gen/0-033/hatch/system | single | ctxblame | causes | 0/1 | 0% | 0% | - | 160 | 90% | 36.0s | $0.000 |
| gen/0-034/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 8.5s | $0.000 |
| gen/0-035/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 90% | 8.5s | $0.000 |
| gen/0-037/ruff/tooldesc+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 255 | 91% | 77.4s | $0.000 |
| gen/0-039/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 8.2s | $0.000 |
| gen/0-041/hatch/tooldesc+doc+user | or_redundant | ctxblame | none_found | 0/3 | 0% | 0% | - | 1300 | 95% | 296.3s | $0.000 |
| gen/0-042/make/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 360 | 93% | 90.8s | $0.000 |
| gen/0-043/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 92% | 8.7s | $0.000 |
| gen/0-046/cargo/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 255 | 91% | 53.1s | $0.000 |
| gen/0-048/tox/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 89% | 32.8s | $0.000 |
| gen/0-049/hatch/system+user | or_redundant | ctxblame | causes | 1/2 | 50% | 100% | - | 275 | 92% | 57.9s | $0.000 |
| gen/0-053/ruff/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 370 | 90% | 89.9s | $0.000 |
| gen/0-054/cargo/tooldesc | single | ctxblame | causes | 0/1 | 0% | 0% | - | 305 | 91% | 59.0s | $0.000 |
| gen/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 465 | 94% | 96.9s | $0.000 |
| gen/0-057/hatch/doc | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 93% | 30.0s | $0.000 |
| gen/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 370 | 91% | 72.9s | $0.000 |
| gen/0-060/uv/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 88% | 28.6s | $0.000 |
| gen/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 300 | 91% | 61.8s | $0.000 |
| gen/0-062/cargo/system+tooldesc+doc | or_redundant | ctxblame | causes | 2/3 | 67% | 67% | - | 565 | 93% | 95.8s | $0.000 |
