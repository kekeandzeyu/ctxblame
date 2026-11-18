"""Phase 2 validation: run `ctxblame why` on every case with a known cause.

Cases: the five Phase 0 scenarios (deepseek-v4-pro records, both formats) and
the Phase 1 agent traces (thinking on). Ground truth is the planted text (or
tool pair) and, for Phase 1, its other carriers. A case is *found* when a
reported cause covers a planted carrier; *precision* is the share of reported
cause members that are planted carriers. A case may also correctly *abstain*
("no stable decision") where Phase 0 showed the plant does not drive the step.

    DEEPSEEK_API_KEY=... uv run python experiments/phase2/run.py [--only pnpm arch]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from ctxblame import blame
from ctxblame.trace import get_step, load_trace

HERE = Path(__file__).parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "experiments" / "phase0"))
sys.path.insert(0, str(REPO / "experiments" / "phase1"))
from scenarios import SCENARIOS  # noqa: E402

import ablations as P1  # noqa: E402

P0_RECORDS = REPO / "experiments" / "phase0" / "results" / "deepseek-v4-pro" / "records"
P1_TRACES = REPO / "experiments" / "phase1" / "results" / "traces"


@dataclass
class Case:
    name: str
    trace: Path
    step: int | None
    argv: list[str]  # matcher / target options for `ctxblame why`
    carriers: list[str]  # planted texts ("pair:<id>" for a whole tool pair)
    expect: str  # what a correct answer looks like, for the table
    protect: list[str] = field(default_factory=list)


def p0_cases() -> list[Case]:
    out = []
    for sc in SCENARIOS:
        target = f"{sc.target}({json.dumps({k: True for k in sc.key_args}, sort_keys=True)})"
        argv = [x for k in sc.key_args for x in ("--key-arg", k)] + ["--target", target]
        carriers = [f"pair:{sc.plant_pair}"] if sc.plant_pair else [sc.plant]
        for fmt in ("anthropic", "openai"):
            out.append(Case(f"p0/{sc.name}/{fmt}", P0_RECORDS / f"{sc.name}.{fmt}.json", None, argv,
                            carriers, "the planted text", sc.protect))
    return out


def p1_cases() -> list[Case]:
    arch = ["--target", "read docs/ARCHITECTURE.md"]
    pyt = ["--key-arg", f"command~{P1.PYTEST_RX}", "--target", f'bash({{"command~{P1.PYTEST_RX}": true}})']
    rule_arch, rule_test, example = P1.RULE_ARCH, P1.RULE_TEST, P1.EXAMPLE.strip(", ")
    out = [
        Case("p1/arch/openai/step2", P1_TRACES / "openai-1.jsonl", 2, arch, [rule_arch], "the rule line"),
        Case("p1/arch/anthropic/step2", P1_TRACES / "anthropic-1.jsonl", 2, arch, [rule_arch],
             "rule line; the restating reasoning cannot be removed at this provider"),
        Case("p1/pytest/openai/step1", P1_TRACES / "openai-1.jsonl", 1, pyt, [rule_test, example],
             "rule + tool example, redundant"),
        Case("p1/pytest/anthropic/step1", P1_TRACES / "anthropic-1.jsonl", 1, pyt, [rule_test, example],
             "rule + tool example, redundant"),
    ]
    for name, trace, step in (("openai", "openai-1", 5), ("anthropic", "anthropic-1", 7)):
        st = get_step(load_trace(P1_TRACES / f"{trace}.jsonl"), step)
        hist = [f"pair:{p}" for p in P1.pair_ids(st, "pytest")]
        out.append(Case(f"p1/pytest/{name}/step{step}", P1_TRACES / f"{trace}.jsonl", step, pyt,
                        [rule_test, example, *hist], "rule + example + earlier pytest call, redundant"))
    return out


def is_carrier(member: dict, carriers: list[str]) -> bool:
    mid, text = member["id"], " ".join(member["text"].split())
    for c in carriers:
        if c.startswith("pair:"):
            if mid == c or mid.startswith(c + "."):
                return True
            continue
        c = " ".join(c.split())
        if text and (text in c or c in text) and len(text) >= 8:
            return True
        if text and len(text) >= 20 and text[:60] in c:  # a line that starts inside the carrier
            return True
    return False


def score(case: Case, rep: dict) -> dict:
    # non-specific findings (random same-size removals flip it too) are context the
    # decision needs, not causes; they are shown but not scored
    members = [m for c in rep.get("causes") or [] if c.get("specific") is not False for m in c["members"]]
    hits = [m for m in members if is_carrier(m, case.carriers)]
    covered = {c for c in case.carriers if any(is_carrier(m, [c]) for m in members)}
    return {"result": rep.get("result"), "found": bool(hits), "carriers_found": len(covered),
            "carriers": len(case.carriers), "members": len(members), "precision":
            len(hits) / len(members) if members else None, "cost": rep.get("cost", 0.0),
            "replays": rep.get("replays", 0)}


def short_causes(rep: dict) -> str:
    out = []
    for c in rep.get("causes") or []:
        ms = " + ".join(f"{m['label']}: {' '.join(m['text'].split())[:50]!r}" for m in c["members"])
        spec = "" if c.get("specific") in (True, None) else " [not specific]"
        out.append(f"{ms} ({c['together']['k']}/{c['together']['n']}){spec}")
    return "; ".join(out) or "-"


async def run_one(case: Case, common: list[str]) -> dict:
    ap = argparse.ArgumentParser()
    blame.add_args(ap)
    argv = [str(case.trace), *(["--step", str(case.step)] if case.step else []), *case.argv, *common]
    for p in case.protect:
        argv += ["--protect", p]
    args = ap.parse_args(argv)
    args.json = True  # quiet
    step = get_step(load_trace(case.trace), case.step)
    base = step.record["upstream"].rstrip("/")
    return await blame.why(step, args, os.environ["DEEPSEEK_API_KEY"], base)


def table(rows: list[tuple[Case, dict, dict]]) -> str:
    lines = ["| Case | Baseline | Result | Planted carriers found | Precision | Causes reported | Cost |",
             "|---|---|---|---|---|---|---|"]
    for case, rep, s in rows:
        b = rep.get("baseline") or {}
        prec = f"{s['precision']:.0%}" if s["precision"] is not None else "-"
        lines.append(f"| {case.name} | {b.get('same_decision')}/{b.get('n_ok')} | {s['result']} | "
                     f"{s['carriers_found']}/{s['carriers']} | {prec} | {short_causes(rep)} | ${s['cost']:.3f} |")
    return "\n".join(lines)


def table_from_reports() -> int:
    """Rebuild results.md from the saved per-case reports (all cases, in order)."""
    rows, missing = [], []
    for case in p0_cases() + p1_cases():
        f = HERE / "results" / "reports" / (case.name.replace("/", "__") + ".json")
        if not f.exists():
            missing.append(case.name)
            continue
        d = json.loads(f.read_text())
        rows.append((case, d["report"], d["score"]))
    (HERE / "results" / "results.md").write_text(table(rows) + "\n")
    print(table(rows))
    print(f"\n{len(rows)} cases, total cost ${sum(s['cost'] for _, _, s in rows):.3f}"
          + (f"; missing: {', '.join(missing)}" if missing else ""))
    return 1 if missing else 0


async def main_async(args) -> int:
    cases = [c for c in p0_cases() + p1_cases() if not args.only or any(o in c.name for o in args.only)]
    common = ["--budget", str(args.budget), "--ledger", str(REPO / ".ctxblame" / "spend.jsonl"),
              "--concurrency", str(args.concurrency)]
    out = HERE / "results"
    (out / "reports").mkdir(parents=True, exist_ok=True)
    rows = []
    for case in cases:
        print(f"== {case.name}", flush=True)
        rep = await run_one(case, common)
        s = score(case, rep)
        rows.append((case, rep, s))
        (out / "reports" / (case.name.replace("/", "__") + ".json")).write_text(
            json.dumps({"case": case.name, "expect": case.expect, "carriers": case.carriers, "score": s,
                        "report": rep}, indent=1, ensure_ascii=False, default=str))
        print(table([(case, rep, s)]).split("\n", 2)[2], flush=True)
    if not args.only:
        (out / "results.md").write_text(table(rows) + "\n")
    print(f"\ntotal cost ${sum(s['cost'] for _, _, s in rows):.3f}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--budget", type=float, default=12.0)
    ap.add_argument("--concurrency", type=int, default=10)
    ap.add_argument("--table-only", action="store_true", help="rebuild results.md from saved reports")
    args = ap.parse_args()
    if args.table_only:
        return table_from_reports()
    if "DEEPSEEK_API_KEY" not in os.environ:
        print("error: set DEEPSEEK_API_KEY", file=sys.stderr)
        return 2
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
