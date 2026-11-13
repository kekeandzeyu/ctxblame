# ctxblame

"git blame" for LLM agent decisions: replay one recorded LLM request with
pieces of context removed and report which chunk caused the decision.
Works with any model: the evidence comes from replays, not from the model's
own explanation. Status: early feasibility spike, not ready for use.

Two wire formats are supported, which covers most models: Anthropic Messages
(`/v1/messages`) and OpenAI Chat Completions (`/chat/completions`).

## Recording proxy

```sh
# Anthropic format (Claude, or DeepSeek's Anthropic endpoint)
uv run ctxblame-proxy --upstream https://api.deepseek.com/anthropic --out traces/
ANTHROPIC_BASE_URL=http://127.0.0.1:8787 your-agent ...

# OpenAI format (OpenAI, DeepSeek, Qwen, OpenRouter, vLLM, Ollama, ...)
uv run ctxblame-proxy --upstream https://api.deepseek.com --out traces/
OPENAI_BASE_URL=http://127.0.0.1:8787 your-agent ...
```

Each `POST /v1/messages` or `POST /chat/completions` exchange is saved as one JSON file: the request body,
and either the response body or (for streams) every raw SSE event plus the
reassembled message. Auth headers are forwarded but never written to disk.
`traces/` is git-ignored because it holds your prompts.

## Replay

```sh
export DEEPSEEK_API_KEY=...        # or ANTHROPIC_API_KEY / OPENAI_API_KEY; see --api-key-env
uv run ctxblame-replay traces/<record>.json -n 10 --key-args command
```

Re-sends the recorded request unchanged N times (no tool is executed) and
reports how often the same decision comes back: same tool name and same
normalized arguments (or only the `--key-args` you name), with a 95% interval.
Every call is priced and logged to `.ctxblame/spend.jsonl`; `--budget`
(default $5) is a hard cap across runs.

## Ablation

```sh
uv run ctxblame-replay traces/<record>.json --list-units          # what can be removed
uv run ctxblame-replay traces/<record>.json -n 20 --remove pair:toolu_12
uv run ctxblame-replay traces/<record>.json -n 20 --remove-text "We use pnpm in this repo."
uv run ctxblame-replay traces/<record>.json -n 10 --remove-random 45 --seed 1 --protect "<the user's task>"
```

Removing a tool call always removes its result too (and the reverse), empty
messages are dropped and same-role neighbours merged, so the ablated request
stays valid. `--key-arg 'command~\bpnpm\b'` makes "same decision" mean "the
command matches this regex" instead of exact arguments.

## Phase 0 results

See [experiments/phase0](experiments/phase0/README.md): five planted-cause
scenarios, both wire formats, two DeepSeek models.

## Tests

```sh
uv run pytest
```
