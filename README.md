# ctxblame

"git blame" for LLM agent decisions: replay one recorded LLM request with
pieces of context removed and report which chunk caused the decision.
Works with any model: the evidence comes from replays, not from the model's
own explanation. Status: early feasibility spike, not ready for use.

## Recording proxy

```sh
uv run ctxblame-proxy --out traces/                    # upstream: api.anthropic.com
uv run ctxblame-proxy --upstream https://api.deepseek.com/anthropic --out traces/
# then point any Anthropic client at it:
ANTHROPIC_BASE_URL=http://127.0.0.1:8787 your-agent ...
```

Each `POST /v1/messages` exchange is saved as one JSON file: the request body,
and either the response body or (for streams) every raw SSE event plus the
reassembled message. Auth headers are forwarded but never written to disk.
`traces/` is git-ignored because it holds your prompts.

## Tests

```sh
uv run pytest
```
