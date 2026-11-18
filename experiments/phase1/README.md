# Phase 1: planted causes in real agent traces

Phase 0 used short hand-written contexts with thinking off. Here a small but
real coding agent ([agent.py](agent.py)) fixes a bug planted in a copy of this
repository, through the recording proxy, **with thinking on**, once per wire
format. Model `deepseek-v4-pro`, run on 2026-11-18. The two traces (8 and 6
steps, up to 20k input tokens) are in [results/traces/](results/traces/).

```sh
uv run ctxblame record --upstream https://api.deepseek.com/anthropic --port 8791 --trace a.jsonl &
DEEPSEEK_API_KEY=... uv run python experiments/phase1/agent.py --format anthropic \
    --base-url http://127.0.0.1:8791 --workspace /tmp/ws
uv run ctxblame steps a.jsonl
DEEPSEEK_API_KEY=... uv run python experiments/phase1/ablations.py      # the table below
```

The agent's AGENTS.md has two rules that show up in the traces, each with
other places in the context that say the same thing:

| Case | Rule in AGENTS.md | Decision | Other carriers |
|---|---|---|---|
| arch | "Before editing anything under src/, read docs/ARCHITECTURE.md" | step 2 reads `docs/ARCHITECTURE.md` | the agent's own earlier thinking (Anthropic trace only) |
| pytest | "Run the test suite with `python -m pytest -q`. Do not use `uv run`" | the call that runs the tests uses `python -m pytest` | the bash tool's parameter description (`e.g. python -m pytest -q`); later in the run, the agent's own earlier pytest call |

"Same decision" = the target is **any** of the reply's parallel calls
(`--any-call`); the agent usually makes 2-3 calls per step and their order is
noise.

## Results: how often the decision is made (20 replays; controls 3 x 10)

| Case | Format, step | Baseline | Rule removed | Other carrier(s) removed | All removed | Random controls |
|---|---|---|---|---|---|---|
| arch | openai, 2 | 20/20 | **0/20** | (none) | | 10, 9, 10 /10 |
| arch | anthropic, 2 | 20/20 | 17/20 | thinking: 20/20 * | 17/20 * | 10, 10, 10 /10 |
| pytest | anthropic, 1 | 14/20 | 5/20 | example: 14/20 | **0/20** | 9, 10, 10 /10 |
| pytest | openai, 1 | 16/20 | 9/20 | example: 15/20 | **1/20** | 6, 7, 8 /10 |
| pytest | anthropic, 7 | 20/20 | 20/20 | example 20/20, history 20/20, rule+example 20/20 | 8/20 | 10, 10, 10 /10 |
| pytest | openai, 5 | 20/20 | 20/20 | example 20/20, history 20/20, rule+example 20/20 | 5/20 | 10, 10, 10 /10 |

\* Not a real removal, see finding 1. Full data: [results/ablations.md](results/ablations.md)
and `results/ablations.json`. Cost: $2.59 for the table, plus $0.06 for the
follow-up below.

## What we saw

1. **DeepSeek restores removed reasoning server-side.** In the Anthropic
   trace, with the rule *and* the earlier thinking removed, nothing in the
   request mentions ARCHITECTURE, yet 17/20 replies read exactly
   `docs/ARCHITECTURE.md`. Follow-up (10 replays each):
   - same request with the tool-call ids of that turn renamed: **rejected**
     with HTTP 400 "`content[].thinking` in the thinking mode must be passed
     back". With the original ids it was accepted, so the server recognises
     its own ids and has the reasoning;
   - `docs/` renamed to `notes/` in the directory listing: still 2/10 read
     `docs/ARCHITECTURE.md`, a folder the request never shows;
   - thinking disabled: 0/10.

   So reasoning is context that the request body does not fully control.
   `ctxblame` now gives fresh ids to the calls whose reasoning it removes, so
   such a provider refuses instead of silently undoing the ablation. On
   DeepSeek's Anthropic endpoint in thinking mode, reasoning is therefore not
   removable. In the OpenAI trace the earlier reasoning never mentioned
   ARCHITECTURE, the rule was the only carrier, and removing it gave 0/20.
2. **Redundant causes are the normal case in real traces.** At the first
   test run, the rule alone moves 14→5 and 16→9, the tool's example alone
   does nothing, and both together give 0/20 and 1/20. Single-unit removal
   would call the example irrelevant and the rule a partial cause; the truth
   is "the rule, backed up by the example".
3. **Later in a run, the agent's own history takes over.** By the second test
   run, removing the rule, the example, or the earlier pytest call (each
   alone or rule+example) changes nothing: 20/20. Only removing all three
   drops it, to 8/20 and 5/20. An agent copies what it already did.
4. **Replaying with thinking works**, in both formats, and the noise verdict
   catches outliers on real traces too: the recorded first call of OpenAI
   step 2 (`find src`) never came back in 10 replays; the model always reads
   ARCHITECTURE.md first.
5. **Cost is set by where the removal is, not how big it is.** The 20k-token
   Anthropic step 7 cost $1.77 of the $2.59: removing text from the system
   prompt invalidates the prompt cache for everything after it, so 1.25M
   input tokens were billed uncached. Removals near the end of the context
   are cheap. The blame engine needs this in its cost model and search order.

## Limits

- One run per format, one provider, one model. Two rules, six cases.
- Random controls can hit task-critical text (one removed the buggy line from
  a `formats.py` tool result); their spread is shown.
- The finding about server-side reasoning is from DeepSeek's Anthropic
  endpoint; the OpenAI endpoint was not tested for it.
