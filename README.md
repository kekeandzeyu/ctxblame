# ctxblame

"git blame" for LLM agent decisions: replay one recorded LLM request with
pieces of context removed and report which chunk caused the decision.
Works with any model: the evidence comes from replays, not from the model's
own explanation. Status: early feasibility spike, not ready for use.

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

## Phase 0 results

See [experiments/phase0](experiments/phase0/README.md): five planted-cause
scenarios, both wire formats, two DeepSeek models.

## Phase 1 results

See [experiments/phase1](experiments/phase1/README.md): planted causes in real
agent traces with thinking on. Causes are usually redundant, the agent's own
history takes over later in a run, and DeepSeek restores removed reasoning
server-side unless the call ids change.

## Tests

```sh
uv run pytest
```
