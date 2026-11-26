"""Phase 3 attribution benchmark: compare upgraded ctxblame against baselines.

Methods:
  ctxblame        Upgraded ctxblame (conditional --given, hitchhiker pruning,
                  AND/OR duality, KV-cache-stratified suffix-first search)
  ctxblame_uncond ctxblame with --given none (ablation of Milestone 1)
  loo             Single-chunk leave-one-out ablation over coarse chunks
  self_explain    LLM self-explanation baseline (ask model which chunk IDs caused it)

Usage (Colab vLLM at $0 API cost):
    python experiments/phase3/benchmark.py \\
        --base-url http://127.0.0.1:8000/v1 \\
        --model Qwen/Qwen3-8B \\
        --free --max-tokens 2048 --no-thinking-param

Offline dry-run validation ($0, no server needed):
    python experiments/phase3/benchmark.py --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
from dataclasses import asdict
from pathlib import Path

from aiohttp import ClientSession, ClientTimeout

from ctxblame import blame
from ctxblame.ablate import validate
from ctxblame.blame import BudgetStop, Chunk, Tester, apply_chunks, chunk_request
from ctxblame.formats import extract_decision, extract_usage
from ctxblame.pricing import Ledger, cost as calc_cost, resolve_model
from ctxblame.replay import (Replayer, build_headers, estimate_cost, parse_extra_body, resolve_api_key,
                             summarize, with_model_override)
from ctxblame.trace import Step, matcher_for

HERE = Path(__file__).parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
from cases import BenchCase, all_cases  # noqa: E402

METHODS = ("ctxblame", "ctxblame_uncond", "loo", "self_explain", "contextcite", "ctxblame_flat")


# ------------------------------------------------------------------ scoring

def is_carrier(member: dict, carriers: list[str]) -> bool:
    mid, text = member["id"], " ".join(member.get("text", "").split())
    for c in carriers:
        if c.startswith("pair:"):
            if mid == c or mid.startswith(c + "."):
                return True
            continue
        c_norm = " ".join(c.split())
        if text and (text in c_norm or c_norm in text) and len(text) >= 8:
            return True
        if text and len(text) >= 20 and text[:60] in c_norm:
            return True
    return False


def score_report(case: BenchCase, rep: dict) -> dict:
    """Grade a method report uniformly across ctxblame, LOO, and self_explain."""
    members = [m for c in rep.get("causes") or [] if c.get("specific") is not False for m in c["members"]]
    pre_members = [m for p in rep.get("preconditions") or [] if p.get("specific") is not False for m in p["members"]]

    if case.category == "negative":
        # Ground truth: NO context chunk causes the decision
        neg_correct = len(members) == 0 and rep.get("result") in ("not_in_context", "none_found", "no_causes")
        return {
            "result": rep.get("result"),
            "carriers_found": 0,
            "carriers": 0,
            "recall": None,
            "precision": 1.0 if neg_correct else 0.0,
            "f1": None,
            "precond_found": None,
            "precond_fp": False,
            "neg_correct": neg_correct,
            "members": len(members),
            "replays": rep.get("replays", 0),
            "cost": rep.get("cost", 0.0),
            "seconds": rep.get("seconds", 0.0),
            "cache_hit_rate": (rep.get("cache_stats") or {}).get("cache_hit_rate"),
            "input_uncached": (rep.get("cache_stats") or {}).get("input_uncached", 0),
        }

    hits = [m for m in members if is_carrier(m, case.carriers)]
    covered = {c for c in case.carriers if any(is_carrier(m, [c]) for m in members)}
    recall = len(covered) / len(case.carriers) if case.carriers else None
    precision = len(hits) / len(members) if members else (0.0 if rep.get("result") != "no_stable_decision" else None)
    f1 = (2 * precision * recall / (precision + recall)) if (precision and recall) else (
        0.0 if precision is not None and recall is not None else None
    )
    precond_fp = bool(case.preconditions and any(is_carrier(m, case.preconditions) for m in members))
    precond_found = (
        any(is_carrier(m, case.preconditions) for m in pre_members)
        if case.preconditions else None
    )
    return {
        "result": rep.get("result"),
        "carriers_found": len(covered),
        "carriers": len(case.carriers),
        "recall": recall,
        "precision": precision,
        "f1": f1,
        "precond_found": precond_found,
        "precond_fp": precond_fp,
        "neg_correct": None,
        "members": len(members),
        "replays": rep.get("replays", 0),
        "cost": rep.get("cost", 0.0),
        "seconds": rep.get("seconds", 0.0),
        "cache_hit_rate": (rep.get("cache_stats") or {}).get("cache_hit_rate"),
        "input_uncached": (rep.get("cache_stats") or {}).get("input_uncached", 0),
    }


# ------------------------------------------------------------------ methods

def _parse_blame_args(case: BenchCase, common: list[str], extra: list[str] = ()):
    ap = argparse.ArgumentParser()
    blame.add_args(ap)
    argv = [f"{case.name}.json", *case.argv, *extra, *common]
    for p in case.protect:
        argv += ["--protect", p]
    args = ap.parse_args(argv)
    args.json = True
    return args


async def run_ctxblame(case: BenchCase, base: str, api_key: str, common: list[str],
                       unconditional: bool = False, flat: bool = False) -> dict:
    extra = (["--given", "none"] if unconditional else []) + (["--no-stratify"] if flat else [])
    args = _parse_blame_args(case, common, extra)
    t0 = time.monotonic()
    rep = await blame.why(case.step, args, api_key, base)
    rep["seconds"] = round(time.monotonic() - t0, 2)
    return rep


async def run_loo(case: BenchCase, base: str, api_key: str, common: list[str]) -> dict:
    """Baseline 1: Single-chunk leave-one-out ablation against unconditional P(target)."""
    args = _parse_blame_args(case, common, ["--given", "none"])
    step = with_model_override(case.step, args.model, args.max_tokens, args.no_thinking_param,
                               args.extra_body)
    fmt = step.fmt
    mode = args.match or ("args" if args.key_arg else "intent")
    matcher = matcher_for(step, mode, args.key_arg or None, any_call=not args.first_call)
    ledger = Ledger(args.ledger, args.budget)
    start_cost = ledger.total
    t0 = time.monotonic()

    recorded = matcher.key(extract_decision(fmt, step.response))
    probe = Tester(step, base, api_key, matcher, recorded, {}, ledger, 1.0, args.n, args.n,
                   args.concurrency, free=args.free)
    samples = await probe.replayer().run(step.body, args.n, matcher)
    target = args.target or recorded
    summ = summarize(samples, target, matcher)
    if not args.target and summ["verdict"] == "atypical":
        target = summ["modal"]
        summ = summarize(samples, target, matcher)
    b_rate = summ["same_rate"] or 0.0
    if summ["verdict"] in ("coin_flip", "too_few") or b_rate < 0.5:
        return {"result": "no_stable_decision", "baseline": summ, "causes": [], "preconditions": [],
                "replays": len(samples), "cost": ledger.total - start_cost,
                "seconds": round(time.monotonic() - t0, 2), "cache_stats": _usage_stats(samples, {})}

    coarse = chunk_request(fmt, step.body, args.protect, not args.no_tool_descs)
    by_id = {c.id: c for c in coarse}
    test = Tester(step, base, api_key, matcher, target, by_id, ledger, b_rate,
                  args.batch, args.max_n, args.concurrency, free=args.free)
    causes = []
    stopped = None
    try:
        for ch in coarse:
            if ch.kind == "thinking":
                continue
            out = await test(frozenset([ch.id]))
            if out.flipped:
                causes.append({
                    "relation": "loo_single",
                    "members": [{"id": ch.id, "kind": ch.kind, "label": ch.label, "text": ch.text}],
                    "together": asdict(out),
                    "specific": True,
                })
    except BudgetStop as e:
        stopped = str(e)
    return {
        "result": "causes" if causes else "not_in_context",
        "baseline": summ,
        "causes": causes,
        "preconditions": [],
        "stopped": stopped,
        "tests": test.log,
        "replays": test.replays + len(samples),
        "cost": ledger.total - start_cost,
        "seconds": round(time.monotonic() - t0, 2),
        "cache_stats": _usage_stats(samples, test.usage),
    }


async def representative_call(case: BenchCase, base: str, api_key: str, args, n: int = 10):
    """(target, call): the decision the benchmark explains and the model's own most common
    tool call that makes it. Recorded calls can come from another model (the Phase 0/1
    records are DeepSeek's) or be atypical, so baselines that need one concrete reply
    (self-explanation's prompt, ContextCite's log-probability) use a sampled one."""
    from collections import Counter
    from ctxblame.formats import ToolCall
    step = with_model_override(case.step, args.model, args.max_tokens, args.no_thinking_param, args.extra_body)
    mode = args.match or ("args" if args.key_arg else "intent")
    matcher = matcher_for(step, mode, args.key_arg or None, any_call=not args.first_call)
    recorded_dec = extract_decision(step.fmt, step.response)
    target = args.target or matcher.key(recorded_dec)
    rec = step.record["request"]
    rp = Replayer(step.fmt, base + rec["path"], build_headers(step.fmt, rec.get("headers"), api_key),
                  Ledger(args.ledger, args.budget), base, estimate_cost(step, base, free=args.free),
                  args.concurrency, free=args.free)
    samples = await rp.run(step.body, n, matcher)
    seen = Counter()
    for smp in samples:
        for c in (smp.calls or []) if smp.ok else []:
            tc = ToolCall(c["name"], c["args"])
            if matcher._one(tc) == target:
                seen[json.dumps([c["name"], c["args"]], sort_keys=True)] += 1
    if seen:
        name, cargs = json.loads(seen.most_common(1)[0][0])
        return target, ToolCall(name, cargs), step
    for c in recorded_dec.calls:
        if matcher._one(c) == target:
            return target, c, step
    return target, (recorded_dec.calls[0] if recorded_dec.calls else None), step


async def run_self_explain(case: BenchCase, base: str, api_key: str, common: list[str]) -> dict:
    """Baseline 2: Ask the LLM directly which context chunk IDs caused its tool call."""
    args = _parse_blame_args(case, common)
    step = with_model_override(case.step, args.model, args.max_tokens, args.no_thinking_param,
                               args.extra_body)
    fmt = step.fmt
    mode = args.match or ("args" if args.key_arg else "intent")
    matcher = matcher_for(step, mode, args.key_arg or None, any_call=not args.first_call)
    ledger = Ledger(args.ledger, args.budget)
    start_cost = ledger.total
    t0 = time.monotonic()

    target, call, _ = await representative_call(case, base, api_key, args)
    coarse = [c for c in chunk_request(fmt, step.body, args.protect, not args.no_tool_descs)
              if c.kind != "thinking"]
    by_id = {c.id: c for c in coarse}

    chunk_lines = "\n".join(
        f"- id={c.id!r} ({c.label}): {' '.join(c.text.split())[:320]}"
        for c in coarse
    )
    prompt = (
        "You are auditing why an LLM coding agent made a specific tool call.\n"
        f"Decision made: {target}\n"
        f"Tool call: {call.name}({json.dumps(call.args)})\n\n"
        "Below are the removable context chunks from the prompt (excluding the user's final task):\n"
        f"{chunk_lines}\n\n"
        "Which chunk id(s) directly caused this specific decision (as opposed to merely being background "
        "or the user's task)? Return ONLY valid JSON of the form:\n"
        '{"chunk_ids": ["id1", ...]}\n'
        "Return an empty list [] if the decision comes only from the user's task and general habits."
    )
    model = step.body.get("model", "")
    req_body = {
        "model": model,
        "max_tokens": min(args.max_tokens or 1024, 1024),
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": "Respond with compact JSON only: {\"chunk_ids\": [...]}."},
            {"role": "user", "content": prompt},
        ],
        **(args.extra_body or {}),
    }
    url = base + "/chat/completions"
    headers = build_headers("openai", {}, api_key)
    est = estimate_cost(step, base, model=model, free=args.free)
    rp = Replayer("openai", url, headers, ledger, base, est, concurrency=1, free=args.free)
    timeout = ClientTimeout(total=300, sock_connect=30)
    raw_text = ""
    usage_dict = {"input_uncached": 0, "input_cache_read": 0, "input_cache_write": 0, "output": 0}
    try:
        async with ClientSession(timeout=timeout) as session:
            resp, usage, c_usd, _ = await rp.call(session, req_body)
        raw_text = ((resp.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        usage_dict = asdict(usage)
    except Exception as e:
        return {"result": "error", "error": str(e)[:300], "causes": [], "preconditions": [],
                "replays": 1, "cost": ledger.total - start_cost,
                "seconds": round(time.monotonic() - t0, 2), "cache_stats": _usage_stats([], usage_dict)}

    picked = _extract_chunk_ids(raw_text, by_id)
    causes = [{
        "relation": "self_explain",
        "members": [{"id": cid, "kind": by_id[cid].kind, "label": by_id[cid].label, "text": by_id[cid].text}
                    for cid in picked],
        "specific": True,
    }] if picked else []
    return {
        "result": "causes" if causes else "not_in_context",
        "raw_response": raw_text[:800],
        "causes": causes,
        "preconditions": [],
        "replays": 1,
        "cost": ledger.total - start_cost,
        "seconds": round(time.monotonic() - t0, 2),
        "cache_stats": _usage_stats([], usage_dict),
    }


def _extract_chunk_ids(raw: str, by_id: dict[str, Chunk]) -> list[str]:
    """Parse {"chunk_ids": [...]} from model text (stripping <think> blocks and code fences)."""
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    m = re.search(r"\{.*?\}", cleaned, flags=re.DOTALL)
    ids: list[str] = []
    if m:
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict) and isinstance(obj.get("chunk_ids"), list):
                ids = [str(x) for x in obj["chunk_ids"]]
        except json.JSONDecodeError:
            pass
    if not ids:
        ids = [cid for cid in by_id if cid in cleaned]
    seen: set[str] = set()
    return [cid for cid in ids if cid in by_id and not (cid in seen or seen.add(cid))]


def _usage_stats(samples: list, extra: dict) -> dict:
    u = {"input_uncached": 0, "input_cache_read": 0, "input_cache_write": 0, "output": 0}
    for k in u:
        u[k] += extra.get(k) or 0
    for s in samples:
        if getattr(s, "usage", None):
            for k in u:
                u[k] += s.usage.get(k) or 0
    total_in = u["input_uncached"] + u["input_cache_read"] + u["input_cache_write"]
    return {**u, "cache_hit_rate": (u["input_cache_read"] / total_in) if total_in else None}


# ------------------------------------------------------------------ reporting

def _mean(vals: list[float]) -> float | None:
    return sum(vals) / len(vals) if vals else None


def _fmt_pct(v: float | None) -> str:
    return f"{v:.0%}" if v is not None else "-"


def render_markdown(rows: list[dict], methods: list[str]) -> str:
    lines = [
        "# Phase 3 Attribution Benchmark",
        "",
        "## Summary by Method",
        "",
        "| Method | Mean Recall | Mean Precision | Mean F1 | Precond FP | Neg-Ctrl Acc | Avg Replays | Avg Cache Hit | Avg Secs | Total Cost |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for meth in methods:
        ms = [r["score"] for r in rows if r["method"] == meth]
        recalls = [s["recall"] for s in ms if s["recall"] is not None]
        precs = [s["precision"] for s in ms if s["precision"] is not None and s["neg_correct"] is None]
        f1s = [s["f1"] for s in ms if s["f1"] is not None]
        pre_cases = [s for s in ms if s["precond_found"] is not None]
        pre_fp = sum(1 for s in pre_cases if s["precond_fp"]) / len(pre_cases) if pre_cases else None
        neg_cases = [s for s in ms if s["neg_correct"] is not None]
        neg_acc = sum(1 for s in neg_cases if s["neg_correct"]) / len(neg_cases) if neg_cases else None
        hits = [s["cache_hit_rate"] for s in ms if s["cache_hit_rate"] is not None]
        avg_rep = _mean([float(s["replays"]) for s in ms]) or 0.0
        avg_sec = _mean([float(s["seconds"]) for s in ms]) or 0.0
        tot_cost = sum(s["cost"] for s in ms)
        lines.append(
            f"| {meth} | {_fmt_pct(_mean(recalls))} | {_fmt_pct(_mean(precs))} | {_fmt_pct(_mean(f1s))} | "
            f"{_fmt_pct(pre_fp)} | {_fmt_pct(neg_acc)} | {avg_rep:.1f} | {_fmt_pct(_mean(hits))} | "
            f"{avg_sec:.1f}s | ${tot_cost:.3f} |"
        )

    lines += [
        "",
        "## Per-Case Results",
        "",
        "| Case | Category | Method | Result | Carriers | Recall | Precision | Precond Separated | Replays | Cache Hit | Secs | Cost |",
        "|---|---|---|---|---|---:|---:|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        s = r["score"]
        carr = f"{s['carriers_found']}/{s['carriers']}" if s["carriers"] else ("OK" if s["neg_correct"] else "FP")
        pre_s = "-" if s["precond_found"] is None else (
            "YES" if s["precond_found"] and not s["precond_fp"] else ("FP" if s["precond_fp"] else "no")
        )
        lines.append(
            f"| {r['case']} | {r['category']} | {r['method']} | {s['result']} | {carr} | "
            f"{_fmt_pct(s['recall'])} | {_fmt_pct(s['precision'])} | {pre_s} | "
            f"{s['replays']} | {_fmt_pct(s['cache_hit_rate'])} | {s['seconds']:.1f}s | ${s['cost']:.3f} |"
        )
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ cli

def dry_run(cases: list[BenchCase]) -> int:
    """Validate every benchmark case offline ($0): chunking, ablation validity, carrier coverage."""
    ok = True
    for c in cases:
        chunks = chunk_request(c.step.fmt, c.step.body, c.protect)
        problems = validate(c.step.fmt, apply_chunks(c.step.fmt, c.step.body, chunks))
        all_members = [{"id": x.id, "text": x.text} for ch in chunks for x in ([ch] + list(ch.children))]
        missing = [car for car in c.carriers if not any(is_carrier(m, [car]) for m in all_members)]
        missing_pre = [p for p in c.preconditions if not any(is_carrier(m, [p]) for m in all_members)]
        status = "OK" if not problems and not missing and not missing_pre else "FAIL"
        if status != "OK":
            ok = False
        print(f"{status:4s} {c.name:28s} [{c.category:15s}] chunks={len(chunks):2d} "
              f"carriers={len(c.carriers)} preconds={len(c.preconditions)}"
              + (f" problems={problems}" if problems else "")
              + (f" missing={missing}" if missing else "")
              + (f" missing_pre={missing_pre}" if missing_pre else ""))
    return 0 if ok else 1


async def main_async(args) -> int:
    cases = [c for c in all_cases(args.suite, args.gen_n, args.gen_seed) if not args.only or any(o in c.name or o in c.category for o in args.only)]
    if args.valid_from:
        valid = set(json.loads(args.valid_from.read_text())["valid"])
        dropped = [c.name for c in cases if c.name not in valid]
        cases = [c for c in cases if c.name in valid]
        print(f"oracle filter: {len(cases)} valid cases kept, {len(dropped)} dropped", flush=True)
    if not cases:
        print("error: no benchmark cases matched --only", file=sys.stderr)
        return 2
    if args.dry_run:
        return dry_run(cases)

    base = args.base_url.rstrip("/")
    api_key, key_env = resolve_api_key("openai", base, args.api_key_env, free=args.free)
    if api_key is None:
        print(f"error: set {key_env} in the environment (or use --free for local/Colab servers)", file=sys.stderr)
        return 2
    if args.model:
        resolve_model(args.model, base, free=args.free)

    common = [
        "--base-url", base,
        "--budget", str(args.budget),
        "--ledger", str(args.ledger),
        "--concurrency", str(args.concurrency),
        "-n", str(args.n),
        "--batch", str(args.batch),
        "--max-n", str(args.max_n),
        "--controls", str(args.controls),
        "--seed", str(args.seed),
    ]
    if args.model:
        common += ["--model", args.model]
    if args.max_tokens is not None:
        common += ["--max-tokens", str(args.max_tokens)]
    if args.no_thinking_param:
        common += ["--no-thinking-param"]
    if args.free:
        common += ["--free"]
    if args.extra_body:
        common += ["--extra-body", json.dumps(args.extra_body)]

    async def run_one(case: BenchCase, meth: str) -> dict:
        print(f"== {case.name} [{meth}]", flush=True)
        try:
            if meth == "ctxblame":
                rep = await run_ctxblame(case, base, api_key, common, unconditional=False)
            elif meth == "ctxblame_uncond":
                rep = await run_ctxblame(case, base, api_key, common, unconditional=True)
            elif meth == "ctxblame_flat":
                rep = await run_ctxblame(case, base, api_key, common, flat=True)
            elif meth == "loo":
                rep = await run_loo(case, base, api_key, common)
            elif meth == "self_explain":
                rep = await run_self_explain(case, base, api_key, common)
            elif meth == "contextcite":
                from contextcite import contextcite
                _, call, step = await representative_call(case, base, api_key, _parse_blame_args(case, common))
                rep = await contextcite(step, base, step.body.get("model", ""), case.protect, call=call,
                                        n_ablations=args.cc_ablations, seed=args.seed,
                                        extra_body=args.extra_body)
            else:
                raise ValueError(f"unknown method {meth!r}")
        except BudgetStop:
            raise
        except Exception as e:  # one broken run must not lose the whole benchmark
            rep = {"result": "error", "error": f"{type(e).__name__}: {e}"[:500], "causes": [],
                   "preconditions": [], "replays": 0, "cost": 0.0, "seconds": 0.0}
        sc = score_report(case, rep)
        print(f"   {case.name} [{meth}] result={sc['result']} carriers={sc['carriers_found']}/{sc['carriers']} "
              f"prec={_fmt_pct(sc['precision'])} replays={sc['replays']} "
              f"cache={_fmt_pct(sc['cache_hit_rate'])} {sc['seconds']:.1f}s ${sc['cost']:.3f}", flush=True)
        return {"case": case.name, "category": case.category, "method": meth, "score": sc, "report": rep}

    sem = asyncio.Semaphore(args.parallel_cases)

    async def guarded(case, meth):
        async with sem:
            return await run_one(case, meth)

    rows: list[dict] = list(await asyncio.gather(*(guarded(c, m) for c in cases for m in args.methods)))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    md = render_markdown(rows, args.methods)
    (out_dir / "benchmark.md").write_text(md)
    (out_dir / "benchmark.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False, default=str))
    print("\n" + md)
    print(f"Saved: {out_dir / 'benchmark.md'} and {out_dir / 'benchmark.json'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Phase 3 attribution benchmark (ctxblame vs LOO vs self-explanation).")
    ap.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    ap.add_argument("--model", default=None, help="override model name (e.g. Qwen/Qwen3-8B)")
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--no-thinking-param", action="store_true",
                    help="strip DeepSeek top-level 'thinking' param (recommended for vLLM / SGLang)")
    ap.add_argument("--free", action="store_true", help="treat endpoint as $0/token")
    ap.add_argument("--extra-body", type=parse_extra_body, default={}, metavar="JSON",
                    help="JSON object merged into every request body (e.g. Qwen3 "
                         "'{\"chat_template_kwargs\": {\"enable_thinking\": false}}')")
    ap.add_argument("--api-key-env", default=None)
    ap.add_argument("--methods", nargs="+", choices=METHODS, default=list(METHODS[:4]))
    ap.add_argument("--parallel-cases", type=int, default=1,
                    help="(case, method) runs in flight at once (a dedicated GPU batches them)")
    ap.add_argument("--seed", type=int, default=0, help="seed for random controls and contextcite masks")
    ap.add_argument("--cc-ablations", type=int, default=64, help="random ablations for the contextcite baseline")
    ap.add_argument("--only", nargs="*", help="filter cases by substring match on name or category")
    ap.add_argument("--suite", choices=("core", "gen", "gen-open", "gen-long", "real", "all"), default="core",
                    help="core = 12 hand-written cases, gen = generated cases (gen_cases.py), all = both")
    ap.add_argument("--gen-n", type=int, default=64, help="number of generated cases")
    ap.add_argument("--valid-from", type=Path, default=None,
                    help="oracle.json from oracle.py: run only the cases it marked valid")
    ap.add_argument("--gen-seed", type=int, default=0, help="seed of the generated suite")
    ap.add_argument("-n", type=int, default=10, help="baseline replays")
    ap.add_argument("--batch", type=int, default=5)
    ap.add_argument("--max-n", type=int, default=15)
    ap.add_argument("--controls", type=int, default=2)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--budget", type=float, default=10.0)
    ap.add_argument("--ledger", type=Path, default=REPO / ".ctxblame" / "phase3_spend.jsonl")
    ap.add_argument("--out-dir", type=Path, default=HERE / "results")
    ap.add_argument("--dry-run", action="store_true", help="validate cases offline without calling any LLM")
    return asyncio.run(main_async(ap.parse_args(argv)))


if __name__ == "__main__":
    sys.exit(main())
