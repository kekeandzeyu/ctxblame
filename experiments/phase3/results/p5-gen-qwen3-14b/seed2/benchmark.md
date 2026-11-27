# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 92% | 92% | 92% | 0% | 100% | 231.7 | 91% | 61.7s | $0.000 |
| ctxblame_uncond | 82% | 72% | 76% | 100% | 100% | 206.6 | 95% | 56.4s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| p0/tool_result_sentence_config | single | ctxblame | none_found | 0/1 | 0% | 0% | - | 200 | 90% | 35.1s | $0.000 |
| p0/tool_result_sentence_config | single | ctxblame_uncond | causes | 0/1 | 0% | 0% | - | 215 | 92% | 56.9s | $0.000 |
| p0/user_message_pnpm | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 92% | 28.7s | $0.000 |
| p0/user_message_pnpm | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 150 | 91% | 28.6s | $0.000 |
| p0/system_section_deploy_freeze | single | ctxblame | causes | 1/1 | 100% | 100% | - | 135 | 91% | 47.0s | $0.000 |
| p0/system_section_deploy_freeze | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 135 | 91% | 47.1s | $0.000 |
| p3/precond_2or_pnpm | precondition_or | ctxblame | none_found | 0/2 | 0% | 0% | no | 215 | 93% | 61.0s | $0.000 |
| p3/precond_2or_pnpm | precondition_or | ctxblame_uncond | causes | 0/2 | 0% | 0% | FP | 160 | 90% | 43.3s | $0.000 |
| p3/precond_3or_unittest | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 395 | 90% | 101.4s | $0.000 |
| p3/precond_3or_unittest | precondition_or | ctxblame_uncond | causes | 0/3 | 0% | 0% | FP | 180 | 93% | 53.7s | $0.000 |
| p3/tail_carrier_long_ctx | tail_long_ctx | ctxblame | causes | 1/1 | 100% | 100% | - | 190 | 95% | 66.8s | $0.000 |
| p3/tail_carrier_long_ctx | tail_long_ctx | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 150 | 98% | 59.0s | $0.000 |
| p3/two_carrier_ruff | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 275 | 88% | 82.5s | $0.000 |
| p3/two_carrier_ruff | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 265 | 93% | 119.2s | $0.000 |
| gen/0-000/tox/user/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 96% | 51.0s | $0.000 |
| gen/0-000/tox/user/long | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 150 | 98% | 49.6s | $0.000 |
| gen/0-001/hatch/tooldesc+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 290 | 91% | 69.8s | $0.000 |
| gen/0-001/hatch/tooldesc+doc | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 285 | 95% | 65.9s | $0.000 |
| gen/0-008/tox/system+doc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 450 | 91% | 124.1s | $0.000 |
| gen/0-008/tox/system+doc+user+pre | precondition_or | ctxblame_uncond | causes | 0/3 | 0% | 0% | FP | 180 | 95% | 52.2s | $0.000 |
| gen/0-009/hatch/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 210 | 92% | 54.4s | $0.000 |
| gen/0-009/hatch/doc+pre | precondition_or | ctxblame_uncond | causes | 1/1 | 100% | 50% | FP | 220 | 93% | 59.0s | $0.000 |
| gen/0-010/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 8.0s | $0.000 |
| gen/0-010/make/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 94% | 8.8s | $0.000 |
| gen/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 470 | 93% | 135.7s | $0.000 |
| gen/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 480 | 97% | 140.8s | $0.000 |
| gen/0-012/uv/user/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 125 | 96% | 41.6s | $0.000 |
| gen/0-012/uv/user/long | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 125 | 98% | 41.1s | $0.000 |
| gen/0-013/ruff/doc+user | or_redundant | ctxblame | none_found | 0/2 | 0% | 0% | - | 335 | 94% | 89.6s | $0.000 |
| gen/0-013/ruff/doc+user | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 290 | 94% | 79.5s | $0.000 |
| gen/0-016/tox/doc+user+pre/long | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 345 | 95% | 106.7s | $0.000 |
| gen/0-016/tox/doc+user+pre/long | precondition_or | ctxblame_uncond | causes | 2/2 | 100% | 67% | FP | 355 | 97% | 109.1s | $0.000 |
| gen/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 465 | 90% | 130.0s | $0.000 |
| gen/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame_uncond | causes | 0/3 | 0% | 0% | FP | 205 | 95% | 66.7s | $0.000 |
| gen/0-018/make/user | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 90% | 44.6s | $0.000 |
| gen/0-018/make/user | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 150 | 94% | 44.5s | $0.000 |
| gen/0-019/pnpm/system+tooldesc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 265 | 89% | 70.9s | $0.000 |
| gen/0-019/pnpm/system+tooldesc | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 265 | 95% | 69.3s | $0.000 |
| gen/0-022/cargo/system+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 260 | 92% | 65.5s | $0.000 |
| gen/0-022/cargo/system+doc | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 260 | 94% | 65.3s | $0.000 |
| gen/0-024/tox/tooldesc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 230 | 91% | 71.9s | $0.000 |
| gen/0-024/tox/tooldesc+pre | precondition_or | ctxblame_uncond | causes | 1/1 | 100% | 50% | FP | 235 | 96% | 72.6s | $0.000 |
| gen/0-025/hatch/system+user/long | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 245 | 94% | 58.7s | $0.000 |
| gen/0-025/hatch/system+user/long | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 245 | 97% | 56.8s | $0.000 |
| gen/0-027/pnpm/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 195 | 90% | 50.4s | $0.000 |
| gen/0-027/pnpm/system+pre | precondition_or | ctxblame_uncond | causes | 1/1 | 100% | 50% | FP | 200 | 94% | 50.9s | $0.000 |
| gen/0-028/uv/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 285 | 95% | 84.0s | $0.000 |
| gen/0-028/uv/system+user | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 260 | 92% | 73.6s | $0.000 |
| gen/0-029/ruff/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 90% | 10.4s | $0.000 |
| gen/0-029/ruff/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 95% | 10.4s | $0.000 |
| gen/0-030/cargo/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 88% | 30.4s | $0.000 |
| gen/0-030/cargo/system | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 130 | 93% | 30.6s | $0.000 |
| gen/0-031/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 9.7s | $0.000 |
| gen/0-031/script/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 95% | 9.9s | $0.000 |
| gen/0-032/tox/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 11.9s | $0.000 |
| gen/0-032/tox/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 95% | 11.3s | $0.000 |
| gen/0-033/hatch/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 88% | 28.4s | $0.000 |
| gen/0-033/hatch/system | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 130 | 93% | 28.0s | $0.000 |
| gen/0-034/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 8.6s | $0.000 |
| gen/0-034/make/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 97% | 7.9s | $0.000 |
| gen/0-035/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 9.5s | $0.000 |
| gen/0-035/pnpm/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 94% | 9.7s | $0.000 |
| gen/0-036/uv/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 210 | 91% | 55.7s | $0.000 |
| gen/0-036/uv/doc+pre | precondition_or | ctxblame_uncond | causes | 1/1 | 100% | 50% | FP | 220 | 94% | 59.0s | $0.000 |
| gen/0-037/ruff/tooldesc+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 370 | 92% | 104.4s | $0.000 |
| gen/0-037/ruff/tooldesc+doc | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 275 | 94% | 68.0s | $0.000 |
| gen/0-038/cargo/tooldesc+user+history+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 440 | 92% | 89.0s | $0.000 |
| gen/0-038/cargo/tooldesc+user+history+pre | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 450 | 95% | 91.8s | $0.000 |
| gen/0-039/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 75 | 93% | 20.2s | $0.000 |
| gen/0-039/script/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 90 | 95% | 26.0s | $0.000 |
| gen/0-041/hatch/tooldesc+doc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 420 | 91% | 98.1s | $0.000 |
| gen/0-041/hatch/tooldesc+doc+user | or_redundant | ctxblame_uncond | causes | 3/3 | 100% | 100% | - | 420 | 95% | 100.4s | $0.000 |
| gen/0-042/make/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 215 | 90% | 70.9s | $0.000 |
| gen/0-042/make/system+pre | precondition_or | ctxblame_uncond | causes | 0/1 | 0% | 0% | FP | 120 | 95% | 35.7s | $0.000 |
| gen/0-043/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 91% | 9.6s | $0.000 |
| gen/0-043/pnpm/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 96% | 10.6s | $0.000 |
| gen/0-045/ruff/history+pre/long | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 520 | 95% | 125.0s | $0.000 |
| gen/0-045/ruff/history+pre/long | precondition_or | ctxblame_uncond | causes | 1/1 | 100% | 50% | FP | 495 | 96% | 115.5s | $0.000 |
| gen/0-048/tox/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 135 | 90% | 34.4s | $0.000 |
| gen/0-048/tox/system | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 135 | 94% | 35.3s | $0.000 |
| gen/0-049/hatch/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 265 | 91% | 63.0s | $0.000 |
| gen/0-049/hatch/system+user | or_redundant | ctxblame_uncond | causes | 2/2 | 100% | 100% | - | 265 | 95% | 64.9s | $0.000 |
| gen/0-051/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 89% | 12.2s | $0.000 |
| gen/0-051/pnpm/neg | negative | ctxblame_uncond | not_in_context | OK | - | 100% | - | 40 | 95% | 12.3s | $0.000 |
| gen/0-052/uv/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 410 | 84% | 138.4s | $0.000 |
| gen/0-052/uv/neg | negative | ctxblame_uncond | none_found | OK | - | 100% | - | 405 | 93% | 135.3s | $0.000 |
| gen/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 445 | 94% | 122.8s | $0.000 |
| gen/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 455 | 97% | 124.3s | $0.000 |
| gen/0-057/hatch/doc | single | ctxblame | causes | 1/1 | 100% | 100% | - | 145 | 91% | 38.6s | $0.000 |
| gen/0-057/hatch/doc | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 145 | 94% | 40.5s | $0.000 |
| gen/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 390 | 90% | 91.9s | $0.000 |
| gen/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame_uncond | causes | 3/3 | 100% | 100% | - | 390 | 96% | 91.5s | $0.000 |
| gen/0-060/uv/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 88% | 47.8s | $0.000 |
| gen/0-060/uv/system | single | ctxblame_uncond | causes | 1/1 | 100% | 100% | - | 150 | 94% | 48.3s | $0.000 |
| gen/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 320 | 90% | 51.6s | $0.000 |
| gen/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame_uncond | causes | 0/2 | 0% | 0% | FP | 160 | 94% | 27.6s | $0.000 |
