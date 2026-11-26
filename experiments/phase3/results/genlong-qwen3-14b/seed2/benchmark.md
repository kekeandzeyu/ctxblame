# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 99% | 94% | 95% | 8% | 100% | 255.0 | 97% | 208.8s | $0.000 |
| ctxblame_flat | 92% | 87% | 88% | 8% | 100% | 376.7 | 98% | 311.0s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| gen-long/0-000/tox/user/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 105 | 96% | 92.3s | $0.000 |
| gen-long/0-000/tox/user/long | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 140 | 99% | 112.3s | $0.000 |
| gen-long/0-001/hatch/tooldesc+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 240 | 98% | 188.5s | $0.000 |
| gen-long/0-001/hatch/tooldesc+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 380 | 97% | 292.7s | $0.000 |
| gen-long/0-003/pnpm/history+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 33% | FP | 230 | 97% | 221.1s | $0.000 |
| gen-long/0-003/pnpm/history+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 33% | FP | 530 | 96% | 536.5s | $0.000 |
| gen-long/0-008/tox/system+doc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 400 | 98% | 390.4s | $0.000 |
| gen-long/0-008/tox/system+doc+user+pre | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 1195 | 95% | 1276.0s | $0.000 |
| gen-long/0-009/hatch/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 170 | 97% | 150.1s | $0.000 |
| gen-long/0-009/hatch/doc+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 580 | 95% | 572.1s | $0.000 |
| gen-long/0-010/make/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 26.8s | $0.000 |
| gen-long/0-010/make/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 100% | 9.3s | $0.000 |
| gen-long/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 400 | 98% | 328.1s | $0.000 |
| gen-long/0-011/pnpm/system+tooldesc+user+pre/long | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | no | 515 | 97% | 488.0s | $0.000 |
| gen-long/0-016/tox/doc+user+pre/long | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 265 | 98% | 227.9s | $0.000 |
| gen-long/0-016/tox/doc+user+pre/long | precondition_or | ctxblame_flat | causes | 2/2 | 100% | 100% | YES | 495 | 96% | 470.3s | $0.000 |
| gen-long/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 405 | 98% | 315.2s | $0.000 |
| gen-long/0-017/hatch/system+tooldesc+user+pre | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 855 | 96% | 699.8s | $0.000 |
| gen-long/0-018/make/user | single | ctxblame | causes | 1/1 | 100% | 100% | - | 105 | 96% | 88.8s | $0.000 |
| gen-long/0-018/make/user | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 140 | 99% | 112.1s | $0.000 |
| gen-long/0-019/pnpm/system+tooldesc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 245 | 97% | 198.5s | $0.000 |
| gen-long/0-019/pnpm/system+tooldesc | or_redundant | ctxblame_flat | causes | 1/2 | 50% | 17% | - | 1055 | 99% | 932.0s | $0.000 |
| gen-long/0-021/ruff/doc/long | single | ctxblame | causes | 1/1 | 100% | 100% | - | 110 | 96% | 106.0s | $0.000 |
| gen-long/0-021/ruff/doc/long | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 160 | 98% | 166.1s | $0.000 |
| gen-long/0-022/cargo/system+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 235 | 98% | 189.9s | $0.000 |
| gen-long/0-022/cargo/system+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 205 | 99% | 158.4s | $0.000 |
| gen-long/0-024/tox/tooldesc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 220 | 98% | 202.4s | $0.000 |
| gen-long/0-024/tox/tooldesc+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | no | 185 | 96% | 165.2s | $0.000 |
| gen-long/0-025/hatch/system+user/long | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 310 | 98% | 209.2s | $0.000 |
| gen-long/0-025/hatch/system+user/long | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 325 | 100% | 209.2s | $0.000 |
| gen-long/0-026/make/system+tooldesc+user | or_redundant | ctxblame | causes | 2/3 | 67% | 50% | - | 1520 | 96% | 1259.5s | $0.000 |
| gen-long/0-026/make/system+tooldesc+user | or_redundant | ctxblame_flat | none_found | 0/3 | 0% | 0% | - | 1830 | 97% | 1461.4s | $0.000 |
| gen-long/0-027/pnpm/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 210 | 97% | 153.9s | $0.000 |
| gen-long/0-027/pnpm/system+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | no | 180 | 96% | 154.7s | $0.000 |
| gen-long/0-028/uv/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 270 | 98% | 250.1s | $0.000 |
| gen-long/0-028/uv/system+user | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 325 | 99% | 278.6s | $0.000 |
| gen-long/0-030/cargo/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 150 | 96% | 106.0s | $0.000 |
| gen-long/0-030/cargo/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 130 | 99% | 85.3s | $0.000 |
| gen-long/0-032/tox/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 26.6s | $0.000 |
| gen-long/0-032/tox/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 100% | 8.4s | $0.000 |
| gen-long/0-033/hatch/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 380 | 98% | 270.0s | $0.000 |
| gen-long/0-033/hatch/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 200 | 98% | 140.6s | $0.000 |
| gen-long/0-035/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 28.3s | $0.000 |
| gen-long/0-035/pnpm/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 100% | 9.8s | $0.000 |
| gen-long/0-036/uv/doc+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 100% | YES | 195 | 97% | 163.6s | $0.000 |
| gen-long/0-036/uv/doc+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 100% | YES | 345 | 96% | 370.2s | $0.000 |
| gen-long/0-039/script/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 31.8s | $0.000 |
| gen-long/0-039/script/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 100% | 6.8s | $0.000 |
| gen-long/0-041/hatch/tooldesc+doc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 390 | 98% | 295.4s | $0.000 |
| gen-long/0-041/hatch/tooldesc+doc+user | or_redundant | ctxblame_flat | causes | 3/3 | 100% | 100% | - | 565 | 98% | 442.6s | $0.000 |
| gen-long/0-042/make/system+pre | precondition_or | ctxblame | causes | 1/1 | 100% | 25% | YES | 490 | 95% | 532.2s | $0.000 |
| gen-long/0-042/make/system+pre | precondition_or | ctxblame_flat | causes | 1/1 | 100% | 50% | YES | 395 | 95% | 422.3s | $0.000 |
| gen-long/0-043/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 26.8s | $0.000 |
| gen-long/0-043/pnpm/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 99% | 10.7s | $0.000 |
| gen-long/0-048/tox/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 155 | 96% | 132.6s | $0.000 |
| gen-long/0-048/tox/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 140 | 99% | 102.9s | $0.000 |
| gen-long/0-049/hatch/system+user | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 215 | 99% | 167.1s | $0.000 |
| gen-long/0-049/hatch/system+user | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 170 | 98% | 128.8s | $0.000 |
| gen-long/0-051/pnpm/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 36.9s | $0.000 |
| gen-long/0-051/pnpm/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 100% | 13.3s | $0.000 |
| gen-long/0-052/uv/neg | negative | ctxblame | not_in_context | OK | - | 100% | - | 40 | 94% | 39.9s | $0.000 |
| gen-long/0-052/uv/neg | negative | ctxblame_flat | not_in_context | OK | - | 100% | - | 15 | 100% | 12.2s | $0.000 |
| gen-long/0-053/ruff/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 410 | 98% | 314.5s | $0.000 |
| gen-long/0-053/ruff/system+tooldesc+user | or_redundant | ctxblame_flat | causes | 3/3 | 100% | 100% | - | 510 | 98% | 398.0s | $0.000 |
| gen-long/0-055/script/system+doc | or_redundant | ctxblame | causes | 2/2 | 100% | 100% | - | 285 | 99% | 202.9s | $0.000 |
| gen-long/0-055/script/system+doc | or_redundant | ctxblame_flat | causes | 2/2 | 100% | 100% | - | 255 | 99% | 175.8s | $0.000 |
| gen-long/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 375 | 98% | 281.8s | $0.000 |
| gen-long/0-056/tox/system+user+history+pre/long | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 985 | 96% | 560.5s | $0.000 |
| gen-long/0-057/hatch/doc | single | ctxblame | causes | 1/1 | 100% | 100% | - | 125 | 97% | 89.5s | $0.000 |
| gen-long/0-057/hatch/doc | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 140 | 99% | 100.1s | $0.000 |
| gen-long/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame | causes | 3/3 | 100% | 100% | - | 330 | 98% | 254.6s | $0.000 |
| gen-long/0-059/pnpm/system+tooldesc+user | or_redundant | ctxblame_flat | none_found | 0/3 | 0% | 0% | - | 565 | 97% | 343.5s | $0.000 |
| gen-long/0-060/uv/system | single | ctxblame | causes | 1/1 | 100% | 100% | - | 170 | 98% | 146.8s | $0.000 |
| gen-long/0-060/uv/system | single | ctxblame_flat | causes | 1/1 | 100% | 100% | - | 155 | 98% | 143.0s | $0.000 |
| gen-long/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame | causes | 2/2 | 100% | 100% | YES | 300 | 97% | 188.1s | $0.000 |
| gen-long/0-061/ruff/system+tooldesc+pre | precondition_or | ctxblame_flat | causes | 2/2 | 100% | 100% | YES | 560 | 97% | 247.4s | $0.000 |
