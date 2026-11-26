# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 96% | 91% | 92% | 8% | 100% | 302.9 | 97% | 244.3s | $0.000 |
| ctxblame_flat | 92% | 90% | 91% | 0% | 100% | 371.3 | 98% | 299.4s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| gen-long/0-000/tox/user/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 105 | 97% | 86.5s | $0.000 |
| gen-long/0-000/tox/user/long | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 140 | 99% | 107.7s | $0.000 |
| gen-long/0-001/hatch/tooldesc+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 235 | 98% | 180.6s | $0.000 |
| gen-long/0-001/hatch/tooldesc+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 380 | 97% | 284.9s | $0.000 |
| gen-long/0-003/pnpm/history+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 33% | FP | 1435 | 90% | 1298.0s | $0.000 |
| gen-long/0-003/pnpm/history+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 540 | 96% | 539.9s | $0.000 |
| gen-long/0-008/tox/system+doc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 400 | 98% | 385.8s | $0.000 |
| gen-long/0-008/tox/system+doc+user+pre | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 1185 | 96% | 1278.2s | $0.000 |
| gen-long/0-009/hatch/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 170 | 97% | 159.0s | $0.000 |
| gen-long/0-009/hatch/doc+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 575 | 95% | 589.2s | $0.000 |
| gen-long/0-010/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 25.9s | $0.000 |
| gen-long/0-010/make/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 100% | 7.3s | $0.000 |
| gen-long/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 400 | 98% | 341.1s | $0.000 |
| gen-long/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | no | 570 | 97% | 567.4s | $0.000 |
| gen-long/0-016/tox/doc+user+pre/long | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 265 | 98% | 238.1s | $0.000 |
| gen-long/0-016/tox/doc+user+pre/long | precondition_or | ctxblame_flat | causes | 2/2 | 100% | 100% | YES | 510 | 96% | 517.0s | $0.000 |
| gen-long/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 405 | 98% | 320.8s | $0.000 |
| gen-long/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 755 | 97% | 658.7s | $0.000 |
| gen-long/0-018/make/user | single | ctxblame | causes | 1/1 | 100% | 100% | - | 105 | 96% | 85.0s | $0.000 |
| gen-long/0-018/make/user | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 140 | 98% | 104.6s | $0.000 |
| gen-long/0-019/pnpm/system+tooldesc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 245 | 98% | 184.4s | $0.000 |
| gen-long/0-019/pnpm/system+tooldesc | or_redundant | ctxblame_flat | none_found | 0/2 | 0% | 0% | - | 400 | 97% | 363.9s | $0.000 |
| gen-long/0-021/ruff/doc/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 130 | 98% | 144.9s | $0.000 |
| gen-long/0-021/ruff/doc/long | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 160 | 99% | 176.8s | $0.000 |
| gen-long/0-022/cargo/system+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 235 | 99% | 191.0s | $0.000 |
| gen-long/0-022/cargo/system+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 205 | 99% | 157.8s | $0.000 |
| gen-long/0-024/tox/tooldesc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 205 | 98% | 167.6s | $0.000 |
| gen-long/0-024/tox/tooldesc+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | no | 185 | 97% | 147.1s | $0.000 |
| gen-long/0-025/hatch/system+user/long | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 310 | 98% | 208.6s | $0.000 |
| gen-long/0-025/hatch/system+user/long | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 330 | 99% | 218.5s | $0.000 |
| gen-long/0-026/make/system+tooldesc+user | or_redundant | ctxblame | causes | 2/3 | 67% | 50% | - | 1745 | 96% | 1409.7s | $0.000 |
| gen-long/0-026/make/system+tooldesc+user | or_redundant | ctxblame_flat | causes | 2/3 | 67% | 50% | - | 1740 | 97% | 1371.1s | $0.000 |
| gen-long/0-027/pnpm/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 210 | 97% | 157.2s | $0.000 |
| gen-long/0-027/pnpm/system+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | no | 180 | 97% | 158.8s | $0.000 |
| gen-long/0-028/uv/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 270 | 98% | 238.8s | $0.000 |
| gen-long/0-028/uv/system+user | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 380 | 99% | 346.4s | $0.000 |
| gen-long/0-030/cargo/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 98% | 98.2s | $0.000 |
| gen-long/0-030/cargo/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 130 | 99% | 79.9s | $0.000 |
| gen-long/0-032/tox/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 30.3s | $0.000 |
| gen-long/0-032/tox/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 100% | 8.6s | $0.000 |
| gen-long/0-033/hatch/system | single | ctxblame | none_found | 0/1 | 0% | 0% | - | 695 | 97% | 482.6s | $0.000 |
| gen-long/0-033/hatch/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 155 | 99% | 104.6s | $0.000 |
| gen-long/0-035/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 30.8s | $0.000 |
| gen-long/0-035/pnpm/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 100% | 7.7s | $0.000 |
| gen-long/0-036/uv/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 195 | 98% | 157.8s | $0.000 |
| gen-long/0-036/uv/doc+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 345 | 96% | 359.8s | $0.000 |
| gen-long/0-039/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 25.9s | $0.000 |
| gen-long/0-039/script/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 100% | 9.5s | $0.000 |
| gen-long/0-041/hatch/tooldesc+doc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 410 | 99% | 313.6s | $0.000 |
| gen-long/0-041/hatch/tooldesc+doc+user | or_redundant | ctxblame_flat | causes | 3/3 | 100% | 100% | - | 555 | 98% | 426.6s | $0.000 |
| gen-long/0-042/make/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 25% | YES | 465 | 95% | 508.2s | $0.000 |
| gen-long/0-042/make/system+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 50% | YES | 430 | 96% | 458.2s | $0.000 |
| gen-long/0-043/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 33.1s | $0.000 |
| gen-long/0-043/pnpm/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 99% | 11.9s | $0.000 |
| gen-long/0-048/tox/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 155 | 98% | 125.4s | $0.000 |
| gen-long/0-048/tox/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 140 | 98% | 106.1s | $0.000 |
| gen-long/0-049/hatch/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 215 | 98% | 158.2s | $0.000 |
| gen-long/0-049/hatch/system+user | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 170 | 99% | 117.6s | $0.000 |
| gen-long/0-051/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 27.9s | $0.000 |
| gen-long/0-051/pnpm/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 100% | 7.0s | $0.000 |
| gen-long/0-052/uv/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 32.5s | $0.000 |
| gen-long/0-052/uv/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 100% | 7.8s | $0.000 |
| gen-long/0-053/ruff/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 405 | 98% | 297.4s | $0.000 |
| gen-long/0-053/ruff/system+tooldesc+user | or_redundant | ctxblame_flat | causes | 3/3 | 100% | 100% | - | 495 | 98% | 363.0s | $0.000 |
| gen-long/0-055/script/system+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 360 | 99% | 253.0s | $0.000 |
| gen-long/0-055/script/system+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 260 | 99% | 180.0s | $0.000 |
| gen-long/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 375 | 98% | 260.7s | $0.000 |
| gen-long/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 1000 | 97% | 642.1s | $0.000 |
| gen-long/0-057/hatch/doc | single | ctxblame | causes | 1/1 | 100% | 100% | - | 125 | 98% | 79.2s | $0.000 |
| gen-long/0-057/hatch/doc | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 140 | 99% | 86.7s | $0.000 |
| gen-long/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 340 | 98% | 239.7s | $0.000 |
| gen-long/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame_flat | none_found | 0/3 | 0% | 0% | - | 1100 | 98% | 471.9s | $0.000 |
| gen-long/0-060/uv/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 170 | 97% | 132.6s | $0.000 |
| gen-long/0-060/uv/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 155 | 99% | 130.5s | $0.000 |
| gen-long/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 300 | 97% | 173.6s | $0.000 |
| gen-long/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame_flat | causes | 2/2 | 100% | 100% | YES | 555 | 97% | 203.9s | $0.000 |
