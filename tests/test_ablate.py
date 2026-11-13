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
