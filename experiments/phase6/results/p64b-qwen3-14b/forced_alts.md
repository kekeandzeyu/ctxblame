## p64b-qwen3-14b

| planted kinds | instead of A | steer sets | most common |
|---|---|---:|---|
| carrier | competing tool | 23 | `run venv` 448, `run npm run` 211, `run flake8` 129 |
| carrier | same program | 3 | `run uv sync` 50, `run tox` 50, `run ruff` 42 |
| carrier | step: inspect | 22 | `run git status` 997, `list .` 44, `run npm test` 21 |
| carrier+precondition | step: edit | 1 | `run echo` 35, `edit src/config.py` 8, `search DEFAULT_TIMEOUT` 7 |
| carrier+precondition | step: inspect | 4 | `run git status` 180, `run echo` 8, `run git diff` 1 |
| carrier+precondition+probe | same program | 1 | `run cargo test` 50 |
| carrier+probe | step: inspect | 3 | `run git status` 123, `run npm run` 9, `run ci.sh` 3 |
| precondition | competing tool | 1 | `run python` 50 |
| precondition | same program | 8 | `run pnpm add` 231, `run uv add` 137, `run npm install` 9 |
| precondition | step: inspect | 6 | `run git status` 267, `run echo` 18, `read src/config.py` 3 |
| precondition+probe | step: edit | 1 | `run echo` 24, `edit src/config.py` 11, `run git status` 2 |
| precondition+probe | step: inspect | 5 | `run git status` 156, `run git diff` 12, `run echo` 6 |
| probe | same program | 1 | `run uv sync` 50 |

