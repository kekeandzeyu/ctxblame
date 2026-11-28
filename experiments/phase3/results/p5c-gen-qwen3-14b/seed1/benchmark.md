# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 95% | 95% | 95% | 7% | 100% | 244.8 | 91% | 69.2s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| p0/tool_result_sentence_config | single | ctxblame | none_found | 0/1 | 0% | 0% | - | 220 | 90% | 51.3s | $0.000 |
| p0/user_message_pnpm | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 90% | 38.6s | $0.000 |
| p0/system_section_deploy_freeze | single | ctxblame | causes | 1/1 | 100% | 100% | - | 135 | 88% | 60.2s | $0.000 |
| p3/precond_2or_pnpm | precondition_or | ctxblame | causes | 0/2 | 0% | 0% | FP | 235 | 91% | 79.3s | $0.000 |
| p3/precond_3or_unittest | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 395 | 89% | 108.4s | $0.000 |
| p3/tail_carrier_long_ctx | tail_long_ctx | ctxblame | causes | 1/1 | 100% | 100% | - | 190 | 95% | 68.1s | $0.000 |
| p3/two_carrier_ruff | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 295 | 87% | 95.2s | $0.000 |
| gen/0-000/tox/user/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 95% | 50.7s | $0.000 |
| gen/0-001/hatch/tooldesc+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 290 | 91% | 79.0s | $0.000 |
| gen/0-008/tox/system+doc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 450 | 91% | 144.0s | $0.000 |
| gen/0-009/hatch/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 205 | 92% | 63.8s | $0.000 |
| gen/0-010/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 11.2s | $0.000 |
| gen/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 470 | 93% | 144.9s | $0.000 |
| gen/0-012/uv/user/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 125 | 95% | 45.2s | $0.000 |
| gen/0-013/ruff/doc+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 380 | 94% | 98.6s | $0.000 |
| gen/0-016/tox/doc+user+pre/long | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 345 | 95% | 110.4s | $0.000 |
| gen/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 465 | 90% | 138.2s | $0.000 |
| gen/0-018/make/user | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 90% | 41.5s | $0.000 |
| gen/0-019/pnpm/system+tooldesc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 265 | 89% | 78.1s | $0.000 |
| gen/0-022/cargo/system+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 260 | 91% | 72.5s | $0.000 |
| gen/0-024/tox/tooldesc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 230 | 91% | 84.1s | $0.000 |
| gen/0-025/hatch/system+user/long | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 245 | 93% | 68.0s | $0.000 |
| gen/0-027/pnpm/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 195 | 90% | 58.1s | $0.000 |
| gen/0-028/uv/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 335 | 92% | 110.6s | $0.000 |
| gen/0-029/ruff/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 90% | 13.5s | $0.000 |
| gen/0-030/cargo/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 87% | 34.3s | $0.000 |
| gen/0-031/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 10.9s | $0.000 |
| gen/0-032/tox/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 12.8s | $0.000 |
| gen/0-033/hatch/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 88% | 34.2s | $0.000 |
| gen/0-034/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 10.6s | $0.000 |
| gen/0-035/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 12.6s | $0.000 |
| gen/0-036/uv/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 210 | 91% | 61.8s | $0.000 |
| gen/0-037/ruff/tooldesc+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 440 | 92% | 161.4s | $0.000 |
| gen/0-038/cargo/tooldesc+user+history+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 440 | 91% | 95.4s | $0.000 |
| gen/0-039/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 75 | 93% | 23.0s | $0.000 |
| gen/0-041/hatch/tooldesc+doc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 420 | 91% | 103.2s | $0.000 |
| gen/0-042/make/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 205 | 92% | 68.4s | $0.000 |
| gen/0-043/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 10.5s | $0.000 |
| gen/0-045/ruff/history+pre/long | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 550 | 94% | 131.8s | $0.000 |
| gen/0-048/tox/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 135 | 90% | 34.7s | $0.000 |
| gen/0-049/hatch/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 265 | 91% | 66.6s | $0.000 |
| gen/0-051/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 10.7s | $0.000 |
| gen/0-052/uv/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 800 | 88% | 158.8s | $0.000 |
| gen/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 445 | 94% | 114.5s | $0.000 |
| gen/0-057/hatch/doc | single | ctxblame | causes | 1/1 | 100% | 100% | - | 145 | 92% | 38.9s | $0.000 |
| gen/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 390 | 90% | 92.1s | $0.000 |
| gen/0-060/uv/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 87% | 49.4s | $0.000 |
| gen/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 320 | 90% | 71.5s | $0.000 |
