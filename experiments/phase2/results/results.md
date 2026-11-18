| Case | Baseline | Result | Planted carriers found | Precision | Causes reported | Cost |
|---|---|---|---|---|---|---|
| p0/system_rule_make_clean/anthropic | 0/10 | no_stable_decision | 0/1 | - | - | $0.003 |
| p0/system_rule_make_clean/openai | 0/10 | no_stable_decision | 0/1 | - | - | $0.003 |
| p0/tool_pair_readme_tests/anthropic | 4/10 | no_stable_decision | 0/1 | - | - | $0.003 |
| p0/tool_pair_readme_tests/openai | 8/10 | causes | 1/1 | 100% | turn 2 Read({"path": "README.md"}) result line 5: 'Run `./scripts/run_tests.sh --fast` instead.' (0/20) | $0.071 |
| p0/tool_result_sentence_config/anthropic | 10/10 | causes | 1/1 | 100% | turn 2 Read({"path": "config.ini"}) + result: '# Settings for the API server. # This file is no l' (3/25) | $0.039 |
| p0/tool_result_sentence_config/openai | 10/10 | none_found | 0/1 | - | - | $0.052 |
| p0/user_message_pnpm/anthropic | 8/10 | causes | 1/1 | 100% | turn 0 user message sentence 3: 'We use pnpm in this repo, never npm or yarn.' (2/20); turn 1 Bash({"command": "ls; cat apps/web/package.json"}) + result: 'apps packages package.json turbo.json README.md --' + turn 2 assistant text sentence 2: 'What would you like me to do?' (3/25) [not specific] | $0.097 |
| p0/user_message_pnpm/openai | 10/10 | causes | 1/1 | 100% | turn 0 user message sentence 3: 'We use pnpm in this repo, never npm or yarn.' (1/20) | $0.135 |
| p0/system_section_deploy_freeze/anthropic | 10/10 | causes | 1/1 | 100% | system ¶2 line 3: 'Before any production deploy, check the `deploy-fr' (0/20) | $0.051 |
| p0/system_section_deploy_freeze/openai | 10/10 | causes | 1/1 | 100% | system ¶2 line 3: 'Before any production deploy, check the `deploy-fr' (0/20) | $0.049 |
| p1/arch/openai/step2 | 10/10 | causes | 1/1 | 100% | system ¶7 line 2: '- Before editing anything under src/, read docs/AR' (0/20) | $0.134 |
| p1/arch/anthropic/step2 | 10/10 | none_found | 0/1 | - | - | $0.541 |
| p1/pytest/openai/step1 | 8/10 | causes | 1/2 | 100% | system ¶7 line 4: '- Run the test suite with `python -m pytest -q`.' (7/35) | $0.370 |
| p1/pytest/anthropic/step1 | 8/10 | none_found | 0/2 | - | - | $0.417 |
| p1/pytest/openai/step5 | 10/10 | causes | 3/3 | 60% | turn 4 edit_file({"path": "src/ctxblame/formats.py", "old_string":…) + result: 'edited src/ctxblame/formats.py' (0/20); tool bash description 2: 'the command line, e.g. `python -m pytest -q`' + tool read_file description 4: 'maximum number of lines' + system ¶7 line 4: '- Run the test suite with `python -m pytest -q`.' + turn 1 bash({"command": "python -m pytest -q", "description":…) + result: '............F.....................................' (2/15) | $2.417 |
| p1/pytest/anthropic/step7 | 10/10 | causes | 0/3 | 0% | turn 6 edit_file({"path": "src/ctxblame/formats.py", "old_string":…) + result: 'edited src/ctxblame/formats.py' (0/20) | $0.198 |
