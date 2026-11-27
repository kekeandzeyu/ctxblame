# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 89% | 86% | 87% | 9% | 100% | 306.7 | 91% | 84.0s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| p0/system_section_deploy_freeze | single | ctxblame | causes | 1/1 | 100% | 50% | - | 180 | 90% | 36.6s | $0.000 |
| p3/precond_2or_pnpm | precondition_or | ctxblame | causes | 0/2 | 0% | 0% | FP | 175 | 90% | 45.0s | $0.000 |
| p3/tail_carrier_long_ctx | tail_long_ctx | ctxblame | causes | 1/1 | 100% | 100% | - | 1875 | 85% | 598.0s | $0.000 |
| p3/two_carrier_ruff | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 275 | 87% | 177.0s | $0.000 |
| p3/negative_habit_only | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 87% | 7.1s | $0.000 |
| gen/0-000/tox/user/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 94% | 29.1s | $0.000 |
| gen/0-001/hatch/tooldesc+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 310 | 92% | 68.0s | $0.000 |
| gen/0-002/make/system+tooldesc+doc+pre | precondition_or | ctxblame | causes | 2/3 | 67% | 67% | YES | 710 | 90% | 175.1s | $0.000 |
| gen/0-003/pnpm/history+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 170 | 93% | 32.1s | $0.000 |
| gen/0-005/ruff/system+doc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 355 | 91% | 163.5s | $0.000 |
| gen/0-006/cargo/tooldesc | single | ctxblame | causes | 1/1 | 100% | 33% | - | 990 | 90% | 215.9s | $0.000 |
| gen/0-008/tox/system+doc+user+pre | precondition_or | ctxblame | none_found | 0/3 | 0% | 0% | YES | 1010 | 93% | 258.5s | $0.000 |
| gen/0-009/hatch/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 170 | 93% | 38.0s | $0.000 |
| gen/0-010/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 6.6s | $0.000 |
| gen/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 400 | 91% | 92.9s | $0.000 |
| gen/0-013/ruff/doc+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 265 | 93% | 79.1s | $0.000 |
| gen/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 455 | 90% | 184.6s | $0.000 |
| gen/0-019/pnpm/system+tooldesc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 225 | 86% | 58.1s | $0.000 |
| gen/0-021/ruff/doc/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 110 | 94% | 39.4s | $0.000 |
| gen/0-022/cargo/system+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 220 | 90% | 52.5s | $0.000 |
| gen/0-025/hatch/system+user/long | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 205 | 91% | 54.6s | $0.000 |
| gen/0-026/make/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 380 | 90% | 94.4s | $0.000 |
| gen/0-027/pnpm/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 220 | 91% | 59.7s | $0.000 |
| gen/0-029/ruff/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 10.0s | $0.000 |
| gen/0-030/cargo/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 110 | 88% | 26.2s | $0.000 |
| gen/0-031/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 90% | 9.7s | $0.000 |
| gen/0-032/tox/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 90% | 11.4s | $0.000 |
| gen/0-033/hatch/system | single | ctxblame | causes | 0/1 | 0% | 0% | - | 155 | 90% | 39.4s | $0.000 |
| gen/0-034/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 8.5s | $0.000 |
| gen/0-035/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 90% | 10.6s | $0.000 |
| gen/0-037/ruff/tooldesc+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 235 | 90% | 79.0s | $0.000 |
| gen/0-039/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 8.9s | $0.000 |
| gen/0-041/hatch/tooldesc+doc+user | or_redundant | ctxblame | causes | 2/3 | 67% | 29% | - | 1055 | 93% | 250.3s | $0.000 |
| gen/0-042/make/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 325 | 93% | 95.8s | $0.000 |
| gen/0-043/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 92% | 8.9s | $0.000 |
| gen/0-046/cargo/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 250 | 90% | 60.1s | $0.000 |
| gen/0-048/tox/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 125 | 89% | 35.1s | $0.000 |
| gen/0-049/hatch/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 255 | 91% | 66.6s | $0.000 |
| gen/0-053/ruff/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 340 | 89% | 101.5s | $0.000 |
| gen/0-054/cargo/tooldesc | single | ctxblame | causes | 1/1 | 100% | 100% | - | 245 | 91% | 55.0s | $0.000 |
| gen/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 420 | 93% | 109.1s | $0.000 |
| gen/0-057/hatch/doc | single | ctxblame | causes | 1/1 | 100% | 100% | - | 145 | 93% | 33.5s | $0.000 |
| gen/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 340 | 90% | 78.7s | $0.000 |
| gen/0-060/uv/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 88% | 30.9s | $0.000 |
| gen/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 305 | 91% | 73.7s | $0.000 |
| gen/0-062/cargo/system+tooldesc+doc | or_redundant | ctxblame | causes | 2/3 | 67% | 100% | - | 485 | 92% | 93.3s | $0.000 |
