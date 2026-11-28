# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 92% | 92% | 92% | 0% | - | 931.5 | 92% | 313.6s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| real/run1/step21 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 630 | 91% | 233.6s | $0.000 |
| real/run2/step19 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 830 | 92% | 433.1s | $0.000 |
| real/run3/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 630 | 91% | 312.8s | $0.000 |
| real/run4/step21 | or_redundant | ctxblame | none_found | 0/3 | 0% | 0% | - | 3160 | 95% | 847.1s | $0.000 |
| real/run6/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 635 | 90% | 267.6s | $0.000 |
| real/run8/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 610 | 91% | 218.3s | $0.000 |
| real/run9/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 610 | 92% | 218.2s | $0.000 |
| real/run9/step20 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 750 | 93% | 279.1s | $0.000 |
| real/run9/step29 | precondition_or | ctxblame | causes | 5/5 | 100% | 100% | YES | 1550 | 93% | 390.0s | $0.000 |
| real/run13/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 610 | 91% | 198.2s | $0.000 |
| real/run13/step17 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 715 | 93% | 230.2s | $0.000 |
| real/run15/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 635 | 93% | 222.2s | $0.000 |
| real/run15/step27 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 745 | 97% | 225.7s | $0.000 |
