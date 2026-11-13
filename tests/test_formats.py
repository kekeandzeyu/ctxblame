import json
from datetime import datetime, timezone

import pytest

from ctxblame.formats import (ANTHROPIC, OPENAI, Usage, detect_format, extract_decision,
                              extract_usage)
from ctxblame.pricing import BudgetExceeded, Ledger, cost, deepseek_multiplier, resolve_model
from ctxblame.sse import assemble_openai_chunks, parse_sse


def chunk(delta=None, finish=None, usage=None):
    c = {"id": "c1", "object": "chat.completion.chunk", "model": "deepseek-flash",
         "choices": [{"index": 0, "delta": delta or {}, "finish_reason": finish}]}
    if usage is not None:
        c["usage"] = usage
    return f"data: {json.dumps(c)}\n\n"


OPENAI_STREAM = "".join([
    chunk({"role": "assistant", "reasoning_content": "user wants "}),
    chunk({"reasoning_content": "a listing"}),
    chunk({"tool_calls": [{"index": 0, "id": "call_1", "type": "function",
                           "function": {"name": "Bash", "arguments": ""}}]}),
    chunk({"tool_calls": [{"index": 0, "function": {"arguments": '{"comm'}}]}),
    chunk({"tool_calls": [{"index": 0, "function": {"arguments": 'and": "ls  -la "}'}}]}),
    chunk({}, finish="tool_calls", usage={"prompt_tokens": 100, "completion_tokens": 20,
                                         "prompt_cache_hit_tokens": 64, "prompt_cache_miss_tokens": 36}),
    "data: [DONE]\n\n",
])


def test_detect_format():
    assert detect_format("/v1/messages") == ANTHROPIC
    assert detect_format("/anthropic/v1/messages?beta=true") == ANTHROPIC
    assert detect_format("/chat/completions") == OPENAI
    assert detect_format("/v1/chat/completions") == OPENAI
    assert detect_format("/v1/messages/count_tokens") is None


def test_openai_stream_assembly_and_decision():
    resp = assemble_openai_chunks(parse_sse(OPENAI_STREAM))
    assert resp["_stream_complete"]
    msg = resp["choices"][0]["message"]
    assert msg["reasoning_content"] == "user wants a listing"
    assert msg["tool_calls"][0]["function"] == {"name": "Bash", "arguments": '{"command": "ls  -la "}'}
    d = extract_decision(OPENAI, resp)
    assert d.stop == "tool_calls"
    # whitespace differences do not count as a different decision
    assert d.key() == 'Bash({"command": "ls -la"})'
    assert d.key(name_only=True) == "Bash"
    assert extract_usage(OPENAI, resp) == Usage(36, 64, 0, 20)


def test_anthropic_decision_key_args_and_text_only():
    resp = {"content": [{"type": "text", "text": "ok"},
                        {"type": "tool_use", "id": "t", "name": "Bash",
                         "input": {"command": "rm -rf build/", "description": "clean"}}],
            "stop_reason": "tool_use", "usage": {"input_tokens": 10, "output_tokens": 5,
                                                 "cache_read_input_tokens": 90}}
    d = extract_decision(ANTHROPIC, resp)
    assert d.key(["command"]) == 'Bash({"command": "rm -rf build"})'
    assert d.key() != d.key(["command"])
    assert extract_usage(ANTHROPIC, resp) == Usage(10, 90, 0, 5)
    text_only = extract_decision(ANTHROPIC, {"content": [{"type": "text", "text": "done"}]})
    assert text_only.key() == "<no tool call>"


def test_pricing_peak_and_mapping():
    mon_peak = datetime(2026, 11, 16, 2, tzinfo=timezone.utc)
    mon_off = datetime(2026, 11, 16, 12, tzinfo=timezone.utc)
    sat = datetime(2026, 11, 14, 2, tzinfo=timezone.utc)
    assert mon_peak.weekday() == 0 and sat.weekday() == 5
    assert (deepseek_multiplier(mon_peak), deepseek_multiplier(mon_off), deepseek_multiplier(sat)) == (1, .5, .5)
    u = Usage(1_000_000, 0, 0, 1_000_000)
    assert cost("deepseek-flash", u, mon_peak) == pytest.approx(1.50)
    assert cost("deepseek-flash", u, mon_off) == pytest.approx(0.75)
    assert cost("deepseek-flash", u, mon_off, assume_peak=True) == pytest.approx(1.50)
    assert resolve_model("claude-opus-5-5", "https://api.deepseek.com/anthropic") == "deepseek-v4-pro"
    assert resolve_model("claude-opus-5-5", "https://api.anthropic.com") == "claude-opus-5-5"
    with pytest.raises(KeyError):
        resolve_model("mystery-model")


def test_ledger_persists_and_enforces_budget(tmp_path):
    p = tmp_path / "spend.jsonl"
    led = Ledger(p, budget=0.10)
    led.add("r", "deepseek-flash", Usage(), 0.06)
    led.check(0.03)
    with pytest.raises(BudgetExceeded):
        led.check(0.05)
    assert Ledger(p, budget=0.10).total == pytest.approx(0.06)  # survives restarts
