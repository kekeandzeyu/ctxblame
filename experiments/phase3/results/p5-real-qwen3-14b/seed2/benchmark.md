# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 92% | 92% | 92% | 0% | - | 708.1 | 94% | 456.7s | $0.000 |
| ctxblame_uncond | 69% | 52% | 60% | 100% | - | 534.2 | 96% | 355.5s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| real/run1/step21 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 550 | 92% | 309.0s | $0.000 |
| real/run1/step21 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 560 | 97% | 315.1s | $0.000 |
| real/run2/step19 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 590 | 94% | 383.2s | $0.000 |
| real/run2/step19 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 560 | 96% | 357.9s | $0.000 |
| real/run3/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 550 | 98% | 416.9s | $0.000 |
| real/run3/step24 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 560 | 91% | 412.5s | $0.000 |
| real/run4/step21 | or_redundant | ctxblame | preconditions_only | 0/3 | 0% | 0% | - | 1540 | 98% | 1474.0s | $0.000 |
| real/run4/step21 | or_redundant | ctxblame_uncond | causes | 0/3 | 0% | 0% | - | 450 | 98% | 661.7s | $0.000 |
| real/run6/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 555 | 94% | 380.1s | $0.000 |
| real/run6/step24 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 565 | 95% | 376.2s | $0.000 |
| real/run8/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 530 | 91% | 305.2s | $0.000 |
| real/run8/step14 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 540 | 98% | 304.6s | $0.000 |
| real/run9/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 530 | 92% | 295.6s | $0.000 |
| real/run9/step14 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 540 | 98% | 299.1s | $0.000 |
| real/run9/step20 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 650 | 92% | 341.6s | $0.000 |
| real/run9/step20 | precondition_or | ctxblame_uncond | causes | 4/4 | 100% | 80% | FP | 660 | 98% | 346.1s | $0.000 |
| real/run9/step29 | precondition_or | ctxblame | causes | 5/5 | 100% | 100% | YES | 1365 | 93% | 697.4s | $0.000 |
| real/run9/step29 | precondition_or | ctxblame_uncond | causes | 0/5 | 0% | 0% | FP | 710 | 93% | 451.5s | $0.000 |
| real/run13/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 530 | 92% | 268.5s | $0.000 |
| real/run13/step14 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 540 | 98% | 280.5s | $0.000 |
| real/run13/step17 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 615 | 97% | 330.6s | $0.000 |
| real/run13/step17 | precondition_or | ctxblame_uncond | causes | 0/4 | 0% | 0% | FP | 335 | 93% | 220.7s | $0.000 |
| real/run15/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 555 | 94% | 363.6s | $0.000 |
| real/run15/step24 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 565 | 97% | 353.9s | $0.000 |
| real/run15/step27 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 645 | 96% | 370.9s | $0.000 |
| real/run15/step27 | precondition_or | ctxblame_uncond | causes | 0/4 | 0% | 0% | FP | 360 | 98% | 242.3s | $0.000 |
