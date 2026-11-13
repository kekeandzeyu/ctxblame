Model: deepseek-flash; N=20 (baseline, cause removed), 3x10 (random controls)

| Scenario | Format | Recorded = target | Baseline | Cause removed | Random (mean, each) | Cost |
|---|---|---|---|---|---|---|
| system_rule_make_clean | anthropic | NO | 13/20 | 6/20 | 53% (4/10, 4/10, 8/10) | $0.0091 |
| system_rule_make_clean | openai | NO | 16/20 | 15/20 | 70% (6/10, 9/10, 6/10) | $0.0130 |
| tool_pair_readme_tests | anthropic | NO | 11/20 | 18/20 | 60% (8/10, 5/10, 5/10) | $0.0148 |
| tool_pair_readme_tests | openai | yes | 4/20 | 0/20 | 27% (1/10, 4/10, 3/10) | $0.0105 |
| tool_result_sentence_config | anthropic | yes | 18/20 | 13/20 | 97% (10/10, 10/10, 9/10) | $0.0080 |
| tool_result_sentence_config | openai | yes | 17/20 | 16/20 | 90% (9/10, 9/10, 9/10) | $0.0125 |
| user_message_pnpm | anthropic | yes | 19/20 | 3/20 | 90% (8/10, 9/10, 10/10) | $0.0091 |
| user_message_pnpm | openai | yes | 17/20 | 3/20 | 80% (4/10, 10/10, 10/10) | $0.0103 |
| system_section_deploy_freeze | anthropic | yes | 20/20 | 0/20 | 97% (9/10, 10/10, 10/10) | $0.0108 |
| system_section_deploy_freeze | openai | yes | 19/20 | 0/20 | 93% (8/10, 10/10, 10/10) | $0.0146 |
