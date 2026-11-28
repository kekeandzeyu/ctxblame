750 case x seed rows, 250 cases

| group | rows | recall | precision | F1 | precond. separated | precond. blamed | neutral probe blamed | negatives correct | unplanted members |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 750 | 63% | 71% | 66% | 70% | 0% | 1% | 95% | 0.07 |
| oracle-dropped | 408 | 39% | 51% | 42% | 57% | 0% | 2% | 95% | 0.09 |
| oracle-valid | 342 | 84% | 89% | 85% | 79% | 0% | 0% | – | 0.03 |
| regime:and | 57 | 45% | 59% | 49% | 100% | 0% | 4% | – | 0.09 |
| regime:e_coupled | 117 | 52% | 72% | 58% | 66% | 0% | 0% | – | 0.08 |
| regime:mixed | 84 | 27% | 60% | 35% | 44% | 0% | 0% | – | 0.10 |
| regime:negative | 108 | – | 0% | – | – | 0% | 4% | 95% | 0.16 |
| regime:non_monotone | 75 | 37% | 50% | 41% | 32% | 0% | 0% | – | 0.03 |
| regime:or | 225 | 64% | 70% | 66% | 70% | 0% | 0% | – | 0.01 |
| regime:precondition_gated | 66 | 81% | 82% | 81% | 76% | 2% | 0% | – | 0.05 |
| regime:probe_interaction | 105 | 24% | 52% | 31% | 20% | 0% | 2% | – | 0.15 |
| regime:single | 261 | 79% | 81% | 79% | 77% | 0% | 0% | – | 0.07 |
