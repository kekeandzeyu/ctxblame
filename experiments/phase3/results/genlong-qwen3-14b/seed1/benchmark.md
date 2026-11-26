# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 99% | 96% | 97% | 0% | 100% | 266.2 | 97% | 206.9s | $0.000 |
| ctxblame_flat | 92% | 89% | 89% | 0% | 100% | 381.3 | 98% | 301.2s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| gen-long/0-000/tox/user/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 105 | 97% | 86.2s | $0.000 |
| gen-long/0-000/tox/user/long | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 140 | 99% | 106.5s | $0.000 |
| gen-long/0-001/hatch/tooldesc+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 240 | 98% | 179.9s | $0.000 |
| gen-long/0-001/hatch/tooldesc+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 380 | 97% | 280.1s | $0.000 |
| gen-long/0-003/pnpm/history+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 280 | 98% | 251.8s | $0.000 |
| gen-long/0-003/pnpm/history+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 535 | 96% | 541.8s | $0.000 |
| gen-long/0-008/tox/system+doc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 400 | 98% | 366.8s | $0.000 |
| gen-long/0-008/tox/system+doc+user+pre | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 1090 | 96% | 1091.3s | $0.000 |
| gen-long/0-009/hatch/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 170 | 98% | 147.2s | $0.000 |
| gen-long/0-009/hatch/doc+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 595 | 96% | 581.1s | $0.000 |
| gen-long/0-010/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 24.4s | $0.000 |
| gen-long/0-010/make/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 100% | 7.2s | $0.000 |
| gen-long/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 400 | 97% | 321.6s | $0.000 |
| gen-long/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | no | 540 | 97% | 514.8s | $0.000 |
| gen-long/0-016/tox/doc+user+pre/long | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 265 | 98% | 235.0s | $0.000 |
| gen-long/0-016/tox/doc+user+pre/long | precondition_or | ctxblame_flat | causes | 2/2 | 100% | 100% | YES | 520 | 96% | 509.5s | $0.000 |
| gen-long/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 405 | 98% | 324.4s | $0.000 |
| gen-long/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 765 | 97% | 645.1s | $0.000 |
| gen-long/0-018/make/user | single | ctxblame | causes | 1/1 | 100% | 100% | - | 105 | 97% | 93.3s | $0.000 |
| gen-long/0-018/make/user | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 140 | 99% | 113.0s | $0.000 |
| gen-long/0-019/pnpm/system+tooldesc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 245 | 97% | 181.7s | $0.000 |
| gen-long/0-019/pnpm/system+tooldesc | or_redundant | ctxblame_flat | causes | 1/2 | 50% | 20% | - | 800 | 98% | 661.3s | $0.000 |
| gen-long/0-021/ruff/doc/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 98% | 114.9s | $0.000 |
| gen-long/0-021/ruff/doc/long | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 160 | 99% | 142.4s | $0.000 |
| gen-long/0-022/cargo/system+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 235 | 98% | 167.2s | $0.000 |
| gen-long/0-022/cargo/system+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 205 | 99% | 139.0s | $0.000 |
| gen-long/0-024/tox/tooldesc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 205 | 98% | 165.4s | $0.000 |
| gen-long/0-024/tox/tooldesc+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | no | 195 | 96% | 162.4s | $0.000 |
| gen-long/0-025/hatch/system+user/long | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 310 | 98% | 201.7s | $0.000 |
| gen-long/0-025/hatch/system+user/long | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 335 | 99% | 224.3s | $0.000 |
| gen-long/0-026/make/system+tooldesc+user | or_redundant | ctxblame | causes | 2/3 | 67% | 50% | - | 785 | 98% | 617.1s | $0.000 |
| gen-long/0-026/make/system+tooldesc+user | or_redundant | ctxblame_flat | none_found | 0/3 | 0% | 0% | - | 1850 | 97% | 1422.3s | $0.000 |
| gen-long/0-027/pnpm/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 210 | 98% | 154.2s | $0.000 |
| gen-long/0-027/pnpm/system+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | no | 180 | 96% | 160.3s | $0.000 |
| gen-long/0-028/uv/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 330 | 98% | 289.1s | $0.000 |
| gen-long/0-028/uv/system+user | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 410 | 99% | 361.7s | $0.000 |
| gen-long/0-030/cargo/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 98% | 97.8s | $0.000 |
| gen-long/0-030/cargo/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 130 | 98% | 82.5s | $0.000 |
| gen-long/0-032/tox/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 26.0s | $0.000 |
| gen-long/0-032/tox/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 100% | 8.4s | $0.000 |
| gen-long/0-033/hatch/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 1450 | 99% | 1013.8s | $0.000 |
| gen-long/0-033/hatch/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 155 | 99% | 100.7s | $0.000 |
| gen-long/0-035/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 24.1s | $0.000 |
| gen-long/0-035/pnpm/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 100% | 7.4s | $0.000 |
| gen-long/0-036/uv/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 195 | 98% | 147.9s | $0.000 |
| gen-long/0-036/uv/doc+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 345 | 96% | 349.2s | $0.000 |
| gen-long/0-039/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 22.3s | $0.000 |
| gen-long/0-039/script/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 100% | 7.9s | $0.000 |
| gen-long/0-041/hatch/tooldesc+doc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 400 | 98% | 289.5s | $0.000 |
| gen-long/0-041/hatch/tooldesc+doc+user | or_redundant | ctxblame_flat | causes | 3/3 | 100% | 100% | - | 555 | 98% | 399.6s | $0.000 |
| gen-long/0-042/make/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 25% | YES | 480 | 94% | 512.9s | $0.000 |
| gen-long/0-042/make/system+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 25% | YES | 535 | 96% | 541.4s | $0.000 |
| gen-long/0-043/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 32.4s | $0.000 |
| gen-long/0-043/pnpm/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 99% | 6.3s | $0.000 |
| gen-long/0-048/tox/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 155 | 97% | 118.1s | $0.000 |
| gen-long/0-048/tox/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 140 | 99% | 95.8s | $0.000 |
| gen-long/0-049/hatch/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 215 | 97% | 149.9s | $0.000 |
| gen-long/0-049/hatch/system+user | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 170 | 99% | 122.7s | $0.000 |
| gen-long/0-051/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 30.6s | $0.000 |
| gen-long/0-051/pnpm/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 100% | 9.7s | $0.000 |
| gen-long/0-052/uv/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 36.3s | $0.000 |
| gen-long/0-052/uv/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 100% | 9.0s | $0.000 |
| gen-long/0-053/ruff/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 405 | 98% | 321.0s | $0.000 |
| gen-long/0-053/ruff/system+tooldesc+user | or_redundant | ctxblame_flat | causes | 3/3 | 100% | 100% | - | 495 | 97% | 392.1s | $0.000 |
| gen-long/0-055/script/system+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 255 | 99% | 186.7s | $0.000 |
| gen-long/0-055/script/system+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 220 | 99% | 159.4s | $0.000 |
| gen-long/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 375 | 98% | 282.3s | $0.000 |
| gen-long/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 885 | 97% | 564.2s | $0.000 |
| gen-long/0-057/hatch/doc | single | ctxblame | causes | 1/1 | 100% | 100% | - | 125 | 97% | 82.9s | $0.000 |
| gen-long/0-057/hatch/doc | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 140 | 99% | 94.4s | $0.000 |
| gen-long/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 340 | 98% | 254.2s | $0.000 |
| gen-long/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame_flat | none_found | 0/3 | 0% | 0% | - | 1065 | 98% | 476.1s | $0.000 |
| gen-long/0-060/uv/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 170 | 97% | 146.0s | $0.000 |
| gen-long/0-060/uv/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 155 | 99% | 125.3s | $0.000 |
| gen-long/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 300 | 98% | 167.6s | $0.000 |
| gen-long/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame_flat | causes | 2/2 | 100% | 100% | YES | 555 | 98% | 230.7s | $0.000 |
