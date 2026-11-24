# ctxblame

"git blame" for LLM agent decisions: replay one recorded LLM request with
pieces of context removed and report which chunk caused the decision.
Works with any model: the evidence comes from replays, not from the model's
own explanation. Status: early; the blame engine works on the validation cases below, not yet on PyPI.

Two wire formats are supported, which covers most models: Anthropic Messages
(`/v1/messages`) and OpenAI Chat Completions (`/chat/completions`).

## Record

```sh
# Anthropic format (Claude, or DeepSeek's Anthropic endpoint)
uv run ctxblame record --upstream https://api.deepseek.com/anthropic
ANTHROPIC_BASE_URL=http://127.0.0.1:8787 your-agent ...

# OpenAI format (OpenAI, DeepSeek, Qwen, OpenRouter, vLLM, Ollama, ...)
uv run ctxblame record --upstream https://api.deepseek.com
OPENAI_BASE_URL=http://127.0.0.1:8787 your-agent ...
```

The proxy appends every `POST /v1/messages` or `POST /chat/completions`
exchange to one JSON-lines trace (`traces/<time>-<id>.jsonl`, or `--trace
FILE`), numbered in send order: the request body, and either the response
body or (for streams) every raw SSE event plus the reassembled message. Auth
headers are forwarded but never written to disk. `traces/` is git-ignored
because it holds your prompts.

```sh
uv run ctxblame steps traces/<trace>.jsonl          # one line per LLM call and its decision
```

## Replay

```sh
export DEEPSEEK_API_KEY=...        # or ANTHROPIC_API_KEY / OPENAI_API_KEY; see --api-key-env
uv run ctxblame replay traces/<trace>.jsonl --step 14 -n 10
```

Re-sends the recorded request unchanged N times (no tool is executed) and
reports how often the same decision comes back, with a 95% interval. "Same
decision" defaults to `--match intent`: what the call does, whichever tool
does it (`Read src/a.py` and `Bash cat src/a.py` are both `read src/a.py`).
`--match exact|args|name` and `--key-arg` are stricter or looser.
Every call is priced and logged to `.ctxblame/spend.jsonl`; `--budget`
(default $5) is a hard cap across runs.

## Ablation

```sh
uv run ctxblame replay T.jsonl --step 14 --list-units          # what can be removed
uv run ctxblame replay T.jsonl --step 14 -n 20 --remove pair:toolu_12
uv run ctxblame replay T.jsonl --step 14 -n 20 --remove-text "We use pnpm in this repo."
uv run ctxblame replay T.jsonl --step 14 -n 10 --remove-random 45 --seed 1 --protect "<the user's task>"
```

Removing a tool call always removes its result too (and the reverse), empty
messages are dropped and same-role neighbours merged, so the ablated request
stays valid. `--key-arg 'command~\bpnpm\b'` makes "same decision" mean "the
command matches this regex" instead of exact arguments. `--any-call` counts a reply as the same
decision when any of its parallel tool calls matches. `thinking:msg[i]`
removes one turn's reasoning (its calls get fresh ids, so a provider that
keeps reasoning server-side cannot restore it).

## Blame

```sh
uv run ctxblame why traces/<trace>.jsonl --step 14
```

```
Decision:  Bash({"command~\\bpnpm\\b": true})
Baseline:  10/10 replays (stable)
Chunks:    8 (3 tool desc, 1 system, 1 user, 2 assistant, 1 tool call)
Everything but the task removed: 0/10  -> the decision comes from the context

Cause 1 (removing it flips the decision: 1/20):
  - turn 0 user message sentence 3: 'We use pnpm in this repo, never npm or yarn.'
  controls (random same-size removals): 5/5, 5/5

Tests: 16, replays: 160, cost $0.07
```

How it works:

1. **Baseline.** Replay the step unchanged. If no decision comes back
   reliably it stops ("coin flip"); if the recorded call is unusual it
   explains the usual one instead.
2. **Chunks.** System-prompt paragraphs, earlier user and assistant text, each
   tool call with its result, each turn's reasoning, tool descriptions. The
   task (the latest user message with text) is never removed.
3. **Search.** If removing every chunk keeps the decision, the context does
   not carry it. Otherwise delta debugging finds a minimal set of chunks
   whose removal flips it: one chunk is a cause; several are *redundant
   carriers* of one cause (only removing all of them flips it, and each one
   alone is shown). Then it looks for further, independent causes.
4. **Refine** each member to the sentences or lines that matter, with the
   other carriers held removed.
5. **Check.** Each finding is confirmed with more replays, and compared with
   random removals of the same size. Findings that random removals reproduce
   too are reported as *context the decision needs (not specific)*, not as
   causes.

Each test replays in batches of 5 until the rate is clearly above or below
half the baseline rate (a flip needs at least 10 replays). By default a reply
counts as the same decision when *any* of its parallel calls matches
(`--first-call` to compare only the first). Removing reasoning gives those
calls fresh ids; a provider that then demands the reasoning makes it
"not removable", and the report says so. `--budget` caps the spend and the
full log of tests is saved as JSON in `runs/`.

## Phase 0 results

See [experiments/phase0](experiments/phase0/README.md): five planted-cause
scenarios, both wire formats, two DeepSeek models.

## Phase 1 results

See [experiments/phase1](experiments/phase1/README.md): planted causes in real
agent traces with thinking on. Causes are usually redundant, the agent's own
history takes over later in a run, and DeepSeek restores removed reasoning
server-side unless the call ids change.

## Phase 2 & Roadmap

See [experiments/phase2/results/results.md](experiments/phase2/results/results.md) for current end-to-end blame precision and recall, and [docs/ROADMAP.md](docs/ROADMAP.md) for the full technical audit, Phase 2 bug diagnosis (`step5`/`step7` precondition confounding and byte-0 cache invalidation), and next algorithmic milestones:

- **Conditional / contrastive blame (`--given`):** score `P(target | action_family)` and auto-protect workflow preconditions so earlier state edits (e.g. `edit_file` before `pytest`) are not confounded with choice/style carriers.
- **AND-preconditions vs. OR-carriers:** separate necessary context chunks from minimal hitting sets of redundant backups (`AGENTS.md` + tool schema examples + prior history).
- **KV-cache-stratified search:** probe suffix tiers before prefix tiers to preserve prompt-cache hits and cut replay spend by 5–10×.

## Tests

```sh
uv run pytest
```
