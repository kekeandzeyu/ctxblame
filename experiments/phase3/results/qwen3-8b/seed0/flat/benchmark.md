# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame_flat | 99% | 98% | 99% | 7% | 100% | 202.5 | 90% | 82.2s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| p0/tool_pair_readme_tests | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 195 | 92% | 51.1s | $0.000 |
| p0/user_message_pnpm | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 110 | 90% | 20.0s | $0.000 |
| p3/precond_2or_pnpm | precondition_or | ctxblame_flat | causes | 1/2 | 50% | 33% | FP | 170 | 90% | 49.3s | $0.000 |
| p3/precond_3or_unittest | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 360 | 87% | 68.2s | $0.000 |
| p3/tail_carrier_long_ctx | tail_long_ctx | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 385 | 97% | 99.2s | $0.000 |
| p3/two_carrier_ruff | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 485 | 88% | 1340.9s | $0.000 |
| p3/negative_habit_only | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 87% | 2.9s | $0.000 |
| gen/0-001/hatch/tooldesc+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 445 | 92% | 76.8s | $0.000 |
| gen/0-003/pnpm/history+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 225 | 91% | 45.1s | $0.000 |
| gen/0-004/uv/system+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 195 | 92% | 44.4s | $0.000 |
| gen/0-006/cargo/tooldesc | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 125 | 88% | 21.9s | $0.000 |
| gen/0-008/tox/system+doc+user+pre | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 355 | 89% | 116.8s | $0.000 |
| gen/0-009/hatch/doc+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 190 | 92% | 43.3s | $0.000 |
| gen/0-010/make/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 91% | 1.7s | $0.000 |
| gen/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 445 | 91% | 97.4s | $0.000 |
| gen/0-012/uv/user/long | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 105 | 95% | 25.7s | $0.000 |
| gen/0-014/cargo/system+tooldesc+doc | or_redundant | ctxblame_flat | causes | 3/3 | 100% | 100% | - | 270 | 87% | 49.6s | $0.000 |
| gen/0-016/tox/doc+user+pre/long | precondition_or | ctxblame_flat | causes | 2/2 | 100% | 100% | YES | 245 | 96% | 87.3s | $0.000 |
| gen/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 470 | 88% | 91.5s | $0.000 |
| gen/0-018/make/user | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 120 | 91% | 24.0s | $0.000 |
| gen/0-019/pnpm/system+tooldesc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 230 | 88% | 44.0s | $0.000 |
| gen/0-022/cargo/system+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 165 | 90% | 33.0s | $0.000 |
| gen/0-024/tox/tooldesc+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 190 | 89% | 44.1s | $0.000 |
| gen/0-025/hatch/system+user/long | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 160 | 92% | 34.4s | $0.000 |
| gen/0-027/pnpm/system+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 165 | 89% | 37.0s | $0.000 |
| gen/0-028/uv/system+user | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 150 | 90% | 33.8s | $0.000 |
| gen/0-029/ruff/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 89% | 2.4s | $0.000 |
| gen/0-030/cargo/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 100 | 88% | 18.3s | $0.000 |
| gen/0-031/script/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 87% | 2.1s | $0.000 |
| gen/0-032/tox/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 87% | 2.1s | $0.000 |
| gen/0-034/make/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 90% | 1.8s | $0.000 |
| gen/0-035/pnpm/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 89% | 2.1s | $0.000 |
| gen/0-037/ruff/tooldesc+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 310 | 88% | 599.0s | $0.000 |
| gen/0-038/cargo/tooldesc+user+history+pre | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 385 | 90% | 65.2s | $0.000 |
| gen/0-039/script/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 91% | 1.8s | $0.000 |
| gen/0-040/tox/system+tooldesc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 385 | 88% | 68.7s | $0.000 |
| gen/0-043/pnpm/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 92% | 2.0s | $0.000 |
| gen/0-045/ruff/history+pre/long | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 325 | 92% | 55.4s | $0.000 |
| gen/0-046/cargo/system+user | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 155 | 89% | 28.1s | $0.000 |
| gen/0-048/tox/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 105 | 88% | 18.6s | $0.000 |
| gen/0-049/hatch/system+user | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 160 | 90% | 29.1s | $0.000 |
| gen/0-051/pnpm/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 92% | 2.0s | $0.000 |
| gen/0-052/uv/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 85% | 1.9s | $0.000 |
| gen/0-053/ruff/system+tooldesc+user | or_redundant | ctxblame_flat | causes | 3/3 | 100% | 100% | - | 450 | 89% | 436.0s | $0.000 |
| gen/0-054/cargo/tooldesc | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 115 | 87% | 18.7s | $0.000 |
| gen/0-055/script/system+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 175 | 91% | 34.7s | $0.000 |
| gen/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 410 | 93% | 96.0s | $0.000 |
| gen/0-058/make/doc+user/long | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 310 | 95% | 61.7s | $0.000 |
| gen/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame_flat | causes | 3/3 | 100% | 100% | - | 395 | 88% | 71.9s | $0.000 |
| gen/0-060/uv/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 120 | 87% | 30.2s | $0.000 |
| gen/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame_flat | causes | 2/2 | 100% | 100% | YES | 265 | 88% | 50.8s | $0.000 |
| gen/0-062/cargo/system+tooldesc+doc | or_redundant | ctxblame_flat | causes | 3/3 | 100% | 100% | - | 315 | 89% | 49.0s | $0.000 |
| gen/0-063/script/doc | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 130 | 94% | 23.3s | $0.000 |
