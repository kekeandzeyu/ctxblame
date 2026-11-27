# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 85% | 83% | 84% | 18% | 100% | 314.2 | 91% | 83.7s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| p0/system_section_deploy_freeze | single | ctxblame | causes | 1/1 | 100% | 50% | - | 175 | 90% | 35.1s | $0.000 |
| p3/precond_2or_pnpm | precondition_or | ctxblame | causes | 0/2 | 0% | 0% | FP | 170 | 90% | 44.2s | $0.000 |
| p3/tail_carrier_long_ctx | tail_long_ctx | ctxblame | causes | 1/1 | 100% | 100% | - | 2130 | 85% | 644.9s | $0.000 |
| p3/two_carrier_ruff | or_redundant | ctxblame | causes | 1/2 | 50% | 100% | - | 255 | 87% | 100.6s | $0.000 |
| p3/negative_habit_only | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 87% | 7.3s | $0.000 |
| gen/0-000/tox/user/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 94% | 28.6s | $0.000 |
| gen/0-001/hatch/tooldesc+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 265 | 92% | 54.8s | $0.000 |
| gen/0-002/make/system+tooldesc+doc+pre | precondition_or | ctxblame | none_found | 0/3 | 0% | 0% | YES | 430 | 92% | 103.1s | $0.000 |
| gen/0-003/pnpm/history+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 50% | FP | 285 | 94% | 65.2s | $0.000 |
| gen/0-005/ruff/system+doc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 350 | 91% | 104.6s | $0.000 |
| gen/0-006/cargo/tooldesc | single | ctxblame | causes | 1/1 | 100% | 100% | - | 605 | 91% | 132.9s | $0.000 |
| gen/0-008/tox/system+doc+user+pre | precondition_or | ctxblame | causes | 1/3 | 33% | 20% | YES | 770 | 92% | 206.0s | $0.000 |
| gen/0-009/hatch/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 165 | 94% | 37.9s | $0.000 |
| gen/0-010/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 6.5s | $0.000 |
| gen/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 400 | 92% | 106.7s | $0.000 |
| gen/0-013/ruff/doc+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 270 | 93% | 96.6s | $0.000 |
| gen/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 455 | 90% | 184.0s | $0.000 |
| gen/0-019/pnpm/system+tooldesc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 225 | 88% | 57.5s | $0.000 |
| gen/0-021/ruff/doc/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 110 | 93% | 39.9s | $0.000 |
| gen/0-022/cargo/system+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 220 | 90% | 51.9s | $0.000 |
| gen/0-025/hatch/system+user/long | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 205 | 91% | 56.8s | $0.000 |
| gen/0-026/make/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 395 | 90% | 98.9s | $0.000 |
| gen/0-027/pnpm/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | no | 215 | 92% | 86.3s | $0.000 |
| gen/0-029/ruff/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 10.9s | $0.000 |
| gen/0-030/cargo/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 110 | 89% | 26.3s | $0.000 |
| gen/0-031/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 90% | 10.5s | $0.000 |
| gen/0-032/tox/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 90% | 11.0s | $0.000 |
| gen/0-033/hatch/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 160 | 91% | 39.4s | $0.000 |
| gen/0-034/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 7.4s | $0.000 |
| gen/0-035/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 90% | 9.6s | $0.000 |
| gen/0-037/ruff/tooldesc+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 245 | 91% | 80.2s | $0.000 |
| gen/0-039/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 9.1s | $0.000 |
| gen/0-041/hatch/tooldesc+doc+user | or_redundant | ctxblame | none_found | 0/3 | 0% | 0% | - | 1870 | 93% | 414.4s | $0.000 |
| gen/0-042/make/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | no | 275 | 93% | 105.3s | $0.000 |
| gen/0-043/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 92% | 10.1s | $0.000 |
| gen/0-046/cargo/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 235 | 91% | 55.9s | $0.000 |
| gen/0-048/tox/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 125 | 90% | 35.6s | $0.000 |
| gen/0-049/hatch/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 245 | 91% | 60.6s | $0.000 |
| gen/0-053/ruff/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 340 | 90% | 106.5s | $0.000 |
| gen/0-054/cargo/tooldesc | single | ctxblame | causes | 0/1 | 0% | 0% | - | 455 | 93% | 103.9s | $0.000 |
| gen/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 425 | 93% | 105.7s | $0.000 |
| gen/0-057/hatch/doc | single | ctxblame | causes | 1/1 | 100% | 100% | - | 140 | 93% | 32.0s | $0.000 |
| gen/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 340 | 89% | 79.8s | $0.000 |
| gen/0-060/uv/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 88% | 33.3s | $0.000 |
| gen/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 300 | 90% | 68.8s | $0.000 |
| gen/0-062/cargo/system+tooldesc+doc | or_redundant | ctxblame | causes | 2/3 | 67% | 67% | - | 475 | 93% | 86.0s | $0.000 |
