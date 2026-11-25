import asyncio
import random

import pytest

from ctxblame.ablate import validate
from ctxblame.blame import (Cause, Outcome, apply_chunks, chunk_request, ddmin, decide, decide_conditional,
                            pick_controls, resolve_given, search)
from ctxblame.formats import ANTHROPIC, OPENAI, Decision, ToolCall
from ctxblame.match import Matcher
from ctxblame.replay import Sample

from test_ablate import PLANT, anth_body, oai_body


def _thinking_anth():
    b = anth_body()
    b["system"] = [{"type": "text", "text": "You are a coding agent.\n\n## Rules\n- " + PLANT +
                    "\n- Be concise.\n\nEnd."}]
    b["messages"][1]["content"].insert(0, {"type": "thinking", "thinking": "hm", "signature": "s"})
    b["tools"][0]["description"] = "Run a shell command."
    return b


@pytest.mark.parametrize("fmt,body", [(ANTHROPIC, _thinking_anth()), (OPENAI, oai_body())])
def test_chunks_cover_context_but_not_the_task(fmt, body):
    chunks = chunk_request(fmt, body)
    ids = [c.id for c in chunks]
    task = "Hurry please."  # the latest user text is the task
    assert not any(task in c.text for c in chunks)
    assert any(c.kind == "tool call" for c in chunks) and any(c.kind == "system" for c in chunks)
    assert len(ids) == len(set(ids))
    # every chunk, every child, and all of them at once give a valid request
    every = [c for c in chunks] + [k for c in chunks for k in c.children]
    for c in every:
        assert validate(fmt, apply_chunks(fmt, body, [c])) == []
    out = apply_chunks(fmt, body, chunks)
    assert validate(fmt, out) == [] and task in str(out)
    assert PLANT not in str(out)


def test_system_paragraph_and_lines():
    b = _thinking_anth()
    chunks = chunk_request(ANTHROPIC, b)
    rules = next(c for c in chunks if c.kind == "system" and PLANT in c.text)
    assert rules.text.startswith("## Rules") and len(rules.children) == 3
    line = next(k for k in rules.children if PLANT in k.text)
    out = apply_chunks(ANTHROPIC, b, [line])
    assert PLANT not in str(out) and "Be concise." in out["system"][0]["text"]
    assert any(c.kind == "thinking" for c in chunks) and any(c.kind == "tool desc" for c in chunks)


def test_protect_and_pair_lines():
    b = anth_body()
    chunks = chunk_request(ANTHROPIC, b, protect=["Hurry"])
    assert not any("Hurry" in c.text for c in chunks)
    pair = next(c for c in chunks if c.id == "pair:A")
    assert [k.text for k in pair.children] == ["Makefile", "src"]
    out = apply_chunks(ANTHROPIC, b, [pair.children[0]])
    assert "Makefile\\n" not in str(out) and "'src'" in str(out) and validate(ANTHROPIC, out) == []


def test_decide():
    assert decide(0, 5, 0.5, 15) == "flipped"
    assert decide(0, 5, 0.5, 15, min_flip_n=10) == "more"
    assert decide(5, 5, 0.5, 15) == "kept"
    assert decide(3, 5, 0.5, 15) == "more"
    assert decide(0, 15, 0.5, 15) == "flipped"
    assert decide(5, 15, 0.4, 15) == "unclear"  # out of replays: not a flip


def fake(rule):
    """A test whose outcome is decided by rule(removed ids)."""
    calls = []

    async def test(removed, extra=(), fresh=False):
        removed = frozenset(removed) | frozenset(c.id for c in extra)
        calls.append(removed)
        return Outcome(0, 5, "flipped") if rule(removed) else Outcome(5, 5, "kept")
    test.calls = calls
    return test


class C:
    def __init__(self, i, children=()):
        self.id, self.text, self.children, self.kind, self.units = i, i * 10, list(children), "x", ()
        self.spans = ((("f",), 0, 1),)

    @property
    def chars(self):
        return len(self.text)


def run(rule, chunks, **kw):
    kw.setdefault("control_pool", [C(f"l{i}") for i in range(40)])  # neutral lines for controls
    return asyncio.run(search(chunks, fake(rule), **kw))


def test_search_single_cause():
    chunks = [C(f"c{i}") for i in range(12)]
    every, causes = run(lambda r: "c7" in r, chunks, n_controls=0)
    assert every.flipped and [c.members for c in causes] == [["c7"]]


def test_search_redundant_carriers():
    chunks = [C(f"c{i}") for i in range(12)]
    every, causes = run(lambda r: {"c2", "c9"} <= r, chunks, n_controls=0)
    assert [sorted(c.members) for c in causes] == [["c2", "c9"]]
    assert {k: v.flipped for k, v in causes[0].alone.items()} == {"c2": False, "c9": False}


def test_search_two_independent_causes():
    chunks = [C(f"c{i}") for i in range(10)]
    _, causes = run(lambda r: "c1" in r or "c8" in r, chunks, n_controls=0)
    assert sorted(m for c in causes for m in c.members) == ["c1", "c8"] and len(causes) == 2


def test_search_not_in_context():
    every, causes = run(lambda r: False, [C(f"c{i}") for i in range(5)], n_controls=0)
    assert not every.flipped and causes == []


def test_refine_to_line_with_other_carrier_held_removed():
    kids = [C(f"p.{i}") for i in range(1, 6)]
    chunks = [C("p", kids), C("q"), C("r")]
    # carriers: line p.3 and chunk q; flips only when both are gone
    rule = lambda r: ("p" in r or "p.3" in r) and "q" in r  # noqa: E731
    _, causes = run(rule, chunks, n_controls=0)
    assert sorted(causes[0].members) == ["p.3", "q"]


def test_pick_controls_avoids_cause_and_matches_size():
    pool = [C(f"l{i}") for i in range(20)]
    ctl = pick_controls(pool, 30, {"l3"}, 2, random.Random(0))
    assert len(ctl) == 2 and all("l3" not in [c.id for c in run_] for run_ in ctl)
    assert all(15 <= sum(c.chars for c in run_) <= 48 for run_ in ctl)


def test_ddmin_minimal():
    items = [f"x{i}" for i in range(16)]
    t = fake(lambda r: {"x3", "x4", "x11"} <= r)
    assert sorted(asyncio.run(ddmin(items, t))) == ["x11", "x3", "x4"]


def test_task_is_the_latest_user_text():
    b = {"model": "m", "max_tokens": 10, "messages": [
        {"role": "user", "content": "Context: we use pnpm."},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "Add lodash."}]}
    texts = [c.text for c in chunk_request(ANTHROPIC, b)]
    assert "Context: we use pnpm." in texts and "Add lodash." not in texts


def test_further_cause_must_be_specific():
    chunks = [C(f"c{i}") for i in range(10)]
    pool = [C(f"l{i}") for i in range(40)]
    # c4 is a cause; removing the other nine together flips too, but so does any random removal
    rule = lambda r: "c4" in r or len(r & {f"c{i}" for i in range(10)}) >= 9 or any(x.startswith("l") for x in r)  # noqa: E731
    notes = []
    _, causes = asyncio.run(search(chunks, fake(rule), n_controls=0, control_pool=pool, notes=notes))
    assert [c.members for c in causes] == [["c4"]]
    assert notes and "only in bulk" in notes[0]


def test_decide_conditional():
    # precondition collapse: E drops to 0/10
    assert decide_conditional(0, 0, 5, 0.5, 0.5, 15, min_flip_n=10) == ("more", "more")
    assert decide_conditional(0, 0, 10, 0.5, 0.5, 15, min_flip_n=10) == ("collapsed", "collapsed")
    # E intact, choice kept
    assert decide_conditional(5, 5, 5, 0.5, 0.5, 15, min_flip_n=10) == ("kept", "intact")
    # E intact, choice flipped
    assert decide_conditional(0, 10, 10, 0.5, 0.5, 15, min_flip_n=10) == ("flipped", "intact")
    # E mostly intact (9/10) with 0/9 target asks for one more batch before calling flip, then flips at cap
    assert decide_conditional(0, 9, 10, 0.5, 0.5, 15, min_flip_n=10) == ("more", "intact")
    assert decide_conditional(0, 13, 15, 0.5, 0.5, 15, min_flip_n=10) == ("flipped", "intact")
    # E borderline below threshold at cap -> unclear (neither collapsed nor flipped)
    assert decide_conditional(0, 5, 15, 0.5, 0.5, 15, min_flip_n=10) == ("unclear", "unclear")


def test_resolve_given_auto_and_explicit():
    py_call = ToolCall("bash", {"command": "python -m pytest -q"})
    py_dec = Decision([py_call])
    py_m = Matcher("args", [r"command~^python -m pytest"], any_call=True)
    gm, gt = resolve_given(None, [r"command~^python -m pytest"], py_m.key(py_dec), py_m, [], py_dec)
    assert gm is not None and gm.mode == "intent" and gt == "run pytest"

    pnpm_call = ToolCall("Bash", {"command": "pnpm add lodash"})
    pnpm_dec = Decision([pnpm_call])
    pnpm_m = Matcher("args", [r"command~\bpnpm\b"], any_call=True)
    gm2, gt2 = resolve_given(None, [r"command~\bpnpm\b"], pnpm_m.key(pnpm_dec), pnpm_m, [], pnpm_dec)
    assert gm2 is not None and gm2.mode == "name" and gt2 == "Bash"

    # no --key-arg and no --given -> unconditional
    assert resolve_given(None, [], "read docs/A.md", Matcher("intent"), [], py_dec) == (None, None)
    # explicit --given none disables auto conditioning
    assert resolve_given("none", [r"command~^python -m pytest"], py_m.key(py_dec), py_m, [], py_dec) == (None, None)
    # explicit specs
    gm3, gt3 = resolve_given("run pytest", [], py_m.key(py_dec), py_m, [], py_dec)
    assert gm3.mode == "intent" and gt3 == "run pytest"
    gm4, gt4 = resolve_given(r"command~\bpytest\b", [], py_m.key(py_dec), py_m, [], py_dec)
    assert gm4.mode == "args" and gt4 == 'bash({"command~\\\\bpytest\\\\b": true})'


def fake_cond(collapse_rule, flip_rule):
    """Conditional test oracle: collapse_rule -> collapsed, else flip_rule -> flipped, else kept."""
    async def test(removed, extra=(), fresh=False):
        removed = frozenset(removed) | frozenset(c.id for c in extra)
        if collapse_rule(removed):
            return Outcome(0, 0, "collapsed", k_given=0, n_total=10, given_verdict="collapsed")
        if flip_rule(removed):
            return Outcome(0, 10, "flipped", k_given=10, n_total=10, given_verdict="intact")
        return Outcome(5, 5, "kept", k_given=5, n_total=5, given_verdict="intact")
    return test


def test_search_isolates_precondition_and_finds_redundant_choice_carriers():
    chunks = [C(x) for x in ("tool_bash", "sys_rule", "c1", "hist_pytest", "c2", "edit_file", "c3")]
    pool = [C(f"l{i}") for i in range(40)]
    t = fake_cond(
        collapse_rule=lambda r: "edit_file" in r,
        flip_rule=lambda r: {"tool_bash", "sys_rule", "hist_pytest"} <= r,
    )
    preconds: list[Cause] = []
    every, causes = asyncio.run(search(chunks, t, n_controls=2, control_pool=pool, preconditions=preconds))
    assert every.flipped
    assert [p.members for p in preconds] == [["edit_file"]]
    assert preconds[0].specific is True
    assert [sorted(c.members) for c in causes] == [["hist_pytest", "sys_rule", "tool_bash"]]
    assert causes[0].specific is True


def test_search_refines_precondition_line_without_hiding_sibling_choice_line():
    kids = [C("sys.1"), C("sys.2"), C("sys.3")]
    chunks = [C("sys", kids), C("other")]
    # sys.1 is a precondition; sys.2 is a choice carrier in the same paragraph
    t = fake_cond(
        collapse_rule=lambda r: "sys" in r or "sys.1" in r,
        flip_rule=lambda r: "sys" in r or "sys.2" in r,
    )
    preconds: list[Cause] = []
    _, causes = asyncio.run(search(chunks, t, n_controls=0, preconditions=preconds))
    assert [p.members for p in preconds] == [["sys.1"]]
    assert [c.members for c in causes] == [["sys.2"]]


def test_search_precondition_only_reports_precondition_and_no_causes():
    chunks = [C("c0"), C("freeze_rule"), C("c2")]
    t = fake_cond(collapse_rule=lambda r: "freeze_rule" in r, flip_rule=lambda r: False)
    preconds: list[Cause] = []
    every, causes = asyncio.run(search(chunks, t, n_controls=0, preconditions=preconds))
    assert not every.flipped
    assert [p.members for p in preconds] == [["freeze_rule"]]
    assert causes == []
