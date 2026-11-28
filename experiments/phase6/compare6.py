"""Paired comparison of two engines on the same truth (Phase 6, $0, offline).

Inputs: two ``score.json`` files from ``score6.py --out`` (same tables, same truth;
e.g. the 5.6 engine and the 6.4 engine, both scored on the forced truth). Per case,
F1 is averaged over that engine's seeds; the difference B - A is then averaged over
the cases of each group, with a 95% percentile interval from a paired bootstrap over
cases (seeds stay inside their case, so the interval is about cases, not replays).

    python experiments/phase6/compare6.py <A>/score.json <B>/score.json --names 5.6 6.4
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path


def _f1(r: dict) -> float | None:
    rec, prec = r["recall"], r["precision"]
    if rec is None or prec is None:
        return None
    return 0.0 if rec + prec == 0 else 2 * rec * prec / (rec + prec)


def per_case(rows: list[dict]) -> dict[str, tuple[float, list[str]]]:
    """case -> (F1 averaged over seeds, groups); cases with no F1 (negatives) are left out."""
    acc: dict[str, list[float]] = defaultdict(list)
    groups: dict[str, list[str]] = {}
    for r in rows:
        f = _f1(r)
        if f is None:
            continue
        acc[r["case"]].append(f)
        groups[r["case"]] = (["all", "oracle-valid" if r["oracle_valid"] else "oracle-dropped"]
                             + [f"regime:{g}" for g in r["regimes"]])
    return {c: (sum(v) / len(v), groups[c]) for c, v in acc.items()}


def compare(a_rows: list[dict], b_rows: list[dict], boot: int = 2000, seed: int = 0) -> dict:
    a, b = per_case(a_rows), per_case(b_rows)
    cases = sorted(set(a) & set(b))
    by_group: dict[str, list[str]] = defaultdict(list)
    for c in cases:
        for g in b[c][1]:
            by_group[g].append(c)
    rng = random.Random(seed)
    out = {}
    for g, cs in by_group.items():
        d = [b[c][0] - a[c][0] for c in cs]
        means = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(boot))
        out[g] = {"cases": len(cs), "a": sum(a[c][0] for c in cs) / len(cs), "b": sum(b[c][0] for c in cs) / len(cs),
                  "diff": sum(d) / len(d), "ci": [means[int(0.025 * boot)], means[int(0.975 * boot) - 1]],
                  "better": sum(x > 1e-9 for x in d), "worse": sum(x < -1e-9 for x in d)}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("a", type=Path)
    ap.add_argument("b", type=Path)
    ap.add_argument("--names", nargs=2, default=["A", "B"])
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)
    res = compare(json.loads(args.a.read_text())["rows"], json.loads(args.b.read_text())["rows"], args.boot)
    na, nb = args.names
    print(f"| group | cases | F1 {na} | F1 {nb} | {nb} − {na} [95% CI, cases] | better / worse cases |")
    print("|---|---:|---:|---:|---:|---:|")
    for g in sorted(res, key=lambda g: (g != "all", not g.startswith("oracle"), g)):
        r = res[g]
        print(f"| {g} | {r['cases']} | {r['a']:.0%} | {r['b']:.0%} | {r['diff'] * 100:+.1f} pp "
              f"[{r['ci'][0] * 100:+.1f}, {r['ci'][1] * 100:+.1f}] | {r['better']} / {r['worse']} |")
    if args.out:
        args.out.write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
