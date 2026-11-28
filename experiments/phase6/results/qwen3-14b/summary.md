750 case x seed rows, 250 cases

| group | rows | recall | precision | F1 | precond. separated | precond. blamed | neutral probe blamed | negatives correct | unplanted members |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 750 | 87% | 80% | 87% | 54% | 5% | 3% | 80% | 0.21 |
| oracle-dropped | 312 | 71% | 55% | 71% | 19% | 11% | 7% | 68% | 0.36 |
| oracle-valid | 438 | 94% | 96% | 95% | 95% | 0% | 0% | 100% | 0.11 |
| regime:and | 12 | 79% | 92% | 83% | 50% | 0% | 0% | – | 0.25 |
| regime:e_coupled | 150 | 45% | 33% | 46% | 10% | 23% | 6% | – | 0.39 |
| regime:mixed | 12 | 33% | 75% | 45% | 33% | 0% | 0% | – | 0.42 |
| regime:negative | 102 | – | 0% | – | – | 0% | 12% | 80% | 0.90 |
| regime:non_monotone | 90 | 44% | 46% | 45% | 18% | 4% | 9% | – | 0.28 |
| regime:or | 300 | 81% | 82% | 81% | 61% | 0% | 0% | – | 0.04 |
| regime:precondition_gated | 147 | 94% | 94% | 94% | 98% | 0% | 0% | – | 0.01 |
| regime:probe_interaction | 102 | 43% | 49% | 46% | 13% | 8% | 2% | – | 0.25 |
| regime:single | 255 | 97% | 97% | 97% | 77% | 0% | 2% | – | 0.00 |
