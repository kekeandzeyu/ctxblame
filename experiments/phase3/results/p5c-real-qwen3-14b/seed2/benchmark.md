# Phase 3 Attribution Benchmark

## Summary by Method

| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxblame | 92% | 92% | 92% | 0% | - | 637.3 | 93% | 453.7s | $0.000 |

## Per-Case Results

| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |
|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| real/run1/step21 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 550 | 91% | 409.4s | $0.000 |
| real/run2/step19 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 580 | 92% | 507.8s | $0.000 |
| real/run3/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 550 | 90% | 531.6s | $0.000 |
| real/run4/step21 | or_redundant | ctxblame | not_in_context | 0/3 | 0% | 0% | - | 820 | 97% | 877.5s | $0.000 |
| real/run6/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 555 | 90% | 463.5s | $0.000 |
| real/run8/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 530 | 91% | 385.3s | $0.000 |
| real/run9/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 530 | 91% | 381.0s | $0.000 |
| real/run9/step20 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 650 | 93% | 487.1s | $0.000 |
| real/run9/step29 | precondition_or | ctxblame | causes | 5/5 | 100% | 100% | YES | 1175 | 92% | 533.2s | $0.000 |
| real/run13/step14 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 530 | 91% | 312.5s | $0.000 |
| real/run13/step17 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 615 | 96% | 359.2s | $0.000 |
| real/run15/step24 | precondition_or | ctxblame | causes | 3/3 | 100% | 100% | YES | 555 | 91% | 315.9s | $0.000 |
| real/run15/step27 | precondition_or | ctxblame | causes | 4/4 | 100% | 100% | YES | 645 | 97% | 334.8s | $0.000 |
