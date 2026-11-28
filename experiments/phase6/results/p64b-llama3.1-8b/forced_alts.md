## p64b-llama3.1-8b

| planted kinds | instead of A | steer sets | most common |
|---|---|---:|---|
| carrier | competing tool | 7 | `run venv` 139, `run pip install` 97, `run pytest` 58 |
| carrier | same program | 1 | `run cargo test` 42 |
| carrier | step: inspect | 3 | `run git status` 130, `run validate.sh` 4 |
| carrier+precondition | competing tool | 5 | `run pip install` 97, `run pip uninstall` 28, `run poetry add` 22 |
| carrier+precondition | same program | 2 | `run pip install` 37, `run cargo test` 32, `run poetry add` 8 |
| carrier+precondition | step: edit | 1 | `run git add` 33, `run echo` 6, `run pytest` 4 |
| carrier+precondition | step: inspect | 1 | `run git status` 32 |
| carrier+precondition+probe | same program | 2 | `run pnpm add` 73 |
| carrier+precondition+probe | step: edit | 1 | `run git add` 18, `run pytest` 10, `run unittest` 5 |
| carrier+probe | step: inspect | 1 | `run git status` 13, `run make test` 6, `run ci.sh` 5 |
| precondition | same program | 3 | `run pnpm add` 82, `run pnpm install` 22, `run pnpm run` 10 |
| precondition | step: edit | 5 | `edit src/text.py` 94, `run edit_file` 76, `run git add` 15 |
| precondition | step: inspect | 10 | `run git status` 259, `run git diff` 109, `run git add` 44 |
| precondition+probe | competing tool | 3 | `run pip uninstall` 47, `run rm` 47, `run pip install` 9 |
| precondition+probe | step: edit | 1 | `run edit` 21, `run git status` 20, `edit src/lib.rs` 1 |

