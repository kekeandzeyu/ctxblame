import asyncio
import random

import pytest

from ctxblame.ablate import validate
from ctxblame.blame import (Cause, Chunk, Outcome, _prune_bundle, apply_chunks, chunk_request, ddmin,
                            decide, decide_conditional, partition_tiers, pick_controls, resolve_given, search)
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


TASK = "Fix the failing test in parser.py."
RULE = "Use tox -e py312 to run tests."
CLAUDE_MD = f"<system-reminder>\n# claudeMd\nContents of CLAUDE.md:\n\n{RULE}\nKeep diffs small.\n</system-reminder>"
TODO = "<system-reminder>\nThe TodoWrite tool hasn't been used recently.\n</system-reminder>"


def _claude_code_anth():
    """Claude Code's wire shape: CLAUDE.md injected into the task message, and a
    reminder appended to a later tool-result turn."""
    return {"model": "m", "max_tokens": 100, "system": "You are Claude Code.",
            "tools": [{"name": "Bash", "description": "Run a command.", "input_schema": {"type": "object"}}],
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": CLAUDE_MD}, {"type": "text", "text": TASK}]},
                {"role": "assistant", "content": [
                    {"type": "tool_use", "id": "A", "name": "Bash", "input": {"command": "ls"}}]},
                {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "A", "content": "parser.py"},
                                             {"type": "text", "text": TODO}]}]}


def _claude_code_oai(list_content: bool):
    first = CLAUDE_MD + "\n" + TASK
    return {"model": "m", "messages": [
        {"role": "system", "content": "You are an agent."},
        {"role": "user", "content": [{"type": "text", "text": first}] if list_content else first},
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": "A", "type": "function", "function": {"name": "Bash", "arguments": '{"command":"ls"}'}}]},
        {"role": "tool", "tool_call_id": "A", "content": "parser.py"},
        {"role": "user", "content": TODO}],
        "tools": [{"type": "function", "function": {"name": "Bash", "description": "Run a command."}}]}


@pytest.mark.parametrize("fmt,body", [(ANTHROPIC, _claude_code_anth()), (OPENAI, _claude_code_oai(False)),
                                      (OPENAI, _claude_code_oai(True))])
def test_injected_reminders_are_chunks_and_the_task_is_the_users_text(fmt, body):
    chunks = chunk_request(fmt, body)
    # the task is the user's text in messages[0], not the later reminder-only turn
    assert not any(TASK in c.text for c in chunks)
    inj = [c for c in chunks if c.kind == "injected"]
    assert len(inj) == 2 and inj[0].id.startswith("inj:msg[1]" if fmt == OPENAI else "inj:msg[0]")
    assert RULE in inj[0].text and "TodoWrite" in inj[1].text
    rule = next(k for k in inj[0].children if k.text == RULE)
    out = apply_chunks(fmt, body, [rule])
    assert RULE not in str(out) and "Keep diffs small." in str(out) and TASK in str(out)
    for c in chunks + [k for c in chunks for k in c.children]:
        assert validate(fmt, apply_chunks(fmt, body, [c])) == []
    out = apply_chunks(fmt, body, chunks)
    assert validate(fmt, out) == [] and TASK in str(out) and "system-reminder" not in str(out)


def test_users_own_text_around_reminders_in_an_earlier_turn_is_a_chunk():
    b = {"model": "m", "max_tokens": 10, "messages": [
        {"role": "user", "content": "Context: we use pnpm.\n" + TODO},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "Add lodash."}]}
    chunks = chunk_request(ANTHROPIC, b)
    assert {c.kind: c.text for c in chunks if c.kind in ("user", "injected")} == {
        "user": "Context: we use pnpm.", "injected": TODO.split("\n")[1]}
    out = apply_chunks(ANTHROPIC, b, [c for c in chunks if c.kind == "injected"])
    assert out["messages"][0]["content"].strip() == "Context: we use pnpm."


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


READS = [f"read.{i}" for i in range(1, 9)]  # scattered lines of files the agent read
CARRIERS = {"tool_bash", "sys_rule", "hist_pytest"}


@pytest.mark.parametrize("stabilize", [True, False])
def test_search_goes_on_when_preconditions_keep_appearing(stabilize):
    # like real/run4/step21: removing any one read line stops the agent testing,
    # so each precondition found reveals another; v0.2 stopped after three
    chunks = [C(x) for x in ("tool_bash", "sys_rule", *READS[:6], "hist_pytest", "c1")]
    t = fake_cond(collapse_rule=lambda r: bool(r & set(READS)), flip_rule=lambda r: CARRIERS <= r)
    preconds, stabs, notes = [], [], []
    _, causes = asyncio.run(search(chunks, t, n_controls=0, preconditions=preconds, stabilizers=stabs,
                                   notes=notes, stabilize=stabilize))
    assert len(preconds) == 3
    if stabilize:
        assert [sorted(s) for s in stabs] == [sorted(set(READS[:6]) - {m for p in preconds for m in p.members})]
        assert [sorted(c.members) for c in causes] == [sorted(CARRIERS)]
    else:
        assert stabs == [] and causes == [] and any("more than 3 preconditions" in n for n in notes)


def test_search_after_stabilizer_searches_the_whole_rest_for_the_choice():
    # like real/run4/step21 on the GPU (p5-real seed 0): with the stabilizer kept,
    # removing all the rest keeps E and flips the choice, but removing only the
    # tail tier stops E (a recent output without the history that explains it).
    # The suffix-tier probe then stopped the search before any choice test.
    chunks = [C(x) for x in ("tool_bash", "sys_rule", "hist_pytest", "r1", "r2", "x1", "x2", "c1")]
    t = fake_cond(collapse_rule=lambda r: bool(r & {"r1", "r2"}) or (bool(r & {"x1", "x2"})
                                                                      and "hist_pytest" not in r),
                  flip_rule=lambda r: CARRIERS <= r)
    preconds, stabs, notes = [], [], []
    _, causes = asyncio.run(search(chunks, t, n_controls=0, preconditions=preconds, stabilizers=stabs,
                                   notes=notes, max_preconditions=0))
    assert stabs == [["r1", "r2"]]
    assert [sorted(c.members) for c in causes] == [sorted(CARRIERS)]


def test_search_reports_triggers_and_steers_when_the_stabilizer_carries_the_choice():
    # real/run4/step21 seed 2 (p5c-real): the bash tool description both enables the
    # action (removing it stops E) and holds the --tb=line example that steers it
    chunks = [C(x) for x in ("tool_bash", "sys_rule", "hist_pytest", "c1")]
    t = fake_cond(collapse_rule=lambda r: "tool_bash" in r, flip_rule=lambda r: "tool_bash" in r)
    stabs, notes = [], []
    _, causes = asyncio.run(search(chunks, t, n_controls=0, stabilizers=stabs, notes=notes,
                                   max_preconditions=0))
    assert stabs == [["tool_bash"]] and causes == []
    assert any(n.startswith("triggers_and_steers suspected") for n in notes)


def test_search_keeps_a_minimal_stabilizer_of_a_diffuse_precondition():
    # the agent tests as long as it still sees any 3 of the 8 reads: the smallest
    # removal that stops it has 6 chunks (> max_members), and no one read matters
    chunks = [C(x) for x in ("tool_bash", "sys_rule", *READS, "hist_pytest")]
    t = fake_cond(collapse_rule=lambda r: len(r & set(READS)) >= 6, flip_rule=lambda r: CARRIERS <= r)
    preconds, stabs, notes = [], [], []
    _, causes = asyncio.run(search(chunks, t, n_controls=0, preconditions=preconds, stabilizers=stabs,
                                   notes=notes))
    assert preconds == [] and len(stabs) == 1 and len(stabs[0]) == 3 and set(stabs[0]) <= set(READS)
    assert [sorted(c.members) for c in causes] == [sorted(CARRIERS)]
    assert any(n.startswith("diffuse precondition") and "stabilizer" in n for n in notes)


def test_search_precondition_only_reports_precondition_and_no_causes():
    chunks = [C("c0"), C("freeze_rule"), C("c2")]
    t = fake_cond(collapse_rule=lambda r: "freeze_rule" in r, flip_rule=lambda r: False)
    preconds: list[Cause] = []
    every, causes = asyncio.run(search(chunks, t, n_controls=0, preconditions=preconds))
    assert not every.flipped
    assert [p.members for p in preconds] == [["freeze_rule"]]
    assert preconds[0].relation == "and_precondition"
    assert causes == []


def test_prune_bundle_drops_noisy_hitchhiker_and_proves_restoration():
    by_id = {x: Chunk(x, "system", x, x * 10, i * 100) for i, x in enumerate(["a", "hitch", "b"])}
    # True minimal OR-carriers are {"a", "b"}; "hitch" is irrelevant
    t = fake(lambda r: {"a", "b"} <= r)
    notes: list[str] = []
    members, restored = asyncio.run(_prune_bundle(["a", "hitch", "b"], by_id, t, lambda o: o.flipped, notes))
    assert members == ["a", "b"]
    assert set(restored) == {"a", "b"}
    assert all(o.verdict == "kept" for o in restored.values())
    assert any("hitch" in n for n in notes)


def test_search_prunes_hitchhiker_under_noisy_ddmin_and_sets_relations():
    chunks = [Chunk(x, "system", x, x * 10, i * 100) for i, x in enumerate(["a", "hitch", "b", "c"])]
    seen_ab = 0

    async def noisy_test(removed, extra=(), fresh=False):
        nonlocal seen_ab
        r = frozenset(removed) | frozenset(c.id for c in extra)
        # First time {"a", "b"} is tested alone (during ddmin), inject a noisy false keep
        # so ddmin keeps "hitch"; subsequent pruning check reveals "hitch" is non-essential.
        if r == frozenset({"a", "b"}) and seen_ab == 0:
            seen_ab += 1
            return Outcome(5, 5, "kept")
        return Outcome(0, 10, "flipped") if {"a", "b"} <= r else Outcome(5, 5, "kept")

    notes: list[str] = []
    _, causes = asyncio.run(search(chunks, noisy_test, n_controls=0, notes=notes))
    assert [sorted(c.members) for c in causes] == [["a", "b"]]
    assert causes[0].relation == "or_carriers"
    assert set(causes[0].restored) == {"a", "b"}
    assert all(o.verdict == "kept" for o in causes[0].restored.values())


def test_partition_tiers_orders_prefix_to_suffix():
    chunks = [
        Chunk("tooldesc:bash", "tool desc", "bash", "x" * 500, 0),
        Chunk("tooldesc:read", "tool desc", "read", "x" * 500, 500),
        Chunk("sys.p1", "system", "sys1", "x" * 500, 1000),
        Chunk("pair:1", "tool call", "p1", "x" * 500, 1500),
        Chunk("pair:2", "tool call", "p2", "x" * 500, 2000),
        Chunk("pair:3", "tool call", "p3", "x" * 500, 2500),
        Chunk("pair:4", "tool call", "p4", "x" * 500, 3000),
    ]
    by_id = {c.id: c for c in chunks}
    tiers = partition_tiers([c.id for c in chunks], by_id)
    assert tiers == [
        ["tooldesc:bash", "tooldesc:read"],
        ["sys.p1"],
        ["pair:1", "pair:2"],
        ["pair:3", "pair:4"],
    ]


def test_suffix_first_search_preserves_prefix_kv_cache_for_tail_cause():
    # 20 chunks totaling 20,000 chars: 4 tool descs (0..4k), 4 system (4k..8k),
    # 6 early history (8k..14k), 6 tail history (14k..20k).
    specs = (
        [(f"tooldesc:t{i}", "tool desc") for i in range(4)]
        + [(f"sys.p{i}", "system") for i in range(4)]
        + [(f"pair:e{i}", "tool call") for i in range(6)]
        + [(f"pair:tail{i}", "tool call") for i in range(6)]
    )
    chunks = [Chunk(cid, kind, cid, "x" * 1000, i * 1000) for i, (cid, kind) in enumerate(specs)]
    by_id = {c.id: c for c in chunks}
    total_chars = 20_000
    calls: list[frozenset] = []
    uncached_chars = 0
    cached_chars = 0

    async def metered_test(removed, extra=(), fresh=False):
        nonlocal uncached_chars, cached_chars
        r = frozenset(removed) | frozenset(c.id for c in extra)
        calls.append(r)
        # Earliest mutated byte offset determines how much KV prefix survives
        first_mut = min((by_id[cid].pos for cid in r), default=total_chars)
        cached_chars += first_mut
        uncached_chars += total_chars - first_mut
        return Outcome(0, 10, "flipped") if "pair:tail4" in r else Outcome(5, 5, "kept")

    _, causes = asyncio.run(search(chunks, metered_test, max_causes=1, n_controls=0))
    assert [c.members for c in causes] == [["pair:tail4"]]
    assert causes[0].relation == "and_cause"
    # Never mutated tool schemas or system prompt at all!
    prefix_ids = {f"tooldesc:t{i}" for i in range(4)} | {f"sys.p{i}" for i in range(4)}
    assert all(not (r & prefix_ids) for r in calls)
    hit_rate = cached_chars / (cached_chars + uncached_chars)
    assert hit_rate >= 0.75  # >75% KV prefix cache hit rate (>4x-5x uncached reduction)


def test_stratified_search_isolates_tail_precondition_without_prefix_misses_then_finds_cross_tier_bundle():
    specs = (
        [(f"tooldesc:t{i}", "tool desc") for i in range(4)]
        + [(f"sys.p{i}", "system") for i in range(4)]
        + [(f"pair:e{i}", "tool call") for i in range(4)]
        + [(f"pair:tail{i}", "tool call") for i in range(4)]
    )
    chunks = [Chunk(cid, kind, cid, "x" * 1000, i * 1000) for i, (cid, kind) in enumerate(specs)]
    calls: list[tuple[frozenset, str]] = []

    async def oracle(removed, extra=(), fresh=False):
        r = frozenset(removed) | frozenset(c.id for c in extra)
        if "pair:tail2" in r:
            out = Outcome(0, 0, "collapsed", k_given=0, n_total=10, given_verdict="collapsed")
        elif {"tooldesc:t1", "sys.p2", "pair:e1"} <= r:
            out = Outcome(0, 10, "flipped", k_given=10, n_total=10, given_verdict="intact")
        else:
            out = Outcome(5, 5, "kept", k_given=5, n_total=5, given_verdict="intact")
        calls.append((r, out.verdict))
        return out

    preconds: list[Cause] = []
    _, causes = asyncio.run(search(chunks, oracle, max_causes=1, n_controls=0, preconditions=preconds))
    assert [p.members for p in preconds] == [["pair:tail2"]]
    assert preconds[0].relation == "and_precondition"
    assert [sorted(c.members) for c in causes] == [["pair:e1", "sys.p2", "tooldesc:t1"]]
    assert causes[0].relation == "or_carriers"
    assert set(causes[0].restored) == {"pair:e1", "sys.p2", "tooldesc:t1"}
    # Every call that hit collapsed (precondition isolation) stayed strictly inside tail history
    prefix_ids = {cid for cid, kind in specs if kind in ("tool desc", "system")}
    collapsed_calls = [r for r, v in calls if v == "collapsed"]
    assert collapsed_calls and all(not (r & prefix_ids) for r in collapsed_calls)


def test_ddmin_complements_keep_prefix_intact_first():
    items = ["p0", "p1", "p2", "p3"]
    order: list[frozenset] = []

    async def t(removed):
        r = frozenset(removed)
        order.append(r)
        # Flips whenever any 3 items are removed (forces complement tests at n=4)
        return Outcome(0, 10, "flipped") if len(r) >= 3 else Outcome(5, 5, "kept")

    asyncio.run(ddmin(items, t))
    # First 3-item complement tried should omit "p0" (keeping earliest prefix "p0" intact!)
    three_item_tests = [r for r in order if len(r) == 3]
    assert three_item_tests[0] == frozenset({"p1", "p2", "p3"})


def test_search_finds_choice_line_inside_a_precondition_chunk():
    # The runbook result is needed to act at all (removing it stops the action),
    # but its line 2 alone decides the flag: report the pair as a precondition and
    # the line as the cause.
    kids = [C("pair:rb.1"), C("pair:rb.2"), C("pair:rb.3")]
    chunks = [C("sys"), C("pair:early"), C("pair:rb", kids)]
    chunks[2].units = ("pair:rb",)  # a tool pair: removing its lines keeps the call
    t = fake_cond(
        collapse_rule=lambda r: "pair:rb" in r or {"pair:rb.1", "pair:rb.2", "pair:rb.3"} <= r,
        flip_rule=lambda r: "pair:rb.2" in r,
    )
    preconds: list[Cause] = []
    _, causes = asyncio.run(search(chunks, t, n_controls=0, preconditions=preconds))
    assert [p.members for p in preconds] == [["pair:rb.1", "pair:rb.2", "pair:rb.3"]]
    assert [c.members for c in causes] == [["pair:rb.2"]]

    # same, but the call itself is the precondition (its lines cannot be split off)
    t2 = fake_cond(collapse_rule=lambda r: "pair:rb" in r, flip_rule=lambda r: "pair:rb.2" in r)
    preconds2: list[Cause] = []
    _, causes2 = asyncio.run(search(chunks, t2, n_controls=0, preconditions=preconds2))
    assert [p.members for p in preconds2] == [["pair:rb"]]
    assert [c.members for c in causes2] == [["pair:rb.2"]]


def test_search_non_monotonic_falls_back_to_tier_windows():
    # Removing everything falls back on the model's habit (kept), but removing the
    # two prefix carriers while the history stays flips the decision.
    chunks = [Chunk("tooldesc:bash", "tool desc", "bash", "x" * 100, 0),
              Chunk("sys.p1", "system", "s1", "x" * 100, 100),
              Chunk("sys.p2", "system", "s2", "x" * 100, 200),
              Chunk("pair:ls", "tool call", "ls", "x" * 100, 300)]
    t = fake(lambda r: {"tooldesc:bash", "sys.p2"} <= r and "pair:ls" not in r)
    notes: list[str] = []
    _, causes = asyncio.run(search(chunks, t, n_controls=0, notes=notes))
    assert [sorted(c.members) for c in causes] == [["sys.p2", "tooldesc:bash"]]
    assert any("non-monotonic" in n for n in notes)


def test_member_controls_drop_neutral_bundle_member():
    """A noisy model: the decision survives removing both carriers A and B as long
    as *some* neutral context (H, or the neutral line X) is left. H then passes the
    leave-one-in check like a carrier; member controls (remove X too) expose it."""
    chunks = [C("A"), C("H"), C("B")] + [C(f"c{i}") for i in range(4)]
    rule = lambda r: {"A", "B"} <= r and ("H" in r or "X" in r)  # noqa: E731
    pool = [C("X")]
    _, plain = run(rule, chunks, n_controls=0, control_pool=pool)
    assert [sorted(c.members) for c in plain] == [["A", "B", "H"]]
    notes: list[str] = []
    _, vetted = run(rule, chunks, n_controls=0, control_pool=pool, member_controls=1, notes=notes)
    assert [sorted(c.members) for c in vetted] == [["A", "B"]]
    assert vetted[0].together.flipped  # confirmed with H removed as well
    assert any("do not restore the decision specifically" in n and "H" in n for n in notes)


def test_strict_restore_drops_member_whose_restoration_is_unclear():
    chunks = [C("A"), C("H"), C("B")] + [C(f"c{i}") for i in range(3)]

    async def test(removed, extra=(), fresh=False):
        r = frozenset(removed) | frozenset(c.id for c in extra)
        if {"A", "B", "H"} <= r:
            return Outcome(0, 10, "flipped")
        if r == frozenset({"A", "B"}):  # keeping only H: borderline, not a clear restore
            return Outcome(4, 15, "unclear")
        return Outcome(5, 5, "kept")

    _, plain = asyncio.run(search(chunks, test, n_controls=0))
    assert [sorted(c.members) for c in plain] == [["A", "B", "H"]]
    _, strict = asyncio.run(search(chunks, test, n_controls=0, strict_restore=True))
    assert [sorted(c.members) for c in strict] == [["A", "B"]]


def test_tester_pins_cache_breakpoints_on_ablated_anthropic_requests(tmp_path):
    from ctxblame.blame import Tester
    from ctxblame.pricing import Ledger
    from ctxblame.trace import Step
    from test_ablate import _cached_body, _marks
    b = _cached_body()
    step = Step(1, {"format": ANTHROPIC, "upstream": "http://127.0.0.1:1", "request": {
        "path": "/v1/messages", "headers": {}, "body": b}, "response": {"streamed": False, "body": {}}})
    by_id = {c.id: c for c in chunk_request(ANTHROPIC, b)}
    t = Tester(step, "http://127.0.0.1:1", "", Matcher("name"), "Bash", by_id, Ledger(tmp_path / "l", 1), 1.0,
               free=True)
    out = t.ablated([by_id["pair:B"]])
    assert _marks(out)[-1] == ("messages", 2, "content", 0) and len(_marks(out)) == 3


# ------------------------------------------------------------------ 6.4: E forced by tool_choice

def test_force_tool_choice_and_when_E_can_be_forced():
    from ctxblame.blame import force_tool_choice, forcing_unavailable
    oai = {"tools": [{"type": "function", "function": {"name": "bash"}}], "messages": []}
    anth = {"tools": [{"name": "Bash", "input_schema": {}}], "messages": []}
    assert force_tool_choice(OPENAI, oai, "bash")["tool_choice"] == {"type": "function", "function": {"name": "bash"}}
    assert force_tool_choice(ANTHROPIC, anth, "Bash")["tool_choice"] == {"type": "tool", "name": "Bash"}
    assert "tool_choice" not in oai  # the recorded request is not changed
    assert forcing_unavailable(OPENAI, oai, Matcher("name"), "bash") is None
    assert "intent-level" in forcing_unavailable(OPENAI, oai, Matcher("intent"), "run pytest")
    assert "not among" in forcing_unavailable(OPENAI, oai, Matcher("name"), "read_file")
    assert "unconditional" in forcing_unavailable(OPENAI, oai, None, None)
    think = {**anth, "thinking": {"type": "enabled", "budget_tokens": 1024}}
    assert "extended thinking" in forcing_unavailable(ANTHROPIC, think, Matcher("name"), "Bash")


def fake_forced(collapse_rule, flip_rule, forced_flip_rule):
    """fake_cond plus E forced: ``forced_flip_rule(removed)`` -> the choice flips under do(E)."""
    base = fake_cond(collapse_rule, flip_rule)

    async def test(removed, extra=(), fresh=False, forced=False):
        if forced:
            r = frozenset(removed) | frozenset(c.id for c in extra)
            return (Outcome(0, 10, "flipped", k_given=10, n_total=10) if forced_flip_rule(r)
                    else Outcome(10, 10, "kept", k_given=10, n_total=10))
        return await base(removed, extra, fresh)

    async def can_force():
        return True
    test.force_tool, test.can_force, test.force_note = "bash", can_force, ""
    return test


def test_search_with_E_forced_separates_triggers_and_steers_from_a_pure_precondition():
    # edit_file: removing it stops E, and with E forced the choice stays (pure precondition).
    # doc_rule: removing it stops E too, and with E forced the agent picks another command
    # (the p3/precond_2or_pnpm shape): it triggers and steers.
    chunks = [C(x) for x in ("tool_bash", "sys_rule", "doc_rule", "edit_file", "c3")]
    t = fake_forced(collapse_rule=lambda r: bool(r & {"edit_file", "doc_rule"}),
                    flip_rule=lambda r: {"tool_bash", "sys_rule"} <= r,
                    forced_flip_rule=lambda r: "doc_rule" in r or {"tool_bash", "sys_rule"} <= r)
    preconds, notes = [], []
    _, causes = asyncio.run(search(chunks, t, n_controls=0, preconditions=preconds, notes=notes, force=True))
    steers = {p.members[0]: p.steers for p in preconds}
    assert steers == {"edit_file": False, "doc_rule": True}
    forced = [c.members for c in causes if c.forced]
    assert forced == [["doc_rule"]]
    assert [sorted(c.members) for c in causes if not c.forced] == [["sys_rule", "tool_bash"]]
    assert any(n.startswith("triggers_and_steers: doc_rule") for n in notes)
    # without forcing (v0.2.1), both are plain preconditions and nothing is said about steering
    preconds2: list[Cause] = []
    _, causes2 = asyncio.run(search(chunks, t, n_controls=0, preconditions=preconds2))
    assert all(p.steers is None for p in preconds2) and not any(c.forced for c in causes2)


def test_search_with_E_forced_finds_the_steering_line_inside_a_stabilizer():
    # real/run4/step21: the bash tool description enables the action (a stabilizer) and
    # one of its lines (the --tb=line example) steers the choice once E is forced
    kids = [C("tool_bash.1"), C("tool_bash.2"), C("tool_bash.3")]
    chunks = [C("tool_bash", kids), C("sys_rule"), C("hist_pytest")]
    t = fake_forced(collapse_rule=lambda r: "tool_bash" in r or "tool_bash.1" in r,
                    flip_rule=lambda r: "tool_bash" in r,
                    forced_flip_rule=lambda r: "tool_bash" in r or "tool_bash.2" in r)
    stabs, notes = [], []
    _, causes = asyncio.run(search(chunks, t, n_controls=0, stabilizers=stabs, notes=notes,
                                   max_preconditions=0, force=True))
    assert stabs == [["tool_bash"]]
    assert [(c.members, c.forced) for c in causes] == [(["tool_bash.2"], True)]
    assert any(n.startswith("triggers_and_steers (E forced)") for n in notes)
