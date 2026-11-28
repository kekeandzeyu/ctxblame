750 case x seed rows, 250 cases

| group | rows | recall | precision | F1 | precond. separated | precond. blamed | neutral probe blamed | negatives correct | unplanted members |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 750 | 61% | 70% | 64% | 67% | 0% | 1% | 94% | 0.07 |
| oracle-dropped | 408 | 38% | 51% | 42% | 52% | 0% | 1% | 94% | 0.07 |
| oracle-valid | 342 | 80% | 86% | 82% | 79% | 1% | 0% | – | 0.06 |
| regime:and | 117 | 62% | 77% | 67% | 73% | 3% | 1% | – | 0.19 |
| regime:e_coupled | 117 | 37% | 66% | 46% | 65% | 0% | 0% | – | 0.09 |
| regime:mixed | 147 | 34% | 63% | 42% | 79% | 0% | 0% | – | 0.06 |
| regime:negative | 108 | – | 0% | – | – | 0% | 4% | 94% | 0.14 |
| regime:non_monotone | 75 | 26% | 41% | 31% | 31% | 0% | 0% | – | 0.00 |
| regime:or | 165 | 64% | 66% | 65% | 11% | 0% | 0% | – | 0.00 |
| regime:precondition_gated | 66 | 79% | 81% | 78% | 71% | 5% | 0% | – | 0.14 |
| regime:probe_interaction | 108 | 28% | 61% | 37% | 42% | 0% | 0% | – | 0.12 |
| regime:single | 198 | 76% | 76% | 76% | 17% | 0% | 1% | – | 0.03 |
