# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 89% | 89% | 89% | 0% | 100% | 230.6 | 91% | 61.8s | $0.000 |
| ctxblame_uncond | 84% | 75% | 78% | 100% | 100% | 202.9 | 94% | 56.3s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| p0/tool_result_sentence_config | single | ctxblame | none_found | 0/1 | 0% | 0% | - | 200 | 92% | 35.2s | $0.000 |
| p0/tool_result_sentence_config | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 210 | 91% | 53.9s | $0.000 |
| p0/user_message_pnpm | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 90% | 28.8s | $0.000 |
| p0/user_message_pnpm | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 150 | 93% | 28.9s | $0.000 |
| p0/system_section_deploy_freeze | single | ctxblame | causes | 1/1 | 100% | 100% | - | 135 | 92% | 48.8s | $0.000 |
| p0/system_section_deploy_freeze | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 135 | 91% | 47.3s | $0.000 |
| p3/precond_2or_pnpm | precondition_or | ctxblame | none_found | 0/2 | 0% | 0% | no | 195 | 90% | 51.4s | $0.000 |
| p3/precond_2or_pnpm | precondition_or | ctxblame_uncond | causes | 0/2 | 0% | 0% | FP | 160 | 93% | 44.9s | $0.000 |
| p3/precond_3or_unittest | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 395 | 89% | 101.0s | $0.000 |
| p3/precond_3or_unittest | precondition_or | ctxblame_uncond | causes | 0/3 | 0% | 0% | FP | 180 | 93% | 51.7s | $0.000 |
| p3/tail_carrier_long_ctx | tail_long_ctx | ctxblame | causes | 1/1 | 100% | 100% | - | 190 | 95% | 65.4s | $0.000 |
| p3/tail_carrier_long_ctx | tail_long_ctx | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 150 | 98% | 56.9s | $0.000 |
| p3/two_carrier_ruff | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 270 | 87% | 85.9s | $0.000 |
| p3/two_carrier_ruff | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 265 | 93% | 118.7s | $0.000 |
| gen/0-000/tox/user/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 95% | 49.2s | $0.000 |
| gen/0-000/tox/user/long | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 150 | 98% | 49.6s | $0.000 |
| gen/0-001/hatch/tooldesc+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 305 | 92% | 75.6s | $0.000 |
| gen/0-001/hatch/tooldesc+doc | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 285 | 95% | 66.0s | $0.000 |
| gen/0-008/tox/system+doc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 450 | 91% | 124.1s | $0.000 |
| gen/0-008/tox/system+doc+user+pre | precondition_or | ctxblame_uncond | causes | 0/3 | 0% | 0% | FP | 180 | 94% | 53.7s | $0.000 |
| gen/0-009/hatch/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 205 | 92% | 52.7s | $0.000 |
| gen/0-009/hatch/doc+pre | precondition_or | ctxblame_uncond | causes | 1/1 | 100% | 50% | FP | 220 | 93% | 58.9s | $0.000 |
| gen/0-010/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 8.0s | $0.000 |
| gen/0-010/make/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 94% | 9.1s | $0.000 |
| gen/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 470 | 93% | 137.2s | $0.000 |
| gen/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 480 | 97% | 140.9s | $0.000 |
| gen/0-012/uv/user/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 125 | 96% | 42.0s | $0.000 |
| gen/0-012/uv/user/long | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 125 | 96% | 41.9s | $0.000 |
| gen/0-013/ruff/doc+user | or_redundant | ctxblame | none_found | 0/2 | 0% | 0% | - | 330 | 94% | 87.7s | $0.000 |
| gen/0-013/ruff/doc+user | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 290 | 94% | 80.4s | $0.000 |
| gen/0-016/tox/doc+user+pre/long | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 345 | 95% | 107.1s | $0.000 |
| gen/0-016/tox/doc+user+pre/long | precondition_or | ctxblame_uncond | causes | 2/2 | 100% | 67% | FP | 355 | 97% | 110.1s | $0.000 |
| gen/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 465 | 90% | 130.0s | $0.000 |
| gen/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame_uncond | causes | 0/3 | 0% | 0% | FP | 205 | 94% | 66.3s | $0.000 |
| gen/0-018/make/user | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 90% | 44.4s | $0.000 |
| gen/0-018/make/user | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 150 | 93% | 45.6s | $0.000 |
| gen/0-019/pnpm/system+tooldesc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 265 | 89% | 69.7s | $0.000 |
| gen/0-019/pnpm/system+tooldesc | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 265 | 95% | 69.0s | $0.000 |
| gen/0-022/cargo/system+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 260 | 91% | 65.2s | $0.000 |
| gen/0-022/cargo/system+doc | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 260 | 95% | 65.2s | $0.000 |
| gen/0-024/tox/tooldesc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 230 | 91% | 72.3s | $0.000 |
| gen/0-024/tox/tooldesc+pre | precondition_or | ctxblame_uncond | causes | 1/1 | 100% | 50% | FP | 240 | 95% | 74.3s | $0.000 |
| gen/0-025/hatch/system+user/long | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 245 | 93% | 59.5s | $0.000 |
| gen/0-025/hatch/system+user/long | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 245 | 97% | 56.6s | $0.000 |
| gen/0-027/pnpm/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 195 | 90% | 49.4s | $0.000 |
| gen/0-027/pnpm/system+pre | precondition_or | ctxblame_uncond | causes | 1/1 | 100% | 50% | FP | 200 | 93% | 50.6s | $0.000 |
| gen/0-028/uv/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 280 | 95% | 79.6s | $0.000 |
| gen/0-028/uv/system+user | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 260 | 92% | 74.1s | $0.000 |
| gen/0-029/ruff/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 90% | 9.9s | $0.000 |
| gen/0-029/ruff/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 95% | 10.1s | $0.000 |
| gen/0-030/cargo/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 87% | 30.1s | $0.000 |
| gen/0-030/cargo/system | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 130 | 93% | 30.4s | $0.000 |
| gen/0-031/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 9.6s | $0.000 |
| gen/0-031/script/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 95% | 9.5s | $0.000 |
| gen/0-032/tox/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 11.1s | $0.000 |
| gen/0-032/tox/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 95% | 12.0s | $0.000 |
| gen/0-033/hatch/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 88% | 28.8s | $0.000 |
| gen/0-033/hatch/system | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 130 | 93% | 28.6s | $0.000 |
| gen/0-034/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 8.1s | $0.000 |
| gen/0-034/make/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 97% | 8.3s | $0.000 |
| gen/0-035/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 9.6s | $0.000 |
| gen/0-035/pnpm/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 94% | 9.6s | $0.000 |
| gen/0-036/uv/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 210 | 91% | 58.8s | $0.000 |
| gen/0-036/uv/doc+pre | precondition_or | ctxblame_uncond | causes | 1/1 | 100% | 50% | FP | 220 | 93% | 61.5s | $0.000 |
| gen/0-037/ruff/tooldesc+doc | or_redundant | ctxblame | none_found | 0/2 | 0% | 0% | - | 280 | 91% | 87.7s | $0.000 |
| gen/0-037/ruff/tooldesc+doc | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 275 | 94% | 71.6s | $0.000 |
| gen/0-038/cargo/tooldesc+user+history+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 440 | 92% | 92.8s | $0.000 |
| gen/0-038/cargo/tooldesc+user+history+pre | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 445 | 95% | 95.0s | $0.000 |
| gen/0-039/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 465 | 91% | 109.8s | $0.000 |
| gen/0-039/script/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 75 | 95% | 21.7s | $0.000 |
| gen/0-041/hatch/tooldesc+doc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 420 | 91% | 103.0s | $0.000 |
| gen/0-041/hatch/tooldesc+doc+user | or_redundant | ctxblame_uncond | causes | 3/3 | 100% | 100% | - | 420 | 95% | 104.1s | $0.000 |
| gen/0-042/make/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 205 | 91% | 68.6s | $0.000 |
| gen/0-042/make/system+pre | precondition_or | ctxblame_uncond | causes | 0/1 | 0% | 0% | FP | 120 | 95% | 39.3s | $0.000 |
| gen/0-043/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 13.2s | $0.000 |
| gen/0-043/pnpm/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 96% | 12.2s | $0.000 |
| gen/0-045/ruff/history+pre/long | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 295 | 95% | 71.0s | $0.000 |
| gen/0-045/ruff/history+pre/long | precondition_or | ctxblame_uncond | causes | 1/1 | 100% | 50% | FP | 320 | 97% | 77.5s | $0.000 |
| gen/0-048/tox/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 135 | 90% | 35.7s | $0.000 |
| gen/0-048/tox/system | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 135 | 95% | 34.7s | $0.000 |
| gen/0-049/hatch/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 265 | 91% | 67.7s | $0.000 |
| gen/0-049/hatch/system+user | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 265 | 95% | 67.6s | $0.000 |
| gen/0-051/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 11.6s | $0.000 |
| gen/0-051/pnpm/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 95% | 11.5s | $0.000 |
| gen/0-052/uv/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 320 | 86% | 109.5s | $0.000 |
| gen/0-052/uv/neg | negative | ctxblame_uncond | none_found | OK | - | 100% | - | 425 | 87% | 138.0s | $0.000 |
| gen/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 445 | 94% | 122.3s | $0.000 |
| gen/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 455 | 97% | 122.7s | $0.000 |
| gen/0-057/hatch/doc | single | ctxblame | causes | 1/1 | 100% | 100% | - | 145 | 92% | 38.6s | $0.000 |
| gen/0-057/hatch/doc | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 145 | 94% | 38.7s | $0.000 |
| gen/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 390 | 93% | 98.4s | $0.000 |
| gen/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame_uncond | causes | 3/3 | 100% | 100% | - | 390 | 92% | 98.2s | $0.000 |
| gen/0-060/uv/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 87% | 45.7s | $0.000 |
| gen/0-060/uv/system | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 150 | 94% | 48.8s | $0.000 |
| gen/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 320 | 90% | 56.1s | $0.000 |
| gen/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame_uncond | causes | 0/2 | 0% | 0% | FP | 160 | 94% | 36.5s | $0.000 |
