"""Exhaustive coalition tables (Phase 6.1): every removal of a case's planted elements.

For each case (``cases6.py``) and each of the 2^m subsets S of its m <= 5 elements,
the request without S is replayed a fixed N times (default 50; no adaptive
stopping, the same N for every cell), and the cell records how many replays came
back, how many were in the action family E (the case's ``--given``), and how many
of those made the recorded choice A. ``truth.label`` turns the table into the
case's ground truth. E is resolved from the N base replays exactly as ctxblame
resolves ``--given``.

Every request of a case is independent, so all cells are in flight together
(bounded by ``--concurrency``): this is a throughput job, unlike the sequential
search. One JSON per case in ``<out>/tables/``; finished cases are skipped, so a
run can be restarted.

    python experiments/phase6/tables.py --model Qwen3-14B --free -n 50 --limit 10 \\
        --extra-body '{"chat_template_kwargs": {"enable_thinking": false}, "temperature": 0.7, "top_p": 0.8, "top_k": 20}' \\
        --out experiments/phase6/results/pilot-qwen3-14b
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "phase3"))

from ctxblame.ablate import AblationError  # noqa: E402
from ctxblame.blame import apply_chunks, chunk_request, force_tool_choice, resolve_given  # noqa: E402
from ctxblame.match import Matcher  # noqa: E402
from ctxblame.formats import extract_decision  # noqa: E402
from ctxblame.pricing import Ledger  # noqa: E402
from ctxblame.replay import (Replayer, build_headers, estimate_cost, parse_extra_body,  # noqa: E402
                             resolve_api_key, sample_decision, with_model_override)
from ctxblame.trace import matcher_for  # noqa: E402

from cases6 import TableCase, phase6_cases  # noqa: E402
from oracle import carrier_chunks  # noqa: E402
from truth import Cell, label  # noqa: E402


def _arg(argv: list[str], flag: str) -> str | None:
    return argv[argv.index(flag) + 1] if flag in argv else None


def resolve_elements(tc: TableCase, chunks) -> dict[str, list]:
    """Element -> the chunks removed for it; refuses a case whose elements overlap or are missing."""
    out = {e: carrier_chunks(chunks, spec) for e, spec in tc.elements.items()}
    missing = [e for e, cs in out.items() if not cs]
    if missing:
        raise ValueError(f"{tc.name}: elements not found in chunks: {missing}")
    ids = [c.id for cs in out.values() for c in cs]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{tc.name}: elements overlap")
    return out


def subsets(elements: list[str]) -> list[frozenset]:
    return [frozenset(c) for r in range(len(elements) + 1) for c in combinations(elements, r)]


def count(samples, matcher, given, gtarget: str, target: str) -> dict:
    ok = [s for s in samples if s.ok]
    in_e = [s for s in ok if (given.same(sample_decision(s), gtarget) if given else True)]
    k = sum(matcher.same(None, target, s.key, s.keys or [s.key]) for s in in_e)
    return {"n": len(ok), "k_given": len(in_e), "k": k, "errors": len(samples) - len(ok),
            "dist": _dist(ok)}


def _dist(ok) -> list:
    from collections import Counter
    return Counter(x for s in ok for x in set(s.keys or [s.key])).most_common(3)


async def table(tc: TableCase, args, rp: Replayer) -> dict:
    case = tc.case
    step = with_model_override(case.step, args.model, args.max_tokens, args.no_thinking_param, args.extra_body)
    fmt = step.fmt
    key_args = [case.argv[i + 1] for i, a in enumerate(case.argv) if a == "--key-arg"]
    matcher = matcher_for(step, "args" if key_args else "intent", key_args or None, any_call=True)
    target = _arg(case.argv, "--target") or matcher.key(extract_decision(fmt, step.response))
    chunks = chunk_request(fmt, step.body, case.protect)
    el = resolve_elements(tc, chunks)
    names = list(tc.elements)
    t0 = time.time()
    base = await rp.run(step.body, args.n, matcher)
    given, gtarget = resolve_given(_arg(case.argv, "--given"), key_args, target, matcher, base,
                                   extract_decision(fmt, step.response), matcher.cwd)
    gtarget = gtarget or ""

    async def cell(s: frozenset) -> tuple[frozenset, dict]:
        if not s:
            return s, count(base, matcher, given, gtarget, target)
        try:
            body = apply_chunks(fmt, step.body, [c for e in s for c in el[e]])
        except AblationError as e:
            return s, {"n": 0, "k_given": 0, "k": 0, "errors": 0, "ablation_error": str(e)}
        return s, count(await rp.run(body, args.n, matcher), matcher, given, gtarget, target)

    rows = dict(await asyncio.gather(*(cell(s) for s in subsets(names))))
    cells = {s: Cell(s, r["n"], r["k_given"], r["k"]) for s, r in rows.items()}
    truth = label(names, tc.kinds, cells)
    return {"case": tc.name, "design": tc.design, "category": case.category, "target": target,
            "given": gtarget or None, "n": args.n, "elements": tc.elements, "kinds": tc.kinds,
            "chunks": {e: [c.id for c in cs] for e, cs in el.items()},
            "cells": [{"removed": sorted(s), **rows[s]} for s in subsets(names)],
            "truth": truth.to_json(), "seconds": round(time.time() - t0, 1),
            "replays": sum(r["n"] + r["errors"] for r in rows.values())}


async def forced_table(tc: TableCase, args, rp: Replayer, base: dict) -> dict:
    """6.4: every removal of ``base`` (a finished table of this case) again, with E
    forced by tool_choice; the case's truth is recomputed from both tables."""
    case = tc.case
    step = with_model_override(case.step, args.model, args.max_tokens, args.no_thinking_param, args.extra_body)
    fmt = step.fmt
    key_args = [case.argv[i + 1] for i, a in enumerate(case.argv) if a == "--key-arg"]
    matcher = matcher_for(step, "args" if key_args else "intent", key_args or None, any_call=True)
    target, tool = base["target"], base["given"]
    given = Matcher("name", any_call=True)
    el = resolve_elements(tc, chunk_request(fmt, step.body, case.protect))
    names = list(tc.elements)
    t0 = time.time()

    async def cell(s: frozenset) -> tuple[frozenset, dict]:
        try:
            body = apply_chunks(fmt, step.body, [c for e in s for c in el[e]]) if s else step.body
        except AblationError as e:
            return s, {"n": 0, "k_given": 0, "k": 0, "errors": 0, "ablation_error": str(e)}
        return s, count(await rp.run(force_tool_choice(fmt, body, tool), args.n, matcher), matcher, given, tool,
                        target)

    rows = dict(await asyncio.gather(*(cell(s) for s in subsets(names))))
    unforced = {frozenset(c["removed"]): Cell(frozenset(c["removed"]), c["n"], c["k_given"], c["k"])
                for c in base["cells"]}
    forced = {s: Cell(s, r["n"], r["k_given"], r["k"]) for s, r in rows.items()}
    truth = label(names, tc.kinds, unforced, forced=forced)
    return {"case": tc.name, "design": tc.design, "target": target, "given": tool, "n": args.n,
            "forced_cells": [{"removed": sorted(s), **rows[s]} for s in subsets(names)],
            "truth": truth.to_json(), "unforced_truth": base["truth"], "seconds": round(time.time() - t0, 1),
            "replays": sum(r["n"] + r["errors"] for r in rows.values())}


def needs_forcing(base: dict) -> bool:
    """A case whose unforced truth has a precondition set: only there can forcing
    change a role (an element whose removal collapses E may also steer)."""
    return bool(base["truth"]["precondition_sets"])


def _fname(name: str) -> str:
    return name.replace("/", "__") + ".json"


async def main_async(args) -> int:
    cases = phase6_cases(args.cases, args.seed)
    if args.only:
        cases = [c for c in cases if any(o in c.name or o == c.design for o in args.only)]
    if args.limit:
        cases = cases[:args.limit]
    bases: dict[str, dict] = {}
    if args.forced:  # forced cells next to finished tables, in a new results dir
        bases = {c.name: json.loads((args.base_tables / _fname(c.name)).read_text()) for c in cases
                 if (args.base_tables / _fname(c.name)).exists()}
        cases = [c for c in cases if c.name in bases and (args.forced_all or needs_forcing(bases[c.name]))]
    out = args.out / ("forced" if args.forced else "tables")
    out.mkdir(parents=True, exist_ok=True)
    todo = [c for c in cases if not (out / _fname(c.name)).exists()]
    print(f"{len(cases)} cases, {len(cases) - len(todo)} done, {len(todo)} to run", flush=True)
    api_key, _ = resolve_api_key("openai", args.base_url, None, free=args.free)
    base = args.base_url.rstrip("/")
    ex = todo[0].case.step if todo else None
    rp = Replayer(ex.fmt, base + ex.record["request"]["path"],
                  build_headers(ex.fmt, ex.record["request"].get("headers"), api_key or ""),
                  Ledger(args.ledger, args.budget), base, estimate_cost(ex, base, free=args.free),
                  args.concurrency, free=args.free) if ex else None
    sem = asyncio.Semaphore(args.parallel_cases)
    t0, done = time.time(), 0

    async def one(tc: TableCase):
        nonlocal done
        async with sem:
            try:
                r = await (forced_table(tc, args, rp, bases[tc.name]) if args.forced else table(tc, args, rp))
            except Exception as e:  # noqa: BLE001 - one bad case must not stop the suite
                print(f"ERROR {tc.name}: {type(e).__name__}: {e}", flush=True)
                return
            (out / _fname(tc.name)).write_text(json.dumps(r, indent=1, default=str))
            done += 1
            t = r["truth"]
            rate = r["replays"] / max(r["seconds"], 1e-9)
            print(f"done {tc.name:48s} m={len(tc.elements)} regimes={','.join(t['regimes'])} "
                  f"carriers={t['carrier_sets']} pre={t['precondition_sets']} amb={t['ambiguous']} "
                  f"{r['replays']} replays {r['seconds']}s ({rate:.1f}/s) "
                  f"[{done}/{len(todo)}, {time.time() - t0:.0f}s]", flush=True)

    await asyncio.gather(*(one(c) for c in todo))
    print(f"finished {done}/{len(todo)} in {time.time() - t0:.0f}s", flush=True)
    return 0 if done == len(todo) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Exhaustive coalition tables (Phase 6.1)")
    ap.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--no-thinking-param", action="store_true")
    ap.add_argument("--extra-body", type=parse_extra_body, default={})
    ap.add_argument("--free", action="store_true")
    ap.add_argument("-n", type=int, default=50)
    ap.add_argument("--cases", type=int, default=250, help="suite size (cases6.phase6_cases)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0, help="run only the first N cases (pilot)")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--concurrency", type=int, default=128, help="requests in flight, all cases together")
    ap.add_argument("--parallel-cases", type=int, default=4)
    ap.add_argument("--budget", type=float, default=5.0)
    ap.add_argument("--ledger", type=Path, default=REPO / ".ctxblame" / "phase6_spend.jsonl")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--forced", action="store_true",
                    help="6.4: replay every removal with E forced by tool_choice, for the cases of "
                         "--base-tables whose truth has a precondition set; writes <out>/forced/")
    ap.add_argument("--base-tables", type=Path, default=None, help="--forced: the finished tables/ dir")
    ap.add_argument("--forced-all", action="store_true", help="--forced: every tabled case, not only gated ones")
    a = ap.parse_args(argv)
    if a.forced and a.base_tables is None:
        ap.error("--forced needs --base-tables")
    return asyncio.run(main_async(a))


if __name__ == "__main__":
    sys.exit(main())
