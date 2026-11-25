"""Replay one recorded LLM request N times and measure how often the same
decision comes back. Only that single call is re-sent; no tool is executed.

    ctxblame replay traces/<trace>.jsonl --step 14 -n 10
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import random
import sys
import time
import uuid
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from aiohttp import ClientError, ClientSession, ClientTimeout

from .formats import (ANTHROPIC, Decision, ToolCall, Usage, assemble_stream, extract_decision,
                      extract_usage)
from .ablate import AblationError, list_units, remove_random_span, remove_text, remove_units
from .match import MODES, Matcher
from .pricing import BudgetExceeded, Ledger, cost, is_local_upstream, resolve_model
from .sse import parse_sse
from .trace import Step, get_step, load_trace, matcher_for

RETRY_STATUS = {408, 409, 429, 500, 502, 503, 504, 529}
FATAL_STATUS = {400, 401, 403, 404, 422}


class FatalReplayError(Exception):
    pass


# ------------------------------------------------------------------ records

def default_key_env(fmt: str, base_url: str) -> str:
    if "deepseek" in base_url:
        return "DEEPSEEK_API_KEY"
    return "ANTHROPIC_API_KEY" if fmt == ANTHROPIC else "OPENAI_API_KEY"


def resolve_api_key(fmt: str, base_url: str, api_key_env: str | None = None,
                    free: bool = False) -> tuple[str | None, str]:
    """Return ``(api_key, env_var_name)``. Local or ``--free`` endpoints do not
    require a key unless ``--api-key-env`` was explicitly requested."""
    key_env = api_key_env or default_key_env(fmt, base_url)
    api_key = os.environ.get(key_env)
    if api_key:
        return api_key, key_env
    if not api_key_env and (free or is_local_upstream(base_url)):
        return "", key_env
    return None, key_env


def with_model_override(step: Step, model: str | None) -> Step:
    """Return a shallow copy of ``step`` with ``body['model']`` replaced."""
    if not model:
        return step
    req = {**step.record["request"], "body": {**step.body, "model": model}}
    return Step(step.step, {**step.record, "request": req})


def build_headers(fmt: str, rec_headers: dict, api_key: str) -> dict:
    h = {"content-type": "application/json"}
    lower = {k.lower(): v for k, v in (rec_headers or {}).items()}
    if fmt == ANTHROPIC:
        h["anthropic-version"] = lower.get("anthropic-version", "2023-06-01")
        if "anthropic-beta" in lower:
            h["anthropic-beta"] = lower["anthropic-beta"]
        if api_key:
            h["x-api-key"] = api_key
    else:
        if api_key:
            h["authorization"] = f"Bearer {api_key}"
    return h


# ------------------------------------------------------------------- replay

@dataclass
class Sample:
    ok: bool
    key: str | None = None
    name: str | None = None
    stop: str | None = None
    text: str = ""
    call: dict | None = None  # first tool call, {"name", "args"}, for inspection
    calls: list | None = None  # every tool call, so results can be re-matched offline
    keys: list | None = None  # the matcher's key for each tool call
    usage: dict | None = None
    cost: float = 0.0
    model: str | None = None
    error: str | None = None
    seconds: float = 0.0


class Replayer:
    """Sends request bodies and charges every response to the ledger."""

    def __init__(self, fmt: str, url: str, headers: dict, ledger: Ledger, upstream: str,
                 est_cost: float, concurrency: int = 4, run_id: str | None = None,
                 free: bool = False) -> None:
        self.fmt, self.url, self.headers = fmt, url, headers
        self.ledger, self.upstream, self.est = ledger, upstream, est_cost
        self.sem = asyncio.Semaphore(concurrency)
        self.inflight = 0
        self.fatal: FatalReplayError | None = None  # once set, nothing more is sent
        self.run_id = run_id or uuid.uuid4().hex[:8]
        self.free = free

    async def call(self, session: ClientSession, body: dict) -> tuple[dict, Usage, float, str]:
        async with self.sem:
            if self.fatal:
                raise self.fatal
            # reserve the estimate for every call in flight before sending
            self.ledger.check(self.est * (self.inflight + 1))
            self.inflight += 1
            try:
                return await self._send(session, body)
            finally:
                self.inflight -= 1

    async def _send(self, session: ClientSession, body: dict) -> tuple[dict, Usage, float, str]:
        for attempt in range(5):
            try:
                async with session.post(self.url, json=body, headers=self.headers) as r:
                    raw = await r.read()
                    if r.status in RETRY_STATUS:
                        raise _Retry(f"HTTP {r.status}", r.headers.get("retry-after"))
                    if r.status != 200:
                        msg = f"HTTP {r.status}: {raw[:300].decode('utf-8', 'replace')}"
                        if r.status in FATAL_STATUS:
                            self.fatal = FatalReplayError(msg)
                            raise self.fatal
                        raise RuntimeError(msg)
                    if r.headers.get("Content-Type", "").startswith("text/event-stream"):
                        resp = assemble_stream(self.fmt, parse_sse(raw))
                        if not resp.get("_stream_complete"):
                            raise _Retry("stream ended early", None)
                    else:
                        resp = json.loads(raw)
            except (_Retry, ClientError, asyncio.TimeoutError) as e:
                if attempt == 4:
                    raise RuntimeError(f"gave up after retries: {e}") from e
                ra = getattr(e, "retry_after", None)
                await asyncio.sleep(float(ra) if ra else min(30, 2 ** attempt + random.random()))
                continue
            usage = extract_usage(self.fmt, resp)
            model = resp.get("model") or body.get("model", "")
            c = cost(model, usage, datetime.now(timezone.utc), self.upstream, free=self.free)
            self.ledger.add(self.run_id, model, usage, c)
            return resp, usage, c, model
        raise AssertionError("unreachable")

    async def sample(self, session: ClientSession, body: dict, matcher=None) -> Sample:
        m = as_matcher(matcher)
        t0 = time.time()
        try:
            resp, usage, c, model = await self.call(session, body)
        except FatalReplayError:
            raise
        except BudgetExceeded as e:  # keep what we already have; skip the rest
            return Sample(ok=False, error=f"skipped: {e}")
        except Exception as e:
            return Sample(ok=False, error=str(e)[:300], seconds=round(time.time() - t0, 2))
        d = extract_decision(self.fmt, resp)
        calls = [{"name": x.name, "args": x.args} for x in d.calls]
        return Sample(ok=True, key=m.key(d), keys=m.keys(d), name=d.key(name_only=True), stop=d.stop,
                      text=d.text[:200], call=calls[0] if calls else None, calls=calls,
                      usage=asdict(usage), cost=c, model=model, seconds=round(time.time() - t0, 2))

    async def run(self, body: dict, n: int, matcher=None) -> list[Sample]:
        timeout = ClientTimeout(total=900, sock_connect=30)
        async with ClientSession(timeout=timeout) as s:
            tasks = [asyncio.create_task(self.sample(s, body, matcher)) for _ in range(n)]
            try:
                return list(await asyncio.gather(*tasks))
            except BaseException:
                for t in tasks:
                    t.cancel()
                raise


def as_matcher(m) -> Matcher:
    """Accept a Matcher, or (older API) a key_args list / None meaning args / exact."""
    if isinstance(m, Matcher):
        return m
    return Matcher("args", m) if m else Matcher("exact")


def sample_decision(s: Sample) -> Decision:
    return Decision([ToolCall(c["name"], c["args"]) for c in (s.calls or [])], s.text, s.stop)


# ------------------------------------------------------------------ summary

STABLE = 0.70  # the recorded decision must come back at least this often


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def verdict(recorded: str, dist: list[tuple[str, int]], n: int) -> tuple[str, str]:
    """(code, sentence): is the recorded decision something the model reliably does?"""
    if n < 5:
        return "too_few", f"only {n} successful replays; not enough to judge"
    same = dict(dist).get(recorded, 0)
    modal, modal_n = dist[0]
    if same / n >= STABLE:
        return "stable", f"the recorded decision comes back in {same}/{n} replays"
    if modal != recorded and modal_n / n >= STABLE:
        return "atypical", (f"the recorded decision is unusual ({same}/{n}); the model usually does "
                            f"{modal} ({modal_n}/{n}). Blame that one instead (--target modal)")
    return "coin_flip", (f"no decision is reliable: the recorded one comes back {same}/{n}, the most "
                         f"common is {modal} ({modal_n}/{n}). This step is a coin flip; "
                         "attributing it would explain noise")


def summarize(samples: list[Sample], baseline: Decision | str, matcher=None) -> dict:
    m = as_matcher(matcher)
    ok = [s for s in samples if s.ok]
    bkey = baseline if isinstance(baseline, str) else m.key(baseline)
    bname = None if isinstance(baseline, str) else baseline.key(name_only=True)
    same = sum(m.same(None, bkey, s.key, s.keys or [s.key]) for s in ok)
    if m.any_call:  # how many replies contain each call
        dist = Counter(k for s in ok for k in set(s.keys or [s.key])).most_common()
    else:
        dist = Counter(s.key for s in ok).most_common()
    code, why = verdict(bkey, dist, len(ok)) if ok else ("too_few", "no successful replays")
    return {
        "baseline": bkey,
        "match": m.mode + (" (any call)" if m.any_call else ""),
        "n_ok": len(ok),
        "n_error": len(samples) - len(ok),
        "same_decision": same,
        "same_rate": same / len(ok) if ok else None,
        "same_rate_ci95": wilson(same, len(ok)),
        "same_tool_name": sum(s.name == bname for s in ok) if bname else None,
        "modal": dist[0][0] if dist else None,
        "modal_rate": dist[0][1] / len(ok) if dist else None,
        "verdict": code,
        "verdict_text": why,
        "distribution": dist,
        "cost": sum(s.cost for s in samples),
    }


def print_summary(label: str, summary: dict, ledger: Ledger, budget: float) -> None:
    n = summary["n_ok"]
    print(f"\n{label}")
    print(f"Decision:  {summary['baseline']}   (match: {summary['match']})")
    if n:
        lo, hi = summary["same_rate_ci95"]
        print(f"Same decision:  {summary['same_decision']}/{n} = {summary['same_rate']:.0%}"
              f"  (95% CI {lo:.0%}-{hi:.0%})")
        if summary["same_tool_name"] is not None:
            print(f"Same tool name: {summary['same_tool_name']}/{n}")
    if summary["n_error"]:
        print(f"Errors:    {summary['n_error']}")
    print("Outcomes:")
    for k, c in summary["distribution"][:6]:
        print(f"  {c:3d}  {k[:110]}")
    print(f"Verdict:   {summary['verdict'].replace('_', ' ')}: {summary['verdict_text']}")
    print(f"Cost: ${summary['cost']:.4f} this run; running total ${ledger.total:.4f} of ${budget:.2f}")


# ---------------------------------------------------------------------- cli

def estimate_cost(step: Step, upstream: str, model: str | None = None, free: bool = False) -> float:
    """Per-call estimate from the recorded call, with 50% headroom."""
    resp, body = step.response, step.body
    model = model or body.get("model") or resp.get("model", "")
    usage = extract_usage(step.fmt, resp)
    if usage.input_uncached + usage.input_cache_read + usage.output == 0:
        usage = Usage(input_uncached=len(json.dumps(body)) // 3, output=2000)
    # price at peak and as if nothing were cached: an upper bound
    full = Usage(usage.input_uncached + usage.input_cache_read + usage.input_cache_write, 0, 0, usage.output)
    return 1.5 * cost(model, full, upstream=upstream, assume_peak=True, free=free)


def add_args(ap: argparse.ArgumentParser) -> None:
    ap.add_argument("trace", type=Path, help="trace (.jsonl), single record (.json) or a directory of records")
    ap.add_argument("--step", type=int, default=None, help="which step to replay (see `ctxblame steps`)")
    ap.add_argument("-n", type=int, default=10)
    ap.add_argument("--match", choices=MODES, default=None,
                    help="what counts as the same decision: intent (default), exact, args, name")
    ap.add_argument("--key-arg", action="append", default=[],
                    help="tool argument that defines 'same decision' (implies --match args); repeatable. "
                         "'arg~regex' compares a regex match instead of the exact value")
    ap.add_argument("--all-calls", action="store_true",
                    help="compare every tool call in the reply, not only the first")
    ap.add_argument("--any-call", action="store_true",
                    help="the decision counts as the same when the target is any of the reply's "
                         "(parallel) tool calls, not only the first")
    ap.add_argument("--target", default="recorded",
                    help="decision to measure: 'recorded' (default), 'modal' (the most common "
                         "replayed one) or an explicit key as printed under Outcomes")
    ap.add_argument("--list-units", action="store_true", help="print removable units and exit")
    ap.add_argument("--remove", action="append", default=[], metavar="UNIT",
                    help="remove a unit (msg[3], pair:<id>, system, tool:<name>); repeatable")
    ap.add_argument("--remove-text", action="append", default=[], metavar="TEXT",
                    help="remove an exact text span wherever it occurs; repeatable")
    ap.add_argument("--remove-random", type=int, default=None, metavar="CHARS",
                    help="control: remove a random run of whole sentences/lines of about CHARS chars")
    ap.add_argument("--protect", action="append", default=[], metavar="TEXT",
                    help="text --remove-random must not touch (e.g. the cause, the user's task)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--base-url", default=None, help="default: the upstream the record was made against")
    ap.add_argument("--model", default=None, help="override the model name in the replayed request")
    ap.add_argument("--free", action="store_true",
                    help="treat the endpoint as $0/token (skips price-table lookup; API key optional)")
    ap.add_argument("--api-key-env", default=None, help="env var holding the key (never pass the key itself)")
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--budget", type=float, default=5.0, help="hard cap on total spend in the ledger (USD)")
    ap.add_argument("--ledger", type=Path, default=Path(".ctxblame/spend.jsonl"))
    ap.add_argument("--out", type=Path, default=Path("runs"))


def run_cli(args) -> int:
    try:
        step = get_step(load_trace(args.trace), args.step)
    except (LookupError, ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 5
    step = with_model_override(step, args.model)
    fmt, body = step.fmt, step.body
    if args.list_units:
        for u in list_units(fmt, body):
            print(f"{u.id:28s} {u.kind:10s} {u.chars:6d}  {u.label}")
        return 0
    try:
        body, ablation = ablate(fmt, body, args)
    except AblationError as e:
        print(f"error: {e}", file=sys.stderr)
        return 6
    base = (args.base_url or step.record["upstream"]).rstrip("/")
    api_key, key_env = resolve_api_key(fmt, base, args.api_key_env, free=args.free)
    if api_key is None:
        print(f"error: set {key_env} in the environment", file=sys.stderr)
        return 2
    resolve_model(body.get("model", ""), base, free=args.free)  # fail early on unknown prices
    mode = args.match or ("args" if args.key_arg else "intent")
    matcher = matcher_for(step, mode, args.key_arg or None, args.all_calls, args.any_call)
    recorded = extract_decision(fmt, step.response)
    est = estimate_cost(step, base, model=body.get("model", ""), free=args.free)

    ledger = Ledger(args.ledger, args.budget)
    if ledger.total + est > args.budget:
        print(f"error: budget exhausted (${ledger.total:.4f} of ${args.budget:.2f})", file=sys.stderr)
        return 3
    if ablation:
        print("Ablation: " + "; ".join(ablation))
    print(f"Step {step.step}: replaying {args.n}x {fmt} request to {base} "
          f"(~${est:.4f}/call worst case; spent so far ${ledger.total:.4f})")
    rp = Replayer(fmt, base + step.record["request"]["path"],
                  build_headers(fmt, step.record["request"].get("headers"), api_key),
                  ledger, base, est, args.concurrency, free=args.free)
    try:
        samples = asyncio.run(rp.run(body, args.n, matcher))
    except FatalReplayError as e:
        print(f"error: {e}", file=sys.stderr)
        return 4

    target: Decision | str = recorded
    if args.target == "modal":
        dist = Counter(k for s in samples if s.ok
                       for k in (set(s.keys or [s.key]) if matcher.any_call else [s.key])).most_common(1)
        target = dist[0][0] if dist else matcher.key(recorded)
    elif args.target != "recorded":
        target = args.target
    summary = summarize(samples, target, matcher)
    summary["recorded"] = matcher.key(recorded)
    print_summary(f"Trace: {args.trace}  step {step.step}", summary, ledger, args.budget)
    skipped = sum(1 for s in samples if (s.error or "").startswith("skipped"))
    if skipped:
        print(f"warning: {skipped} replays skipped because of the budget", file=sys.stderr)
    args.out.mkdir(parents=True, exist_ok=True)
    out = args.out / f"{args.trace.stem}.step{step.step}.replay-{rp.run_id}.json"
    out.write_text(json.dumps({"trace": str(args.trace), "step": step.step, "n": args.n,
                               "match": mode, "key_args": args.key_arg or None, "base_url": base,
                               "ablation": ablation, "summary": summary,
                               "samples": [asdict(s) for s in samples]}, indent=1, ensure_ascii=False))
    print(f"Saved: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Replay one recorded LLM request N times.")
    add_args(ap)
    return run_cli(ap.parse_args(argv))


def ablate(fmt: str, body: dict, args) -> tuple[dict, list[str]]:
    done = []
    if args.remove:
        body = remove_units(fmt, body, args.remove)
        done.append("removed " + ", ".join(args.remove))
    for t in args.remove_text:
        body = remove_text(fmt, body, t)
        done.append(f"removed text {t[:60]!r}")
    if args.remove_random:
        body, removed = remove_random_span(fmt, body, args.remove_random, random.Random(args.seed), args.protect)
        done.append(f"removed random span ({len(removed)} chars, seed {args.seed}): {removed.strip()[:80]!r}")
    return body, done


class _Retry(Exception):
    def __init__(self, msg: str, retry_after: str | None) -> None:
        super().__init__(msg)
        self.retry_after = retry_after


if __name__ == "__main__":
    sys.exit(main())
