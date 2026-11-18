N=20 per condition, 3x10 random controls; cost $2.5873

| Case | Condition | Target rate | Most common other outcome |
|---|---|---|---|
| arch/anthropic-1/step2 | baseline | 20/20 | read tests/test_formats.py (16) |
| arch/anthropic-1/step2 | rule | 17/20 | list src (14) |
| arch/anthropic-1/step2 | thinking | 20/20 | read tests/test_formats.py (18) |
| arch/anthropic-1/step2 | rule+thinking | 17/20 | read tests/test_formats.py (14) |
| arch/anthropic-1/step2 | random_0 | 10/10 | read tests/test_formats.py (10) |
| arch/anthropic-1/step2 | random_1 | 10/10 | read tests/test_formats.py (9) |
| arch/anthropic-1/step2 | random_2 | 10/10 | read tests/test_formats.py (7) |
| pytest/anthropic-1/step1 | baseline | 14/20 | list_dir({"command~^python -m pytest": false}) (18) |
| pytest/anthropic-1/step1 | rule | 5/20 | list_dir({"command~^python -m pytest": false}) (15) |
| pytest/anthropic-1/step1 | example | 14/20 | list_dir({"command~^python -m pytest": false}) (19) |
| pytest/anthropic-1/step1 | rule+example | 0/20 | list_dir({"command~^python -m pytest": false}) (16) |
| pytest/anthropic-1/step1 | random_0 | 9/10 | list_dir({"command~^python -m pytest": false}) (10) |
| pytest/anthropic-1/step1 | random_1 | 10/10 | list_dir({"command~^python -m pytest": false}) (9) |
| pytest/anthropic-1/step1 | random_2 | 10/10 | list_dir({"command~^python -m pytest": false}) (7) |
| pytest/anthropic-1/step7 | baseline | 20/20 |  |
| pytest/anthropic-1/step7 | rule | 20/20 |  |
| pytest/anthropic-1/step7 | example | 20/20 |  |
| pytest/anthropic-1/step7 | rule+example | 20/20 |  |
| pytest/anthropic-1/step7 | history | 20/20 |  |
| pytest/anthropic-1/step7 | rule+example+history | 8/20 | bash({"command~^python -m pytest": false}) (12) |
| pytest/anthropic-1/step7 | random_0 | 10/10 |  |
| pytest/anthropic-1/step7 | random_1 | 10/10 |  |
| pytest/anthropic-1/step7 | random_2 | 10/10 |  |
| arch/openai-1/step2 | baseline | 20/20 | read tests/test_formats.py (16) |
| arch/openai-1/step2 | rule | 0/20 | read tests/test_formats.py (10) |
| arch/openai-1/step2 | random_0 | 10/10 | read tests/test_formats.py (9) |
| arch/openai-1/step2 | random_1 | 9/10 | read tests/test_formats.py (9) |
| arch/openai-1/step2 | random_2 | 10/10 | read tests/test_formats.py (7) |
| pytest/openai-1/step1 | baseline | 16/20 | list_dir({"command~^python -m pytest": false}) (19) |
| pytest/openai-1/step1 | rule | 9/20 | list_dir({"command~^python -m pytest": false}) (17) |
| pytest/openai-1/step1 | example | 15/20 | list_dir({"command~^python -m pytest": false}) (19) |
| pytest/openai-1/step1 | rule+example | 1/20 | list_dir({"command~^python -m pytest": false}) (18) |
| pytest/openai-1/step1 | random_0 | 6/10 | list_dir({"command~^python -m pytest": false}) (10) |
| pytest/openai-1/step1 | random_1 | 7/10 | list_dir({"command~^python -m pytest": false}) (8) |
| pytest/openai-1/step1 | random_2 | 8/10 | list_dir({"command~^python -m pytest": false}) (10) |
| pytest/openai-1/step5 | baseline | 20/20 |  |
| pytest/openai-1/step5 | rule | 20/20 |  |
| pytest/openai-1/step5 | example | 20/20 |  |
| pytest/openai-1/step5 | rule+example | 20/20 |  |
| pytest/openai-1/step5 | history | 20/20 |  |
| pytest/openai-1/step5 | rule+example+history | 5/20 | bash({"command~^python -m pytest": false}) (15) |
| pytest/openai-1/step5 | random_0 | 10/10 | read_file({"command~^python -m pytest": false}) (1) |
| pytest/openai-1/step5 | random_1 | 10/10 |  |
| pytest/openai-1/step5 | random_2 | 10/10 |  |
