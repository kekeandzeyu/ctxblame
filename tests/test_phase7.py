import asyncio
import json
import random
import sys
from argparse import Namespace
from pathlib import Path

import numpy as np
from aiohttp import web
from aiohttp.test_utils import TestServer

ROOT = Path(__file__).parents[1]
for p in ("experiments/phase7", "experiments/phase6", "experiments/phase3"):
    sys.path.insert(0, str(ROOT / p))

from baselines import (Case, effective, masks, one_case, parse_design, parse_self_explain,  # noqa: E402
                       removal, units)
from cases6 import phase6_cases  # noqa: E402
from estimate import action_rows, case_reports, choice_rows, design_matrix, select  # noqa: E402
from score7 import best_by_budget, family, method_budget  # noqa: E402

from ctxblame.pricing import Ledger  # noqa: E402
from ctxblame.replay import Replayer  # noqa: E402

CASE = "p6/0-1040/tox/system+pre"  # c1: a rule line (the choice), pre: a tool-call pair (the action)


def _case():
    return next(tc for tc in phase6_cases(250, 0) if tc.name == CASE)


def test_designs_and_units():
    assert parse_design("q0.25") == (False, 0.25) and parse_design("fq0.5") == (True, 0.5)
    rows = masks(30, 0.5, 64, 10, random.Random(0))
    assert len(rows) == 64 and rows[:10] == [[]] * 10 and all(rows[10:])
    longer = masks(30, 0.5, 128, 10, random.Random(0))
    assert longer[:64] == rows  # a budget M is a prefix of the full design

    tc = _case()
    us, parent = units("openai", tc.case.step.body, tc.case.protect)
    ids = [u.id for u in us]
    assert tc.elements["pre"] in ids  # a pair is one unit
    p = next(i for i, u in enumerate(us) if u.id.startswith("pair:") and u.children)
    kids = [i for i, x in enumerate(parent) if x == p]
    assert kids and all(ids[i].startswith(ids[p] + ".") for i in kids)  # ... next to its own lines
    assert effective([p], parent) == sorted([p] + kids)
    assert [c.id for c in removal(us, [p] + kids, parent)] == [ids[p]]  # the pair takes its lines along
    c1 = tc.elements["c1"]
    assert any(c1 in u.text for u in us if not u.id.startswith("pair:"))


def _sim(truth, q, n, d=32, pre=None, noise=0.05, seed=0):
    rng = random.Random(seed)
    out = []
    for r in masks(d, q, n, 0, rng):
        s = set(r)
        e = pre is None or pre not in s
        a = e and not truth(s)
        if rng.random() < noise:
            a = not a
        out.append([r, True, e, a])
    return out


def test_estimators_find_single_or_and_precondition_and_report_nothing_on_noise():
    cases = {(3,): lambda s: 3 in s, (5, 6): lambda s: {5, 6} <= s, (): lambda s: False}
    for est in ("banzhaf", "lasso", "gt"):
        for want, f in cases.items():
            rows = _sim(f, 0.5, 400, pre=12)
            cr, cy = choice_rows(rows)
            ar, ay = action_rows(rows)
            g = np.random.default_rng(1)
            assert select(est, design_matrix(cr, 32), cy, g) == list(want), (est, want)
            assert select(est, design_matrix(ar, 32), ay, g) == [12], est


def test_gate_wastes_rows_behind_preconditions():
    rows = _sim(lambda s: 3 in s, 0.25, 400, pre=12)
    assert 0.15 < len(choice_rows(rows)[0]) / len(rows) < 0.35  # about q^1 of the rows stay in E


class FakeModel:
    """A deterministic stand-in for vLLM on one case: it calls bash only with the
    precondition pair present, and runs the target command only with the rule line."""

    def __init__(self, tc):
        self.rule = tc.elements["c1"]
        self.pair = tc.elements["pre"].removeprefix("pair:")
        self.target = json.loads(tc.case.step.response["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"])
        self.chats = 0

    def present(self, text: str) -> tuple[bool, bool]:
        return self.pair in text, self.rule in text

    @staticmethod
    def render(messages: list, gen: bool) -> str:
        out = "".join(f"<{m['role']}>{m.get('content') or ''}{json.dumps(m.get('tool_calls') or [])}</>"
                      for m in messages)
        return out + ("<assistant>" if gen else "")

    def app(self) -> web.Application:
        async def chat(request):
            body = await request.json()
            self.chats += 1
            if "tools" not in body:  # the self-explanation prompt
                return self._reply({"content": json.dumps({"choice": ["sys@msg0.p2.2"], "action": []})})
            has_pair, has_rule = self.present(json.dumps(body["messages"]))
            if not has_pair and "tool_choice" not in body:
                return self._reply({"content": "Nothing to do yet."})
            cmd = self.target["command"] if has_rule else "python -m pytest"
            return self._reply({"content": None, "tool_calls": [{"id": "c", "type": "function", "function": {
                "name": "bash", "arguments": json.dumps({"command": cmd})}}]})

        async def tokenize(request):
            b = await request.json()
            text = self.render(b["messages"], b["add_generation_prompt"])
            if not b["add_generation_prompt"]:  # the reply as the last turn: <assistant> + call + </>
                text = text[:text.rfind("<assistant>")] + "<assistant>" + text[text.rfind("<assistant>") + 11:]
            return web.json_response({"tokens": [ord(c) for c in text]})

        async def detokenize(request):
            return web.json_response({"prompt": "".join(map(chr, (await request.json())["tokens"]))})

        async def completions(request):
            toks = (await request.json())["prompt"]
            text = "".join(map(chr, toks))
            r0 = text.rfind("<assistant>")
            nb = text.find("bash", r0) + 4
            has_pair, has_rule = self.present(text[:r0])
            lps = [None]
            for i, t in enumerate(toks[1:], 1):
                lp = -0.01
                if i >= r0 and ((i < nb and not has_pair) or (i >= nb and not has_rule)):
                    lp = -2.0
                lps.append({str(t): {"logprob": lp}})
            return web.json_response({"choices": [{"prompt_logprobs": lps, "text": ""}]})

        app = web.Application()
        app.router.add_post("/v1/chat/completions", chat)
        app.router.add_post("/tokenize", tokenize)
        app.router.add_post("/detokenize", detokenize)
        app.router.add_post("/v1/completions", completions)
        return app

    @staticmethod
    def _reply(msg: dict):
        return web.json_response({"id": "x", "object": "chat.completion", "model": "m", "choices": [
            {"index": 0, "finish_reason": "tool_calls" if msg.get("tool_calls") else "stop",
             "message": {"role": "assistant", **msg}}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}})


def test_baselines_end_to_end_on_a_fake_server(tmp_path):
    tc = _case()
    fake = FakeModel(tc)

    async def go():
        async with TestServer(fake.app()) as srv:
            base = str(srv.make_url("/v1"))
            args = Namespace(base_url=base, model=None, max_tokens=256, no_thinking_param=True, extra_body={},
                             free=True, designs=["fq0.5", "q0.5"], m=96, base=10, cc_masks=64, cc_concurrency=8,
                             self_explain=True)
            step = tc.case.step
            rp = Replayer("openai", base + step.record["request"]["path"], {}, Ledger(tmp_path / "l.jsonl", 1.0),
                          base, 0.0, 16, free=True)
            return await one_case(tc, args, rp, 0)

    raw = asyncio.run(go())
    assert raw["given"] == "bash" and raw["call"][0] == "bash"
    assert raw["replays"] == 2 * 96 + 1 and fake.chats == 2 * 96 + 1
    q, f = raw["designs"]["q0.5"], raw["designs"]["fq0.5"]
    assert all(r[1] and r[2] and r[3] for r in q["rows"][:10])  # base rows: E and A
    assert all(r[2] for r in f["rows"])  # forced: always in E
    assert 0.3 < sum(r[2] for r in q["rows"][10:]) / 86 < 0.7  # the pair is kept half the time
    assert len(raw["contextcite"]["rows"]) == 64
    assert raw["self_explain"]["choice"] == ["sys@msg0.p2.2"]

    rule = next(u for u in raw["units"] if u.startswith("sys@") and tc.elements["c1"] in
                next(x.text for x in Case(tc, Namespace(model=None, max_tokens=256, no_thinking_param=True,
                                                        extra_body={})).units if x.id == u))
    pair = tc.elements["pre"]
    reps = dict(case_reports(json.loads(json.dumps(raw)), budgets=(64, 96)))
    ids = lambda r, k: [m["id"] for c in r[k] for m in c["members"]]  # noqa: E731
    for est in ("banzhaf", "lasso", "gt"):
        r = reps[f"{est}:q0.5:M96"]
        assert ids(r, "causes") == [rule], est
        assert pair in ids(r, "preconditions"), est
        assert ids(reps[f"{est}:fq0.5:M96"], "causes") == [rule]
        assert reps[f"{est}:fq0.5:M96"]["preconditions"] == []  # forced rows cannot see the action
        assert f"{est}:fq0.5+q0.5:M96" in reps
    cc = reps["cc:M64"]
    assert ids(cc, "causes") == [rule] and pair in ids(cc, "preconditions")
    assert ids(reps["self_explain_full"], "causes") == ["sys@msg0.p2.2"]


def test_parse_self_explain_and_method_names():
    ids = {"a", "b", "c"}
    assert parse_self_explain('<think>x</think> {"choice": ["a", "z", "a"], "action": ["c"]}', ids) == (["a"], ["c"])
    assert parse_self_explain("no json", ids) == ([], [])
    assert method_budget("gt:fq0.5+q0.5:M128") == 128 and method_budget("self_explain_full") is None
    assert family("cc:M64") == "cc"
    summ = {"gt:q0.5:M64": {"all": {"f1": 0.5}}, "gt:q0.25:M64": {"all": {"f1": 0.6}},
            "cc:M64": {"all": {"f1": 0.4}}, "self_explain_full": {"all": {"f1": 0.9}}}
    assert best_by_budget(summ) == {("gt", 64): "gt:q0.25:M64", ("cc", 64): "cc:M64"}
