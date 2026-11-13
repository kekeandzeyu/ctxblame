"""Wire-format adapters: Anthropic Messages and OpenAI Chat Completions.

Everything format-specific lives here, so the rest of ctxblame works on the
neutral ``Decision`` and ``Usage`` types.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from .sse import assemble_message, assemble_openai_chunks

ANTHROPIC = "anthropic"
OPENAI = "openai"


def detect_format(path: str) -> str | None:
    p = path.split("?", 1)[0].rstrip("/")
    if p.endswith("/v1/messages"):
        return ANTHROPIC
    if p.endswith("/chat/completions"):
        return OPENAI
    return None


def assemble_stream(fmt: str, events: list) -> dict:
    return assemble_message(events) if fmt == ANTHROPIC else assemble_openai_chunks(events)


# ---------------------------------------------------------------- decisions

@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict | str  # str only when the model emitted unparseable JSON


@dataclass
class Decision:
    calls: list[ToolCall] = field(default_factory=list)
    text: str = ""
    stop: str | None = None

    def key(self, key_args: list[str] | None = None, name_only: bool = False) -> str:
        """Comparable label for 'the same decision'.

        The decision is the first tool call: its name plus normalized
        arguments (all of them, or only ``key_args``). No tool call -> a
        fixed label, so "answered in text" is itself a decision. A key_args
        entry "arg~regex" compares whether the argument matches the regex
        instead of its exact value.
        """
        if not self.calls:
            return "<no tool call>"
        c = self.calls[0]
        if name_only:
            return c.name
        args = c.args
        if isinstance(args, dict) and key_args:
            sel = {}
            for spec in key_args:
                if "~" in spec:  # "arg~regex": does the argument match?
                    k, rx = spec.split("~", 1)
                    v = args.get(k)
                    sel[spec] = v is not None and re.search(rx, str(v)) is not None
                else:
                    sel[spec] = args.get(spec)
            args = sel
        return f"{c.name}({json.dumps(normalize(args), sort_keys=True, ensure_ascii=False)})"


def normalize(v):
    """Ignore formatting noise: surrounding/duplicate whitespace, trailing '/'."""
    if isinstance(v, str):
        s = re.sub(r"\s+", " ", v.strip())
        return s[:-1] if len(s) > 1 and s.endswith("/") else s
    if isinstance(v, dict):
        return {k: normalize(x) for k, x in v.items()}
    if isinstance(v, list):
        return [normalize(x) for x in v]
    return v


def _parse_args(s) -> dict | str:
    if isinstance(s, dict):
        return s
    try:
        v = json.loads(s) if s else {}
        return v if isinstance(v, dict) else s
    except (json.JSONDecodeError, TypeError):
        return s


def extract_decision(fmt: str, response: dict) -> Decision:
    if fmt == ANTHROPIC:
        calls, texts = [], []
        for b in response.get("content") or []:
            if b.get("type") == "tool_use":
                calls.append(ToolCall(b.get("name", ""), _parse_args(b.get("input", {}))))
            elif b.get("type") == "text":
                texts.append(b.get("text", ""))
        return Decision(calls, "".join(texts), response.get("stop_reason"))
    ch = (response.get("choices") or [{}])[0]
    msg = ch.get("message") or {}
    calls = [ToolCall((tc.get("function") or {}).get("name", ""),
                      _parse_args((tc.get("function") or {}).get("arguments", "")))
             for tc in msg.get("tool_calls") or []]
    return Decision(calls, msg.get("content") or "", ch.get("finish_reason"))


# -------------------------------------------------------------------- usage

@dataclass
class Usage:
    input_uncached: int = 0
    input_cache_read: int = 0
    input_cache_write: int = 0
    output: int = 0

    def __add__(self, o: "Usage") -> "Usage":
        return Usage(self.input_uncached + o.input_uncached, self.input_cache_read + o.input_cache_read,
                     self.input_cache_write + o.input_cache_write, self.output + o.output)


def extract_usage(fmt: str, response: dict) -> Usage:
    u = response.get("usage") or {}
    if fmt == ANTHROPIC:
        # input_tokens excludes cache reads/writes (Anthropic and DeepSeek agree)
        return Usage(u.get("input_tokens") or 0, u.get("cache_read_input_tokens") or 0,
                     u.get("cache_creation_input_tokens") or 0, u.get("output_tokens") or 0)
    prompt = u.get("prompt_tokens") or 0
    if "prompt_cache_hit_tokens" in u:  # DeepSeek
        hit = u.get("prompt_cache_hit_tokens") or 0
    else:
        hit = (u.get("prompt_tokens_details") or {}).get("cached_tokens") or 0
    return Usage(prompt - hit, hit, 0, u.get("completion_tokens") or 0)


def response_model(response: dict) -> str | None:
    return response.get("model")
