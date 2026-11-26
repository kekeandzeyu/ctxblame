"""Oracle validation of benchmark cases on the model under test.

A planted carrier is ground truth only if the model actually uses it. For each
case this measures, with a fixed number of replays per condition (no adaptive
stopping, so rates are comparable):

  base        P(E) and P(A | E) on the unchanged request
  all_off     every planted carrier removed               -> P(A | E) should drop
  only[c]     every carrier but c removed (c kept alone)  -> P(A | E) should stay
  pre_off     the precondition removed                    -> P(E) should collapse
  ctx_off     (negatives) every removable chunk removed   -> P(A) should stay

E is the case's ``--given`` family (``bash``), A its ``--key-arg`` target.
A case is **valid** when the base decision is reliable (P(E), P(A|E) >= 0.8),
removing all carriers flips it (P(A|E) <= half of base), every carrier alone
restores it (>= half of base), and a precondition, if any, collapses P(E).
Negatives are valid when the decision survives removing all context.

    python experiments/phase3/oracle.py --suite gen --model Qwen3-8B --free -n 20 \\
        --out experiments/phase3/results/qwen3-8b/oracle.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from ctxblame.blame import Chunk, apply_chunks, chunk_request, resolve_given
from ctxblame.ablate import AblationError
from ctxblame.formats import extract_decision
from ctxblame.match import Matcher
from ctxblame.pricing import Ledger
from ctxblame.replay import (Replayer, build_headers, estimate_cost, parse_extra_body, resolve_api_key,
                             sample_decision, with_model_override)
from ctxblame.trace import matcher_for

HERE = Path(__file__).parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
from benchmark import is_carrier  # noqa: E402
from cases import all_cases  # noqa: E402


def carrier_chunks(chunks: list[Chunk], spec: str) -> list[Chunk]:
    """The smallest chunks that hold this carrier (a tool pair, or the lines/paragraph with its text)."""
    if spec.startswith("pair:"):
        return [c for c in chunks if c.id == spec]
    flat = [k for c in chunks for k in (c.children or [])] + list(chunks)
    hits = [c for c in flat if is_carrier({"id": c.id, "text": c.text}, [spec])]
    if not hits:
        return []
    best = min(hits, key=lambda c: c.chars)
    return [best]


def _arg(argv: list[str], flag: str) -> str | None:
    return argv[argv.index(flag) + 1] if flag in argv else None


def _rates(samples: list, matcher: Matcher, given: Matcher | None, gtarget: str, target: str) -> dict:
    ok = [s for s in samples if s.ok]
    kg = sum(given.same(sample_decision(s), gtarget) for s in ok) if given else len(ok)
    ka = sum((given.same(sample_decision(s), gtarget) if given else True)
             and matcher.same(None, target, s.key, s.keys or [s.key]) for s in ok)
    return {"n": len(ok), "k_given": kg, "k": ka,
            "p_given": kg / len(ok) if ok else None,
            "p_cond": ka / kg if kg else None,
            "errors": len(samples) - len(ok)}


async def rates(rp: Replayer, body: dict, n: int, matcher: Matcher, given: Matcher | None, gtarget: str,
                target: str) -> dict:
    return _rates(await rp.run(body, n, matcher), matcher, given, gtarget, target)


async def check(case, args, api_key: str) -> dict:
    step = with_model_override(case.step, args.model, args.max_tokens, args.no_thinking_param, args.extra_body)
    fmt = step.fmt
    key_args = [case.argv[i + 1] for i, a in enumerate(case.argv) if a == "--key-arg"]
    matcher = matcher_for(step, "args" if key_args else "intent", key_args or None, any_call=True)
    target = _arg(case.argv, "--target") or matcher.key(extract_decision(fmt, step.response))
    gname = _arg(case.argv, "--given")
    base = args.base_url.rstrip("/")
    rec = step.record["request"]
    rp = Replayer(fmt, base + rec["path"], build_headers(fmt, rec.get("headers"), api_key),
                  Ledger(args.ledger, args.budget), base, estimate_cost(step, base, free=args.free),
                  args.concurrency, free=args.free)
    chunks = chunk_request(fmt, step.body, case.protect)
    # the action family E, resolved exactly as ctxblame resolves --given (auto when --key-arg is used)
    base_samples = await rp.run(step.body, args.n, matcher)
    given, gtarget = resolve_given(gname, key_args, target, matcher, base_samples,
                                   extract_decision(fmt, step.response), matcher.cwd)
    gtarget = gtarget or ""
    R = lambda body: rates(rp, body, args.n, matcher, given, gtarget, target)  # noqa: E731

    def without(cs: list[Chunk]) -> dict | None:
        try:
            return apply_chunks(fmt, step.body, cs)
        except AblationError:
            return None

    out: dict = {"case": case.name, "category": case.category, "target": target, "given": gtarget or None}
    out["base"] = _rates(base_samples, matcher, given, gtarget, target)
    b = out["base"]
    if case.category == "negative":
        body = without([c for c in chunks if c.kind != "thinking"])
        out["ctx_off"] = await R(body) if body else None
        ok = (b["p_given"] or 0) >= 0.8 and (b["p_cond"] or 0) >= 0.8 and out["ctx_off"] and \
            (out["ctx_off"]["p_cond"] or 0) >= 0.5 * b["p_cond"] and (out["ctx_off"]["p_given"] or 0) >= 0.5
        out["valid"] = bool(ok)
        out["why"] = "" if ok else "negative decision not stable without context"
        return out

    cmap = {c: carrier_chunks(chunks, c) for c in case.carriers}
    missing = [c for c, cs in cmap.items() if not cs]
    reasons = []
    if missing:
        reasons.append(f"carrier not found in chunks: {missing}")
    if (b["p_given"] or 0) < 0.8 or (b["p_cond"] or 0) < 0.8:
        reasons.append(f"unreliable baseline (P(E)={b['k_given']}/{b['n']}, P(A|E)={b['k']}/{b['k_given']})")
    all_cs = [x for cs in cmap.values() for x in cs]
    body = without(all_cs)
    out["all_off"] = await R(body) if body else None
    half = 0.5 * (b["p_cond"] or 0)
    a = out["all_off"]
    if not a or a["p_cond"] is None or a["p_cond"] > half:
        reasons.append(f"removing all carriers does not flip ({a and a['k']}/{a and a['k_given']})")
    if a and (a["p_given"] or 0) < 0.5 * (b["p_given"] or 0):
        reasons.append("removing all carriers collapses the action family")
    out["only"] = {}
    if len(case.carriers) > 1:
        for c, cs in cmap.items():
            others = [x for c2, cs2 in cmap.items() if c2 != c for x in cs2]
            body = without(others)
            r = await R(body) if body else None
            out["only"][c] = r
            if not r or r["p_cond"] is None or r["p_cond"] < half:
                reasons.append(f"carrier alone does not restore: {c[:50]!r} ({r and r['k']}/{r and r['k_given']})")
    if case.preconditions:
        pcs = [x for p in case.preconditions for x in carrier_chunks(chunks, p)]
        body = without(pcs)
        out["pre_off"] = await R(body) if body else None
        p = out["pre_off"]
        if not p or (p["p_given"] or 0) > 0.5 * (b["p_given"] or 0):
            reasons.append(f"precondition removal does not collapse E ({p and p['k_given']}/{p and p['n']})")
    out["valid"] = not reasons
    out["why"] = "; ".join(reasons)
    # the carriers decide whether the agent acts at all, not only how (see gen_cases "open" style)
    out["e_coupled"] = bool(a and (b["p_given"] or 0) >= 0.8 and (a["p_given"] or 0) < 0.5 * b["p_given"])
    return out


async def main_async(args) -> int:
    cases = [c for c in all_cases(args.suite, args.gen_n, args.gen_seed)
             if not args.only or any(o in c.name or o in c.category for o in args.only)]
    api_key, _ = resolve_api_key("openai", args.base_url, None, free=args.free)
    sem = asyncio.Semaphore(args.parallel_cases)

    async def one(c):
        async with sem:
            r = await check(c, args, api_key or "")
            b = r["base"]
            print(f"{'VALID' if r['valid'] else 'drop '} {r['case']:44s} base E={b['k_given']}/{b['n']} "
                  f"A|E={b['k']}/{b['k_given']}  {r['why']}", flush=True)
            return r

    rows = await asyncio.gather(*(one(c) for c in cases))
    valid = [r["case"] for r in rows if r["valid"]]
    print(f"\n{len(valid)}/{len(rows)} cases valid; "
          f"{sum(bool(r.get('e_coupled')) for r in rows)} with carriers that also drive the action family")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"model": args.model, "extra_body": args.extra_body, "n": args.n,
                                        "suite": args.suite, "gen_n": args.gen_n, "gen_seed": args.gen_seed,
                                        "valid": valid, "rows": rows}, indent=1, default=str))
        print(f"Saved: {args.out}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Oracle validation of benchmark cases")
    ap.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--no-thinking-param", action="store_true")
    ap.add_argument("--extra-body", type=parse_extra_body, default={})
    ap.add_argument("--free", action="store_true")
    ap.add_argument("-n", type=int, default=20)
    ap.add_argument("--concurrency", type=int, default=32)
    ap.add_argument("--parallel-cases", type=int, default=4)
    ap.add_argument("--suite", choices=("core", "gen", "gen-open", "gen-long", "real", "all"), default="gen")
    ap.add_argument("--gen-n", type=int, default=64)
    ap.add_argument("--gen-seed", type=int, default=0)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--budget", type=float, default=5.0)
    ap.add_argument("--ledger", type=Path, default=REPO / ".ctxblame" / "phase3_spend.jsonl")
    ap.add_argument("--out", type=Path, default=None)
    return asyncio.run(main_async(ap.parse_args(argv)))


if __name__ == "__main__":
    sys.exit(main())
