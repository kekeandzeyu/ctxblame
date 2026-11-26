"""Aggregate Phase 3 benchmark runs (all seeds of one model) into summary tables.

    python experiments/phase3/analyze.py experiments/phase3/results/qwen3-8b

Reads ``<dir>/seed*/benchmark.json`` and writes ``<dir>/summary.md`` with:
  - per method: recall, precision, F1, precondition separation, negative-control
    accuracy, replays and wall time (mean over case x seed, 95% bootstrap CI
    over cases for F1)
  - F1 per case category, recall per carrier kind (system / tooldesc / doc /
    user / history), and recall by redundancy (number of carriers)
"""

from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from benchmark import is_carrier  # noqa: E402
from cases import all_cases  # noqa: E402
from gen_cases import FAMILIES  # noqa: E402

KINDS = ("system", "tooldesc", "doc", "user", "history")


def carrier_kind(case_name: str, carrier: str) -> str | None:
    if not case_name.startswith("gen"):
        return None
    fam = next(f for f in FAMILIES if f"/{f.name}/" in case_name)
    if carrier.startswith("pair:"):
        return "history"
    if carrier == fam.rule:
        return "system"
    if carrier.startswith("e.g."):
        return "tooldesc"
    if carrier == fam.doc:
        return "doc"
    if carrier == fam.user:
        return "user"
    return None


def _lcp(a: str, b: str) -> int:
    n = min(len(a), len(b))
    lo, hi = 0, n  # binary search on prefix equality (fast for long strings)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if a[:mid] == b[:mid]:
            lo = mid
        else:
            hi = mid - 1
    return lo


def simulated_cache(case, rep: dict) -> tuple[int, int] | None:
    """(uncached chars, total chars) a per-run provider prefix cache would bill for the
    distinct request bodies of this run, in test order (each body's first send; repeats
    of a body are fully cached). Independent of what else shared the vLLM server."""
    from ctxblame.ablate import AblationError
    from ctxblame.blame import apply_chunks, chunk_request
    tests = rep.get("tests")
    if not tests:
        return None
    step = case.step
    by_id = {}
    for c in chunk_request(step.fmt, step.body, case.protect):
        by_id[c.id] = c
        for k in c.children:
            by_id[k.id] = k

    def text(body: dict) -> str:  # prompt order: tools, then system/messages
        return json.dumps(body.get("tools"), sort_keys=True) + json.dumps(body.get("system")) + \
            json.dumps(body.get("messages"))

    sent = [text(step.body)]
    unc, tot = len(sent[0]), len(sent[0])
    seen = {frozenset()}
    for t in tests:
        key = frozenset(t["removed"])
        if key in seen:
            continue
        seen.add(key)
        try:
            b = apply_chunks(step.fmt, step.body, [by_id[i] for i in key if i in by_id])
        except AblationError:
            continue
        s = text(b)
        unc += len(s) - max(_lcp(s, p) for p in sent)
        tot += len(s)
        sent.append(s)
    return unc, tot


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def boot_ci(per_case: dict[str, list[float]], n: int = 2000, seed: int = 0):
    """95% CI of the mean over cases (resampling cases; each case = mean over its seeds)."""
    vals = [mean(v) for v in per_case.values() if mean(v) is not None]
    if len(vals) < 2:
        return None
    rng = random.Random(seed)
    ms = sorted(sum(rng.choice(vals) for _ in vals) / len(vals) for _ in range(n))
    return ms[int(0.025 * n)], ms[int(0.975 * n) - 1]


def pct(v) -> str:
    return "-" if v is None else f"{v:.0%}"


def main(argv=None) -> int:
    d = Path((argv or sys.argv[1:])[0])
    rows = []
    for f in sorted(d.glob("seed*/benchmark.json")) + sorted(d.glob("seed*/*/benchmark.json")):
        seed = f.relative_to(d).parts[0]  # seedN/<extra methods>/benchmark.json merges into seedN
        for r in json.loads(f.read_text()):
            r["seed"] = seed
            rows.append(r)
    if not rows:
        print(f"no seed*/benchmark.json under {d}")
        return 1
    cases = {c.name: c for c in all_cases("all") + all_cases("gen-open") + all_cases("gen-long") + all_cases("real")}
    methods = list(dict.fromkeys(r["method"] for r in rows))
    seeds = sorted({r["seed"] for r in rows})

    # per-carrier hits (recomputed from the reported members)
    kind_hits = defaultdict(lambda: defaultdict(list))  # method -> kind -> [0/1]
    k_hits = defaultdict(lambda: defaultdict(list))  # method -> n carriers -> [recall]
    for r in rows:
        case = cases.get(r["case"])
        if not case or not case.carriers:
            continue
        rep = r["report"]
        members = [m for c in rep.get("causes") or [] if c.get("specific") is not False for m in c["members"]]
        for car in case.carriers:
            kind = carrier_kind(case.name, car)
            if kind:
                kind_hits[r["method"]][kind].append(1.0 if any(is_carrier(m, [car]) for m in members) else 0.0)
        if r["score"]["recall"] is not None:
            k_hits[r["method"]][len(case.carriers)].append(r["score"]["recall"])

    sim = {}
    for r in rows:
        case = cases.get(r["case"])
        if case is not None and (r["method"].startswith("ctxblame") or r["method"] == "loo"):
            v = simulated_cache(case, r["report"]) if case is not None else None
            if v:
                sim[(r["case"], r["seed"], r["method"])] = v

    out = [f"# Phase 3 benchmark summary: `{d.name}`", "",
           f"{len({r['case'] for r in rows})} oracle-valid cases x {len(seeds)} seed(s) ({', '.join(seeds)}). "
           "Means over case x seed; F1 CI = 95% bootstrap over cases. "
           "Sim. uncached chars = what a per-run provider prefix cache would bill once per distinct "
           "request body (live vLLM hit rates are shared across concurrent runs, so not comparable).", "",
           "| Method | Recall | Precision | F1 [95% CI] | Precond. separated | Precond. blamed as cause | "
           "Negatives correct | Replays/case | Distinct requests/case | Sim. uncached chars/case | Secs/case |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for m in methods:
        ms = [r for r in rows if r["method"] == m]
        sc = [r["score"] for r in ms]
        f1_case = defaultdict(list)
        for r in ms:
            if r["score"]["f1"] is not None:
                f1_case[r["case"]].append(r["score"]["f1"])
        ci = boot_ci(f1_case)
        pre = [s for s in sc if s["precond_found"] is not None]
        neg = [s for s in sc if s["neg_correct"] is not None]
        out.append(
            f"| {m} | {pct(mean([s['recall'] for s in sc]))} | "
            f"{pct(mean([s['precision'] for s in sc if s['neg_correct'] is None]))} | "
            f"{pct(mean([s['f1'] for s in sc]))}" + (f" [{ci[0]:.0%}, {ci[1]:.0%}]" if ci else "") + " | "
            f"{pct(mean([1.0 if s['precond_found'] and not s['precond_fp'] else 0.0 for s in pre]))} | "
            f"{pct(mean([1.0 if s['precond_fp'] else 0.0 for s in pre]))} | "
            f"{pct(mean([1.0 if s['neg_correct'] else 0.0 for s in neg]))} | "
            f"{mean([s['replays'] for s in sc]) or 0:.0f} | "
            f"{mean([len({frozenset(t['removed']) for t in r['report'].get('tests') or []}) for r in ms]) or 0:.0f} | "
            f"{mean([sim[(r['case'], r['seed'], m)][0] for r in ms if (r['case'], r['seed'], m) in sim]) or 0:,.0f} | "
            f"{mean([s['seconds'] for s in sc]) or 0:.0f} |")

    cats = list(dict.fromkeys(r["category"] for r in rows))
    out += ["", "## F1 by case category (negatives: share correct)", "",
            "| Method | " + " | ".join(f"{c} (n={len({r['case'] for r in rows if r['category'] == c})})"
                                     for c in cats) + " |",
            "|---|" + "---:|" * len(cats)]
    for m in methods:
        cells = []
        for c in cats:
            sc = [r["score"] for r in rows if r["method"] == m and r["category"] == c]
            v = mean([1.0 if s["neg_correct"] else 0.0 for s in sc]) if c == "negative" else mean(
                [s["f1"] for s in sc])
            cells.append(pct(v))
        out.append(f"| {m} | " + " | ".join(cells) + " |")

    out += ["", "## Recall by carrier kind (generated cases)", "",
            "| Method | " + " | ".join(KINDS) + " |", "|---|" + "---:|" * len(KINDS)]
    for m in methods:
        out.append(f"| {m} | " + " | ".join(
            f"{pct(mean(kind_hits[m][k]))} (n={len(kind_hits[m][k])})" for k in KINDS) + " |")

    ks = sorted({k for m in methods for k in k_hits[m]})
    out += ["", "## Recall by redundancy (number of planted carriers)", "",
            "| Method | " + " | ".join(f"{k} carrier{'s' if k > 1 else ''}" for k in ks) + " |",
            "|---|" + "---:|" * len(ks)]
    for m in methods:
        out.append(f"| {m} | " + " | ".join(pct(mean(k_hits[m][k])) for k in ks) + " |")

    text = "\n".join(out) + "\n"
    (d / "summary.md").write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
