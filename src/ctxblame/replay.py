"""Replay one recorded LLM request N times and measure how often the same
decision comes back. Only that single call is re-sent; no tool is executed.

    ctxblame-replay traces/<record>.json -n 10 --key-args command
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

from .formats import (ANTHROPIC, Decision, Usage, assemble_stream, detect_format,
                      extract_decision, extract_usage)
from .ablate import AblationError, list_units, remove_random_span, remove_text, remove_units
from .pricing import BudgetExceeded, Ledger, cost, resolve_model
from .sse import parse_sse

RETRY_STATUS = {408, 409, 429, 500, 502, 503, 504, 529}
FATAL_STATUS = {400, 401, 403, 404, 422}


class FatalReplayError(Exception):
    pass


# ------------------------------------------------------------------ records

def load_record(path: Path) -> dict:
    rec = json.loads(path.read_text())
    rec.setdefault("format", detect_format(rec["request"]["path"]))
    if rec["format"] is None:
        raise ValueError(f"{path}: not an Anthropic or OpenAI chat request")
    return rec


def record_response(rec: dict) -> dict:
    r = rec.get("response") or {}
    return r.get("message") if r.get("streamed") else (r.get("body") or {})


def default_key_env(fmt: str, base_url: str) -> str:
    if "deepseek" in base_url:
        return "DEEPSEEK_API_KEY"
    return "ANTHROPIC_API_KEY" if fmt == ANTHROPIC else "OPENAI_API_KEY"


def build_headers(fmt: str, rec_headers: dict, api_key: str) -> dict:
    h = {"content-type": "application/json"}
    lower = {k.lower(): v for k, v in (rec_headers or {}).items()}
    if fmt == ANTHROPIC:
        h["anthropic-version"] = lower.get("anthropic-version", "2023-06-01")
        if "anthropic-beta" in lower:
            h["anthropic-beta"] = lower["anthropic-beta"]
        h["x-api-key"] = api_key
    else:
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
    usage: dict | None = None
    cost: float = 0.0
    model: str | None = None
    error: str | None = None
    seconds: float = 0.0


class Replayer:
    """Sends request bodies and charges every response to the ledger."""

    def __init__(self, fmt: str, url: str, headers: dict, ledger: Ledger, upstream: str,
                 est_cost: float, concurrency: int = 4, run_id: str | None = None) -> None:
        self.fmt, self.url, self.headers = fmt, url, headers
        self.ledger, self.upstream, self.est = ledger, upstream, est_cost
        self.sem = asyncio.Semaphore(concurrency)
        self.inflight = 0
        self.fatal: FatalReplayError | None = None  # once set, nothing more is sent
        self.run_id = run_id or uuid.uuid4().hex[:8]

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
            c = cost(model, usage, datetime.now(timezone.utc), self.upstream)
            self.ledger.add(self.run_id, model, usage, c)
            return resp, usage, c, model
        raise AssertionError("unreachable")

    async def sample(self, session: ClientSession, body: dict, key_args: list[str] | None) -> Sample:
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
        call = {"name": d.calls[0].name, "args": d.calls[0].args} if d.calls else None
        return Sample(ok=True, key=d.key(key_args), name=d.key(name_only=True), stop=d.stop,
                      text=d.text[:200], call=call, usage=asdict(usage), cost=c, model=model,
                      seconds=round(time.time() - t0, 2))

    async def run(self, body: dict, n: int, key_args: list[str] | None) -> list[Sample]:
        timeout = ClientTimeout(total=900, sock_connect=30)
        async with ClientSession(timeout=timeout) as s:
            tasks = [asyncio.create_task(self.sample(s, body, key_args)) for _ in range(n)]
            try:
                return list(await asyncio.gather(*tasks))
            except BaseException:
                for t in tasks:
                    t.cancel()
                raise


# ------------------------------------------------------------------ summary

def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def summarize(samples: list[Sample], baseline: Decision, key_args: list[str] | None) -> dict:
    ok = [s for s in samples if s.ok]
    bkey, bname = baseline.key(key_args), baseline.key(name_only=True)
    same = sum(s.key == bkey for s in ok)
    same_name = sum(s.name == bname for s in ok)
    return {
        "baseline": bkey,
        "n_ok": len(ok),
        "n_error": len(samples) - len(ok),
        "same_decision": same,
        "same_rate": same / len(ok) if ok else None,
        "same_rate_ci95": wilson(same, len(ok)),
        "same_tool_name": same_name,
        "distribution": Counter(s.key for s in ok).most_common(),
        "cost": sum(s.cost for s in samples),
    }


def print_summary(rec_path: Path, summary: dict, ledger: Ledger, budget: float) -> None:
    n = summary["n_ok"]
    print(f"\nRecord:    {rec_path}")
    print(f"Decision:  {summary['baseline']}")
    if n:
        lo, hi = summary["same_rate_ci95"]
        print(f"Same decision:  {summary['same_decision']}/{n} = {summary['same_rate']:.0%}"
              f"  (95% CI {lo:.0%}-{hi:.0%})")
        print(f"Same tool name: {summary['same_tool_name']}/{n}")
    if summary["n_error"]:
        print(f"Errors:    {summary['n_error']}")
    print("Outcomes:")
    for k, c in summary["distribution"][:6]:
        print(f"  {c:3d}  {k[:110]}")
    print(f"Cost: ${summary['cost']:.4f} this run; running total ${ledger.total:.4f} of ${budget:.2f}")


# ---------------------------------------------------------------------- cli

def estimate_cost(rec: dict, upstream: str) -> float:
    """Per-call estimate from the recorded call, with 50% headroom."""
    resp = record_response(rec)
    model = resp.get("model") or rec["request"]["body"].get("model", "")
    usage = extract_usage(rec["format"], resp)
    if usage.input_uncached + usage.input_cache_read + usage.output == 0:
        chars = len(json.dumps(rec["request"]["body"]))
        usage = Usage(input_uncached=chars // 3, output=2000)
    # price at peak and as if nothing were cached: an upper bound
    full = Usage(usage.input_uncached + usage.input_cache_read + usage.input_cache_write, 0, 0, usage.output)
    return 1.5 * cost(model, full, upstream=upstream, assume_peak=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Replay a recorded LLM request N times.")
    ap.add_argument("record", type=Path)
    ap.add_argument("-n", type=int, default=10)
    ap.add_argument("--key-arg", action="append", default=[],
                    help="tool argument that defines 'same decision'; repeatable. "
                         "'arg~regex' compares a regex match instead of the exact value (default: all args)")
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
    ap.add_argument("--api-key-env", default=None, help="env var holding the key (never pass the key itself)")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--budget", type=float, default=5.0, help="hard cap on total spend in the ledger (USD)")
    ap.add_argument("--ledger", type=Path, default=Path(".ctxblame/spend.jsonl"))
    ap.add_argument("--out", type=Path, default=Path("runs"))
    args = ap.parse_args(argv)

    rec = load_record(args.record)
    fmt = rec["format"]
    body = rec["request"]["body"]
    if args.list_units:
        for u in list_units(fmt, body):
            print(f"{u.id:28s} {u.kind:10s} {u.chars:6d}  {u.label}")
        return 0
    try:
        body, ablation = ablate(fmt, body, args)
    except AblationError as e:
        print(f"error: {e}", file=sys.stderr)
        return 6
    base = (args.base_url or rec["upstream"]).rstrip("/")
    key_env = args.api_key_env or default_key_env(fmt, base)
    api_key = os.environ.get(key_env)
    if not api_key:
        print(f"error: set {key_env} in the environment", file=sys.stderr)
        return 2
    resolve_model(body.get("model", ""), base)  # fail early on unknown prices
    key_args = args.key_arg or None
    baseline = extract_decision(fmt, record_response(rec))
    est = estimate_cost(rec, base)

    ledger = Ledger(args.ledger, args.budget)
    if ledger.total + est > args.budget:
        print(f"error: budget exhausted (${ledger.total:.4f} of ${args.budget:.2f})", file=sys.stderr)
        return 3
    if ablation:
        print("Ablation: " + "; ".join(ablation))
    print(f"Replaying {args.n}x {fmt} request to {base} (~${est:.4f}/call worst case; "
          f"spent so far ${ledger.total:.4f})")
    rp = Replayer(fmt, base + rec["request"]["path"], build_headers(fmt, rec["request"].get("headers"), api_key),
                  ledger, base, est, args.concurrency)
    try:
        samples = asyncio.run(rp.run(body, args.n, key_args))
    except FatalReplayError as e:
        print(f"error: {e}", file=sys.stderr)
        return 4

    summary = summarize(samples, baseline, key_args)
    print_summary(args.record, summary, ledger, args.budget)
    skipped = sum(1 for s in samples if (s.error or "").startswith("skipped"))
    if skipped:
        print(f"warning: {skipped} replays skipped because of the budget", file=sys.stderr)
    args.out.mkdir(parents=True, exist_ok=True)
    out = args.out / f"{args.record.stem}.replay-{rp.run_id}.json"
    out.write_text(json.dumps({"record": str(args.record), "n": args.n, "key_args": key_args,
                               "base_url": base, "ablation": ablation, "summary": summary,
                               "samples": [asdict(s) for s in samples]}, indent=1, ensure_ascii=False))
    print(f"Saved: {out}")
    return 0


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
