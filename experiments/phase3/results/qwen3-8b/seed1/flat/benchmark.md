# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame_flat | 94% | 94% | 94% | 7% | 100% | 188.5 | 90% | 52.1s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| p0/tool_pair_readme_tests | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 150 | 94% | 38.2s | $0.000 |
| p0/user_message_pnpm | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 115 | 90% | 21.2s | $0.000 |
| p3/precond_2or_pnpm | precondition_or | ctxblame_flat | causes | 1/2 | 50% | 33% | FP | 170 | 89% | 49.6s | $0.000 |
| p3/precond_3or_unittest | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 370 | 87% | 70.4s | $0.000 |
| p3/tail_carrier_long_ctx | tail_long_ctx | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 340 | 97% | 90.2s | $0.000 |
| p3/two_carrier_ruff | or_redundant | ctxblame_flat | not_in_context | 0/2 | 0% | 0% | - | 40 | 96% | 187.1s | $0.000 |
| p3/negative_habit_only | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 87% | 3.0s | $0.000 |
| gen/0-001/hatch/tooldesc+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 435 | 92% | 75.4s | $0.000 |
| gen/0-003/pnpm/history+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 215 | 92% | 43.7s | $0.000 |
| gen/0-004/uv/system+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 195 | 92% | 43.8s | $0.000 |
| gen/0-006/cargo/tooldesc | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 155 | 89% | 26.4s | $0.000 |
| gen/0-008/tox/system+doc+user+pre | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 355 | 89% | 110.6s | $0.000 |
| gen/0-009/hatch/doc+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 185 | 92% | 42.5s | $0.000 |
| gen/0-010/make/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 91% | 2.1s | $0.000 |
| gen/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 445 | 91% | 97.2s | $0.000 |
| gen/0-012/uv/user/long | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 105 | 94% | 26.8s | $0.000 |
| gen/0-014/cargo/system+tooldesc+doc | or_redundant | ctxblame_flat | causes | 3/3 | 100% | 100% | - | 270 | 87% | 49.8s | $0.000 |
| gen/0-016/tox/doc+user+pre/long | precondition_or | ctxblame_flat | causes | 2/2 | 100% | 100% | YES | 245 | 95% | 80.2s | $0.000 |
| gen/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 470 | 88% | 92.4s | $0.000 |
| gen/0-018/make/user | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 120 | 91% | 23.8s | $0.000 |
| gen/0-019/pnpm/system+tooldesc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 225 | 87% | 42.8s | $0.000 |
| gen/0-022/cargo/system+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 165 | 89% | 34.5s | $0.000 |
| gen/0-024/tox/tooldesc+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 190 | 90% | 46.0s | $0.000 |
| gen/0-025/hatch/system+user/long | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 160 | 91% | 35.8s | $0.000 |
| gen/0-027/pnpm/system+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 165 | 90% | 37.3s | $0.000 |
| gen/0-028/uv/system+user | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 150 | 90% | 34.7s | $0.000 |
| gen/0-029/ruff/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 89% | 2.2s | $0.000 |
| gen/0-030/cargo/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 100 | 87% | 18.2s | $0.000 |
| gen/0-031/script/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 87% | 1.9s | $0.000 |
| gen/0-032/tox/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 87% | 2.2s | $0.000 |
| gen/0-034/make/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 90% | 2.0s | $0.000 |
| gen/0-035/pnpm/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 89% | 2.1s | $0.000 |
| gen/0-037/ruff/tooldesc+doc | or_redundant | ctxblame_flat | not_in_context | 0/2 | 0% | 0% | - | 40 | 90% | 160.1s | $0.000 |
| gen/0-038/cargo/tooldesc+user+history+pre | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 385 | 90% | 65.8s | $0.000 |
| gen/0-039/script/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 91% | 1.9s | $0.000 |
| gen/0-040/tox/system+tooldesc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 380 | 88% | 68.3s | $0.000 |
| gen/0-043/pnpm/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 92% | 1.9s | $0.000 |
| gen/0-045/ruff/history+pre/long | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 325 | 92% | 56.5s | $0.000 |
| gen/0-046/cargo/system+user | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 155 | 89% | 28.2s | $0.000 |
| gen/0-048/tox/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 105 | 90% | 19.1s | $0.000 |
| gen/0-049/hatch/system+user | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 160 | 90% | 29.5s | $0.000 |
| gen/0-051/pnpm/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 92% | 1.9s | $0.000 |
| gen/0-052/uv/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 85% | 1.9s | $0.000 |
| gen/0-053/ruff/system+tooldesc+user | or_redundant | ctxblame_flat | causes | 3/3 | 100% | 100% | - | 450 | 89% | 435.4s | $0.000 |
| gen/0-054/cargo/tooldesc | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 115 | 88% | 18.6s | $0.000 |
| gen/0-055/script/system+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 175 | 91% | 36.1s | $0.000 |
| gen/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 410 | 93% | 98.0s | $0.000 |
| gen/0-058/make/doc+user/long | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 365 | 96% | 74.6s | $0.000 |
| gen/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame_flat | causes | 3/3 | 100% | 100% | - | 395 | 88% | 72.0s | $0.000 |
| gen/0-060/uv/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 120 | 87% | 31.0s | $0.000 |
| gen/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame_flat | causes | 2/2 | 100% | 100% | YES | 265 | 88% | 50.5s | $0.000 |
| gen/0-062/cargo/system+tooldesc+doc | or_redundant | ctxblame_flat | causes | 3/3 | 100% | 100% | - | 315 | 89% | 51.8s | $0.000 |
| gen/0-063/script/doc | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 130 | 95% | 25.2s | $0.000 |
