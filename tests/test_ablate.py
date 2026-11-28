import copy
import random

import pytest

from ctxblame.ablate import (AblationError, list_units, remove_random_span, remove_text,
                             remove_units, validate)
from ctxblame.formats import ANTHROPIC, OPENAI

PLANT = "Always run make clean before building."


def anth_body():
    return {"model": "m", "max_tokens": 100,
            "system": f"You are a coding agent. {PLANT} Be concise.",
            "tools": [{"name": "Bash", "input_schema": {"type": "object"}},
                      {"name": "Read", "input_schema": {"type": "object"}}],
            "messages": [
                {"role": "user", "content": "The build fails. Fix it."},
                {"role": "assistant", "content": [
                    {"type": "text", "text": "Let me look."},
                    {"type": "tool_use", "id": "A", "name": "Bash", "input": {"command": "ls"}}]},
                {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "A", "content": "Makefile\nsrc"}]},
                {"role": "assistant", "content": [
                    {"type": "tool_use", "id": "B", "name": "Read", "input": {"path": "Makefile"}},
                    {"type": "tool_use", "id": "C", "name": "Bash", "input": {"command": "git log -1"}}]},
                {"role": "user", "content": [
                    {"type": "tool_result", "tool_use_id": "B", "content": "all:\n\tcc main.c"},
                    {"type": "tool_result", "tool_use_id": "C", "content": "commit abc fix linker"},
                    {"type": "text", "text": "Hurry please."}]},
            ]}


def oai_body():
    return {"model": "m", "messages": [
        {"role": "system", "content": f"You are a coding agent. {PLANT} Be concise."},
        {"role": "user", "content": "The build fails. Fix it."},
        {"role": "assistant", "content": "Let me look.", "tool_calls": [
            {"id": "A", "type": "function", "function": {"name": "Bash", "arguments": '{"command":"ls"}'}}]},
        {"role": "tool", "tool_call_id": "A", "content": "Makefile\nsrc"},
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": "B", "type": "function", "function": {"name": "Read", "arguments": '{"path":"Makefile"}'}},
            {"id": "C", "type": "function", "function": {"name": "Bash", "arguments": '{"command":"git log -1"}'}}]},
        {"role": "tool", "tool_call_id": "B", "content": "all:\n\tcc main.c"},
        {"role": "tool", "tool_call_id": "C", "content": "commit abc fix linker"},
        {"role": "user", "content": "Hurry please."},
    ], "tools": [{"type": "function", "function": {"name": "Bash"}},
                 {"type": "function", "function": {"name": "Read"}}]}


def ids_in(body):
    out = []
    for m in body["messages"]:
        if isinstance(m.get("content"), list):
            out += [b.get("id") or b.get("tool_use_id") for b in m["content"] if b["type"] != "text"]
        out += [c["id"] for c in m.get("tool_calls") or []]
        if m.get("role") == "tool":
            out.append(m["tool_call_id"])
    return out


@pytest.mark.parametrize("fmt,body", [(ANTHROPIC, anth_body), (OPENAI, oai_body)])
def test_fixtures_are_valid_and_listed(fmt, body):
    b = body()
    assert validate(fmt, b) == []
    ids = [u.id for u in list_units(fmt, b)]
    assert {"pair:A", "pair:B", "pair:C", "tool:Bash"} <= set(ids)
    pair_b = next(u for u in list_units(fmt, b) if u.id == "pair:B")
    assert pair_b.chars == len("all:\n\tcc main.c")


def test_remove_pair_anthropic_keeps_text_and_merges():
    b = remove_units(ANTHROPIC, anth_body(), ["pair:A"])
    assert sorted(ids_in(b)) == ["B", "B", "C", "C"]
    roles = [m["role"] for m in b["messages"]]
    assert roles == ["user", "assistant", "user"]  # "Let me look." merged into the next assistant turn
    assert b["messages"][1]["content"][0] == {"type": "text", "text": "Let me look."}
    assert validate(ANTHROPIC, b) == []


def test_remove_one_of_parallel_calls():
    for fmt, body in ((ANTHROPIC, anth_body), (OPENAI, oai_body)):
        b = remove_units(fmt, body(), ["pair:C"])
        assert sorted(ids_in(b)) == ["A", "A", "B", "B"], fmt
        assert validate(fmt, b) == []


def test_removing_a_message_removes_its_partners():
    # assistant turn with calls B, C -> their results go too; user text survives
    b = remove_units(ANTHROPIC, anth_body(), ["msg[3]"])
    assert sorted(ids_in(b)) == ["A", "A"]
    assert b["messages"][-1]["role"] == "user"
    assert [x["type"] for x in b["messages"][-1]["content"]] == ["tool_result", "text"]
    # results message -> its calls go too, empty assistant turn dropped
    b = remove_units(ANTHROPIC, anth_body(), ["msg[4]"])
    assert sorted(ids_in(b)) == ["A", "A"] and b["messages"][-1]["role"] == "user"
    # OpenAI: removing one tool message removes only that call
    b = remove_units(OPENAI, oai_body(), ["msg[5]"])
    assert sorted(ids_in(b)) == ["A", "A", "C", "C"]
    assert validate(OPENAI, b) == []


def test_remove_system_and_tool_and_errors():
    b = remove_units(ANTHROPIC, anth_body(), ["system", "tool:Read"])
    assert "system" not in b and [t["name"] for t in b["tools"]] == ["Bash"]
    with pytest.raises(AblationError):
        remove_units(ANTHROPIC, anth_body(), ["pair:nope"])
    with pytest.raises(AblationError):
        remove_units(ANTHROPIC, anth_body(), ["msg[99]"])
    with pytest.raises(AblationError):
        remove_units(OPENAI, oai_body(), ["system"])  # OpenAI system is a message
    with pytest.raises(AblationError):  # removing the only user turn leaves an invalid request
        remove_units(ANTHROPIC, anth_body(), ["msg[0]"])


@pytest.mark.parametrize("fmt,body", [(ANTHROPIC, anth_body), (OPENAI, oai_body)])
def test_remove_text_tidies_seam(fmt, body):
    b = remove_text(fmt, body(), PLANT)
    sysmsg = b["system"] if fmt == ANTHROPIC else b["messages"][0]["content"]
    assert sysmsg == "You are a coding agent. Be concise."
    b = remove_text(fmt, body(), "commit abc fix linker")  # inside a tool result
    assert "linker" not in str(b)
    with pytest.raises(AblationError):
        remove_text(fmt, body(), "not in there")


def test_remove_text_drops_emptied_line():
    body = {"messages": [{"role": "user", "content": "line one\nPLANTED LINE\nline three"}]}
    assert remove_text(OPENAI, body, "PLANTED LINE")["messages"][0]["content"] == "line one\nline three"


@pytest.mark.parametrize("fmt,body", [(ANTHROPIC, anth_body), (OPENAI, oai_body)])
def test_random_span_respects_protect_and_size(fmt, body):
    seen = set()
    for seed in range(20):
        b, removed = remove_random_span(fmt, body(), len(PLANT), random.Random(seed),
                                        protect=[PLANT, "The build fails. Fix it."])
        assert PLANT in str(b) and "The build fails. Fix it." in str(b)
        assert removed.strip() and len(removed.strip()) <= len(PLANT) * 1.5
        assert validate(fmt, b) == []
        seen.add(removed)
    assert len(seen) > 1  # actually random
    b1, r1 = remove_random_span(fmt, body(), 20, random.Random(7))
    b2, r2 = remove_random_span(fmt, body(), 20, random.Random(7))
    assert (b1, r1) == (b2, r2)  # deterministic per seed


def _with_thinking(fmt):
    b = anth_body() if fmt == ANTHROPIC else oai_body()
    if fmt == ANTHROPIC:
        b["messages"][1]["content"].insert(0, {"type": "thinking", "thinking": "AGENTS.md says ls first.",
                                               "signature": "sig"})
        b["messages"][3]["content"].insert(0, {"type": "thinking", "thinking": "Read it.", "signature": "s2"})
    else:
        b["messages"][2]["reasoning_content"] = "AGENTS.md says ls first."
        b["messages"][4]["reasoning_content"] = "Read it."
    return b


@pytest.mark.parametrize("fmt", [ANTHROPIC, OPENAI])
def test_thinking_units_remove_reasoning_only(fmt):
    b = _with_thinking(fmt)
    i = 1 if fmt == ANTHROPIC else 2
    ids = {u.id for u in list_units(fmt, b)}
    assert {"thinking", f"thinking:msg[{i}]"} <= ids
    out = remove_units(fmt, b, [f"thinking:msg[{i}]"])
    assert "AGENTS.md says" not in str(out) and "Read it." in str(out)
    assert len(out["messages"]) == len(b["messages"])  # tool calls stay
    out = remove_units(fmt, b, ["thinking"])
    assert "AGENTS.md says" not in str(out) and "Read it." not in str(out)
    assert validate(fmt, out) == []
    with pytest.raises(AblationError):
        remove_units(fmt, b, ["thinking:msg[0]"])


@pytest.mark.parametrize("fmt", [ANTHROPIC, OPENAI])
def test_tool_descriptions_are_removable_text(fmt):
    b = anth_body() if fmt == ANTHROPIC else oai_body()
    tool = {"name": "Bash", "description": "Run a command, e.g. `make test`.", "input_schema": {}}
    b["tools"] = [tool if fmt == ANTHROPIC else {"type": "function", "function": {
        "name": "Bash", "description": tool["description"], "parameters": {}}}]
    out = remove_text(fmt, b, " e.g. `make test`.")
    assert "make test" not in str(out["tools"])
    assert next(u for u in list_units(fmt, b) if u.id == "tool:Bash").chars > 0


def test_parameter_descriptions_are_removable_text():
    b = anth_body()
    b["tools"][0]["input_schema"] = {"type": "object", "properties": {
        "command": {"type": "string", "description": "the command, e.g. `make test`"}}}
    out = remove_text(ANTHROPIC, b, ", e.g. `make test`")
    assert out["tools"][0]["input_schema"]["properties"]["command"]["description"] == "the command"


@pytest.mark.parametrize("fmt", [ANTHROPIC, OPENAI])
def test_removing_thinking_gives_its_calls_fresh_ids(fmt):
    b = _with_thinking(fmt)
    i = 1 if fmt == ANTHROPIC else 2  # the message whose calls are id "A"
    out = remove_units(fmt, b, [f"thinking:msg[{i}]"])
    s = str(out)
    assert "'A'" not in s and "ctxb0000" in s  # call and result both renamed
    assert "'B'" in s  # calls of messages that keep their reasoning keep their ids
    assert validate(fmt, out) == []


# ------------------------------------------------------------- prompt caching

EPH = {"type": "ephemeral"}


def _cached_body():
    """Claude Code-like: breakpoints on the last system block, the first user turn and the last turn."""
    b = anth_body()
    b["system"] = [{"type": "text", "text": "You are a coding agent."},
                   {"type": "text", "text": f"{PLANT} Be concise.", "cache_control": dict(EPH)}]
    b["messages"][0]["content"] = [{"type": "text", "text": "The build fails. Fix it.", "cache_control": dict(EPH)}]
    b["messages"][-1]["content"][-1]["cache_control"] = dict(EPH)
    return b


def _marks(body):
    from ctxblame.ablate import _blocks
    return [p for p, blk in _blocks(body) if isinstance(blk, dict) and "cache_control" in blk]


def test_cache_breakpoint_pinned_at_frozen_prefix_and_stale_ones_stripped():
    from ctxblame.ablate import pin_cache_breakpoints
    b = _cached_body()
    out = pin_cache_breakpoints(b, remove_units(ANTHROPIC, b, ["pair:B"]))
    # msg[0..2] are unchanged; the change starts in msg[3]: pin on msg[2]'s last block, drop the tail mark
    assert _marks(out) == [("system", 1), ("messages", 0, "content", 0), ("messages", 2, "content", 0)]
    assert validate(ANTHROPIC, out) == []
    # a change in the second system block: the prefix ends with the first one
    assert _marks(pin_cache_breakpoints(b, remove_text(ANTHROPIC, b, PLANT))) == [("system", 0)]
    # a change in the first system block: the frozen prefix ends at the last tool
    assert _marks(pin_cache_breakpoints(b, remove_units(ANTHROPIC, b, ["system[0]"]))) == [("tools", 1)]


def test_cache_breakpoints_untouched_without_caching_and_limited_to_four():
    from ctxblame.ablate import pin_cache_breakpoints
    plain = anth_body()
    abl = remove_units(ANTHROPIC, plain, ["pair:B"])
    assert pin_cache_breakpoints(plain, abl) == abl  # recorded without caching: replay as recorded
    b = _cached_body()
    b["tools"][0]["cache_control"] = dict(EPH)
    b["messages"][1]["content"][0]["cache_control"] = {"type": "ephemeral", "ttl": "1h"}
    out = pin_cache_breakpoints(b, remove_units(ANTHROPIC, b, ["pair:B"]))
    assert len(_marks(out)) == 4 and ("tools", 0) not in _marks(out)  # the earliest one goes
    assert out["messages"][2]["content"][0]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}


def test_cache_breakpoint_on_string_content_and_never_on_thinking():
    from ctxblame.ablate import pin_cache_breakpoints
    b = _cached_body()
    b["messages"][0]["content"] = "The build fails. Fix it."
    b["messages"][1]["content"].insert(0, {"type": "thinking", "thinking": "hm", "signature": "s"})
    out = pin_cache_breakpoints(b, remove_units(ANTHROPIC, b, ["msg[1]"]))
    # msg[1] is gone (its pair too), so the prefix ends with msg[0]: a string, now one marked text block
    assert out["messages"][0]["content"] == [{"type": "text", "text": "The build fails. Fix it.",
                                              "cache_control": EPH}]
    # the last unchanged block is reasoning, which cannot carry a mark: pin the block before it
    b2 = _cached_body()
    b2["messages"][1]["content"] = [{"type": "thinking", "thinking": "hm", "signature": "s"},
                                    b2["messages"][1]["content"][1]]
    abl = copy.deepcopy(b2)
    abl["messages"][1]["content"][1]["input"] = {"command": "ls -la"}
    out = pin_cache_breakpoints(b2, abl)
    assert _marks(out) == [("system", 1), ("messages", 0, "content", 0)]
