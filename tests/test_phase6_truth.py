"""Phase 6.1 truth labels from exhaustive coalition tables (deterministic synthetic tables)."""

import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "phase6"))

from truth import Cell, label  # noqa: E402


def table(elements, p_e, p_a, n=50):
    """Exact-count cells from rate functions of the removed set."""
    cells = {}
    for r in range(len(elements) + 1):
        for c in combinations(elements, r):
            s = frozenset(c)
            kg = round(n * p_e(s))
            cells[s] = Cell(s, n, kg, round(kg * p_a(s)))
    return cells


K = {"a": "carrier", "b": "carrier", "pre": "precondition", "probe": "probe"}


def test_or_bundle_with_precondition_and_neutral_probe():
    t = label(["a", "b", "pre", "probe"], K,
              table(["a", "b", "pre", "probe"], lambda s: 0.05 if "pre" in s else 0.95,
                    lambda s: 0.05 if {"a", "b"} <= s else 0.9))
    assert t.carrier_sets == [frozenset("ab")] and t.precondition_sets == [frozenset({"pre"})]
    assert t.roles == {"a": "carrier", "b": "carrier", "pre": "precondition", "probe": "neutral"}
    assert t.regimes == ["or", "precondition_gated"] and t.ambiguous == 0


def test_and_carriers_and_a_probe_that_really_interacts():
    # A needs both a and b present; the probe line matters too (Llama's neutral lines)
    t = label(["a", "b", "probe"], K, table(["a", "b", "probe"], lambda s: 0.95,
                                            lambda s: 0.05 if s & {"a", "b"} or {"probe"} == s else 0.9))
    assert t.carrier_sets == [frozenset("a"), frozenset("b"), frozenset({"probe"})]
    assert "and" in t.regimes and "probe_interaction" in t.regimes and t.roles["probe"] == "carrier"


def test_coupled_carrier_is_triggers_and_steers_and_non_monotone():
    # p0 shape: removing b alone stops E, removing a and b keeps E and flips A
    t = label(["a", "b"], K, table(["a", "b"], lambda s: 0.05 if s == {"b"} else 0.95,
                                   lambda s: 0.05 if {"a", "b"} <= s else 0.9))
    assert t.carrier_sets == [frozenset("ab")] and t.precondition_sets == [frozenset("b")]
    assert t.roles["b"] == "triggers_and_steers" and "e_coupled" in t.regimes
    assert (["b"], ["a", "b"], "collapse undone") in [tuple(x) for x in t.non_monotone]


def test_negative_and_ambiguous_cells():
    t = label(["probe"], K, table(["probe"], lambda s: 0.95, lambda s: 0.9))
    assert t.regimes == ["negative"] and t.roles == {"probe": "neutral"}
    # a removal right at the A threshold is ambiguous, not a carrier
    t = label(["a"], K, table(["a"], lambda s: 0.95, lambda s: 0.45 if s else 0.9))
    assert t.carrier_sets == [] and t.ambiguous == 1


def test_incomplete_table_is_refused():
    cells = table(["a", "b"], lambda s: 0.95, lambda s: 0.9)
    del cells[frozenset("ab")]
    try:
        label(["a", "b"], K, cells)
    except ValueError as e:
        assert "incomplete" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_table_runner_enumerates_every_removal_with_a_simulated_model(tmp_path, capsys):
    """tables.table() on a real Phase 6 case: the simulated model uses the convention
    while any carrier is in the request and stops acting without the precondition."""
    import asyncio
    import random

    from ctxblame.formats import ToolCall
    from ctxblame.replay import Sample
    from cases6 import phase6_cases
    from tables import table

    tc = next(c for c in phase6_cases(250) if c.design == "precondition_gated" and len(c.elements) == 4)
    carriers = [v for k, v in tc.elements.items() if tc.kinds[k] == "carrier"]
    pre = next(v for k, v in tc.elements.items() if tc.kinds[k] == "precondition")
    cmd = __import__("json").loads(tc.case.step.response["choices"][0]["message"]["tool_calls"][0]
                                   ["function"]["arguments"])["command"]

    class Sim:
        def __init__(self):
            self.rng, self.calls = random.Random(0), 0

        async def run(self, body, n, matcher=None):
            self.calls += 1
            text = __import__("json").dumps(body)
            has = lambda spec: (spec.split(":", 1)[1] in text) if spec.startswith("pair:") else (  # noqa: E731
                __import__("json").dumps(spec)[1:-1] in text)
            out = []
            for _ in range(n):
                if not has(pre):
                    call = ToolCall("edit_file", {"path": "x"})
                elif any(has(c) for c in carriers):
                    call = ToolCall("bash", {"command": cmd})
                else:
                    call = ToolCall("bash", {"command": "python -m pytest"})
                k = matcher._one(call)
                out.append(Sample(ok=True, key=k, keys=[k], calls=[{"name": call.name, "args": call.args}]))
            return out

    class A:
        model, max_tokens, no_thinking_param, extra_body, n = None, 1024, False, {}, 20

    sim = Sim()
    r = asyncio.run(table(tc, A, sim))
    m = len(tc.elements)
    assert len(r["cells"]) == 2 ** m and sim.calls == 2 ** m  # the base cell reuses the base replays
    t = r["truth"]
    c_names = sorted(k for k in tc.elements if tc.kinds[k] == "carrier")
    assert t["carrier_sets"] == [c_names] and t["precondition_sets"] == [["pre"]]
    assert all(t["roles"][p] == "neutral" for p in tc.elements if tc.kinds[p] == "probe")

    # tables only (the 6.2 pilot): score6 summarizes the tables and sizes the suite
    from score6 import main as score_main
    (tmp_path / "t.json").write_text(__import__("json").dumps(r, default=str))
    out = tmp_path / "score.json"
    assert score_main([str(tmp_path), "--wall-seconds", "8", "--suite", "100", "--out", str(out)]) == 0
    s = __import__("json").loads(out.read_text())["tables_summary"]
    assert s["cases"] == 1 and s["replays"] == r["replays"] == 20 * 2 ** m and s["cells_per_case"] == 2 ** m
    assert s["replays_per_second"] == r["replays"] / 8 and abs(s["suite_hours"] - 100 * 8 / 3600) < 1e-9
    assert s["regimes"] == {g: 1 for g in t["regimes"]} and "tables only" in capsys.readouterr().out


def test_score_maps_refined_lines_to_elements_and_flags_neutral_probes():
    from score6 import element_of, score_case
    chunks = {"c1": ["sys@msg0.p2"], "pre": ["pair:call_9"], "p1": ["pair:call_3"]}
    assert element_of("sys@msg0.p2.4", chunks) == "c1" and element_of("tooldesc:bash.2", chunks) is None
    t = {"chunks": chunks, "kinds": {"c1": "carrier", "pre": "precondition", "p1": "probe"},
         "truth": {"roles": {"c1": "carrier", "pre": "precondition", "p1": "neutral"}, "regimes": ["single"]}}
    rep = {"causes": [{"members": [{"id": "sys@msg0.p2.4"}, {"id": "pair:call_3"}, {"id": "msg[1].2"}]}],
           "preconditions": [{"members": [{"id": "pair:call_9"}]}]}
    s = score_case(t, rep)
    assert s["recall"] == 1.0 and s["precision"] == 0.5 and s["probe_fp"] and s["unplanted"] == 1
    assert s["precond"] == 1.0 and not s["precond_blamed"] and s["negative_ok"] is None
    # a negative case: only planted elements are judged; an unplanted cause is counted apart
    neg = {**t, "truth": {**t["truth"], "roles": {"c1": "neutral", "pre": "neutral", "p1": "neutral"},
                          "regimes": ["negative"]}}
    s = score_case(neg, {"causes": [{"members": [{"id": "sys@msg0.p1.1"}]}]})
    assert s["negative_ok"] is True and s["unplanted"] == 1
    s = score_case(neg, {"causes": [{"members": [{"id": "sys@msg0.p2.4"}]}]})
    assert s["negative_ok"] is False and s["unplanted"] == 0


def test_forced_cells_decide_whether_a_precondition_also_steers():
    # p3/precond_2or_pnpm shape: removing `edit` or `read` stops E. Unforced, neither can be
    # judged on the choice. With E forced, removing `edit` changes the command, `read` does not.
    els = ["rule", "edit", "read"]
    k = {"rule": "carrier", "edit": "precondition", "read": "probe"}
    p_e = lambda s: 0.05 if s & {"edit", "read"} else 0.95  # noqa: E731
    p_a = lambda s: 0.05 if "rule" in s else 0.9  # noqa: E731
    unforced = table(els, p_e, p_a)
    t0 = label(els, k, unforced)
    assert t0.roles == {"rule": "carrier", "edit": "precondition", "read": "precondition"} and t0.forced is None
    forced = table(els, lambda s: 1.0, lambda s: 0.05 if s & {"rule", "edit"} else 0.9)
    t = label(els, k, unforced, forced=forced)
    assert t.steer_sets == [frozenset({"edit"}), frozenset({"rule"})]
    assert t.roles == {"rule": "carrier", "edit": "triggers_and_steers", "read": "precondition"}
    assert "e_coupled" in t.regimes and t.forced["used"] is True
    js = t.to_json()
    assert js["steer_sets"] == [["edit"], ["rule"]] and js["f_state"]["edit"] == "flipped"
    # forcing that changes the choice even with the whole context is not informative: not used
    bad = table(els, lambda s: 1.0, lambda s: 0.3)
    t2 = label(els, k, unforced, forced=bad)
    assert t2.forced["used"] is False and t2.steer_sets == [] and t2.roles == t0.roles


def test_a_set_minimal_only_because_a_smaller_one_collapses_E_is_not_a_choice_set():
    # p6/0-1179 shape: removing c1 stops E unless p1 is removed too; with E intact,
    # removing both flips. Unforced, {c1, p1} is the minimal flip, so p1 looks like a
    # carrier. With E forced, removing c1 alone already flips: p1 modulates E, not A.
    els = ["c1", "p1"]
    k = {"c1": "carrier", "p1": "probe"}
    unforced = table(els, lambda s: 0.05 if s == {"c1"} else 0.95, lambda s: 0.05 if "c1" in s else 0.9)
    t0 = label(els, k, unforced)
    assert t0.carrier_sets == [frozenset({"c1", "p1"})] and t0.roles["p1"] == "carrier"
    forced = table(els, lambda s: 1.0, lambda s: 0.05 if "c1" in s else 0.9)
    t = label(els, k, unforced, forced=forced)
    assert t.carrier_sets == [frozenset({"c1"})] and t.steer_sets == [frozenset({"c1"})]
    assert t.roles == {"c1": "triggers_and_steers", "p1": "neutral"}


def test_forced_table_runner_replays_every_removal_with_tool_choice(tmp_path):
    import asyncio
    import json

    from ctxblame.formats import ToolCall
    from ctxblame.replay import Sample
    from cases6 import phase6_cases
    from tables import forced_table, needs_forcing, table as run_table

    tc = next(c for c in phase6_cases(250) if c.design == "precondition_gated" and len(c.elements) == 4)
    carriers = [v for kk, v in tc.elements.items() if tc.kinds[kk] == "carrier"]
    pre = next(v for kk, v in tc.elements.items() if tc.kinds[kk] == "precondition")
    cmd = json.loads(tc.case.step.response["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"])["command"]

    class Sim:
        """Without the precondition the agent edits instead; forced to bash, it then runs
        another command, so the precondition also steers. Carriers pick the command."""
        def __init__(self):
            self.forced_calls = 0

        async def run(self, body, n, matcher=None):
            text = json.dumps(body)
            forced = bool(body.get("tool_choice"))
            self.forced_calls += forced
            has = lambda spec: (spec.split(":", 1)[1] in text) if spec.startswith("pair:") else (  # noqa: E731
                json.dumps(spec)[1:-1] in text)
            out = []
            for _ in range(n):
                if not has(pre):
                    call = ToolCall("bash", {"command": "make it"}) if forced else ToolCall("edit_file", {"path": "x"})
                elif any(has(c) for c in carriers):
                    call = ToolCall("bash", {"command": cmd})
                else:
                    call = ToolCall("bash", {"command": "python -m pytest"})
                kk = matcher._one(call)
                out.append(Sample(ok=True, key=kk, keys=[kk], calls=[{"name": call.name, "args": call.args}]))
            return out

    class A:
        model, max_tokens, no_thinking_param, extra_body, n = None, 1024, False, {}, 20

    base = asyncio.run(run_table(tc, A, Sim()))
    assert needs_forcing(base) and base["truth"]["roles"]["pre"] == "precondition"
    sim = Sim()
    f = asyncio.run(forced_table(tc, A, sim, json.loads(json.dumps(base, default=str))))
    m = len(tc.elements)
    assert len(f["forced_cells"]) == 2 ** m and sim.forced_calls == 2 ** m
    assert f["forced_cells"][0]["k_given"] == 20 and f["truth"]["forced"]["used"]
    assert f["truth"]["roles"]["pre"] == "triggers_and_steers" and f["unforced_truth"] == base["truth"]

    # score6 --forced scores the case on the forced truth: a forced cause on the precondition
    # is now a found carrier, not a precondition blamed as a cause
    from score6 import main as score_main
    (tmp_path / "tables").mkdir()
    (tmp_path / "forced").mkdir()
    (tmp_path / "tables" / "t.json").write_text(json.dumps(base, default=str))
    (tmp_path / "forced" / "t.json").write_text(json.dumps(f, default=str))
    pre_id = base["chunks"]["pre"][0]
    rep = {"causes": [{"members": [{"id": pre_id}], "forced": True}], "preconditions": [{"members": [{"id": pre_id}]}]}
    (tmp_path / "seed0").mkdir()
    (tmp_path / "seed0" / "benchmark.json").write_text(json.dumps([{"case": tc.name, "method": "ctxblame",
                                                                     "report": rep}]))
    for forced_arg, blamed in (([], True), (["--forced", str(tmp_path / "forced")], False)):
        out = tmp_path / "score.json"
        assert score_main([str(tmp_path / "tables"), str(tmp_path / "seed0" / "benchmark.json"),
                           "--out", str(out), *forced_arg]) == 0
        row = json.loads(out.read_text())["rows"][0]
        assert row["precond_blamed"] is blamed and row["precond"] == 1.0


def test_forced_alternatives_tell_another_step_from_a_competing_tool(tmp_path):
    import json

    from forced_alts import kind_of, summarize
    a = {"pnpm"}
    assert kind_of("run git status", a) == "step: inspect" and kind_of("read src/a.py", a) == "step: inspect"
    assert kind_of("edit package.json", a) == "step: edit" and kind_of("run git add", a) == "step: edit"
    assert kind_of("run pnpm add", a) == "same program" and kind_of("run npm install", a) == "competing tool"
    # one case: removing the edit (pre) flips A under do(E) to `pnpm add`; c1's flip is npm
    truth = {"forced": {"used": True}, "precondition_sets": [["pre"]], "steer_sets": [["c1"], ["pre"]],
             "kinds": {"c1": "carrier", "pre": "precondition"}}
    cells = [{"removed": [], "replies": [[True, "run pnpm install", 50]]},
             {"removed": ["c1"], "replies": [[False, "run npm install", 50]]},
             {"removed": ["pre"], "replies": [[False, "run pnpm add", 45], [True, "run pnpm install", 5]]},
             {"removed": ["c1", "pre"], "replies": [[False, "run npm install", 50]]}]
    (tmp_path / "forced").mkdir()
    (tmp_path / "forced" / "x.json").write_text(json.dumps({"truth": truth, "forced_cells": cells}))
    rows = summarize(tmp_path)["rows"]
    assert rows == [{"kinds": "precondition", "instead": "same program", "steer_sets": 1,
                     "examples": [("run pnpm add", 45)]}]  # c1 is no precondition: not listed


def test_paired_comparison_averages_seeds_inside_a_case_and_skips_negatives():
    from compare6 import compare
    row = lambda c, s, r, p, reg=("single",), ov=True: {"case": c, "seed": s, "recall": r, "precision": p,  # noqa: E731
                                                        "regimes": list(reg), "oracle_valid": ov}
    a = [row("x", "seed0", 0.0, 0.0), row("x", "seed1", 1.0, 1.0), row("y", "seed0", 1.0, 1.0),
         row("n", "seed0", None, 0.0, ("negative",))]
    b = [row("x", "seed0", 1.0, 1.0), row("y", "seed0", 1.0, 1.0), row("n", "seed0", None, None, ("negative",))]
    res = compare(a, b, boot=200)
    assert res["all"]["cases"] == 2 and abs(res["all"]["a"] - 0.75) < 1e-9 and res["all"]["b"] == 1.0
    assert abs(res["all"]["diff"] - 0.25) < 1e-9 and res["all"]["better"] == 1 and res["all"]["worse"] == 0
    assert "regime:negative" not in res and res["all"]["ci"][0] >= 0
