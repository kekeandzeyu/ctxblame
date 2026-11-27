# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 92% | 90% | 90% | 9% | 100% | 312.4 | 91% | 84.5s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| p0/system_section_deploy_freeze | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 90% | 36.7s | $0.000 |
| p3/precond_2or_pnpm | precondition_or | ctxblame | causes | 0/2 | 0% | 0% | FP | 180 | 90% | 46.2s | $0.000 |
| p3/tail_carrier_long_ctx | tail_long_ctx | ctxblame | causes | 1/1 | 100% | 100% | - | 2600 | 88% | 771.5s | $0.000 |
| p3/two_carrier_ruff | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 270 | 87% | 189.5s | $0.000 |
| p3/negative_habit_only | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 87% | 7.1s | $0.000 |
| gen/0-000/tox/user/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 94% | 28.8s | $0.000 |
| gen/0-001/hatch/tooldesc+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 315 | 92% | 70.5s | $0.000 |
| gen/0-002/make/system+tooldesc+doc+pre | precondition_or | ctxblame | none_found | 0/3 | 0% | 0% | YES | 730 | 92% | 176.5s | $0.000 |
| gen/0-003/pnpm/history+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | no | 295 | 95% | 78.2s | $0.000 |
| gen/0-005/ruff/system+doc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 345 | 91% | 145.0s | $0.000 |
| gen/0-006/cargo/tooldesc | single | ctxblame | causes | 1/1 | 100% | 100% | - | 620 | 92% | 140.5s | $0.000 |
| gen/0-008/tox/system+doc+user+pre | precondition_or | ctxblame | causes | 2/3 | 67% | 100% | YES | 545 | 93% | 148.0s | $0.000 |
| gen/0-009/hatch/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 170 | 93% | 45.4s | $0.000 |
| gen/0-010/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 7.5s | $0.000 |
| gen/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 400 | 91% | 106.4s | $0.000 |
| gen/0-013/ruff/doc+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 250 | 92% | 89.2s | $0.000 |
| gen/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 440 | 90% | 162.6s | $0.000 |
| gen/0-019/pnpm/system+tooldesc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 225 | 87% | 57.3s | $0.000 |
| gen/0-021/ruff/doc/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 110 | 94% | 39.4s | $0.000 |
| gen/0-022/cargo/system+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 220 | 91% | 50.2s | $0.000 |
| gen/0-025/hatch/system+user/long | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 205 | 91% | 54.0s | $0.000 |
| gen/0-026/make/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 420 | 91% | 103.1s | $0.000 |
| gen/0-027/pnpm/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | no | 220 | 92% | 84.7s | $0.000 |
| gen/0-029/ruff/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 10.7s | $0.000 |
| gen/0-030/cargo/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 110 | 88% | 26.0s | $0.000 |
| gen/0-031/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 90% | 9.7s | $0.000 |
| gen/0-032/tox/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 90% | 10.8s | $0.000 |
| gen/0-033/hatch/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 170 | 92% | 45.6s | $0.000 |
| gen/0-034/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 7.9s | $0.000 |
| gen/0-035/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 90% | 9.9s | $0.000 |
| gen/0-037/ruff/tooldesc+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 235 | 91% | 73.2s | $0.000 |
| gen/0-039/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 9.3s | $0.000 |
| gen/0-041/hatch/tooldesc+doc+user | or_redundant | ctxblame | causes | 2/3 | 67% | 29% | - | 1035 | 93% | 235.0s | $0.000 |
| gen/0-042/make/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 400 | 93% | 107.7s | $0.000 |
| gen/0-043/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 92% | 8.2s | $0.000 |
| gen/0-046/cargo/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 225 | 90% | 49.4s | $0.000 |
| gen/0-048/tox/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 115 | 89% | 29.7s | $0.000 |
| gen/0-049/hatch/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 235 | 91% | 57.3s | $0.000 |
| gen/0-053/ruff/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 340 | 89% | 91.5s | $0.000 |
| gen/0-054/cargo/tooldesc | single | ctxblame | causes | 1/1 | 100% | 33% | - | 450 | 92% | 93.2s | $0.000 |
| gen/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 410 | 93% | 93.1s | $0.000 |
| gen/0-057/hatch/doc | single | ctxblame | causes | 1/1 | 100% | 100% | - | 125 | 92% | 27.6s | $0.000 |
| gen/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 340 | 89% | 68.8s | $0.000 |
| gen/0-060/uv/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 89% | 27.2s | $0.000 |
| gen/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 305 | 91% | 63.0s | $0.000 |
| gen/0-062/cargo/system+tooldesc+doc | or_redundant | ctxblame | causes | 2/3 | 67% | 67% | - | 545 | 93% | 92.0s | $0.000 |
