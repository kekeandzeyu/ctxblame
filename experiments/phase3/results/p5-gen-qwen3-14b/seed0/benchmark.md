# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 89% | 89% | 89% | 7% | 90% | 227.1 | 91% | 61.6s | $0.000 |
| ctxblame_uncond | 82% | 72% | 76% | 100% | 100% | 204.7 | 94% | 55.4s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| p0/tool_result_sentence_config | single | ctxblame | none_found | 0/1 | 0% | 0% | - | 200 | 90% | 33.4s | $0.000 |
| p0/tool_result_sentence_config | single | ctxblame_uncond | causes | 0/1 | 0% | 0% | - | 230 | 93% | 58.2s | $0.000 |
| p0/user_message_pnpm | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 91% | 63.7s | $0.000 |
| p0/user_message_pnpm | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 145 | 92% | 26.4s | $0.000 |
| p0/system_section_deploy_freeze | single | ctxblame | causes | 1/1 | 100% | 100% | - | 135 | 90% | 44.7s | $0.000 |
| p0/system_section_deploy_freeze | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 135 | 93% | 45.0s | $0.000 |
| p3/precond_2or_pnpm | precondition_or | ctxblame | causes | 0/2 | 0% | 0% | FP | 170 | 93% | 46.0s | $0.000 |
| p3/precond_2or_pnpm | precondition_or | ctxblame_uncond | causes | 0/2 | 0% | 0% | FP | 160 | 88% | 40.6s | $0.000 |
| p3/precond_3or_unittest | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 395 | 89% | 96.5s | $0.000 |
| p3/precond_3or_unittest | precondition_or | ctxblame_uncond | causes | 0/3 | 0% | 0% | FP | 180 | 95% | 49.5s | $0.000 |
| p3/tail_carrier_long_ctx | tail_long_ctx | ctxblame | causes | 1/1 | 100% | 100% | - | 190 | 98% | 62.5s | $0.000 |
| p3/tail_carrier_long_ctx | tail_long_ctx | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 150 | 97% | 52.7s | $0.000 |
| p3/two_carrier_ruff | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 280 | 92% | 121.3s | $0.000 |
| p3/two_carrier_ruff | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 265 | 88% | 84.3s | $0.000 |
| gen/0-000/tox/user/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 96% | 47.8s | $0.000 |
| gen/0-000/tox/user/long | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 150 | 98% | 47.1s | $0.000 |
| gen/0-001/hatch/tooldesc+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 290 | 91% | 68.5s | $0.000 |
| gen/0-001/hatch/tooldesc+doc | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 285 | 95% | 66.9s | $0.000 |
| gen/0-008/tox/system+doc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 450 | 91% | 126.4s | $0.000 |
| gen/0-008/tox/system+doc+user+pre | precondition_or | ctxblame_uncond | causes | 0/3 | 0% | 0% | FP | 180 | 95% | 54.6s | $0.000 |
| gen/0-009/hatch/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 210 | 91% | 55.6s | $0.000 |
| gen/0-009/hatch/doc+pre | precondition_or | ctxblame_uncond | causes | 1/1 | 100% | 50% | FP | 220 | 93% | 58.4s | $0.000 |
| gen/0-010/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 8.4s | $0.000 |
| gen/0-010/make/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 94% | 8.0s | $0.000 |
| gen/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 470 | 93% | 136.6s | $0.000 |
| gen/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 480 | 97% | 139.6s | $0.000 |
| gen/0-012/uv/user/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 125 | 95% | 41.8s | $0.000 |
| gen/0-012/uv/user/long | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 125 | 98% | 40.5s | $0.000 |
| gen/0-013/ruff/doc+user | or_redundant | ctxblame | none_found | 0/2 | 0% | 0% | - | 335 | 94% | 88.3s | $0.000 |
| gen/0-013/ruff/doc+user | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 290 | 94% | 81.0s | $0.000 |
| gen/0-016/tox/doc+user+pre/long | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 345 | 96% | 103.4s | $0.000 |
| gen/0-016/tox/doc+user+pre/long | precondition_or | ctxblame_uncond | causes | 2/2 | 100% | 67% | FP | 355 | 97% | 107.3s | $0.000 |
| gen/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 465 | 90% | 129.5s | $0.000 |
| gen/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame_uncond | causes | 0/3 | 0% | 0% | FP | 205 | 94% | 64.8s | $0.000 |
| gen/0-018/make/user | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 90% | 43.3s | $0.000 |
| gen/0-018/make/user | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 150 | 94% | 43.4s | $0.000 |
| gen/0-019/pnpm/system+tooldesc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 265 | 89% | 69.8s | $0.000 |
| gen/0-019/pnpm/system+tooldesc | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 265 | 95% | 70.0s | $0.000 |
| gen/0-022/cargo/system+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 260 | 91% | 66.8s | $0.000 |
| gen/0-022/cargo/system+doc | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 260 | 95% | 66.8s | $0.000 |
| gen/0-024/tox/tooldesc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 230 | 90% | 73.5s | $0.000 |
| gen/0-024/tox/tooldesc+pre | precondition_or | ctxblame_uncond | causes | 1/1 | 100% | 50% | FP | 240 | 95% | 76.6s | $0.000 |
| gen/0-025/hatch/system+user/long | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 245 | 94% | 59.0s | $0.000 |
| gen/0-025/hatch/system+user/long | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 245 | 97% | 57.0s | $0.000 |
| gen/0-027/pnpm/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 195 | 90% | 49.7s | $0.000 |
| gen/0-027/pnpm/system+pre | precondition_or | ctxblame_uncond | causes | 1/1 | 100% | 50% | FP | 200 | 93% | 51.3s | $0.000 |
| gen/0-028/uv/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 285 | 95% | 81.9s | $0.000 |
| gen/0-028/uv/system+user | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 260 | 92% | 75.9s | $0.000 |
| gen/0-029/ruff/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 90% | 10.5s | $0.000 |
| gen/0-029/ruff/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 95% | 10.4s | $0.000 |
| gen/0-030/cargo/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 87% | 31.2s | $0.000 |
| gen/0-030/cargo/system | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 130 | 93% | 31.2s | $0.000 |
| gen/0-031/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 9.8s | $0.000 |
| gen/0-031/script/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 95% | 10.4s | $0.000 |
| gen/0-032/tox/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 13.0s | $0.000 |
| gen/0-032/tox/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 95% | 11.4s | $0.000 |
| gen/0-033/hatch/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 87% | 29.8s | $0.000 |
| gen/0-033/hatch/system | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 130 | 93% | 28.9s | $0.000 |
| gen/0-034/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 8.2s | $0.000 |
| gen/0-034/make/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 97% | 8.2s | $0.000 |
| gen/0-035/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 9.4s | $0.000 |
| gen/0-035/pnpm/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 94% | 10.0s | $0.000 |
| gen/0-036/uv/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 210 | 92% | 57.0s | $0.000 |
| gen/0-036/uv/doc+pre | precondition_or | ctxblame_uncond | causes | 1/1 | 100% | 50% | FP | 220 | 93% | 60.3s | $0.000 |
| gen/0-037/ruff/tooldesc+doc | or_redundant | ctxblame | none_found | 0/2 | 0% | 0% | - | 270 | 91% | 81.2s | $0.000 |
| gen/0-037/ruff/tooldesc+doc | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 275 | 94% | 67.8s | $0.000 |
| gen/0-038/cargo/tooldesc+user+history+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 440 | 92% | 88.6s | $0.000 |
| gen/0-038/cargo/tooldesc+user+history+pre | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 445 | 95% | 90.8s | $0.000 |
| gen/0-039/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 50 | 92% | 11.8s | $0.000 |
| gen/0-039/script/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 45 | 96% | 10.2s | $0.000 |
| gen/0-041/hatch/tooldesc+doc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 420 | 92% | 98.5s | $0.000 |
| gen/0-041/hatch/tooldesc+doc+user | or_redundant | ctxblame_uncond | causes | 3/3 | 100% | 100% | - | 420 | 95% | 99.0s | $0.000 |
| gen/0-042/make/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 215 | 91% | 72.2s | $0.000 |
| gen/0-042/make/system+pre | precondition_or | ctxblame_uncond | causes | 0/1 | 0% | 0% | FP | 120 | 94% | 36.3s | $0.000 |
| gen/0-043/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 9.6s | $0.000 |
| gen/0-043/pnpm/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 96% | 11.3s | $0.000 |
| gen/0-045/ruff/history+pre/long | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 295 | 96% | 73.0s | $0.000 |
| gen/0-045/ruff/history+pre/long | precondition_or | ctxblame_uncond | causes | 1/1 | 100% | 50% | FP | 475 | 95% | 112.7s | $0.000 |
| gen/0-048/tox/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 135 | 89% | 37.1s | $0.000 |
| gen/0-048/tox/system | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 135 | 95% | 36.0s | $0.000 |
| gen/0-049/hatch/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 265 | 91% | 63.9s | $0.000 |
| gen/0-049/hatch/system+user | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 265 | 95% | 67.0s | $0.000 |
| gen/0-051/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 10.7s | $0.000 |
| gen/0-051/pnpm/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 95% | 11.2s | $0.000 |
| gen/0-052/uv/neg | negative | ctxblame | preconditions_only | FP | - | 0% | - | 585 | 87% | 159.4s | $0.000 |
| gen/0-052/uv/neg | negative | ctxblame_uncond | none_found | OK | - | 100% | - | 375 | 86% | 130.8s | $0.000 |
| gen/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 445 | 94% | 126.2s | $0.000 |
| gen/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 455 | 97% | 127.6s | $0.000 |
| gen/0-057/hatch/doc | single | ctxblame | causes | 1/1 | 100% | 100% | - | 140 | 92% | 38.5s | $0.000 |
| gen/0-057/hatch/doc | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 140 | 94% | 39.9s | $0.000 |
| gen/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 390 | 90% | 98.0s | $0.000 |
| gen/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame_uncond | causes | 3/3 | 100% | 100% | - | 390 | 96% | 97.0s | $0.000 |
| gen/0-060/uv/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 87% | 47.8s | $0.000 |
| gen/0-060/uv/system | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 150 | 94% | 49.8s | $0.000 |
| gen/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 320 | 90% | 55.4s | $0.000 |
| gen/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame_uncond | causes | 0/2 | 0% | 0% | FP | 160 | 95% | 32.6s | $0.000 |
