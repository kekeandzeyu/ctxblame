750 case x seed rows, 250 cases

| group | rows | recall | precision | F1 | precond. separated | precond. blamed | neutral probe blamed | negatives correct | unplanted members |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 750 | 65% | 68% | 65% | 70% | 6% | 1% | 95% | 0.07 |
| oracle-dropped | 408 | 41% | 49% | 43% | 57% | 2% | 2% | 95% | 0.09 |
| oracle-valid | 342 | 85% | 83% | 84% | 79% | 11% | 0% | – | 0.03 |
| regime:and | 57 | 46% | 59% | 51% | 100% | 0% | 4% | – | 0.09 |
| regime:e_coupled | 27 | 15% | 25% | 18% | 6% | 0% | 0% | – | 0.07 |
| regime:mixed | 84 | 27% | 57% | 34% | 44% | 5% | 0% | – | 0.10 |
| regime:negative | 108 | – | 0% | – | – | 0% | 4% | 95% | 0.16 |
| regime:non_monotone | 75 | 40% | 47% | 42% | 32% | 8% | 0% | – | 0.03 |
| regime:or | 225 | 65% | 64% | 65% | 70% | 9% | 0% | – | 0.01 |
| regime:precondition_gated | 156 | 75% | 68% | 70% | 81% | 28% | 0% | – | 0.06 |
| regime:probe_interaction | 105 | 24% | 50% | 30% | 20% | 4% | 2% | – | 0.15 |
| regime:single | 261 | 81% | 77% | 79% | 77% | 7% | 0% | – | 0.07 |
