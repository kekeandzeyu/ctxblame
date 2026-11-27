# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 88% | 88% | 87% | 18% | 100% | 313.0 | 91% | 84.7s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| p0/system_section_deploy_freeze | single | ctxblame | causes | 1/1 | 100% | 50% | - | 200 | 90% | 41.0s | $0.000 |
| p3/precond_2or_pnpm | precondition_or | ctxblame | causes | 0/2 | 0% | 0% | FP | 155 | 90% | 38.4s | $0.000 |
| p3/tail_carrier_long_ctx | tail_long_ctx | ctxblame | causes | 1/1 | 100% | 100% | - | 2185 | 86% | 642.7s | $0.000 |
| p3/two_carrier_ruff | or_redundant | ctxblame | causes | 1/2 | 50% | 100% | - | 285 | 88% | 184.3s | $0.000 |
| p3/negative_habit_only | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 86% | 7.2s | $0.000 |
| gen/0-000/tox/user/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 94% | 29.1s | $0.000 |
| gen/0-001/hatch/tooldesc+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 305 | 92% | 64.3s | $0.000 |
| gen/0-002/make/system+tooldesc+doc+pre | precondition_or | ctxblame | none_found | 0/3 | 0% | 0% | YES | 460 | 92% | 113.6s | $0.000 |
| gen/0-003/pnpm/history+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 50% | FP | 320 | 94% | 76.0s | $0.000 |
| gen/0-005/ruff/system+doc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 385 | 92% | 149.0s | $0.000 |
| gen/0-006/cargo/tooldesc | single | ctxblame | causes | 1/1 | 100% | 25% | - | 950 | 91% | 216.4s | $0.000 |
| gen/0-008/tox/system+doc+user+pre | precondition_or | ctxblame | causes | 2/3 | 67% | 100% | YES | 755 | 94% | 204.8s | $0.000 |
| gen/0-009/hatch/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 170 | 93% | 46.5s | $0.000 |
| gen/0-010/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 7.8s | $0.000 |
| gen/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 430 | 92% | 114.0s | $0.000 |
| gen/0-013/ruff/doc+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 280 | 93% | 98.8s | $0.000 |
| gen/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 480 | 91% | 184.8s | $0.000 |
| gen/0-019/pnpm/system+tooldesc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 245 | 88% | 62.5s | $0.000 |
| gen/0-021/ruff/doc/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 110 | 94% | 39.9s | $0.000 |
| gen/0-022/cargo/system+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 240 | 91% | 56.1s | $0.000 |
| gen/0-025/hatch/system+user/long | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 225 | 92% | 61.1s | $0.000 |
| gen/0-026/make/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 405 | 91% | 98.1s | $0.000 |
| gen/0-027/pnpm/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | no | 420 | 91% | 129.3s | $0.000 |
| gen/0-029/ruff/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 11.2s | $0.000 |
| gen/0-030/cargo/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 120 | 89% | 29.0s | $0.000 |
| gen/0-031/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 90% | 9.7s | $0.000 |
| gen/0-032/tox/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 90% | 11.8s | $0.000 |
| gen/0-033/hatch/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 190 | 92% | 48.4s | $0.000 |
| gen/0-034/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 8.1s | $0.000 |
| gen/0-035/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 90% | 10.5s | $0.000 |
| gen/0-037/ruff/tooldesc+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 255 | 91% | 79.1s | $0.000 |
| gen/0-039/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 9.6s | $0.000 |
| gen/0-041/hatch/tooldesc+doc+user | or_redundant | ctxblame | causes | 2/3 | 67% | 33% | - | 1110 | 94% | 258.2s | $0.000 |
| gen/0-042/make/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 355 | 93% | 97.3s | $0.000 |
| gen/0-043/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 92% | 10.2s | $0.000 |
| gen/0-046/cargo/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 255 | 90% | 53.8s | $0.000 |
| gen/0-048/tox/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 125 | 89% | 31.4s | $0.000 |
| gen/0-049/hatch/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 265 | 92% | 63.0s | $0.000 |
| gen/0-053/ruff/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 370 | 90% | 103.7s | $0.000 |
| gen/0-054/cargo/tooldesc | single | ctxblame | no_stable_decision | 0/1 | 0% | - | - | 0 | - | 1.3s | $0.000 |
| gen/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 450 | 94% | 97.1s | $0.000 |
| gen/0-057/hatch/doc | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 92% | 33.4s | $0.000 |
| gen/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 370 | 90% | 78.7s | $0.000 |
| gen/0-060/uv/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 89% | 28.7s | $0.000 |
| gen/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 310 | 91% | 65.8s | $0.000 |
| gen/0-062/cargo/system+tooldesc+doc | or_redundant | ctxblame | causes | 2/3 | 67% | 100% | - | 450 | 92% | 90.4s | $0.000 |
