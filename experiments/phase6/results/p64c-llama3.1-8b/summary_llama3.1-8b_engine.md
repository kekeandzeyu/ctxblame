750 case x seed rows, 250 cases

| group | rows | recall | precision | F1 | precond. separated | precond. blamed | neutral probe blamed | negatives correct | unplanted members |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 750 | 61% | 70% | 64% | 67% | 0% | 1% | 94% | 0.07 |
| oracle-dropped | 408 | 38% | 51% | 42% | 52% | 0% | 1% | 94% | 0.07 |
| oracle-valid | 342 | 80% | 86% | 82% | 79% | 1% | 0% | – | 0.06 |
| regime:and | 57 | 48% | 65% | 54% | 100% | 0% | 2% | – | 0.11 |
| regime:e_coupled | 117 | 39% | 66% | 48% | 65% | 0% | 0% | – | 0.09 |
| regime:mixed | 84 | 25% | 58% | 33% | 39% | 0% | 0% | – | 0.07 |
| regime:negative | 108 | – | 0% | – | – | 0% | 4% | 94% | 0.14 |
| regime:non_monotone | 75 | 25% | 41% | 30% | 31% | 0% | 0% | – | 0.00 |
| regime:or | 225 | 60% | 66% | 62% | 68% | 0% | 0% | – | 0.01 |
| regime:precondition_gated | 66 | 79% | 81% | 78% | 71% | 5% | 0% | – | 0.14 |
| regime:probe_interaction | 105 | 23% | 52% | 30% | 17% | 0% | 0% | – | 0.12 |
| regime:single | 261 | 76% | 80% | 77% | 73% | 1% | 0% | – | 0.08 |
