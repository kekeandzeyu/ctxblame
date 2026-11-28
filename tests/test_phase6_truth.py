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
