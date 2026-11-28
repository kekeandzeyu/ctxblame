"""Phase 7.1: collect the raw data for the steelmanned baselines (GPU, $0 on vLLM).

For each Phase 6 case, on the same units ctxblame searches (every line, and each
tool-call pair as one unit, since a pair can only be removed whole):

  designs       non-adaptive random removal designs. Row t removes each unit
                independently with probability 1 - q (q = keep probability) and is
                replayed once. The first ``--base`` rows remove nothing. ``fq<q>`` is
                the same design with E forced by ``tool_choice`` (tool-level E only).
                Each row records whether the reply was in E and whether it made A.
  contextcite   ``--cc-masks`` random masks (q = 1/2), each scored with one prefill:
                log p(reply tokens up to and including the tool name), the E part,
                and log p(the remaining tokens | that prefix), the choice part.
                The reply is the model's most common call making A in the base rows.
  self_explain  one call listing every unit in full, with A and E stated, asking
                which units decided the choice and which made the agent act at all.

Rows are stored in order, so a budget M is the first M rows; nothing is estimated
here. ``estimate.py`` turns the raw data into reports offline (and can be re-run
with other estimators without a GPU).

One JSON per case in ``<out>/raw/``; finished cases are skipped.

    python experiments/phase7/baselines.py --tables experiments/phase6/results/qwen3-14b/tables \\
        --model Qwen3-14B --free --no-thinking-param --extra-body '{...}' --seed 0 \\
        --out experiments/phase7/results/p71-qwen3-14b/seed0
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path

from aiohttp import ClientSession, ClientTimeout

HERE = Path(__file__).parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "phase6"))
sys.path.insert(0, str(HERE.parent / "phase3"))

from ctxblame.ablate import AblationError  # noqa: E402
from ctxblame.blame import Chunk, apply_chunks, chunk_request, force_tool_choice, resolve_given  # noqa: E402
from ctxblame.formats import ToolCall, extract_decision  # noqa: E402
from ctxblame.match import Matcher  # noqa: E402
from ctxblame.pricing import Ledger  # noqa: E402
from ctxblame.replay import (Replayer, build_headers, estimate_cost, parse_extra_body,  # noqa: E402
                             resolve_api_key, sample_decision, with_model_override)
from ctxblame.trace import matcher_for  # noqa: E402

from cases6 import TableCase, phase6_cases  # noqa: E402

DESIGNS = ("q0.25", "q0.5", "q0.75", "q0.9", "fq0.5")


def parse_design(d: str) -> tuple[bool, float]:
    m = re.fullmatch(r"(f?)q(0?\.\d+|1)", d)
    if not m:
        raise ValueError(f"design {d!r}: expected q<keep-prob> or fq<keep-prob>, e.g. q0.5")
    return bool(m.group(1)), float(m.group(2))


def units(fmt: str, body: dict, protect=()) -> tuple[list[Chunk], list[int]]:
    """The units a baseline may remove, and each unit's parent pair (-1 if none):
    every line, and every tool-call pair as one unit next to its own lines."""
    out: list[Chunk] = []
    parent: list[int] = []
    for c in chunk_request(fmt, body, protect):
        if c.kind == "thinking":
            continue
        if c.id.startswith("pair:"):
            out.append(c)
            parent.append(-1)
            p = len(out) - 1
            for ch in c.children:
                out.append(ch)
                parent.append(p)
        else:
            for ch in c.children or [c]:
                out.append(ch)
                parent.append(-1)
    return out, parent


def masks(n_units: int, q: float, m: int, base: int, rng: random.Random) -> list[list[int]]:
    """m rows of removed unit indices: ``base`` empty rows, then Bernoulli(1 - q) removals."""
    return [[] for _ in range(min(base, m))] + [
        [i for i in range(n_units) if rng.random() >= q] for _ in range(m - min(base, m))]


def effective(removed: list[int], parent: list[int]) -> list[int]:
    """Units gone from the request: the removed ones and the lines of a removed pair."""
    r = set(removed)
    return sorted(i for i in range(len(parent)) if i in r or parent[i] in r)


def removal(us: list[Chunk], removed: list[int], parent: list[int]) -> list[Chunk]:
    """Chunks to pass to ``apply_chunks`` (a removed pair's lines go with it)."""
    r = set(removed)
    return [us[i] for i in sorted(r) if parent[i] not in r]


def _arg(argv: list[str], flag: str) -> str | None:
    return argv[argv.index(flag) + 1] if flag in argv else None


class Case:
    """A Phase 6 case prepared for replay: units, matcher, target A, family E."""

    def __init__(self, tc: TableCase, args) -> None:
        c = tc.case
        self.tc = tc
        self.step = with_model_override(c.step, args.model, args.max_tokens, args.no_thinking_param,
                                        args.extra_body)
        self.fmt, self.body = self.step.fmt, self.step.body
        self.key_args = [c.argv[i + 1] for i, a in enumerate(c.argv) if a == "--key-arg"]
        self.matcher = matcher_for(self.step, "args" if self.key_args else "intent", self.key_args or None,
                                   any_call=True)
        self.recorded = extract_decision(self.fmt, self.step.response)
        self.target = _arg(c.argv, "--target") or self.matcher.key(self.recorded)
        self.units, self.parent = units(self.fmt, self.body, c.protect)
        self.given: Matcher | None = None
        self.gtarget = ""

    def resolve(self, base_samples) -> None:
        self.given, g = resolve_given(_arg(self.tc.case.argv, "--given"), self.key_args, self.target, self.matcher,
                                      base_samples, self.recorded, self.matcher.cwd)
        self.gtarget = g or ""

    @property
    def forceable(self) -> bool:
        return self.given is not None and self.given.mode == "name" and bool(self.gtarget)

    def outcome(self, s) -> list:
        """[ok, in E, A] for one replay."""
        if not s.ok:
            return [False, False, False]
        e = self.given.same(sample_decision(s), self.gtarget) if self.given else True
        a = e and self.matcher.same(None, self.target, s.key, s.keys or [s.key])
        return [True, bool(e), bool(a)]

    def body_without(self, removed: list[int]) -> dict:
        return apply_chunks(self.fmt, self.body, removal(self.units, removed, self.parent)) if removed else self.body


async def run_design(cs: Case, design: str, args, rp: Replayer, session: ClientSession, seed: int) -> dict:
    forced, q = parse_design(design)
    rng = random.Random(f"p7-{cs.tc.name}-{design}-{seed}")
    rows = masks(len(cs.units), q, args.m, args.base, rng)
    if forced and not cs.forceable:
        return {"design": design, "skipped": "E is not a tool name; it cannot be forced"}

    async def one(removed: list[int]):
        try:
            body = cs.body_without(removed)
        except AblationError as e:
            return None, f"ablation: {e}"
        if forced:
            body = force_tool_choice(cs.fmt, body, cs.gtarget)
        return await rp.sample(session, body, cs.matcher), None

    res = await asyncio.gather(*(one(r) for r in rows))
    samples = [s for s, _ in res]
    if cs.given is None and not forced:
        cs.resolve([s for s in samples[:args.base] if s is not None])
    out_rows = []
    for removed, (s, err) in zip(rows, res):
        o = cs.outcome(s) if s is not None else [False, False, False]
        out_rows.append([effective(removed, cs.parent), *o])
    return {"design": design, "forced": forced, "q": q, "rows": out_rows,
            "errors": sum(1 for s, err in res if s is None or not s.ok),
            "_samples": samples[:args.base]}


def representative_call(cs: Case, base_samples) -> ToolCall | None:
    """The model's most common call making A among the base rows; the recorded one as fallback."""
    seen: Counter = Counter()
    for s in base_samples:
        for c in (s.calls or []) if s is not None and s.ok else []:
            tc = ToolCall(c["name"], c["args"])
            if cs.matcher._one(tc) == cs.target:
                seen[json.dumps([c["name"], c["args"]], sort_keys=True)] += 1
    if seen:
        name, cargs = json.loads(seen.most_common(1)[0][0])
        return ToolCall(name, cargs)
    return next((c for c in cs.recorded.calls if cs.matcher._one(c) == cs.target), None)


# ------------------------------------------------------------------ ContextCite (prefill scoring)

def _root(base: str) -> str:
    return base[:-3] if base.endswith("/v1") else base


async def _post(session: ClientSession, url: str, req: dict) -> dict:
    async with session.post(url, json=req) as r:
        j = await r.json()
        if r.status != 200:
            raise RuntimeError(f"{url.rsplit('/', 1)[-1]} {r.status}: {str(j)[:300]}")
        return j


async def tokenize(session, base: str, model: str, messages: list, tools, gen_prompt: bool, extra: dict) -> list[int]:
    req = {"model": model, "messages": messages, "add_generation_prompt": gen_prompt, "add_special_tokens": False}
    if tools:
        req["tools"] = tools
    if extra.get("chat_template_kwargs"):
        req["chat_template_kwargs"] = extra["chat_template_kwargs"]
    return (await _post(session, _root(base) + "/tokenize", req))["tokens"]


async def detokenize(session, base: str, model: str, tokens: list[int]) -> str:
    return (await _post(session, _root(base) + "/detokenize", {"model": model, "tokens": tokens}))["prompt"]


async def token_logprobs(session, base: str, model: str, prompt: list[int], reply: list[int]) -> list[float]:
    req = {"model": model, "prompt": prompt + reply, "max_tokens": 1, "prompt_logprobs": 0, "temperature": 0}
    plp = (await _post(session, base + "/completions", req))["choices"][0]["prompt_logprobs"]
    out = []
    for pos, tok in zip(range(len(prompt), len(prompt) + len(reply)), reply):
        e = (plp[pos] or {}).get(str(tok))
        if e is None:
            raise RuntimeError("missing prompt logprob")
        out.append(e["logprob"] if isinstance(e, dict) else float(e))
    return out


async def _split_tokens(session, base: str, model: str, reply: list[int], name: str) -> int:
    lo, hi = 1, len(reply)  # smallest j with name in detok(reply[:j]); containment is monotone in j
    while lo < hi:
        mid = (lo + hi) // 2
        if name in await detokenize(session, base, model, reply[:mid]):
            hi = mid
        else:
            lo = mid + 1
    return lo


async def run_contextcite(cs: Case, call: ToolCall, args, session: ClientSession, seed: int) -> dict:
    base, model, extra = args.base_url.rstrip("/"), cs.body.get("model", ""), args.extra_body or {}
    reply_msg = {"role": "assistant", "content": "", "tool_calls": [
        {"id": "call_cc", "type": "function", "function": {"name": call.name, "arguments": json.dumps(call.args)}}]}
    rng = random.Random(f"p7cc-{cs.tc.name}-{seed}")
    rows = masks(len(cs.units), 0.5, args.cc_masks, 1, rng)
    sem = asyncio.Semaphore(args.cc_concurrency)
    split: dict[str, int] = {}

    async def score(removed: list[int]):
        try:
            b = cs.body_without(removed)
        except AblationError:
            return None
        async with sem:
            p = await tokenize(session, base, model, b["messages"], b.get("tools"), True, extra)
            full = await tokenize(session, base, model, b["messages"] + [reply_msg], b.get("tools"), False, extra)
            k = 0  # the template may re-render earlier turns: the reply is what follows the common prefix
            while k < min(len(p), len(full)) and p[k] == full[k]:
                k += 1
            reply = full[k:]
            key = json.dumps(reply)
            if key not in split:  # tokens of the E part (through the tool name), once per distinct reply
                split[key] = await _split_tokens(session, base, model, reply, call.name)
            lps = await token_logprobs(session, base, model, full[:k], reply)
        j = split[key]
        return [effective(removed, cs.parent), sum(lps[:j]), sum(lps[j:])]

    res = await asyncio.gather(*(score(r) for r in rows))
    return {"call": [call.name, call.args], "rows": [r for r in res if r is not None],
            "failed": sum(r is None for r in res)}


# ------------------------------------------------------------------ self-explanation (full)

SELF_EXPLAIN = """You are auditing one decision of an LLM coding agent.

The agent was given the context below (split into numbered units) and replied with a tool call.
Action family (E): it called the `{tool}` tool.
Choice within that family (A): {target}
The exact call: {call}

Context units (id: text):
{units}

1. Which units decided the choice A, i.e. without them the agent would still call `{tool}` but with a different command or arguments?
2. Which units made the agent act at all, i.e. without them it would not have called `{tool}` at this step?
A unit can be in both lists. Leave a list empty if nothing in the context does that (e.g. the choice is the model's habit).
Answer with JSON only: {{"choice": ["id", ...], "action": ["id", ...]}}"""


def self_explain_prompt(cs: Case, call: ToolCall | None) -> str:
    lines = "\n".join(f"{u.id}: {' '.join(u.text.split())}" for u in cs.units)
    return SELF_EXPLAIN.format(tool=cs.gtarget or (call.name if call else "?"), target=cs.target,
                               call=f"{call.name}({json.dumps(call.args)})" if call else "?", units=lines)


def parse_self_explain(raw: str, ids: set[str]) -> tuple[list[str], list[str]]:
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
    m = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    try:
        obj = json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        obj = {}
    pick = lambda k: list(dict.fromkeys(str(x) for x in (obj.get(k) or []) if str(x) in ids))  # noqa: E731
    return pick("choice"), pick("action")


async def run_self_explain(cs: Case, call: ToolCall | None, args, rp: Replayer, session) -> dict:
    body = {"model": cs.body.get("model", ""), "max_tokens": 1024,
            "messages": [{"role": "user", "content": self_explain_prompt(cs, call)}],
            **(args.extra_body or {}), "temperature": 0.0}
    try:
        resp, *_ = await rp.call(session, body)
        raw = ((resp.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)[:300]}
    choice, action = parse_self_explain(raw, {u.id for u in cs.units})
    return {"raw": raw[:1500], "choice": choice, "action": action}


# ------------------------------------------------------------------ driver

async def one_case(tc: TableCase, args, rp: Replayer, seed: int) -> dict:
    t0 = time.time()
    cs = Case(tc, args)
    out = {"case": tc.name, "design": tc.design, "target": cs.target, "base": args.base,
           "units": [u.id for u in cs.units], "parent": cs.parent, "designs": {}}
    async with ClientSession(timeout=ClientTimeout(total=900, sock_connect=30)) as session:
        designs = sorted(args.designs, key=lambda d: parse_design(d)[0])  # unforced first: they resolve E
        base_samples = []
        for d in designs:
            r = await run_design(cs, d, args, rp, session, seed)
            base_samples += [s for s in r.pop("_samples", []) if s is not None]
            out["designs"][d] = r
        out["given"] = cs.gtarget or None
        call = representative_call(cs, base_samples)
        out["call"] = [call.name, call.args] if call else None
        if args.cc_masks and call is not None and cs.fmt == "openai":
            try:
                out["contextcite"] = await run_contextcite(cs, call, args, session, seed)
            except Exception as e:  # noqa: BLE001 - keep the designs even if scoring fails
                out["contextcite"] = {"error": f"{type(e).__name__}: {e}"[:300]}
        if args.self_explain:
            out["self_explain"] = await run_self_explain(cs, call, args, rp, session)
    out["seconds"] = round(time.time() - t0, 1)
    out["replays"] = sum(len(d.get("rows", [])) for d in out["designs"].values()) + bool(args.self_explain)
    return out


def _fname(name: str) -> str:
    return name.replace("/", "__") + ".json"


async def main_async(args) -> int:
    cases = phase6_cases(args.cases, args.case_seed)
    if args.tables:  # exactly the tabled cases
        tabled = {p.name for p in args.tables.glob("*.json")}
        cases = [c for c in cases if _fname(c.name) in tabled]
    if args.only:
        cases = [c for c in cases if any(o in c.name or o == c.design for o in args.only)]
    if args.limit:
        cases = cases[:args.limit]
    out = args.out / "raw"
    out.mkdir(parents=True, exist_ok=True)
    todo = [c for c in cases if not (out / _fname(c.name)).exists()]
    print(f"{len(cases)} cases, {len(cases) - len(todo)} done, {len(todo)} to run; designs {args.designs}, "
          f"M={args.m}, cc={args.cc_masks}, seed {args.seed}", flush=True)
    if not todo:
        return 0
    api_key, _ = resolve_api_key("openai", args.base_url, None, free=args.free)
    base = args.base_url.rstrip("/")
    ex = todo[0].case.step
    rp = Replayer(ex.fmt, base + ex.record["request"]["path"],
                  build_headers(ex.fmt, ex.record["request"].get("headers"), api_key or ""),
                  Ledger(args.ledger, args.budget), base, estimate_cost(ex, base, free=args.free),
                  args.concurrency, free=args.free)
    sem = asyncio.Semaphore(args.parallel_cases)
    t0, done = time.time(), 0

    async def one(tc: TableCase):
        nonlocal done
        async with sem:
            try:
                r = await one_case(tc, args, rp, args.seed)
            except Exception as e:  # noqa: BLE001 - one bad case must not stop the suite
                print(f"ERROR {tc.name}: {type(e).__name__}: {e}", flush=True)
                return
            (out / _fname(tc.name)).write_text(json.dumps(r, default=str))
            done += 1
            e_rate = {d: (sum(row[2] for row in v["rows"]) / max(1, len(v["rows"]))) for d, v in r["designs"].items()
                      if "rows" in v}
            print(f"done {tc.name:48s} units={len(r['units'])} replays={r['replays']} "
                  f"E-rate {' '.join(f'{d}={x:.2f}' for d, x in e_rate.items())} "
                  f"cc={len((r.get('contextcite') or {}).get('rows', []))} {r['seconds']}s "
                  f"[{done}/{len(todo)}, {time.time() - t0:.0f}s]", flush=True)

    await asyncio.gather(*(one(c) for c in todo))
    print(f"finished {done}/{len(todo)} in {time.time() - t0:.0f}s", flush=True)
    return 0 if done == len(todo) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Phase 7.1 baselines: raw replay data")
    ap.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--no-thinking-param", action="store_true")
    ap.add_argument("--extra-body", type=parse_extra_body, default={})
    ap.add_argument("--free", action="store_true")
    ap.add_argument("--designs", nargs="+", default=list(DESIGNS))
    ap.add_argument("-m", type=int, default=512, help="rows per design (the largest budget)")
    ap.add_argument("--base", type=int, default=10, help="rows with nothing removed, first in each design")
    ap.add_argument("--cc-masks", type=int, default=512, help="ContextCite prefills (0: skip)")
    ap.add_argument("--cc-concurrency", type=int, default=32)
    ap.add_argument("--no-self-explain", dest="self_explain", action="store_false")
    ap.add_argument("--tables", type=Path, default=None, help="a Phase 6 tables/ dir: run exactly its cases")
    ap.add_argument("--cases", type=int, default=250, help="suite size (cases6.phase6_cases)")
    ap.add_argument("--case-seed", type=int, default=0, help="seed of the Phase 6 suite")
    ap.add_argument("--seed", type=int, default=0, help="seed of the designs and masks")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--concurrency", type=int, default=128)
    ap.add_argument("--parallel-cases", type=int, default=8)
    ap.add_argument("--budget", type=float, default=1.0)
    ap.add_argument("--ledger", type=Path, default=REPO / ".ctxblame" / "phase7_spend.jsonl")
    ap.add_argument("--out", type=Path, required=True)
    return asyncio.run(main_async(ap.parse_args(argv)))


if __name__ == "__main__":
    sys.exit(main())
