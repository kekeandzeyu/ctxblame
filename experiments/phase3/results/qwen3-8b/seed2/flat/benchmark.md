# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame_flat | 94% | 94% | 94% | 7% | 100% | 188.9 | 90% | 59.9s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| p0/tool_pair_readme_tests | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 160 | 94% | 40.2s | $0.000 |
| p0/user_message_pnpm | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 115 | 90% | 20.9s | $0.000 |
| p3/precond_2or_pnpm | precondition_or | ctxblame_flat | causes | 1/2 | 50% | 33% | FP | 170 | 90% | 48.6s | $0.000 |
| p3/precond_3or_unittest | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 360 | 88% | 67.4s | $0.000 |
| p3/tail_carrier_long_ctx | tail_long_ctx | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 285 | 97% | 71.1s | $0.000 |
| p3/two_carrier_ruff | or_redundant | ctxblame_flat | not_in_context | 0/2 | 0% | 0% | - | 40 | 95% | 183.6s | $0.000 |
| p3/negative_habit_only | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 87% | 3.0s | $0.000 |
| gen/0-001/hatch/tooldesc+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 430 | 92% | 74.3s | $0.000 |
| gen/0-003/pnpm/history+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 205 | 92% | 40.7s | $0.000 |
| gen/0-004/uv/system+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 190 | 91% | 42.0s | $0.000 |
| gen/0-006/cargo/tooldesc | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 120 | 89% | 19.1s | $0.000 |
| gen/0-008/tox/system+doc+user+pre | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 355 | 90% | 109.8s | $0.000 |
| gen/0-009/hatch/doc+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 190 | 92% | 41.8s | $0.000 |
| gen/0-010/make/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 91% | 1.9s | $0.000 |
| gen/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 445 | 91% | 97.3s | $0.000 |
| gen/0-012/uv/user/long | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 105 | 95% | 24.9s | $0.000 |
| gen/0-014/cargo/system+tooldesc+doc | or_redundant | ctxblame_flat | causes | 3/3 | 100% | 100% | - | 270 | 87% | 48.6s | $0.000 |
| gen/0-016/tox/doc+user+pre/long | precondition_or | ctxblame_flat | causes | 2/2 | 100% | 100% | YES | 245 | 95% | 86.3s | $0.000 |
| gen/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 470 | 89% | 92.3s | $0.000 |
| gen/0-018/make/user | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 120 | 91% | 23.8s | $0.000 |
| gen/0-019/pnpm/system+tooldesc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 225 | 87% | 43.0s | $0.000 |
| gen/0-022/cargo/system+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 165 | 90% | 33.6s | $0.000 |
| gen/0-024/tox/tooldesc+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 190 | 90% | 45.3s | $0.000 |
| gen/0-025/hatch/system+user/long | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 160 | 92% | 35.2s | $0.000 |
| gen/0-027/pnpm/system+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 165 | 90% | 37.1s | $0.000 |
| gen/0-028/uv/system+user | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 150 | 90% | 34.5s | $0.000 |
| gen/0-029/ruff/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 89% | 2.2s | $0.000 |
| gen/0-030/cargo/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 100 | 88% | 17.5s | $0.000 |
| gen/0-031/script/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 87% | 2.0s | $0.000 |
| gen/0-032/tox/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 87% | 2.3s | $0.000 |
| gen/0-034/make/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 90% | 1.7s | $0.000 |
| gen/0-035/pnpm/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 89% | 2.0s | $0.000 |
| gen/0-037/ruff/tooldesc+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 235 | 88% | 442.7s | $0.000 |
| gen/0-038/cargo/tooldesc+user+history+pre | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 385 | 90% | 64.4s | $0.000 |
| gen/0-039/script/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 91% | 2.0s | $0.000 |
| gen/0-040/tox/system+tooldesc | or_redundant | ctxblame_flat | none_found | 0/2 | 0% | 0% | - | 275 | 88% | 54.5s | $0.000 |
| gen/0-043/pnpm/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 92% | 1.9s | $0.000 |
| gen/0-045/ruff/history+pre/long | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 330 | 92% | 55.8s | $0.000 |
| gen/0-046/cargo/system+user | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 155 | 89% | 28.6s | $0.000 |
| gen/0-048/tox/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 105 | 89% | 19.1s | $0.000 |
| gen/0-049/hatch/system+user | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 160 | 91% | 29.7s | $0.000 |
| gen/0-051/pnpm/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 92% | 2.0s | $0.000 |
| gen/0-052/uv/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 85% | 2.0s | $0.000 |
| gen/0-053/ruff/system+tooldesc+user | or_redundant | ctxblame_flat | causes | 3/3 | 100% | 100% | - | 480 | 89% | 623.0s | $0.000 |
| gen/0-054/cargo/tooldesc | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 110 | 88% | 17.4s | $0.000 |
| gen/0-055/script/system+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 215 | 92% | 42.9s | $0.000 |
| gen/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 410 | 93% | 99.2s | $0.000 |
| gen/0-058/make/doc+user/long | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 330 | 95% | 67.1s | $0.000 |
| gen/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame_flat | causes | 3/3 | 100% | 100% | - | 395 | 88% | 71.9s | $0.000 |
| gen/0-060/uv/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 120 | 88% | 31.4s | $0.000 |
| gen/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame_flat | causes | 2/2 | 100% | 100% | YES | 265 | 87% | 50.1s | $0.000 |
| gen/0-062/cargo/system+tooldesc+doc | or_redundant | ctxblame_flat | causes | 3/3 | 100% | 100% | - | 315 | 89% | 49.7s | $0.000 |
| gen/0-063/script/doc | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 130 | 94% | 23.6s | $0.000 |
