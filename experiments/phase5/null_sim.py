"""Type-I error of reported causes under least-favourable nulls (Phase 5.3, $0, offline).

Runs the real search (``blame.search``) and the real ``Tester`` (sequential search
tests, ``apply_chunks``, the audit stage) against a simulated model: the HTTP
replayer is replaced by Bernoulli draws whose rate depends on which planted
system-prompt lines are still in the request. Only the model is fake.

Scenarios (baseline rate b, search threshold tau = b/2):

  boundary_single  removing X gives rate tau exactly: "X flips it" is a true null
                   sitting on the boundary, the hardest case for the search's
                   peeking tests. Every reported cause is false.
  boundary_bundle  removing X and Y gives tau; removing X, Y and Z gives 0.05;
                   other pairs keep b. Every candidate has a true null ({X,Y}:
                   no flip; {X,Y,Z}: keeping Z alone does not restore). Every
                   reported cause is false.
  power_bundle     a real 2-way OR bundle (removing both: 0.05). Measures how
                   often the true bundle is still reported (power).
  hitchhiker       one real carrier X (removing it: 0.05) and a weak line Y
                   (removing Y alone: 0.5, just above tau). A cause containing Y
                   is false; power = reporting exactly {X}. Models the GPU-run
                   failure where a bundle {carrier, hitchhiker} was rejected whole.

Scenarios with an action family E (conditional blame, P(E) at baseline 0.95, E
threshold 0.475; E = calling bash, the choice = its flag):

  coupled_power    p0/tool_result_sentence_config: X and Y are an OR bundle for the
                   choice (removing both: 0.05 given E), but removing Y while X stays
                   stops E (0.05). Keeping X alone stops E, so X's restoration is
                   untestable. Power = reporting exactly {X, Y}.
  boundary_coupled removing X, Y, Z flips (0.05 given E); removing X, Y with Z kept
                   puts both P(E) and P(A | E) exactly on their thresholds, so "Z
                   restores" and "Z is coupled" are both true nulls on the boundary,
                   and so is "removing X, Y flips". Every reported cause is false.

Usage:
  uv run python experiments/phase5/null_sim.py --runs 500 --out experiments/phase5/results/<tag>/null_sim.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from ctxblame.blame import Cause, Tester, chunk_request, search  # noqa: E402
from ctxblame.formats import ToolCall  # noqa: E402
from ctxblame.match import Matcher  # noqa: E402
from ctxblame.pricing import Ledger  # noqa: E402
from ctxblame.replay import Sample, wilson  # noqa: E402
from ctxblame.trace import Step  # noqa: E402

B = 0.9
TAU = B / 2
BE = 0.95  # P(E) at baseline in the conditional scenarios
TAU_E = BE / 2
GIVEN = ("coupled_power", "boundary_coupled")
LINES = [f"Rule {c}: follow convention {c}." for c in "ABCDEFGH"]  # X = A, Y = B, Z = C


def _rate_fn(scenario: str):
    def rate(present: set[str]) -> float:
        gone = {c for c in "ABCDEFGH" if c not in present}
        if scenario == "boundary_single":
            return TAU if "A" in gone else B
        if scenario == "boundary_bundle":
            if {"A", "B", "C"} <= gone:
                return 0.05
            return TAU if {"A", "B"} <= gone else B
        if scenario == "power_bundle":
            return 0.05 if {"A", "B"} <= gone else B
        if scenario == "hitchhiker":
            return 0.05 if "A" in gone else 0.5 if "B" in gone else B
        # conditional scenarios: (P(E), P(A | E))
        if scenario == "coupled_power":
            if {"A", "B"} <= gone:
                return BE, 0.05
            return (0.05, B) if "B" in gone else (BE, B)
        if scenario == "boundary_coupled":
            if {"A", "B", "C"} <= gone:
                return BE, 0.05
            return (TAU_E, TAU) if {"A", "B"} <= gone else (BE, B)
        raise ValueError(scenario)
    return rate


def _step() -> Step:
    body = {"model": "sim", "messages": [
        {"role": "system", "content": "\n\n".join(LINES)},
        {"role": "user", "content": "Run the tests."}],
        "tools": [{"type": "function", "function": {"name": "bash"}}]}
    return Step(1, {"format": "openai", "upstream": "http://127.0.0.1:1/v1",
                    "request": {"path": "/chat/completions", "headers": {}, "body": body},
                    "response": {"streamed": False, "body": {"choices": [{"message": {
                        "role": "assistant", "content": None, "tool_calls": [
                            {"id": "c", "type": "function", "function": {"name": "bash", "arguments": "{}"}}]}}],
                        "usage": {"prompt_tokens": 100, "completion_tokens": 10}}}})


EXACT = Matcher("exact")
TARGET = EXACT._one(ToolCall("bash", {"flag": "x"}))


class _SimReplayer:
    def __init__(self, rate, rng: random.Random) -> None:
        self.rate, self.rng = rate, rng

    async def run(self, body: dict, n: int, matcher=None) -> list[Sample]:
        text = body["messages"][0]["content"] if body["messages"][0]["role"] == "system" else ""
        present = {line.split()[1][0] for line in LINES if line in text}
        p = self.rate(present)
        out = []
        for _ in range(n):
            if isinstance(p, tuple):  # E = calls bash; the choice = its flag
                if self.rng.random() < p[0]:
                    call = {"name": "bash", "args": {"flag": "x" if self.rng.random() < p[1] else "y"}}
                else:
                    call = {"name": "read", "args": {}}
                k = EXACT._one(ToolCall(call["name"], call["args"]))
                out.append(Sample(ok=True, key=k, keys=[k], calls=[call]))
                continue
            k = "bash" if self.rng.random() < p else "read"
            out.append(Sample(ok=True, key=k, keys=[k], calls=[{"name": k, "args": {}}]))
        return out


class SimTester(Tester):
    def __init__(self, *a, sim: _SimReplayer, **kw) -> None:
        super().__init__(*a, **kw)
        self.sim = sim

    def replayer(self):
        return self.sim


def _is_false(scenario: str, c: Cause) -> bool:
    """Is this reported cause a false discovery (some component null true)?"""
    m = {x.split(".")[1][1] if x.startswith("sys") else x for x in c.members}
    letters = {"ABCDEFGH"[int(x) - 1] if x.isdigit() else x for x in m}
    if scenario == "power_bundle":
        return letters != {"A", "B"}
    if scenario == "hitchhiker":
        return letters != {"A"}
    if scenario == "coupled_power":
        return letters != {"A", "B"}
    return True


async def one(scenario: str, seed: int, audit_n: int, alpha: float, ledger_path: Path) -> dict:
    rng = random.Random(seed)
    step = _step()
    coarse = chunk_request(step.fmt, step.body)
    by_id = {c.id: c for c in coarse}
    for c in coarse:
        for k in c.children:
            by_id[k.id] = k
    sim = _SimReplayer(_rate_fn(scenario), rng)
    if scenario in GIVEN:
        test = SimTester(step, "http://127.0.0.1:1/v1", "", EXACT, TARGET, by_id, Ledger(ledger_path, 1.0), B,
                         given_matcher=Matcher("name"), given_target="bash", baseline_given_rate=BE,
                         free=True, sim=sim)
    else:
        test = SimTester(step, "http://127.0.0.1:1/v1", "", Matcher("name"), "bash", by_id,
                         Ledger(ledger_path, 1.0), B, free=True, sim=sim)
    notes: list[str] = []
    _, causes = await search(coarse, test, n_controls=0, rng=random.Random(seed), notes=notes,
                             audit_n=audit_n, alpha=alpha, uncertified=[])
    return {"reported": [sorted(c.members) for c in causes], "coupled": [c.coupled for c in causes],
            "false": sum(_is_false(scenario, c) for c in causes), "replays": test.replays}


def simulate(scenario: str, runs: int, seed: int, audit_n: int, alpha: float) -> dict:
    with tempfile.TemporaryDirectory() as d:
        rows = [asyncio.run(one(scenario, seed * 100_003 + r, audit_n, alpha, Path(d) / f"l{r}.jsonl"))
                for r in range(runs)]
    any_false = sum(1 for r in rows if r["false"])
    true_found = sum(1 for r in rows if any(not _is_false(scenario, Cause(m)) for m in r["reported"])) \
        if scenario in ("power_bundle", "hitchhiker", "coupled_power") else None
    lo, hi = wilson(any_false, runs)
    return {"scenario": scenario, "audit_n": audit_n, "alpha": alpha, "runs": runs,
            "fwer": any_false / runs, "fwer_ci": [lo, hi],
            "power": (true_found / runs) if true_found is not None else None,
            "replays_mean": sum(r["replays"] for r in rows) / runs}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--runs", type=int, default=500)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--audit-n", type=int, default=20)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--scenarios", nargs="+", default=["boundary_single", "boundary_bundle", "power_bundle",
                                                       "hitchhiker", *GIVEN])
    a = ap.parse_args(argv)
    res = []
    print("| scenario | audit | runs | P(any false cause) [95% CI] | power | replays/run |")
    print("|---|---|---:|---:|---:|---:|")
    for sc in a.scenarios:
        for n in (0, a.audit_n):
            r = simulate(sc, a.runs, a.seed, n, a.alpha)
            res.append(r)
            pw = "–" if r["power"] is None else f"{r['power']:.0%}"
            print(f"| {sc} | {'off (v0.2)' if n == 0 else f'n={n}, α={a.alpha}'} | {r['runs']} | "
                  f"{r['fwer']:.1%} [{r['fwer_ci'][0]:.1%}, {r['fwer_ci'][1]:.1%}] | {pw} | "
                  f"{r['replays_mean']:.0f} |", flush=True)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps({"b": B, "tau": TAU, "seed": a.seed, "results": res}, indent=1))
        print(f"Saved: {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
