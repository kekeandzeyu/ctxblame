# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 95% | 88% | 90% | 40% | 100% | 279.4 | 91% | 43.2s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| p0/tool_result_sentence_config | single | ctxblame | causes | 1/1 | 100% | 100% | - | 295 | 91% | 31.5s | $0.000 |
| p0/user_message_pnpm | single | ctxblame | causes | 1/1 | 100% | 100% | - | 145 | 90% | 20.1s | $0.000 |
| p0/system_section_deploy_freeze | single | ctxblame | causes | 1/1 | 100% | 100% | - | 135 | 88% | 31.7s | $0.000 |
| p3/precond_2or_pnpm | precondition_or | ctxblame | causes | 0/2 | 0% | 0% | FP | 170 | 89% | 33.1s | $0.000 |
| p3/precond_3or_unittest | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 495 | 90% | 67.6s | $0.000 |
| p3/tail_carrier_long_ctx | tail_long_ctx | ctxblame | causes | 1/1 | 100% | 100% | - | 190 | 96% | 37.8s | $0.000 |
| p3/two_carrier_ruff | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 340 | 87% | 99.8s | $0.000 |
| gen/0-000/tox/user/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 96% | 27.0s | $0.000 |
| gen/0-001/hatch/tooldesc+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 350 | 92% | 49.3s | $0.000 |
| gen/0-008/tox/system+doc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 550 | 92% | 89.7s | $0.000 |
| gen/0-009/hatch/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 50% | FP | 275 | 91% | 43.2s | $0.000 |
| gen/0-010/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 87% | 6.6s | $0.000 |
| gen/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 570 | 94% | 91.7s | $0.000 |
| gen/0-012/uv/user/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 125 | 95% | 23.4s | $0.000 |
| gen/0-013/ruff/doc+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 410 | 94% | 59.9s | $0.000 |
| gen/0-016/tox/doc+user+pre/long | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 425 | 96% | 70.9s | $0.000 |
| gen/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 565 | 91% | 86.4s | $0.000 |
| gen/0-018/make/user | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 90% | 23.3s | $0.000 |
| gen/0-019/pnpm/system+tooldesc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 325 | 90% | 50.3s | $0.000 |
| gen/0-022/cargo/system+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 320 | 92% | 49.2s | $0.000 |
| gen/0-024/tox/tooldesc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 250 | 90% | 49.3s | $0.000 |
| gen/0-025/hatch/system+user/long | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 305 | 95% | 45.3s | $0.000 |
| gen/0-027/pnpm/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 50% | FP | 260 | 90% | 44.5s | $0.000 |
| gen/0-028/uv/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 335 | 93% | 53.6s | $0.000 |
| gen/0-029/ruff/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 88% | 7.2s | $0.000 |
| gen/0-030/cargo/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 87% | 20.6s | $0.000 |
| gen/0-031/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 6.8s | $0.000 |
| gen/0-032/tox/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 7.0s | $0.000 |
| gen/0-033/hatch/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 87% | 18.5s | $0.000 |
| gen/0-034/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 5.7s | $0.000 |
| gen/0-035/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 6.5s | $0.000 |
| gen/0-036/uv/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 50% | FP | 275 | 92% | 43.9s | $0.000 |
| gen/0-037/ruff/tooldesc+doc | or_redundant | ctxblame | none_found | 0/2 | 0% | 0% | - | 445 | 92% | 69.1s | $0.000 |
| gen/0-038/cargo/tooldesc+user+history+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 540 | 92% | 65.5s | $0.000 |
| gen/0-039/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 835 | 88% | 122.1s | $0.000 |
| gen/0-041/hatch/tooldesc+doc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 500 | 92% | 68.0s | $0.000 |
| gen/0-042/make/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 50% | FP | 280 | 91% | 49.9s | $0.000 |
| gen/0-043/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 5.7s | $0.000 |
| gen/0-045/ruff/history+pre/long | precondition_or | ctxblame | causes | 1/1 | 100% | 50% | FP | 335 | 96% | 45.9s | $0.000 |
| gen/0-048/tox/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 135 | 89% | 20.8s | $0.000 |
| gen/0-049/hatch/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 325 | 92% | 44.6s | $0.000 |
| gen/0-051/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 7.9s | $0.000 |
| gen/0-052/uv/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 295 | 84% | 53.1s | $0.000 |
| gen/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 570 | 95% | 70.2s | $0.000 |
| gen/0-057/hatch/doc | single | ctxblame | causes | 1/1 | 100% | 100% | - | 140 | 92% | 21.2s | $0.000 |
| gen/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 470 | 91% | 57.6s | $0.000 |
| gen/0-060/uv/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 87% | 25.3s | $0.000 |
| gen/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 400 | 91% | 46.9s | $0.000 |
