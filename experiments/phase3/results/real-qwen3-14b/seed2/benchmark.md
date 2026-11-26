# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 92% | 92% | 92% | 0% | - | 526.2 | 92% | 559.0s | $0.000 |
| ctxblame_uncond | 69% | 52% | 60% | 100% | - | 458.8 | 96% | 470.4s | $0.000 |
| ctxblame_flat | 92% | 92% | 92% | 0% | - | 708.8 | 90% | 678.9s | $0.000 |
| loo | 0% | 0% | 0% | 100% | - | 206.2 | 89% | 231.0s | $0.000 |
| self_explain | 52% | 48% | 44% | 8% | - | 1.0 | 0% | 27.5s | $0.000 |
| contextcite | 36% | 20% | 24% | 83% | - | 64.0 | - | 46.0s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| real/run1/step21 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 450 | 90% | 437.1s | $0.000 |
| real/run1/step21 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 460 | 98% | 442.1s | $0.000 |
| real/run1/step21 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 455 | 92% | 439.8s | $0.000 |
| real/run1/step21 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 190 | 88% | 227.2s | $0.000 |
| real/run1/step21 | precondition_or | self_explain | causes | 2/3 | 67% | 40% | no | 1 | 0% | 53.8s | $0.000 |
| real/run1/step21 | precondition_or | contextcite | causes | 0/3 | 0% | 0% | FP | 64 | - | 47.1s | $0.000 |
| real/run2/step19 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 545 | 94% | 799.1s | $0.000 |
| real/run2/step19 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 460 | 91% | 548.0s | $0.000 |
| real/run2/step19 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 515 | 90% | 652.3s | $0.000 |
| real/run2/step19 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 175 | 88% | 171.0s | $0.000 |
| real/run2/step19 | precondition_or | self_explain | causes | 2/3 | 67% | 100% | no | 1 | 0% | 14.4s | $0.000 |
| real/run2/step19 | precondition_or | contextcite | causes | 3/3 | 100% | 100% | no | 64 | - | 45.9s | $0.000 |
| real/run3/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 450 | 97% | 629.8s | $0.000 |
| real/run3/step24 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 460 | 89% | 537.1s | $0.000 |
| real/run3/step24 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 460 | 88% | 602.0s | $0.000 |
| real/run3/step24 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 210 | 88% | 270.5s | $0.000 |
| real/run3/step24 | precondition_or | self_explain | causes | 2/3 | 67% | 22% | no | 1 | 0% | 21.6s | $0.000 |
| real/run3/step24 | precondition_or | contextcite | causes | 1/3 | 33% | 8% | FP | 64 | - | 61.9s | $0.000 |
| real/run4/step21 | or_redundant | ctxblame | preconditions_only | 0/3 | 0% | 0% | - | 585 | 98% | 1038.5s | $0.000 |
| real/run4/step21 | or_redundant | ctxblame_uncond | causes | 0/3 | 0% | 0% | - | 430 | 98% | 877.0s | $0.000 |
| real/run4/step21 | or_redundant | ctxblame_flat | none_found | 0/3 | 0% | 0% | - | 1605 | 93% | 1988.1s | $0.000 |
| real/run4/step21 | or_redundant | loo | causes | 0/3 | 0% | 0% | - | 425 | 94% | 676.3s | $0.000 |
| real/run4/step21 | or_redundant | self_explain | causes | 0/3 | 0% | 0% | - | 1 | 0% | 72.0s | $0.000 |
| real/run4/step21 | or_redundant | contextcite | causes | 3/3 | 100% | 43% | - | 64 | - | 46.4s | $0.000 |
| real/run6/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 455 | 95% | 429.6s | $0.000 |
| real/run6/step24 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 465 | 95% | 427.5s | $0.000 |
| real/run6/step24 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 450 | 87% | 397.0s | $0.000 |
| real/run6/step24 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 205 | 89% | 163.8s | $0.000 |
| real/run6/step24 | precondition_or | self_explain | causes | 2/3 | 67% | 100% | no | 1 | 0% | 6.6s | $0.000 |
| real/run6/step24 | precondition_or | contextcite | causes | 0/3 | 0% | 0% | FP | 64 | - | 52.2s | $0.000 |
| real/run8/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 430 | 89% | 286.7s | $0.000 |
| real/run8/step14 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 440 | 98% | 290.3s | $0.000 |
| real/run8/step14 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 570 | 88% | 414.6s | $0.000 |
| real/run8/step14 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 155 | 88% | 89.8s | $0.000 |
| real/run8/step14 | precondition_or | self_explain | causes | 1/3 | 33% | 100% | no | 1 | 0% | 10.9s | $0.000 |
| real/run8/step14 | precondition_or | contextcite | causes | 0/3 | 0% | 0% | FP | 64 | - | 33.2s | $0.000 |
| real/run9/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 430 | 89% | 338.8s | $0.000 |
| real/run9/step14 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 440 | 98% | 321.5s | $0.000 |
| real/run9/step14 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 590 | 89% | 450.1s | $0.000 |
| real/run9/step14 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 155 | 89% | 142.5s | $0.000 |
| real/run9/step14 | precondition_or | self_explain | causes | 2/3 | 67% | 22% | no | 1 | 0% | 39.0s | $0.000 |
| real/run9/step14 | precondition_or | contextcite | causes | 0/3 | 0% | 0% | FP | 64 | - | 32.7s | $0.000 |
| real/run9/step20 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 530 | 91% | 435.3s | $0.000 |
| real/run9/step20 | precondition_or | ctxblame_uncond | causes | 4/4 | 100% | 80% | FP | 540 | 98% | 437.3s | $0.000 |
| real/run9/step20 | precondition_or | ctxblame_flat | causes | 4/4 | 100% | 100% | YES | 820 | 90% | 722.9s | $0.000 |
| real/run9/step20 | precondition_or | loo | causes | 0/4 | 0% | 0% | FP | 185 | 89% | 166.2s | $0.000 |
| real/run9/step20 | precondition_or | self_explain | causes | 1/4 | 25% | 50% | no | 1 | 0% | 7.1s | $0.000 |
| real/run9/step20 | precondition_or | contextcite | causes | 3/4 | 75% | 33% | no | 64 | - | 41.8s | $0.000 |
| real/run9/step29 | precondition_or | ctxblame | causes | 5/5 | 100% | 100% | YES | 1060 | 90% | 944.2s | $0.000 |
| real/run9/step29 | precondition_or | ctxblame_uncond | causes | 0/5 | 0% | 0% | FP | 710 | 94% | 650.0s | $0.000 |
| real/run9/step29 | precondition_or | ctxblame_flat | causes | 5/5 | 100% | 100% | YES | 925 | 90% | 876.6s | $0.000 |
| real/run9/step29 | precondition_or | loo | causes | 0/5 | 0% | 0% | FP | 230 | 90% | 243.4s | $0.000 |
| real/run9/step29 | precondition_or | self_explain | causes | 1/5 | 20% | 20% | no | 1 | 0% | 14.8s | $0.000 |
| real/run9/step29 | precondition_or | contextcite | causes | 4/5 | 80% | 44% | FP | 64 | - | 54.0s | $0.000 |
| real/run13/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 430 | 89% | 397.2s | $0.000 |
| real/run13/step14 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 440 | 98% | 383.8s | $0.000 |
| real/run13/step14 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 590 | 89% | 499.1s | $0.000 |
| real/run13/step14 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 155 | 88% | 155.8s | $0.000 |
| real/run13/step14 | precondition_or | self_explain | causes | 2/3 | 67% | 40% | no | 1 | 0% | 13.2s | $0.000 |
| real/run13/step14 | precondition_or | contextcite | causes | 0/3 | 0% | 0% | FP | 64 | - | 33.4s | $0.000 |
| real/run13/step17 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 495 | 90% | 547.4s | $0.000 |
| real/run13/step17 | precondition_or | ctxblame_uncond | causes | 0/4 | 0% | 0% | FP | 315 | 98% | 369.6s | $0.000 |
| real/run13/step17 | precondition_or | ctxblame_flat | causes | 4/4 | 100% | 100% | YES | 740 | 90% | 772.0s | $0.000 |
| real/run13/step17 | precondition_or | loo | causes | 0/4 | 0% | 0% | FP | 170 | 88% | 190.9s | $0.000 |
| real/run13/step17 | precondition_or | self_explain | causes | 2/4 | 50% | 50% | no | 1 | 0% | 13.0s | $0.000 |
| real/run13/step17 | precondition_or | contextcite | causes | 2/4 | 50% | 18% | FP | 64 | - | 41.0s | $0.000 |
| real/run15/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 455 | 93% | 499.1s | $0.000 |
| real/run15/step24 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 465 | 95% | 494.6s | $0.000 |
| real/run15/step24 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 450 | 92% | 495.5s | $0.000 |
| real/run15/step24 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 205 | 89% | 244.9s | $0.000 |
| real/run15/step24 | precondition_or | self_explain | causes | 2/3 | 67% | 50% | no | 1 | 0% | 19.5s | $0.000 |
| real/run15/step24 | precondition_or | contextcite | causes | 0/3 | 0% | 0% | FP | 64 | - | 52.9s | $0.000 |
| real/run15/step27 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 525 | 90% | 483.7s | $0.000 |
| real/run15/step27 | precondition_or | ctxblame_uncond | causes | 0/4 | 0% | 0% | FP | 340 | 98% | 336.6s | $0.000 |
| real/run15/step27 | precondition_or | ctxblame_flat | causes | 4/4 | 100% | 100% | YES | 1045 | 91% | 515.4s | $0.000 |
| real/run15/step27 | precondition_or | loo | causes | 0/4 | 0% | 0% | FP | 220 | 89% | 260.3s | $0.000 |
| real/run15/step27 | precondition_or | self_explain | causes | 3/4 | 75% | 25% | FP | 1 | 0% | 71.8s | $0.000 |
| real/run15/step27 | precondition_or | contextcite | causes | 1/4 | 25% | 8% | FP | 64 | - | 55.2s | $0.000 |
