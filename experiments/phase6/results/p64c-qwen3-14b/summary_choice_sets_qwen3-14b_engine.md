750 case x seed rows, 250 cases

| group | rows | recall | precision | F1 | precond. separated | precond. blamed | neutral probe blamed | negatives correct | unplanted members |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 750 | 80% | 83% | 81% | 54% | 1% | 4% | 80% | 0.21 |
| oracle-dropped | 312 | 65% | 62% | 65% | 19% | 2% | 9% | 68% | 0.36 |
| oracle-valid | 438 | 88% | 96% | 91% | 95% | 0% | 0% | 100% | 0.11 |
| regime:and | 75 | 81% | 91% | 84% | 72% | 0% | 7% | – | 0.05 |
| regime:e_coupled | 225 | 50% | 63% | 53% | 39% | 3% | 8% | – | 0.26 |
| regime:mixed | 129 | 62% | 86% | 70% | 77% | 0% | 0% | – | 0.05 |
| regime:negative | 102 | – | 0% | – | – | 0% | 12% | 80% | 0.90 |
| regime:non_monotone | 90 | 44% | 41% | 41% | 18% | 3% | 18% | – | 0.28 |
| regime:or | 210 | 78% | 78% | 78% | 1% | 3% | 1% | – | 0.14 |
| regime:precondition_gated | 72 | 100% | 100% | 100% | 100% | 0% | 0% | – | 0.00 |
| regime:probe_interaction | 87 | 45% | 69% | 51% | 33% | 7% | 2% | – | 0.18 |
| regime:single | 219 | 91% | 90% | 90% | 19% | 0% | 4% | – | 0.11 |
