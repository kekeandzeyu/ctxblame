"""Score ctxblame reports against coalition-table truth (Phase 6, offline).

Inputs: ``<tables-dir>`` from ``tables.py`` and one or more ``benchmark.json`` from
``benchmark.py --suite phase6`` (one per seed). A reported member is mapped to the
element whose chunks contain it (the chunk itself or one of its lines); a member
outside every element is ``unplanted`` (other context: not judged by the table,
counted apart).

Per case and seed:
  recall      truth carriers (elements in some minimal carrier set) reported as causes
  precision   reported planted cause elements that are truth carriers
  precond     truth precondition elements reported as preconditions, not causes
  probe_fp    a probe the table calls neutral, reported as a cause
  negative    truth "negative": correct when no planted element is reported as a cause
              (unplanted causes are not judged by the table; they are counted in
              ``unplanted``, e.g. a role line the choice really depends on)

Rows are grouped by truth regime; the subset the Phase 3 oracle would have kept
(``oracle_valid``, computed from the table's own cells) is reported apart, so the
numbers can be compared with ``v0.2``.

    uv run python experiments/phase6/score6.py experiments/phase6/results/<tag>/tables \\
        experiments/phase3/results/<bench-tag>/seed*/benchmark.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def oracle_valid(t: dict) -> bool:
    """The Phase 3 oracle's rule, read off the table: reliable base, all carriers off
    flips, each carrier alone restores, a precondition collapses E."""
    cells = {"+".join(c["removed"]): c for c in t["cells"]}
    pg = lambda c: c["k_given"] / c["n"] if c["n"] else 0  # noqa: E731
    pc = lambda c: c["k"] / c["k_given"] if c["k_given"] else None  # noqa: E731
    b = cells[""]
    if pg(b) < 0.8 or (pc(b) or 0) < 0.8:
        return False
    carriers = sorted(e for e, k in t["kinds"].items() if k == "carrier")
    pres = sorted(e for e, k in t["kinds"].items() if k == "precondition")
    if t["category"] == "negative":
        return True  # the table has no "all context" cell; see truth regime instead
    half = 0.5 * pc(b)
    a = cells["+".join(carriers)]
    if pc(a) is None or pc(a) > half or pg(a) < 0.5 * pg(b):
        return False
    if len(carriers) > 1:
        for c in carriers:
            r = cells["+".join(x for x in carriers if x != c)]
            if pc(r) is None or pc(r) < half:
                return False
    if pres and pg(cells["+".join(pres)]) > 0.5 * pg(b):
        return False
    return True


def element_of(mid: str, chunks: dict[str, list[str]]) -> str | None:
    for e, ids in chunks.items():
        if any(mid == i or mid.startswith(i + ".") or i.startswith(mid + ".") for i in ids):
            return e
    return None


def score_case(t: dict, rep: dict) -> dict:
    truth = t["truth"]
    roles = truth["roles"]
    t_car = {e for e, r in roles.items() if r in ("carrier", "triggers_and_steers")}
    t_pre = {e for e, r in roles.items() if r in ("precondition", "triggers_and_steers")}
    cause_ids = [m["id"] for c in rep.get("causes", []) for m in c["members"]]
    pre_ids = [m["id"] for c in rep.get("preconditions", []) for m in c["members"]]
    found = {element_of(m, t["chunks"]) for m in cause_ids}
    unplanted = sum(element_of(m, t["chunks"]) is None for m in cause_ids)
    found.discard(None)
    found_pre = {element_of(m, t["chunks"]) for m in pre_ids} - {None}
    neutral_probes = {e for e, k in t["kinds"].items() if k == "probe" and roles[e] == "neutral"}
    return {
        "recall": len(found & t_car) / len(t_car) if t_car else None,
        "precision": len(found & t_car) / len(found) if found else (None if not t_car else 0.0),
        "precond": len(found_pre & t_pre) / len(t_pre) if t_pre else None,
        "precond_blamed": bool((t_pre - t_car) & found),
        "probe_fp": bool(found & neutral_probes),
        "negative_ok": (not found) if "negative" in truth["regimes"] else None,
        "unplanted": unplanted,
        "coupled_reported": any(c.get("coupled") for c in rep.get("causes", [])),
        "triggers_and_steers_suspected": bool(rep.get("triggers_and_steers_suspected")),
    }


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def f1(r, p):
    return None if r is None or p is None else (0.0 if r + p == 0 else 2 * r * p / (r + p))


def tables_summary(tables: dict[str, dict], wall: float | None = None, suite: int = 250) -> dict:
    """The tables alone (no ctxblame run, e.g. the 6.2 pilot): regimes, ambiguity and
    throughput, with the wall time of a ``suite``-case run at the same rate."""
    ts = list(tables.values())
    replays = sum(t["replays"] for t in ts)
    regimes: dict[str, int] = defaultdict(int)
    for t in ts:
        for g in t["truth"]["regimes"]:
            regimes[g] += 1
    rate = replays / wall if wall else None
    per_case = replays / len(ts) if ts else 0
    return {"cases": len(ts), "replays": replays, "replays_per_case": per_case,
            "cells_per_case": mean(len(t.get("cells") or t.get("forced_cells") or []) for t in ts),
            "ambiguous_cells_per_case": mean(t["truth"]["ambiguous"] for t in ts),
            "oracle_valid": sum(oracle_valid(t) for t in ts if "cells" in t),
            "regimes": dict(sorted(regimes.items())),
            "wall_seconds": wall, "replays_per_second": rate,
            "suite": suite, "suite_hours": per_case * suite / rate / 3600 if rate else None}


def print_tables_summary(s: dict) -> None:
    print(f"{s['cases']} tables, no ctxblame run (tables only)\n")
    print("| cases | replays | replays/case | cells/case | ambiguous cells/case | oracle-valid | "
          "wall | replays/s | est. hours for suite |")
    print("|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    fmt = lambda x, f: "–" if x is None else format(x, f)  # noqa: E731
    print(f"| {s['cases']} | {s['replays']} | {s['replays_per_case']:.0f} | {fmt(s['cells_per_case'], '.1f')} | "
          f"{fmt(s['ambiguous_cells_per_case'], '.1f')} | {s['oracle_valid']}/{s['cases']} | "
          f"{fmt(s['wall_seconds'], '.0f')}s | {fmt(s['replays_per_second'], '.1f')} | "
          f"{fmt(s['suite_hours'], '.1f')} ({s['suite']} cases) |")
    print("\n| regime | cases |\n|---|---:|")
    for g, n in s["regimes"].items():
        print(f"| {g} | {n} |")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("tables", type=Path)
    ap.add_argument("bench", type=Path, nargs="*", help="none: summarize the tables only")
    ap.add_argument("--method", default="ctxblame")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--wall-seconds", type=float, default=None, help="tables-only: wall time of tables.py")
    ap.add_argument("--suite", type=int, default=250, help="tables-only: suite size to estimate the run time for")
    ap.add_argument("--forced", type=Path, default=None,
                    help="6.4: a forced/ dir from tables.py --forced; its cases are scored on the truth "
                         "recomputed with E forced")
    a = ap.parse_args(argv)
    tables = {json.loads(p.read_text())["case"]: json.loads(p.read_text()) for p in a.tables.glob("*.json")}
    if a.forced:
        for p in a.forced.glob("*.json"):
            f = json.loads(p.read_text())
            if f["case"] in tables:
                tables[f["case"]] = {**tables[f["case"]], "truth": f["truth"], "forced_truth": True}
    if not a.bench:
        if not tables:
            print(f"no tables in {a.tables}")
            return 1
        s = tables_summary(tables, a.wall_seconds, a.suite)
        print_tables_summary(s)
        if a.out:
            a.out.write_text(json.dumps({"tables_summary": s}, indent=1))
        return 0
    rows = []
    for bp in a.bench:
        for r in json.loads(bp.read_text()):
            if r["method"] != a.method or r["case"] not in tables:
                continue
            t = tables[r["case"]]
            s = score_case(t, r["report"])
            rows.append({"case": r["case"], "seed": bp.parent.name, "design": t["design"],
                         "regimes": t["truth"]["regimes"], "oracle_valid": oracle_valid(t), **s})
    if not rows:
        print("no scored rows (case names must match the tables)")
        return 1
    groups: dict[str, list] = defaultdict(list)
    for r in rows:
        groups["all"].append(r)
        groups["oracle-valid" if r["oracle_valid"] else "oracle-dropped"].append(r)
        for g in r["regimes"]:
            groups[f"regime:{g}"].append(r)
    print(f"{len(rows)} case x seed rows, {len({r['case'] for r in rows})} cases\n")
    print("| group | rows | recall | precision | F1 | precond. separated | precond. blamed | "
          "neutral probe blamed | negatives correct | unplanted members |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    pct = lambda x: "–" if x is None else f"{x:.0%}"  # noqa: E731
    summary = {}
    for g in sorted(groups, key=lambda g: (g != "all", not g.startswith("oracle"), g)):
        rs = groups[g]
        rec, prec = mean(r["recall"] for r in rs), mean(r["precision"] for r in rs)
        row = {"rows": len(rs), "recall": rec, "precision": prec, "f1": mean(f1(r["recall"], r["precision"])
                                                                            for r in rs),
               "precond": mean(r["precond"] for r in rs), "precond_blamed": mean(r["precond_blamed"] for r in rs),
               "probe_fp": mean(r["probe_fp"] for r in rs), "negative_ok": mean(r["negative_ok"] for r in rs),
               "unplanted": mean(r["unplanted"] for r in rs)}
        summary[g] = row
        print(f"| {g} | {len(rs)} | {pct(rec)} | {pct(prec)} | {pct(row['f1'])} | {pct(row['precond'])} | "
              f"{pct(row['precond_blamed'])} | {pct(row['probe_fp'])} | {pct(row['negative_ok'])} | "
              f"{row['unplanted']:.2f} |")
    if a.out:
        a.out.write_text(json.dumps({"summary": summary, "rows": rows}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
