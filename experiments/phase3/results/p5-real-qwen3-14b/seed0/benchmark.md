# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 92% | 92% | 92% | 0% | - | 681.9 | 94% | 468.9s | $0.000 |
| ctxblame_uncond | 69% | 52% | 60% | 100% | - | 553.5 | 96% | 382.2s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| real/run1/step21 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 550 | 94% | 295.6s | $0.000 |
| real/run1/step21 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 560 | 96% | 300.6s | $0.000 |
| real/run2/step19 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 620 | 95% | 441.5s | $0.000 |
| real/run2/step19 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 575 | 94% | 368.0s | $0.000 |
| real/run3/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 550 | 99% | 417.0s | $0.000 |
| real/run3/step24 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 560 | 91% | 414.1s | $0.000 |
| real/run4/step21 | or_redundant | ctxblame | not_in_context | 0/3 | 0% | 0% | - | 1270 | 98% | 1462.2s | $0.000 |
| real/run4/step21 | or_redundant | ctxblame_uncond | causes | 0/3 | 0% | 0% | - | 740 | 98% | 983.7s | $0.000 |
| real/run6/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 555 | 91% | 358.6s | $0.000 |
| real/run6/step24 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 565 | 98% | 379.2s | $0.000 |
| real/run8/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 530 | 92% | 306.6s | $0.000 |
| real/run8/step14 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 540 | 95% | 303.1s | $0.000 |
| real/run9/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 530 | 92% | 296.6s | $0.000 |
| real/run9/step14 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 540 | 98% | 298.3s | $0.000 |
| real/run9/step20 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 650 | 93% | 341.2s | $0.000 |
| real/run9/step20 | precondition_or | ctxblame_uncond | causes | 4/4 | 100% | 80% | FP | 660 | 98% | 343.5s | $0.000 |
| real/run9/step29 | precondition_or | ctxblame | causes | 5/5 | 100% | 100% | YES | 1265 | 92% | 707.4s | $0.000 |
| real/run9/step29 | precondition_or | ctxblame_uncond | causes | 0/5 | 0% | 0% | FP | 655 | 93% | 406.4s | $0.000 |
| real/run13/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 530 | 92% | 282.5s | $0.000 |
| real/run13/step14 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 540 | 98% | 287.1s | $0.000 |
| real/run13/step17 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 615 | 92% | 392.0s | $0.000 |
| real/run13/step17 | precondition_or | ctxblame_uncond | causes | 0/4 | 0% | 0% | FP | 335 | 98% | 208.0s | $0.000 |
| real/run15/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 555 | 93% | 396.8s | $0.000 |
| real/run15/step24 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 565 | 99% | 397.1s | $0.000 |
| real/run15/step27 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 645 | 96% | 397.1s | $0.000 |
| real/run15/step27 | precondition_or | ctxblame_uncond | causes | 0/4 | 0% | 0% | FP | 360 | 94% | 279.9s | $0.000 |
