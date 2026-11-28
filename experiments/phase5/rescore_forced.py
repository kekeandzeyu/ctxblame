"""Rescore a v0.2-case run with the forced causes set aside (6.4, $0, offline).

The v0.2 oracle labels each planted precondition as a pure precondition: it has no
forced truth. A 6.4 engine that reports "with E forced, removing X flips the
choice" (``Cause.forced``) therefore scores as "precondition blamed as cause" there,
whether or not X really steers. This writes ``<run>/forced_set_aside/seed*/
benchmark.json`` with the forced causes removed from each report (and re-scored
with ``benchmark.score_report``), so ``analyze.py`` gives the like-for-like v0.2
number, and lists every forced claim with its planted label and what the forced
replies did instead.

    uv run python experiments/phase5/rescore_forced.py experiments/phase3/results/p64-gen-qwen3-14b
    uv run --with numpy python experiments/phase3/analyze.py experiments/phase3/results/p64-gen-qwen3-14b/forced_set_aside
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "experiments" / "phase3"))

from benchmark import is_carrier, score_report  # noqa: E402
from cases import all_cases  # noqa: E402


def label_of(member: dict, case) -> str:
    if is_carrier(member, case.carriers):
        return "carrier"
    if case.preconditions and is_carrier(member, case.preconditions):
        return "precondition"
    return "other"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("run", type=Path)
    ap.add_argument("--suite", default="all")
    ap.add_argument("--gen-n", type=int, default=64)
    args = ap.parse_args(argv)
    cases = {c.name: c for c in all_cases(args.suite, args.gen_n) + all_cases("real")}
    out = args.run / "forced_set_aside"
    claims = []
    for bp in sorted(args.run.glob("seed*/benchmark.json")):
        rows = []
        for r in json.loads(bp.read_text()):
            if r["method"] == "ctxblame" and r["case"] in cases:
                rep, case = r["report"], cases[r["case"]]
                forced = [c for c in rep.get("causes") or [] if c.get("forced")]
                for c in forced:
                    claims.append({"seed": bp.parent.name, "case": r["case"],
                                   "members": [label_of(m, case) for m in c["members"]],
                                   "instead": (c.get("together") or {}).get("dist") or []})
                if forced:
                    kept = [c for c in rep["causes"] if not c.get("forced")]
                    rep = {**rep, "causes": kept}
                    if not kept and rep.get("result") == "causes":
                        rep["result"] = "preconditions_only" if rep.get("preconditions") else "none_found"
                    r = {**r, "report": rep, "score": score_report(case, rep)}
            rows.append(r)
        d = out / bp.parent.name
        d.mkdir(parents=True, exist_ok=True)
        (d / "benchmark.json").write_text(json.dumps(rows, indent=1, default=str))
    (out / "forced_claims.json").write_text(json.dumps(claims, indent=1))
    by = {}
    for c in claims:
        k = "+".join(sorted(set(c["members"])))
        by.setdefault(k, []).append(c)
    print(f"{len(claims)} forced causes over {len({(c['seed'], c['case']) for c in claims})} case x seed rows")
    for k, cs in sorted(by.items()):
        eg = cs[0]
        print(f"  {k}: {len(cs)} (e.g. {eg['case']} {eg['seed']}: instead {eg['instead'][:2]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
