# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 92% | 92% | 92% | 0% | - | 545.0 | 92% | 591.5s | $0.000 |
| ctxblame_uncond | 69% | 52% | 60% | 100% | - | 453.8 | 95% | 469.3s | $0.000 |
| ctxblame_flat | 92% | 92% | 92% | 0% | - | 715.4 | 90% | 676.8s | $0.000 |
| loo | 0% | 0% | 0% | 100% | - | 203.1 | 89% | 230.7s | $0.000 |
| self_explain | 48% | 57% | 47% | 17% | - | 1.0 | 0% | 26.8s | $0.000 |
| contextcite | 45% | 23% | 28% | 92% | - | 64.0 | - | 45.5s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| real/run1/step21 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 450 | 89% | 430.9s | $0.000 |
| real/run1/step21 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 460 | 98% | 435.6s | $0.000 |
| real/run1/step21 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 455 | 92% | 431.9s | $0.000 |
| real/run1/step21 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 190 | 88% | 226.0s | $0.000 |
| real/run1/step21 | precondition_or | self_explain | causes | 2/3 | 67% | 40% | no | 1 | 0% | 53.1s | $0.000 |
| real/run1/step21 | precondition_or | contextcite | causes | 2/3 | 67% | 18% | FP | 64 | - | 46.3s | $0.000 |
| real/run2/step19 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 545 | 94% | 798.3s | $0.000 |
| real/run2/step19 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 460 | 90% | 505.9s | $0.000 |
| real/run2/step19 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 515 | 91% | 663.5s | $0.000 |
| real/run2/step19 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 175 | 88% | 170.3s | $0.000 |
| real/run2/step19 | precondition_or | self_explain | causes | 2/3 | 67% | 100% | no | 1 | 0% | 15.4s | $0.000 |
| real/run2/step19 | precondition_or | contextcite | causes | 3/3 | 100% | 75% | FP | 64 | - | 46.3s | $0.000 |
| real/run3/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 450 | 89% | 584.5s | $0.000 |
| real/run3/step24 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 460 | 90% | 671.5s | $0.000 |
| real/run3/step24 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 450 | 88% | 590.0s | $0.000 |
| real/run3/step24 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 210 | 87% | 274.2s | $0.000 |
| real/run3/step24 | precondition_or | self_explain | causes | 2/3 | 67% | 11% | no | 1 | 0% | 47.2s | $0.000 |
| real/run3/step24 | precondition_or | contextcite | causes | 0/3 | 0% | 0% | FP | 64 | - | 59.9s | $0.000 |
| real/run4/step21 | or_redundant | ctxblame | preconditions_only | 0/3 | 0% | 0% | - | 610 | 98% | 1361.8s | $0.000 |
| real/run4/step21 | or_redundant | ctxblame_uncond | causes | 0/3 | 0% | 0% | - | 440 | 98% | 800.5s | $0.000 |
| real/run4/step21 | or_redundant | ctxblame_flat | none_found | 0/3 | 0% | 0% | - | 1765 | 93% | 2090.9s | $0.000 |
| real/run4/step21 | or_redundant | loo | causes | 0/3 | 0% | 0% | - | 385 | 94% | 676.2s | $0.000 |
| real/run4/step21 | or_redundant | self_explain | causes | 0/3 | 0% | 0% | - | 1 | 0% | 82.6s | $0.000 |
| real/run4/step21 | or_redundant | contextcite | causes | 3/3 | 100% | 30% | - | 64 | - | 48.1s | $0.000 |
| real/run6/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 455 | 98% | 439.9s | $0.000 |
| real/run6/step24 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 465 | 89% | 433.6s | $0.000 |
| real/run6/step24 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 450 | 91% | 386.9s | $0.000 |
| real/run6/step24 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 205 | 89% | 170.3s | $0.000 |
| real/run6/step24 | precondition_or | self_explain | causes | 2/3 | 67% | 100% | no | 1 | 0% | 7.5s | $0.000 |
| real/run6/step24 | precondition_or | contextcite | causes | 1/3 | 33% | 25% | FP | 64 | - | 49.9s | $0.000 |
| real/run8/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 430 | 89% | 295.6s | $0.000 |
| real/run8/step14 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 440 | 93% | 310.7s | $0.000 |
| real/run8/step14 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 590 | 89% | 431.2s | $0.000 |
| real/run8/step14 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 155 | 89% | 124.0s | $0.000 |
| real/run8/step14 | precondition_or | self_explain | causes | 1/3 | 33% | 100% | no | 1 | 0% | 3.5s | $0.000 |
| real/run8/step14 | precondition_or | contextcite | causes | 1/3 | 33% | 50% | FP | 64 | - | 30.9s | $0.000 |
| real/run9/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 430 | 89% | 317.6s | $0.000 |
| real/run9/step14 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 440 | 98% | 325.4s | $0.000 |
| real/run9/step14 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 580 | 89% | 451.0s | $0.000 |
| real/run9/step14 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 155 | 88% | 147.7s | $0.000 |
| real/run9/step14 | precondition_or | self_explain | causes | 1/3 | 33% | 33% | no | 1 | 0% | 8.1s | $0.000 |
| real/run9/step14 | precondition_or | contextcite | causes | 0/3 | 0% | 0% | FP | 64 | - | 31.6s | $0.000 |
| real/run9/step20 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 530 | 91% | 423.0s | $0.000 |
| real/run9/step20 | precondition_or | ctxblame_uncond | causes | 4/4 | 100% | 80% | FP | 540 | 97% | 482.1s | $0.000 |
| real/run9/step20 | precondition_or | ctxblame_flat | causes | 4/4 | 100% | 100% | YES | 785 | 90% | 668.0s | $0.000 |
| real/run9/step20 | precondition_or | loo | causes | 0/4 | 0% | 0% | FP | 185 | 89% | 163.6s | $0.000 |
| real/run9/step20 | precondition_or | self_explain | causes | 2/4 | 50% | 100% | no | 1 | 0% | 7.4s | $0.000 |
| real/run9/step20 | precondition_or | contextcite | causes | 2/4 | 50% | 22% | FP | 64 | - | 41.2s | $0.000 |
| real/run9/step29 | precondition_or | ctxblame | causes | 5/5 | 100% | 100% | YES | 1280 | 91% | 1082.5s | $0.000 |
| real/run9/step29 | precondition_or | ctxblame_uncond | causes | 0/5 | 0% | 0% | FP | 635 | 94% | 579.1s | $0.000 |
| real/run9/step29 | precondition_or | ctxblame_flat | causes | 5/5 | 100% | 100% | YES | 935 | 90% | 859.9s | $0.000 |
| real/run9/step29 | precondition_or | loo | causes | 0/5 | 0% | 0% | FP | 230 | 89% | 215.0s | $0.000 |
| real/run9/step29 | precondition_or | self_explain | causes | 1/5 | 20% | 20% | FP | 1 | 0% | 12.6s | $0.000 |
| real/run9/step29 | precondition_or | contextcite | causes | 2/5 | 40% | 20% | FP | 64 | - | 55.2s | $0.000 |
| real/run13/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 430 | 89% | 404.5s | $0.000 |
| real/run13/step14 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 440 | 97% | 377.3s | $0.000 |
| real/run13/step14 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 590 | 89% | 485.4s | $0.000 |
| real/run13/step14 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 155 | 90% | 170.0s | $0.000 |
| real/run13/step14 | precondition_or | self_explain | causes | 1/3 | 33% | 100% | no | 1 | 0% | 6.2s | $0.000 |
| real/run13/step14 | precondition_or | contextcite | causes | 0/3 | 0% | 0% | FP | 64 | - | 33.3s | $0.000 |
| real/run13/step17 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 495 | 91% | 518.3s | $0.000 |
| real/run13/step17 | precondition_or | ctxblame_uncond | causes | 0/4 | 0% | 0% | FP | 315 | 97% | 311.6s | $0.000 |
| real/run13/step17 | precondition_or | ctxblame_flat | causes | 4/4 | 100% | 100% | YES | 725 | 89% | 702.2s | $0.000 |
| real/run13/step17 | precondition_or | loo | causes | 0/4 | 0% | 0% | FP | 170 | 88% | 150.8s | $0.000 |
| real/run13/step17 | precondition_or | self_explain | causes | 2/4 | 50% | 50% | no | 1 | 0% | 11.9s | $0.000 |
| real/run13/step17 | precondition_or | contextcite | causes | 1/4 | 25% | 8% | FP | 64 | - | 41.1s | $0.000 |
| real/run15/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 455 | 92% | 538.7s | $0.000 |
| real/run15/step24 | precondition_or | ctxblame_uncond | causes | 3/3 | 100% | 75% | FP | 465 | 96% | 520.3s | $0.000 |
| real/run15/step24 | precondition_or | ctxblame_flat | causes | 3/3 | 100% | 100% | YES | 450 | 92% | 503.9s | $0.000 |
| real/run15/step24 | precondition_or | loo | causes | 0/3 | 0% | 0% | FP | 205 | 89% | 253.1s | $0.000 |
| real/run15/step24 | precondition_or | self_explain | causes | 2/3 | 67% | 50% | no | 1 | 0% | 20.5s | $0.000 |
| real/run15/step24 | precondition_or | contextcite | causes | 1/3 | 33% | 20% | FP | 64 | - | 51.9s | $0.000 |
| real/run15/step27 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 525 | 90% | 493.6s | $0.000 |
| real/run15/step27 | precondition_or | ctxblame_uncond | causes | 0/4 | 0% | 0% | FP | 340 | 98% | 346.9s | $0.000 |
| real/run15/step27 | precondition_or | ctxblame_flat | causes | 4/4 | 100% | 100% | YES | 1010 | 91% | 533.3s | $0.000 |
| real/run15/step27 | precondition_or | loo | causes | 0/4 | 0% | 0% | FP | 220 | 89% | 258.2s | $0.000 |
| real/run15/step27 | precondition_or | self_explain | causes | 3/4 | 75% | 38% | FP | 1 | 0% | 72.4s | $0.000 |
| real/run15/step27 | precondition_or | contextcite | causes | 4/4 | 100% | 29% | no | 64 | - | 55.8s | $0.000 |
