750 case x seed rows, 250 cases

| group | rows | recall | precision | F1 | precond. separated | precond. blamed | neutral probe blamed | negatives correct | unplanted members |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 750 | 86% | 79% | 86% | 54% | 10% | 2% | 80% | 0.17 |
| oracle-dropped | 312 | 68% | 57% | 70% | 19% | 12% | 5% | 68% | 0.26 |
| oracle-valid | 438 | 94% | 92% | 93% | 96% | 8% | 0% | 100% | 0.11 |
| regime:and | 12 | 62% | 92% | 72% | 50% | 0% | 0% | – | 0.42 |
| regime:e_coupled | 150 | 43% | 39% | 47% | 11% | 22% | 3% | – | 0.25 |
| regime:mixed | 12 | 25% | 58% | 34% | 0% | 0% | 0% | – | 0.58 |
| regime:negative | 102 | – | 0% | – | – | 0% | 12% | 80% | 0.80 |
| regime:non_monotone | 90 | 37% | 50% | 42% | 19% | 8% | 3% | – | 0.28 |
| regime:or | 300 | 80% | 81% | 80% | 61% | 8% | 0% | – | 0.02 |
| regime:precondition_gated | 147 | 95% | 86% | 89% | 98% | 27% | 0% | – | 0.00 |
| regime:probe_interaction | 102 | 39% | 52% | 44% | 11% | 8% | 1% | – | 0.25 |
| regime:single | 255 | 97% | 94% | 95% | 78% | 6% | 0% | – | 0.00 |
