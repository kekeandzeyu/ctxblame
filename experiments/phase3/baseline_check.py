"""Baseline stability check for the Phase 3 benchmark cases on a new model.

Before running blame, every case must show its target decision reliably on the
model under test; otherwise the benchmark measures noise. This replays each
case's request N times unchanged and reports, per case:

  target   how often the case's target decision comes back (what blame explains)
  given    how often the action family E comes back (the ``--given`` matcher)
  top      the most common decisions

    python experiments/phase3/baseline_check.py --base-url http://127.0.0.1:8000/v1 \\
        --model Qwen/Qwen3-8B --free -n 20 \\
        --extra-body '{"chat_template_kwargs": {"enable_thinking": false}}'
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import Counter
from pathlib import Path

from ctxblame import blame
from ctxblame.formats import extract_decision
from ctxblame.match import intent
from ctxblame.pricing import Ledger
from ctxblame.replay import (Replayer, build_headers, estimate_cost, parse_extra_body, resolve_api_key,
                             sample_decision, summarize, wilson, with_model_override)
from ctxblame.trace import matcher_for

HERE = Path(__file__).parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
from cases import all_cases  # noqa: E402


async def check(case, args, api_key: str) -> dict:
    ap = argparse.ArgumentParser()
    blame.add_args(ap)
    bargs = ap.parse_args([f"{case.name}.json", *case.argv])
    step = with_model_override(case.step, args.model, args.max_tokens, args.no_thinking_param, args.extra_body)
    mode = bargs.match or ("args" if bargs.key_arg else "intent")
    matcher = matcher_for(step, mode, bargs.key_arg or None, any_call=not bargs.first_call)
    recorded_dec = extract_decision(step.fmt, step.response)
    target = bargs.target or matcher.key(recorded_dec)
    base = args.base_url.rstrip("/")
    rec = step.record["request"]
    ledger = Ledger(args.ledger, args.budget)
    rp = Replayer(step.fmt, base + rec["path"], build_headers(step.fmt, rec.get("headers"), api_key), ledger,
                  base, estimate_cost(step, base, free=args.free), args.concurrency, free=args.free)
    samples = await rp.run(step.body, args.n, matcher)
    summ = summarize(samples, target, matcher)
    ok = [s for s in samples if s.ok]
    k = sum(matcher.same(None, target, s.key, s.keys or [s.key]) for s in ok)
    gm, gt = blame.resolve_given(bargs.given, bargs.key_arg, target, matcher, samples, recorded_dec, matcher.cwd)
    kg = sum(gm.same(sample_decision(s), gt) for s in ok) if gm else None
    top = summ.get("distribution") or []
    raw = Counter(" | ".join(intent(c, matcher.cwd) for c in sample_decision(s).calls) or "(text) " + s.text[:60]
                  for s in ok).most_common(4)
    return {"case": case.name, "category": case.category, "target": target, "n_ok": len(ok), "k": k,
            "given": gt, "k_given": kg, "top": top[:4], "raw": raw, "verdict": summ["verdict"],
            "errors": [s.error for s in samples if not s.ok][:2]}


async def main_async(args) -> int:
    cases = [c for c in all_cases(args.suite, args.gen_n, args.gen_seed) if not args.only or any(o in c.name or o in c.category for o in args.only)]
    api_key, _ = resolve_api_key("openai", args.base_url, None, free=args.free)
    rows = []
    for c in cases:
        r = await check(c, args, api_key or "")
        rows.append(r)
        lo, hi = wilson(r["k"], r["n_ok"]) if r["n_ok"] else (0, 0)
        g = f" given={r['k_given']}/{r['n_ok']}" if r["k_given"] is not None else ""
        print(f"{r['case']:30s} target={r['k']:2d}/{r['n_ok']:2d} [{lo:.2f},{hi:.2f}]{g}  {r['verdict']}", flush=True)
        for key, cnt in r["raw"]:
            print(f"    {cnt:3d}  {str(key)[:110]}")
        if r["errors"]:
            print(f"    errors: {r['errors']}")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"model": args.model, "extra_body": args.extra_body, "n": args.n,
                                        "rows": rows}, indent=1, default=str))
        print(f"Saved: {args.out}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--no-thinking-param", action="store_true")
    ap.add_argument("--extra-body", type=parse_extra_body, default={})
    ap.add_argument("--free", action="store_true")
    ap.add_argument("-n", type=int, default=20)
    ap.add_argument("--concurrency", type=int, default=20)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--suite", choices=("core", "gen", "gen-open", "gen-long", "real", "all"), default="core")
    ap.add_argument("--gen-n", type=int, default=64)
    ap.add_argument("--gen-seed", type=int, default=0)
    ap.add_argument("--budget", type=float, default=5.0)
    ap.add_argument("--ledger", type=Path, default=REPO / ".ctxblame" / "phase3_spend.jsonl")
    ap.add_argument("--out", type=Path, default=None)
    return asyncio.run(main_async(ap.parse_args(argv)))


if __name__ == "__main__":
    sys.exit(main())
