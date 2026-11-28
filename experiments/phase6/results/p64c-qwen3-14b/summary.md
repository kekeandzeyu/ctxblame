750 case x seed rows, 250 cases

| group | rows | recall | precision | F1 | precond. separated | precond. blamed | neutral probe blamed | negatives correct | unplanted members |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 750 | 81% | 84% | 83% | 54% | 1% | 2% | 80% | 0.17 |
| oracle-dropped | 312 | 62% | 65% | 65% | 19% | 1% | 5% | 68% | 0.26 |
| oracle-valid | 438 | 92% | 96% | 94% | 96% | 0% | 0% | 100% | 0.11 |
| regime:and | 12 | 62% | 92% | 72% | 50% | 0% | 0% | – | 0.42 |
| regime:e_coupled | 225 | 56% | 69% | 61% | 39% | 2% | 2% | – | 0.16 |
| regime:mixed | 12 | 25% | 58% | 34% | 0% | 0% | 0% | – | 0.58 |
| regime:negative | 102 | – | 0% | – | – | 0% | 12% | 80% | 0.80 |
| regime:non_monotone | 90 | 36% | 53% | 41% | 19% | 4% | 3% | – | 0.28 |
| regime:or | 300 | 78% | 85% | 80% | 61% | 0% | 0% | – | 0.02 |
| regime:precondition_gated | 72 | 99% | 100% | 99% | 100% | 0% | 0% | – | 0.00 |
| regime:probe_interaction | 102 | 37% | 54% | 42% | 11% | 4% | 1% | – | 0.25 |
| regime:single | 255 | 94% | 97% | 95% | 78% | 0% | 0% | – | 0.00 |
