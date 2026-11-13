# Phase 0: is an agent's decision stable enough to attribute?

Before building a blame engine we checked the premise on five small agent
situations where we know the cause, because we planted it. For each one we
record one real call, then replay it with:

- **baseline**: the full context, 20 replays
- **cause removed**: the planted sentence (or tool call + result) removed, 20 replays
- **random control**: a random run of whole sentences/lines of the same size
  removed instead (never the cause or the user's task), 3 different spans x 10 replays

Run on 2026-11-13 against DeepSeek's API in **both wire formats** (Anthropic
Messages via `api.deepseek.com/anthropic`, OpenAI Chat Completions via
`api.deepseek.com`), with `deepseek-flash` and `deepseek-v4-pro`, thinking
disabled (see Limits). Total cost of everything below: about $0.52.

```sh
DEEPSEEK_API_KEY=... uv run python experiments/phase0/run.py --model deepseek-flash
```

## Scenarios

| # | Where the cause is | Removed by | Planted decision |
|---|---|---|---|
| 1 | a rule line in the system prompt (AGENTS.md section) | exact text | `make clean` before rebuilding |
| 2 | a whole tool call + result (reading README) | tool pair | `./scripts/run_tests.sh`, not `pytest` |
| 3 | one sentence inside a tool result | exact text | read `config/server.yaml`, not `config.ini` |
| 4 | a sentence in an earlier user message | exact text | `pnpm add`, not `npm install` |
| 5 | a section of the system prompt | exact text | `check_calendar` before `deploy` |

## Results: how often the planted decision is made

| Scenario | Format | flash: base / cause removed / random | v4-pro: base / cause removed / random |
|---|---|---|---|
| 1 make clean | anthropic | 0% / 0% / 0% | 5% / 0% / 0% |
| 1 make clean | openai | 0% / 0% / 0% | 0% / 0% / 0% |
| 2 README pair | anthropic | 30% / 0% / 17% | 50% / 0% / 50% |
| 2 README pair | openai | 20% / 0% / 27% | 80% / 0% / 33% |
| 3 config sentence | anthropic | 90% / 65% / 97% | 100% / 0% / 100% |
| 3 config sentence | openai | 85% / 80% / 90% | 100% / 0% / 100% |
| 4 pnpm | anthropic | 95% / 15% / 90% | 95% / 0% / 100% |
| 4 pnpm | openai | 85% / 15% / 80% | 95% / 0% / 93% |
| 5 deploy freeze | anthropic | 100% / 0% / 97% | 95% / 0% / 90% |
| 5 deploy freeze | openai | 95% / 0% / 93% | 90% / 0% / 97% |

"random" is the mean of the three control spans. Full per-condition data
(including how often the *recorded* call's decision comes back, which is
what the tool will measure) is in `results/<model>/results.md` and
`results.json`; the recorded calls are in `results/<model>/records/`.

## What we saw

1. **Where the plant really drives the decision, removing it flips the
   decision and random removals do not.** Scenarios 4 and 5 on both models,
   and 3 on v4-pro: 85-100% with the full context, 0-15% with the cause
   removed, 80-100% with a same-size random span removed. Both wire formats
   agree.
2. **A plant is not automatically a cause.** In scenario 1 neither model
   followed the rule at this step (they inspect the Makefile first), and in
   scenario 2 the README instruction drives the call only 20-80% of the
   time. There is nothing to attribute there; the replays show that directly.
3. **Causes can be redundant.** In scenario 3 on flash, the `ls config`
   output also lists `server.yaml`. Removing only the planted sentence leaves
   65-80%; removing only the `ls` line leaves 0% reading the file directly
   (most runs start investigating instead: the comment now points at a file
   the listing doesn't show); removing both: 0/40 touch `server.yaml`
   (`results/deepseek-flash/followup/`). Search must test combinations.
4. **The recorded call can be an outlier.** In scenario 4 (v4-pro, openai) the
   model chose `pnpm` in 95% of replays, but the one recorded call was an
   `ls`. Blame anchored on that call would see a 0% baseline; the tool must
   report how typical the recorded decision is.
5. **Random controls are not always neutral.** Removing generic system-prompt
   lines moved scenario 2 on v4-pro from 80% to 33%, and one control in
   scenario 4 (flash, openai) gave 4/10. Several controls per test, with
   their spread reported, are needed.
6. **"Same decision" needs intent, not just tool + argument.** Reading
   `server.yaml` with `Bash cat` instead of `Read` counts as different under
   a tool-name + argument matcher.

## Limits

- Short synthetic contexts (about 600-1000 tokens); real agent requests are
  often 20k-100k tokens.
- Thinking disabled: DeepSeek's thinking mode requires earlier turns'
  reasoning to be passed back, which hand-written histories don't have.
  Traces recorded from a real agent through the proxy include it.
- One provider family (two models); 20 replays per main condition, 10 per
  control, so single numbers carry about +-15-20 points of uncertainty.
