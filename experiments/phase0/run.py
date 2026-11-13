"""Phase 0 experiment: for each planted-cause scenario and each wire format,
record one real call, then measure how often that decision comes back with
(a) the full context, (b) the planted cause removed, (c) a random same-size
span removed (several seeds).

    DEEPSEEK_API_KEY=... uv run python experiments/phase0/run.py --model deepseek-flash
    uv run python experiments/phase0/run.py --dry-run     # build + validate only, no calls
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
import time
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scenarios import SCENARIOS, Scenario, to_anthropic, to_openai  # noqa: E402

from ctxblame.ablate import remove_random_span, remove_text, remove_units, validate
from ctxblame.formats import ANTHROPIC, OPENAI, Decision, ToolCall, Usage, extract_decision
from ctxblame.pricing import Ledger, cost
from ctxblame.replay import Replayer, build_headers, summarize

HERE = Path(__file__).parent
ENDPOINTS = {ANTHROPIC: ("https://api.deepseek.com/anthropic", "/v1/messages"),
             OPENAI: ("https://api.deepseek.com", "/chat/completions")}


def target_key(sc: Scenario) -> str:
    return Decision([ToolCall(sc.target, {})]).key() if not sc.key_args else \
        f"{sc.target}({json.dumps({k: True for k in sc.key_args}, sort_keys=True)})"


THINKING = "disabled"  # set by --thinking


def build(sc: Scenario, fmt: str, model: str) -> dict:
    b = to_anthropic(sc, model) if fmt == ANTHROPIC else to_openai(sc, model)
    # Handwritten histories carry no reasoning, and DeepSeek's thinking mode
    # requires earlier turns' reasoning to be passed back, so thinking is off
    # (explicitly, in both formats, to keep them comparable).
    b["thinking"] = {"type": THINKING}
    return b


def conditions(sc: Scenario, fmt: str, body: dict, n_controls: int) -> list[tuple[str, dict, str]]:
    """(name, body, description) for every condition."""
    out = [("baseline", body, "full context")]
    if sc.plant_pair:
        out.append(("cause_removed", remove_units(fmt, body, [f"pair:{sc.plant_pair}"]),
                    f"removed tool pair {sc.plant_pair}"))
    else:
        out.append(("cause_removed", remove_text(fmt, body, sc.plant), "removed planted text"))
    size = len(sc.plant)
    seen, seed = set(), 0
    while len(seen) < n_controls and seed < 100:  # distinct spans only
        b, removed = remove_random_span(fmt, body, size, random.Random(seed), protect=[sc.plant, *sc.protect])
        seed += 1
        if removed in seen:
            continue
        seen.add(removed)
        out.append((f"random_{len(seen) - 1}", b,
                    f"removed random span ({len(removed.strip())} chars): {removed.strip()!r}"))
    for name, b, _ in out:
        problems = validate(fmt, b)
        assert not problems, (sc.name, fmt, name, problems)
    return out


async def run_pair(sc: Scenario, fmt: str, model: str, rp: Replayer, n: int, n_ctrl: int,
                   n_controls: int, records_dir: Path) -> dict:
    body = build(sc, fmt, model)
    conds = conditions(sc, fmt, body, n_controls)
    # 1. the "recorded" run: one real call, saved like a proxy record
    from aiohttp import ClientSession
    async with ClientSession() as s:
        resp, usage, c, resp_model = await rp.call(s, body)
    base, path = ENDPOINTS[fmt]
    rec = {"version": 1, "format": fmt, "upstream": base, "scenario": sc.name,
           "request": {"path": path, "headers": {"anthropic-version": "2023-06-01"} if fmt == ANTHROPIC else {},
                       "body": body},
           "response": {"status": 200, "streamed": False, "body": resp}}
    (records_dir / f"{sc.name}.{fmt}.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False))
    recorded = extract_decision(fmt, resp)

    # 2. replays for every condition, all at once (the semaphore limits concurrency)
    async def one(name, b, desc):
        samples = await rp.run(b, n if name in ("baseline", "cause_removed") else n_ctrl, sc.key_args)
        summ = summarize(samples, recorded, sc.key_args)
        tk = target_key(sc)
        ok = [x for x in samples if x.ok]
        summ["target_rate"] = sum(x.key == tk for x in ok) / len(ok) if ok else None
        return name, {"description": desc, "summary": summ, "samples": [asdict(x) for x in samples]}

    results = dict(await asyncio.gather(*(one(*cnd) for cnd in conds)))
    return {"scenario": sc.name, "format": fmt, "model": resp_model,
            "recorded_decision": recorded.key(sc.key_args), "target": target_key(sc),
            "recorded_is_target": recorded.key(sc.key_args) == target_key(sc),
            "record_cost": c, "conditions": results}


def table(rows: list[dict]) -> str:
    lines = ["| Scenario | Format | Recorded = target | Baseline | Cause removed | Random (mean, each) | Cost |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        cd = r["conditions"]
        pct = lambda s: "n/a" if s["same_rate"] is None else f"{s['same_decision']}/{s['n_ok']}"  # noqa: E731
        rnd = [v["summary"] for k, v in cd.items() if k.startswith("random_")]
        rates = [x["same_rate"] for x in rnd if x["same_rate"] is not None]
        mean = f"{sum(rates) / len(rates):.0%}" if rates else "n/a"
        each = ", ".join(pct(x) for x in rnd)
        total = r["record_cost"] + sum(v["summary"]["cost"] for v in cd.values())
        lines.append(f"| {r['scenario']} | {r['format']} | {'yes' if r['recorded_is_target'] else 'NO'} "
                     f"| {pct(cd['baseline']['summary'])} | {pct(cd['cause_removed']['summary'])} "
                     f"| {mean} ({each}) | ${total:.4f} |")
    return "\n".join(lines)


async def main_async(args) -> int:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key and not args.dry_run:
        print("error: set DEEPSEEK_API_KEY", file=sys.stderr)
        return 2
    scs = [s for s in SCENARIOS if not args.only or s.name in args.only]
    fmts = args.formats.split(",")
    if args.dry_run:
        for sc in scs:
            for fmt in fmts:
                for name, b, desc in conditions(sc, fmt, build(sc, fmt, args.model), args.controls):
                    print(f"{sc.name:30s} {fmt:9s} {name:14s} {len(json.dumps(b)):6d} chars  {desc[:90]}")
        return 0

    ledger = Ledger(Path(args.ledger), args.budget)
    start_total = ledger.total
    # worst-case per-call estimate: ~4 chars/token, 1000 output tokens, peak price
    est = max(cost(args.model, Usage(len(json.dumps(build(sc, f, args.model))) // 3, 0, 0, 1000),
                   upstream="https://api.deepseek.com", assume_peak=True) for sc in scs for f in fmts)
    rps = {f: Replayer(f, ENDPOINTS[f][0] + ENDPOINTS[f][1], build_headers(f, {}, key), ledger,
                       ENDPOINTS[f][0], est, concurrency=args.concurrency, run_id=f"phase0-{f}") for f in fmts}
    out_dir = HERE / "results" / args.model
    rec_dir = out_dir / "records"
    rec_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rows = list(await asyncio.gather(*(run_pair(sc, f, args.model, rps[f], args.n, args.n_ctrl, args.controls, rec_dir)
                                       for sc in scs for f in fmts)))
    (out_dir / "results.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    md = table(rows)
    (out_dir / "results.md").write_text(f"Model: {args.model}; N={args.n} (baseline, cause removed), "
                                        f"{args.controls}x{args.n_ctrl} (random controls)\n\n{md}\n")
    print(md)
    print(f"\n{time.time() - t0:.0f}s; this run ${ledger.total - start_total:.4f}; "
          f"running total ${ledger.total:.4f}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="deepseek-flash")
    ap.add_argument("--formats", default="anthropic,openai")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("-n", type=int, default=20)
    ap.add_argument("--n-ctrl", type=int, default=10)
    ap.add_argument("--controls", type=int, default=3)
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--budget", type=float, default=5.0)
    ap.add_argument("--ledger", default=".ctxblame/spend.jsonl")
    ap.add_argument("--thinking", default="disabled", choices=["disabled", "enabled"])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    global THINKING
    THINKING = args.thinking
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
