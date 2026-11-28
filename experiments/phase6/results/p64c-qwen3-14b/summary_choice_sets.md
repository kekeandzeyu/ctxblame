750 case x seed rows, 250 cases

| group | rows | recall | precision | F1 | precond. separated | precond. blamed | neutral probe blamed | negatives correct | unplanted members |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 750 | 82% | 84% | 83% | 54% | 1% | 2% | 80% | 0.17 |
| oracle-dropped | 312 | 66% | 65% | 67% | 19% | 1% | 6% | 68% | 0.26 |
| oracle-valid | 438 | 92% | 96% | 93% | 96% | 0% | 0% | 100% | 0.11 |
| regime:and | 75 | 89% | 94% | 90% | 74% | 0% | 1% | – | 0.07 |
| regime:e_coupled | 225 | 59% | 69% | 62% | 39% | 2% | 3% | – | 0.16 |
| regime:mixed | 129 | 68% | 87% | 73% | 76% | 0% | 0% | – | 0.05 |
| regime:negative | 102 | – | 0% | – | – | 0% | 12% | 80% | 0.80 |
| regime:non_monotone | 90 | 48% | 53% | 49% | 19% | 4% | 4% | – | 0.28 |
| regime:or | 210 | 77% | 78% | 78% | 2% | 1% | 1% | – | 0.10 |
| regime:precondition_gated | 72 | 99% | 100% | 99% | 100% | 0% | 0% | – | 0.00 |
| regime:probe_interaction | 87 | 43% | 67% | 50% | 31% | 5% | 1% | – | 0.22 |
| regime:single | 219 | 93% | 92% | 92% | 19% | 0% | 1% | – | 0.05 |
