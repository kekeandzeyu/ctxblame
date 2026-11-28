750 case x seed rows, 250 cases

| group | rows | recall | precision | F1 | precond. separated | precond. blamed | neutral probe blamed | negatives correct | unplanted members |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 750 | 65% | 70% | 66% | 67% | 1% | 1% | 94% | 0.07 |
| oracle-dropped | 408 | 41% | 51% | 44% | 52% | 0% | 1% | 94% | 0.07 |
| oracle-valid | 342 | 85% | 85% | 85% | 79% | 3% | 0% | – | 0.06 |
| regime:and | 57 | 49% | 65% | 55% | 100% | 0% | 2% | – | 0.11 |
| regime:e_coupled | 27 | 11% | 21% | 14% | 0% | 0% | 0% | – | 0.00 |
| regime:mixed | 84 | 26% | 58% | 34% | 39% | 0% | 0% | – | 0.07 |
| regime:negative | 108 | – | 0% | – | – | 0% | 4% | 94% | 0.14 |
| regime:non_monotone | 75 | 31% | 41% | 34% | 31% | 0% | 0% | – | 0.00 |
| regime:or | 225 | 64% | 65% | 65% | 68% | 1% | 0% | – | 0.01 |
| regime:precondition_gated | 156 | 75% | 77% | 74% | 79% | 6% | 0% | – | 0.12 |
| regime:probe_interaction | 105 | 24% | 52% | 31% | 17% | 0% | 0% | – | 0.12 |
| regime:single | 261 | 81% | 80% | 80% | 73% | 2% | 0% | – | 0.08 |
