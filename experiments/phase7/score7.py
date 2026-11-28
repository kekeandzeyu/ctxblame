"""Phase 7.1: score the baselines and ctxblame on the Phase 6 truth (offline, $0).

    uv run python experiments/phase7/score7.py \\
        --tables experiments/phase6/results/qwen3-14b/tables \\
        --forced experiments/phase6/results/p64c-qwen3-14b/forced \\
        --ctxblame experiments/phase6/results/p64c-qwen3-14b/seed*/benchmark.json \\
        experiments/phase7/results/p71-qwen3-14b/seed*  > .../summary.md

Every method is scored by ``score6.score_case`` on the same truth (E forced where
6.4 measured it). Sections:

  1. the best design of each estimator at each budget M (best by F1 over all cases,
     i.e. tuned on the test cases: this favours the baselines), next to ctxblame
  2. ctxblame minus the best baseline at each M, paired over cases (95% bootstrap CI)
  3. every method
  4. the gate: share of design rows still in E, by keep-probability q and number m of
     necessary precondition elements (removing one alone collapses E), next to q^m
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "phase6"))

from compare6 import compare  # noqa: E402
from score6 import group_rows, load_tables, mean, score_rows, summarize  # noqa: E402

GROUPS = ("all", "oracle-valid", "oracle-dropped", "regime:single", "regime:or", "regime:and",
          "regime:precondition_gated", "regime:e_coupled")


def pct(x) -> str:
    return "–" if x is None else f"{x:.0%}"


def method_budget(m: str) -> int | None:
    x = re.search(r":M(\d+)$", m)
    return int(x.group(1)) if x else None


def family(m: str) -> str:
    """'banzhaf:q0.5:M64' -> 'banzhaf'; 'cc:M64' -> 'cc'."""
    return m.split(":", 1)[0]


def score_all(tables: dict, bench: list[tuple[str, list[dict]]]) -> dict[str, list[dict]]:
    methods = sorted({r["method"] for _, rs in bench for r in rs})
    return {m: score_rows(tables, bench, m) for m in methods}


def best_by_budget(summaries: dict[str, dict]) -> dict[tuple[str, int], str]:
    """(estimator, M) -> the method (design) with the highest F1 over all cases."""
    best: dict[tuple[str, int], str] = {}
    for m, s in summaries.items():
        b = method_budget(m)
        if b is None:
            continue
        k = (family(m), b)
        f = s["all"]["f1"] or 0
        if k not in best or f > (summaries[best[k]]["all"]["f1"] or 0):
            best[k] = m
    return best


def gate_table(raw_dirs: list[Path], tables: dict) -> dict:
    """(q, m) -> [share of non-base design rows in E] over cases, unforced designs only."""
    acc: dict[tuple[float, int], list[float]] = defaultdict(list)
    for d in raw_dirs:
        for p in (d / "raw").glob("*.json"):
            raw = json.loads(p.read_text())
            t = tables.get(raw["case"])
            if t is None:
                continue
            m = sum(len(s) == 1 for s in t["truth"]["precondition_sets"])  # necessary preconditions
            for v in raw["designs"].values():
                if "rows" not in v or v["forced"]:
                    continue
                rows = [r for r in v["rows"][raw.get("base", 0):] if r[1]]
                if rows:
                    acc[(v["q"], m)].append(sum(r[2] for r in rows) / len(rows))
    return acc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("seed_dirs", type=Path, nargs="+", help="baseline seed dirs (benchmark.json from estimate.py)")
    ap.add_argument("--tables", type=Path, required=True)
    ap.add_argument("--forced", type=Path, default=None)
    ap.add_argument("--ctxblame", type=Path, nargs="*", default=[], help="ctxblame benchmark.json files (6.4 run)")
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)
    tables = load_tables(a.tables, a.forced)
    bench = [(d.name, json.loads((d / "benchmark.json").read_text())) for d in a.seed_dirs]
    scored = score_all(tables, bench)
    cases = {r["case"] for rs in scored.values() for r in rs}  # every method on the baselines' cases
    if a.ctxblame:
        scored["ctxblame"] = [r for r in score_rows(tables, [(p.parent.name, json.loads(p.read_text()))
                                                             for p in a.ctxblame], "ctxblame") if r["case"] in cases]
    scored = {m: rs for m, rs in scored.items() if rs}
    summ = {m: {g: summarize(rs) for g, rs in group_rows(rows).items()} for m, rows in scored.items()}
    best = best_by_budget(summ)
    n_cases = len(cases)
    print(f"# Phase 7.1 baselines\n\n{n_cases} cases; seeds: {', '.join(d.name for d in a.seed_dirs)}"
          + (f"; ctxblame: {len(a.ctxblame)} seeds" if a.ctxblame else "") + "\n")

    cols = ["all"] + [g for g in GROUPS[1:]]
    head = ("| method | replays | " + " | ".join(f"F1 {g.replace('regime:', '')}" for g in cols)
            + " | negatives correct | precond. separated | precond. blamed | neutral probe blamed |")
    sep = "|---|---:|" + "---:|" * (len(cols) + 4)

    def line(name: str, m: str) -> str:
        s = summ[m]
        f = lambda g: pct((s.get(g) or {}).get("f1"))  # noqa: E731
        rep = mean(r.get("replays") for r in scored[m])
        al = s["all"]
        return (f"| {name} | {'–' if rep is None else f'{rep:.0f}'} | " + " | ".join(f(g) for g in cols)
                + f" | {pct(al['negative_ok'])} | {pct(al['precond'])} | {pct(al['precond_blamed'])} | "
                  f"{pct(al['probe_fp'])} |")

    print("## 1. Best design per estimator and budget (tuned on these cases)\n")
    print("`replays`: mean per case (ContextCite: prefills, scored with log-probabilities instead of sampled).\n")
    print(head + "\n" + sep)
    if "ctxblame" in summ:
        print(line("**ctxblame** (adaptive)", "ctxblame"))
    for (est, b), m in sorted(best.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        print(line(f"{est} @ M={b} (`{m.split(':')[1] if est != 'cc' else 'q0.5'}`)", m))
    if "self_explain_full" in summ:
        print(line("self_explain_full", "self_explain_full"))

    out: dict = {"summary": summ, "best": {f"{e}@{b}": m for (e, b), m in best.items()}}
    if "ctxblame" in scored:
        print("\n## 2. ctxblame minus the best baseline at each budget (paired over cases)\n")
        print("| budget M | best baseline | group | cases | F1 baseline | F1 ctxblame | ctxblame − baseline [95% CI] |")
        print("|---:|---|---|---:|---:|---:|---:|")
        out["paired"] = {}
        for b in sorted({b for _, b in best}):
            cand = [m for (e, bb), m in best.items() if bb == b]
            top = max(cand, key=lambda m: summ[m]["all"]["f1"] or 0)
            res = compare(scored[top], scored["ctxblame"], a.boot)
            out["paired"][str(b)] = {"baseline": top, **res}
            for g in ("all", "oracle-valid", "oracle-dropped", "regime:e_coupled", "regime:or"):
                if g in res:
                    r = res[g]
                    print(f"| {b} | `{top}` | {g} | {r['cases']} | {r['a']:.0%} | {r['b']:.0%} | "
                          f"{r['diff'] * 100:+.1f} pp [{r['ci'][0] * 100:+.1f}, {r['ci'][1] * 100:+.1f}] |")

    print("\n## 3. Every method\n")
    print(head + "\n" + sep)
    for m in sorted(summ, key=lambda m: (m != "ctxblame", method_budget(m) or 0, m)):
        print(line(f"`{m}`", m))

    gate = gate_table(a.seed_dirs, tables)
    if gate:
        print("\n## 4. The gate: share of design rows in E, by keep-probability q and necessary preconditions m\n")
        ms = sorted({m for _, m in gate})
        print("| q | " + " | ".join(f"m={m} (cases·seeds)" for m in ms) + " |")
        print("|---:|" + "---:|" * len(ms))
        for q in sorted({q for q, _ in gate}):
            cells = []
            for m in ms:
                v = gate.get((q, m))
                cells.append("–" if not v else f"{mean(v):.2f} (q^m={q ** m:.2f}, n={len(v)})")
            print(f"| {q} | " + " | ".join(cells) + " |")
        out["gate"] = {f"{q}:{m}": v for (q, m), v in gate.items()}
    if a.out:
        a.out.write_text(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
