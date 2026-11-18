"""Phase 1 experiment: planted causes in *real* agent traces.

The traces come from experiments/phase1/agent.py (recorded through the proxy,
thinking on). Its AGENTS.md has two rules whose effect we can see in the
trace, and each has other carriers that the model can also follow:

  arch   "Before editing anything under src/, read docs/ARCHITECTURE.md"
         -> the step where the agent reads docs/ARCHITECTURE.md.
         Other carrier: the agent's own earlier thinking may restate the rule.
  pytest "Run the test suite with `python -m pytest -q`. Do not use `uv run`"
         -> the bash call that runs the tests.
         Other carriers: the bash tool's parameter description
         ("e.g. `python -m pytest -q`") and, later in the run, the agent's
         own earlier pytest call.

For each case: baseline, each carrier removed alone, all carriers removed,
and random same-size controls (several spans).

    DEEPSEEK_API_KEY=... uv run python experiments/phase1/ablations.py
    uv run python experiments/phase1/ablations.py --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ctxblame.ablate import AblationError, remove_random_span, remove_text, remove_units, validate
from ctxblame.match import Matcher
from ctxblame.pricing import Ledger
from ctxblame.replay import Replayer, build_headers, estimate_cost, summarize
from ctxblame.trace import find_cwd, get_step, load_trace, request_text

HERE = Path(__file__).parent
REPO = HERE.parents[1]
TRACES = HERE / "results" / "traces"  # copies of the recorded traces (no auth headers)

TASK = "Running the test suite shows a failure in tests/test_formats.py."
RULE_ARCH = ("- Before editing anything under src/, read docs/ARCHITECTURE.md; it explains\n"
             "  which module owns which wire format.")
RULE_TEST = ("- Run the test suite with `python -m pytest -q`. Do not use `uv run`; the\n"
             "  sandbox has no network.")
EXAMPLE = ", e.g. `python -m pytest -q`"
PYTEST_RX = r"^python -m pytest"


@dataclass
class Case:
    name: str
    trace: str
    step: int
    target: str
    matcher: Matcher
    # condition name -> list of ops; an op is ("text", s) or ("unit", id)
    removals: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    control_size: int = 0
    protect: list[str] = field(default_factory=list)


def arch_case(trace: str, step: int, thinking_units: list[str]) -> Case:
    rem = {"rule": [("text", RULE_ARCH)]}
    if thinking_units:
        rem["thinking"] = [("unit", u) for u in thinking_units]
        rem["rule+thinking"] = rem["rule"] + rem["thinking"]
    return Case(f"arch/{trace}/step{step}", trace, step, "read docs/ARCHITECTURE.md",
                Matcher("intent", any_call=True), rem, len(RULE_ARCH), [RULE_ARCH, TASK])


def pytest_case(trace: str, step: int, history_pairs: list[str]) -> Case:
    rem = {"rule": [("text", RULE_TEST)], "example": [("text", EXAMPLE)],
           "rule+example": [("text", RULE_TEST), ("text", EXAMPLE)]}
    if history_pairs:
        hist = [("unit", f"pair:{p}") for p in history_pairs]
        rem["history"] = hist
        rem["rule+example+history"] = rem["rule+example"] + hist
    m = Matcher("args", [f"command~{PYTEST_RX}"], any_call=True)
    return Case(f"pytest/{trace}/step{step}", trace, step,
                f'bash({{"command~{PYTEST_RX}": true}})', m, rem, len(RULE_TEST),
                [RULE_TEST, EXAMPLE, TASK])


def pair_ids(step, pattern: str) -> list[str]:
    """Ids of earlier tool calls in this step's history whose arguments match."""
    from ctxblame.ablate import list_units
    return [u.id[5:] for u in list_units(step.fmt, step.body)
            if u.kind == "tool pair" and pattern in u.label]


def thinking_units_mentioning(step, word: str) -> list[str]:
    from ctxblame.ablate import list_units
    return [u.id for u in list_units(step.fmt, step.body)
            if u.id.startswith("thinking:") and word in _full_thinking(step, u.id)]


def _full_thinking(step, uid: str) -> str:
    i = int(uid.split("[")[1].rstrip("]"))
    m = step.body["messages"][i]
    if step.fmt == "anthropic":
        return "\n".join(b.get("thinking", "") for b in m["content"] if b.get("type") == "thinking")
    return m.get("reasoning_content") or ""


def build_cases() -> list[Case]:
    cases = []
    for trace, arch_step, first_test_step, later_test_step in (
            ("anthropic-1", 2, 1, 7), ("openai-1", 2, 1, 5)):
        st = get_step(load_trace(TRACES / f"{trace}.jsonl"), arch_step)
        cases.append(arch_case(trace, arch_step, thinking_units_mentioning(st, "ARCHITECTURE")))
        cases.append(pytest_case(trace, first_test_step, []))
        st = get_step(load_trace(TRACES / f"{trace}.jsonl"), later_test_step)
        cases.append(pytest_case(trace, later_test_step, pair_ids(st, "pytest")))
    return cases


def apply(fmt: str, body: dict, ops: list[tuple[str, str]]) -> dict:
    units = [v for k, v in ops if k == "unit"]
    if units:
        body = remove_units(fmt, body, units)
    for k, v in ops:
        if k == "text":
            body = remove_text(fmt, body, v)
    return body


def conditions(case: Case, fmt: str, body: dict, n_controls: int) -> list[tuple[str, dict, str]]:
    out = [("baseline", body, "full context")]
    for name, ops in case.removals.items():
        try:
            out.append((name, apply(fmt, body, ops), "removed " + ", ".join(v[:50] for _, v in ops)))
        except AblationError as e:
            print(f"  skip {case.name} {name}: {e}", file=sys.stderr)
    seen, seed = set(), 0
    while len(seen) < n_controls and seed < 200:
        b, removed = remove_random_span(fmt, body, case.control_size, random.Random(seed), case.protect)
        seed += 1
        if removed in seen:
            continue
        seen.add(removed)
        out.append((f"random_{len(seen) - 1}", b, f"random span: {removed.strip()[:80]!r}"))
    for name, b, _ in out:
        assert not validate(fmt, b), (case.name, name, validate(fmt, b))
    return out


async def run_case(case: Case, ledger: Ledger, n: int, n_ctrl: int, n_controls: int,
                   concurrency: int) -> dict:
    step = get_step(load_trace(TRACES / f"{case.trace}.jsonl"), case.step)
    case.matcher.cwd = find_cwd(request_text(step.fmt, step.body))
    base = step.record["upstream"].rstrip("/")
    key = os.environ["DEEPSEEK_API_KEY"]
    rp = Replayer(step.fmt, base + step.record["request"]["path"],
                  build_headers(step.fmt, step.record["request"].get("headers"), key),
                  ledger, base, estimate_cost(step, base), concurrency)
    conds = conditions(case, step.fmt, step.body, n_controls)

    async def one(name, b, desc):
        k = n_ctrl if name.startswith("random_") else n
        samples = await rp.run(b, k, case.matcher)
        s = summarize(samples, case.target, case.matcher)
        return name, {"description": desc, "summary": s, "samples": [asdict(x) for x in samples]}

    results = dict(await asyncio.gather(*(one(*c) for c in conds)))
    return {"case": case.name, "format": step.fmt, "target": case.target, "conditions": results}


def rate(c: dict) -> str:
    s = c["summary"]
    return f"{s['same_decision']}/{s['n_ok']}" + (f" ({s['n_error']} err)" if s["n_error"] else "")


def table(rows: list[dict]) -> str:
    lines = ["| Case | Condition | Target rate | Most common other outcome |", "|---|---|---|---|"]
    for r in rows:
        for name, c in r["conditions"].items():
            other = [(k, v) for k, v in c["summary"]["distribution"] if k != r["target"]]
            o = f"{other[0][0][:60]} ({other[0][1]})" if other else ""
            lines.append(f"| {r['case']} | {name} | {rate(c)} | {o} |")
    return "\n".join(lines)


async def main_async(args) -> int:
    cases = [c for c in build_cases() if not args.only or any(o in c.name for o in args.only)]
    if args.dry_run:
        for c in cases:
            st = get_step(load_trace(TRACES / f"{c.trace}.jsonl"), c.step)
            for name, _, desc in conditions(c, st.fmt, st.body, args.controls):
                print(f"{c.name:32s} {name:24s} {desc[:90]}")
        return 0
    if "DEEPSEEK_API_KEY" not in os.environ:
        print("error: set DEEPSEEK_API_KEY", file=sys.stderr)
        return 2
    ledger = Ledger(Path(args.ledger), args.budget)
    start = ledger.total
    rows = []
    for c in cases:
        r = await run_case(c, ledger, args.n, args.n_ctrl, args.controls, args.concurrency)
        rows.append(r)
        print(table([r]).split("\n", 2)[2], flush=True)
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    (out / "ablations.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    md = (f"N={args.n} per condition, {args.controls}x{args.n_ctrl} random controls; "
          f"cost ${ledger.total - start:.4f}\n\n" + table(rows) + "\n")
    (out / "ablations.md").write_text(md)
    print(f"\ncost this run ${ledger.total - start:.4f}; ledger total ${ledger.total:.4f}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("-n", type=int, default=20)
    ap.add_argument("--n-ctrl", type=int, default=10)
    ap.add_argument("--controls", type=int, default=3)
    ap.add_argument("--concurrency", type=int, default=12)
    ap.add_argument("--budget", type=float, default=5.0)
    ap.add_argument("--ledger", default=str(REPO / ".ctxblame" / "spend.jsonl"))
    ap.add_argument("--dry-run", action="store_true")
    return asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    sys.exit(main())
