750 case x seed rows, 250 cases

| group | rows | recall | precision | F1 | precond. separated | precond. blamed | neutral probe blamed | negatives correct | unplanted members |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 750 | 80% | 83% | 82% | 54% | 1% | 3% | 80% | 0.21 |
| oracle-dropped | 312 | 65% | 64% | 66% | 19% | 2% | 7% | 68% | 0.36 |
| oracle-valid | 438 | 89% | 96% | 91% | 95% | 0% | 0% | 100% | 0.11 |
| regime:and | 12 | 79% | 92% | 83% | 50% | 0% | 0% | – | 0.25 |
| regime:e_coupled | 225 | 51% | 65% | 56% | 39% | 3% | 4% | – | 0.26 |
| regime:mixed | 12 | 33% | 75% | 45% | 33% | 0% | 0% | – | 0.42 |
| regime:negative | 102 | – | 0% | – | – | 0% | 12% | 80% | 0.90 |
| regime:non_monotone | 90 | 41% | 46% | 42% | 18% | 3% | 9% | – | 0.28 |
| regime:or | 300 | 76% | 82% | 79% | 61% | 0% | 0% | – | 0.04 |
| regime:precondition_gated | 72 | 100% | 100% | 100% | 100% | 0% | 0% | – | 0.00 |
| regime:probe_interaction | 102 | 41% | 52% | 44% | 13% | 6% | 2% | – | 0.25 |
| regime:single | 255 | 92% | 97% | 93% | 77% | 0% | 2% | – | 0.00 |
