750 case x seed rows, 250 cases

| group | rows | recall | precision | F1 | precond. separated | precond. blamed | neutral probe blamed | negatives correct | unplanted members |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 750 | 63% | 71% | 66% | 70% | 0% | 1% | 95% | 0.07 |
| oracle-dropped | 408 | 39% | 51% | 42% | 57% | 0% | 2% | 95% | 0.09 |
| oracle-valid | 342 | 83% | 89% | 85% | 79% | 0% | 0% | – | 0.03 |
| regime:and | 117 | 67% | 76% | 70% | 76% | 1% | 2% | – | 0.12 |
| regime:e_coupled | 117 | 50% | 72% | 56% | 66% | 0% | 0% | – | 0.08 |
| regime:mixed | 147 | 39% | 68% | 47% | 79% | 0% | 0% | – | 0.05 |
| regime:negative | 108 | – | 0% | – | – | 0% | 4% | 95% | 0.16 |
| regime:non_monotone | 75 | 37% | 50% | 41% | 32% | 0% | 0% | – | 0.03 |
| regime:or | 165 | 66% | 68% | 67% | 39% | 0% | 0% | – | 0.01 |
| regime:precondition_gated | 66 | 81% | 82% | 81% | 76% | 2% | 0% | – | 0.05 |
| regime:probe_interaction | 108 | 29% | 60% | 37% | 43% | 0% | 2% | – | 0.15 |
| regime:single | 198 | 76% | 76% | 76% | 25% | 0% | 1% | – | 0.04 |
