# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 92% | 92% | 92% | 0% | - | 564.2 | 91% | 603.9s | $0.000 |
| ctxblame_uncond | 69% | 52% | 60% | 100% | - | 470.0 | 95% | 534.5s | $0.000 |
| ctxblame_flat | 92% | 92% | 92% | 0% | - | 696.9 | 90% | 660.5s | $0.000 |
| loo | 0% | 0% | 0% | 100% | - | 201.9 | 89% | 231.0s | $0.000 |
| self_explain | 51% | 56% | 46% | 8% | - | 1.0 | 0% | 19.1s | $0.000 |
| contextcite | 51% | 28% | 34% | 100% | - | 64.0 | - | 46.5s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| real/run1/step21 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 450 | 92% | 429.6s | $0.000 |
| real/run1/step21 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 460 | 96% | 435.0s | $0.000 |
| real/run1/step21 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 455 | 92% | 431.4s | $0.000 |
| real/run1/step21 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 190 | 88% | 225.4s | $0.000 |
| real/run1/step21 | precondition_or | self_explain | causes | 2/3 | 67% | 33% | no | 1 | 0% | 56.2s | $0.000 |
| real/run1/step21 | precondition_or | contextcite | causes | 1/3 | 33% | 10% | FP | 64 | - | 49.9s | $0.000 |
| real/run2/step19 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 540 | 96% | 715.1s | $0.000 |
| real/run2/step19 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 460 | 92% | 533.6s | $0.000 |
| real/run2/step19 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 515 | 90% | 591.9s | $0.000 |
| real/run2/step19 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 175 | 88% | 173.4s | $0.000 |
| real/run2/step19 | precondition_or | self_explain | causes | 2/3 | 67% | 100% | no | 1 | 0% | 9.8s | $0.000 |
| real/run2/step19 | precondition_or | contextcite | causes | 2/3 | 67% | 40% | FP | 64 | - | 45.0s | $0.000 |
| real/run3/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 450 | 89% | 630.9s | $0.000 |
| real/run3/step24 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 460 | 98% | 603.7s | $0.000 |
| real/run3/step24 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 460 | 88% | 586.1s | $0.000 |
| real/run3/step24 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 210 | 87% | 281.1s | $0.000 |
| real/run3/step24 | precondition_or | self_explain | causes | 2/3 | 67% | 20% | no | 1 | 0% | 22.3s | $0.000 |
| real/run3/step24 | precondition_or | contextcite | causes | 0/3 | 0% | 0% | FP | 64 | - | 62.5s | $0.000 |
| real/run4/step21 | or_redundant | ctxblame | preconditions_only | 0/3 | 0% | 0% | - | 795 | 99% | 1555.7s | $0.000 |
| real/run4/step21 | or_redundant | ctxblame_uncond | causes | 0/3 | 0% | 0% | - | 655 | 98% | 1678.9s | $0.000 |
| real/run4/step21 | or_redundant | ctxblame_flat | none_found | 0/3 | 0% | 0% | - | 1505 | 93% | 1614.3s | $0.000 |
| real/run4/step21 | or_redundant | loo | causes | 0/3 | 0% | 0% | - | 370 | 94% | 658.8s | $0.000 |
| real/run4/step21 | or_redundant | self_explain | causes | 0/3 | 0% | 0% | - | 1 | 0% | 21.1s | $0.000 |
| real/run4/step21 | or_redundant | contextcite | causes | 2/3 | 67% | 33% | - | 64 | - | 49.9s | $0.000 |
| real/run6/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 455 | 89% | 414.9s | $0.000 |
| real/run6/step24 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 465 | 92% | 438.3s | $0.000 |
| real/run6/step24 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 450 | 92% | 418.7s | $0.000 |
| real/run6/step24 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 205 | 90% | 170.5s | $0.000 |
| real/run6/step24 | precondition_or | self_explain | causes | 2/3 | 67% | 100% | no | 1 | 0% | 7.7s | $0.000 |
| real/run6/step24 | precondition_or | contextcite | causes | 1/3 | 33% | 25% | FP | 64 | - | 51.9s | $0.000 |
| real/run8/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 430 | 90% | 319.7s | $0.000 |
| real/run8/step14 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 440 | 98% | 284.4s | $0.000 |
| real/run8/step14 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 575 | 88% | 387.7s | $0.000 |
| real/run8/step14 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 155 | 88% | 118.4s | $0.000 |
| real/run8/step14 | precondition_or | self_explain | causes | 1/3 | 33% | 100% | no | 1 | 0% | 4.6s | $0.000 |
| real/run8/step14 | precondition_or | contextcite | causes | 1/3 | 33% | 33% | FP | 64 | - | 31.6s | $0.000 |
| real/run9/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 430 | 89% | 291.8s | $0.000 |
| real/run9/step14 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 440 | 97% | 290.6s | $0.000 |
| real/run9/step14 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 575 | 89% | 416.9s | $0.000 |
| real/run9/step14 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 155 | 89% | 107.2s | $0.000 |
| real/run9/step14 | precondition_or | self_explain | causes | 1/3 | 33% | 100% | no | 1 | 0% | 5.1s | $0.000 |
| real/run9/step14 | precondition_or | contextcite | causes | 1/3 | 33% | 33% | FP | 64 | - | 32.4s | $0.000 |
| real/run9/step20 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 530 | 91% | 365.0s | $0.000 |
| real/run9/step20 | precondition_or | ctxblame_uncond | causes | 4/4 | 100% | 80% | FP | 540 | 98% | 374.6s | $0.000 |
| real/run9/step20 | precondition_or | ctxblame_flat | causes | 4/4 | 100% | 100% | YES | 820 | 90% | 633.6s | $0.000 |
| real/run9/step20 | precondition_or | loo | causes | 0/4 | 0% | 0% | FP | 185 | 90% | 117.1s | $0.000 |
| real/run9/step20 | precondition_or | self_explain | causes | 2/4 | 50% | 100% | no | 1 | 0% | 5.2s | $0.000 |
| real/run9/step20 | precondition_or | contextcite | causes | 4/4 | 100% | 40% | FP | 64 | - | 41.4s | $0.000 |
| real/run9/step29 | precondition_or | ctxblame | causes | 5/5 | 100% | 100% | YES | 1350 | 91% | 1232.7s | $0.000 |
| real/run9/step29 | precondition_or | ctxblame_uncond | causes | 0/5 | 0% | 0% | FP | 630 | 93% | 589.7s | $0.000 |
| real/run9/step29 | precondition_or | ctxblame_flat | causes | 5/5 | 100% | 100% | YES | 925 | 90% | 967.2s | $0.000 |
| real/run9/step29 | precondition_or | loo | causes | 0/5 | 0% | 0% | FP | 230 | 90% | 220.7s | $0.000 |
| real/run9/step29 | precondition_or | self_explain | causes | 1/5 | 20% | 33% | no | 1 | 0% | 13.1s | $0.000 |
| real/run9/step29 | precondition_or | contextcite | causes | 5/5 | 100% | 33% | FP | 64 | - | 52.6s | $0.000 |
| real/run13/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 430 | 89% | 358.1s | $0.000 |
| real/run13/step14 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 440 | 91% | 379.8s | $0.000 |
| real/run13/step14 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 570 | 89% | 510.3s | $0.000 |
| real/run13/step14 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 155 | 89% | 157.8s | $0.000 |
| real/run13/step14 | precondition_or | self_explain | causes | 2/3 | 67% | 33% | no | 1 | 0% | 16.7s | $0.000 |
| real/run13/step14 | precondition_or | contextcite | causes | 1/3 | 33% | 33% | FP | 64 | - | 33.6s | $0.000 |
| real/run13/step17 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 495 | 93% | 485.4s | $0.000 |
| real/run13/step17 | precondition_or | ctxblame_uncond | causes | 0/4 | 0% | 0% | FP | 315 | 95% | 318.6s | $0.000 |
| real/run13/step17 | precondition_or | ctxblame_flat | causes | 4/4 | 100% | 100% | YES | 750 | 90% | 860.2s | $0.000 |
| real/run13/step17 | precondition_or | loo | causes | 0/4 | 0% | 0% | FP | 170 | 89% | 191.5s | $0.000 |
| real/run13/step17 | precondition_or | self_explain | causes | 2/4 | 50% | 50% | no | 1 | 0% | 13.4s | $0.000 |
| real/run13/step17 | precondition_or | contextcite | causes | 2/4 | 50% | 29% | FP | 64 | - | 41.1s | $0.000 |
| real/run15/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 455 | 89% | 557.7s | $0.000 |
| real/run15/step24 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 465 | 90% | 630.5s | $0.000 |
| real/run15/step24 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 450 | 90% | 615.1s | $0.000 |
| real/run15/step24 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 205 | 89% | 308.2s | $0.000 |
| real/run15/step24 | precondition_or | self_explain | causes | 2/3 | 67% | 20% | no | 1 | 0% | 37.3s | $0.000 |
| real/run15/step24 | precondition_or | contextcite | causes | 1/3 | 33% | 33% | FP | 64 | - | 53.2s | $0.000 |
| real/run15/step27 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 525 | 90% | 494.6s | $0.000 |
| real/run15/step27 | precondition_or | ctxblame_uncond | causes | 0/4 | 0% | 0% | FP | 340 | 98% | 391.2s | $0.000 |
| real/run15/step27 | precondition_or | ctxblame_flat | causes | 4/4 | 100% | 100% | YES | 1010 | 91% | 553.0s | $0.000 |
| real/run15/step27 | precondition_or | loo | causes | 0/4 | 0% | 0% | FP | 220 | 89% | 273.4s | $0.000 |
| real/run15/step27 | precondition_or | self_explain | causes | 3/4 | 75% | 33% | FP | 1 | 0% | 35.5s | $0.000 |
| real/run15/step27 | precondition_or | contextcite | causes | 3/4 | 75% | 20% | FP | 64 | - | 59.1s | $0.000 |
