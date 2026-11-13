Model: deepseek-v4-pro; N=20 (baseline, cause removed), 3x10 (random controls)

| Scenario | Format | Recorded = target | Baseline | Cause removed | Random (mean, each) | Cost |
|---|---|---|---|---|---|---|
| system_rule_make_clean | anthropic | NO | 5/20 | 6/20 | 40% (4/10, 4/10, 4/10) | $0.0231 |
| system_rule_make_clean | openai | NO | 7/20 | 5/20 | 37% (3/10, 2/10, 6/10) | $0.0597 |
| tool_pair_readme_tests | anthropic | NO | 3/20 | 9/20 | 17% (3/10, 2/10, 0/10) | $0.0483 |
| tool_pair_readme_tests | openai | NO | 4/20 | 10/20 | 53% (5/10, 6/10, 5/10) | $0.0271 |
| tool_result_sentence_config | anthropic | yes | 20/20 | 0/20 | 100% (10/10, 10/10, 10/10) | $0.0238 |
| tool_result_sentence_config | openai | yes | 20/20 | 0/20 | 100% (10/10, 10/10, 10/10) | $0.0456 |
| user_message_pnpm | anthropic | yes | 19/20 | 0/20 | 100% (10/10, 10/10, 10/10) | $0.0333 |
| user_message_pnpm | openai | NO | 0/20 | 16/20 | 3% (0/10, 1/10, 0/10) | $0.0246 |
| system_section_deploy_freeze | anthropic | yes | 19/20 | 0/20 | 90% (9/10, 8/10, 10/10) | $0.0333 |
| system_section_deploy_freeze | openai | yes | 18/20 | 0/20 | 97% (10/10, 9/10, 10/10) | $0.0597 |
