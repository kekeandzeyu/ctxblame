"""Blame: find the context chunks whose removal flips a decision.

1. Baseline: replay the step unchanged. If no decision is reliable, stop
   ("coin flip"); if the recorded one is unusual, blame the usual one.
2. Chunk the request (coarse): system paragraphs, earlier user and assistant
   text, each tool call + result, each turn's reasoning, tool descriptions.
   The user's task is never removed.
3. Search: if removing every chunk keeps the decision, the context does not
   carry it. Otherwise delta debugging finds a minimal set whose removal flips
   it. One chunk = a cause; several = redundant carriers of one cause (only
   removing all of them flips it). Repeat on the rest for further causes.
4. Refine each member to the lines that matter, with the set's other members
   held removed (so it is the only carrier).
5. Measure each member alone, and random same-size controls.

Every test is statistical: replays in batches until the rate is clearly above
or below half the baseline rate (Wilson interval), or ``max_n`` is reached.
"""

from __future__ import annotations

import asyncio
import copy
import json
import os
import random
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Awaitable, Callable

from .ablate import (AblationError, _cut, _segments, _short, _thinking_text, pin_cache_breakpoints, remove_units,
                     text_fields, validate)
from .formats import ANTHROPIC, Decision, ToolCall, extract_decision
from .match import MODES, Matcher, intent
from .pricing import Ledger, resolve_model
from .stats import binom_cdf, binom_sf, holm
from .replay import (FatalReplayError, Replayer, Sample, build_headers, estimate_cost, resolve_api_key,
                     parse_extra_body, sample_decision, summarize, wilson, with_model_override)
from .trace import Step, get_step, load_trace, matcher_for

# ------------------------------------------------------------------ chunks

STUB = "(removed)"


@dataclass
class Chunk:
    id: str
    kind: str  # system | user | assistant | tool result | tool call | thinking | tool desc | line
    label: str
    text: str
    pos: int  # rough offset in the prompt, for cache cost and ordering
    units: tuple = ()  # unit ids for remove_units
    spans: tuple = ()  # ((field path), start, end)
    children: list["Chunk"] = field(default_factory=list)

    @property
    def chars(self) -> int:
        return len(self.text)


def _get(body: dict, path: tuple):
    o = body
    for p in path:
        o = o[p]
    return o


def _line_chunks(parent_id: str, label: str, path: tuple, s: str, base: int, pos: int,
                 min_chars: int = 1) -> list[Chunk]:
    """Sentence/line children of the text s[base:base+len(sub)]."""
    out = []
    unit = "line" if "\n" in s.strip() else "sentence"
    for st, en in _segments(s):
        piece = s[st:en]
        if len(piece.strip()) < min_chars:
            continue
        out.append(Chunk(f"{parent_id}.{len(out) + 1}", "line", f"{label} {unit} {len(out) + 1}",
                         piece.strip(), pos + st, spans=((path, base + st, base + en),)))
    return out


def _paragraphs(s: str) -> list[tuple[int, int]]:
    """Spans of blank-line separated paragraphs (a heading starts a new one)."""
    spans, start = [], None
    lines, off = s.splitlines(keepends=True), 0
    for ln in lines:
        blank = not ln.strip()
        heading = ln.lstrip().startswith("#")
        if blank:
            if start is not None:
                spans.append((start, off))
                start = None
        else:
            if heading and start is not None:
                spans.append((start, off))
                start = None
            if start is None:
                start = off
        off += len(ln)
    if start is not None:
        spans.append((start, off))
    return spans


# Context a harness injects into user turns (Claude Code's <system-reminder>,
# Cline's <environment_details>, ...): not written by the user, so removable.
INJECTED_TAGS = ("system-reminder", "environment_details", "context")
_INJECTED = re.compile(r"<(" + "|".join(INJECTED_TAGS) + r")(?:\s[^>]*)?>(.*?)</\1>", re.S)


def injected_blocks(s: str) -> list[re.Match]:
    """Harness-injected ``<tag>...</tag>`` blocks in a user text, in order."""
    return list(_INJECTED.finditer(s))


def _own_text(s: str) -> str:
    """The user's own text: ``s`` without injected blocks."""
    return _INJECTED.sub("", s).strip()


def _gaps(s: str, blocks: list[re.Match]) -> list[tuple[int, int]]:
    """Spans of ``s`` outside ``blocks`` that hold non-blank text."""
    out, at = [], 0
    for m in blocks + [None]:
        end = m.start() if m else len(s)
        if s[at:end].strip():
            out.append((at, end))
        at = m.end() if m else at
    return out


def chunk_request(fmt: str, body: dict, protect: list[str] = (), tool_descs: bool = True) -> list[Chunk]:
    """Coarse chunks (with line-level children), in prompt order. The user's own
    text in the task message and any text in ``protect`` are left out; context
    blocks a harness injects into user turns (``<system-reminder>`` etc.) are
    chunks of kind ``injected``, wherever they are."""
    msgs = body.get("messages") or []
    fields = text_fields(fmt, body)

    def is_result(p: tuple) -> bool:
        return len(p) >= 4 and isinstance(msgs[p[1]].get("content"), list) and \
            msgs[p[1]]["content"][p[3]].get("type") == "tool_result"

    # the task = the latest user message with text the user wrote (in an agent's
    # tool loop that is the first one; in a chat it is the current request); a
    # tool-result turn that only carries injected reminders is not a task
    task_i = None
    for p, s in fields:
        if p[0] == "messages" and msgs[p[1]].get("role") == "user" and _own_text(s) and not is_result(p):
            task_i = p[1]

    # rough prompt positions: tools, then system, then messages
    pos, at = {}, 0
    order = sorted(fields, key=lambda f: (0 if f[0][0] == "tools" else 1 if f[0][0] == "system" else 2,
                                          f[0][1] if len(f[0]) > 1 and isinstance(f[0][1], int) else 0))
    for p, s in order:
        pos[p] = at
        at += len(s)
    msg_pos = {}
    for p, _ in order:
        if p[0] == "messages":
            msg_pos.setdefault(p[1], pos[p])
    for i in range(len(msgs)):
        msg_pos.setdefault(i, msg_pos.get(i - 1, at))

    turn, turns = 0, []
    for m in msgs:
        if m.get("role") == "assistant":
            turn += 1
        turns.append(turn)

    def protected(s: str) -> bool:
        return any(p and p in s for p in protect)

    out: list[Chunk] = []
    # tool descriptions
    if tool_descs:
        for ti, t in enumerate(body.get("tools") or []):
            name = t.get("name") or (t.get("function") or {}).get("name")
            fs = [(p, s) for p, s in fields if p[:2] == ("tools", ti) and s.strip()]
            if not fs:
                continue
            kids = [Chunk(f"tooldesc:{name}.{k + 1}", "line", f"tool {name} description {k + 1}", s.strip(),
                          pos[p], spans=((p, 0, len(s)),)) for k, (p, s) in enumerate(fs)]
            out.append(Chunk(f"tooldesc:{name}", "tool desc", f"tool {name}: descriptions",
                             "\n".join(s for _, s in fs), pos[fs[0][0]], spans=tuple(k.spans[0] for k in kids),
                             children=kids if len(kids) > 1 else []))
    # system paragraphs (Anthropic system blocks, OpenAI system messages)
    for p, s in fields:
        is_sys = p[0] == "system" or (p[0] == "messages" and msgs[p[1]].get("role") in ("system", "developer"))
        if not is_sys:
            continue
        tag = f"sys{p[1] if len(p) > 1 and p[0] == 'system' else ''}" if p[0] == "system" else f"sys@msg{p[1]}"
        for k, (st, en) in enumerate(_paragraphs(s), 1):
            text = s[st:en]
            if protected(text):
                continue
            cid = f"{tag}.p{k}"
            label = f"system ¶{k}"
            kids = _line_chunks(cid, label, p, text, st, pos[p])
            out.append(Chunk(cid, "system", label, text.strip(), pos[p] + st, spans=((p, st, en),),
                             children=kids if len(kids) > 1 else []))
    # messages
    pair_fields: dict[str, list[tuple[tuple, str]]] = {}
    for p, s in fields:
        if p[0] != "messages":
            continue
        m = msgs[p[1]]
        if fmt == ANTHROPIC and len(p) >= 4 and m["content"][p[3]].get("type") == "tool_result":
            pair_fields.setdefault(m["content"][p[3]]["tool_use_id"], []).append((p, s))
        elif fmt != ANTHROPIC and m.get("role") == "tool":
            pair_fields.setdefault(m["tool_call_id"], []).append((p, s))

    for i, m in enumerate(msgs):
        role = m.get("role")
        if role in ("system", "developer"):
            continue
        t = turns[i]
        # injected context blocks inside user turns (the task's included)
        if role == "user":
            for p, s in fields:
                if p[0] != "messages" or p[1] != i or is_result(p):
                    continue
                where = f"b{p[3]}" if len(p) >= 4 else "s"
                for k, mt in enumerate(injected_blocks(s), 1):
                    inner = mt.group(2)
                    if not inner.strip() or protected(inner):
                        continue
                    cid = f"inj:msg[{i}].{where}#{k}"
                    label = f"turn {t} user message <{mt.group(1)}> {k}"
                    kids = _line_chunks(cid, label, p, inner, mt.start(2), pos[p] + mt.start(2))
                    out.append(Chunk(cid, "injected", label, inner.strip(), pos[p] + mt.start(),
                                     spans=((p, mt.start(), mt.end()),),
                                     children=kids if len(kids) > 1 else []))
        if i == task_i:
            continue
        # plain text of user / assistant messages
        for p, s in fields:
            if p[0] != "messages" or p[1] != i or not s.strip() or protected(s):
                continue
            if role == "tool" or is_result(p):
                continue
            if role not in ("user", "assistant"):
                continue
            blocks = injected_blocks(s) if role == "user" else []
            if blocks:  # the user's own text around injected blocks, one chunk per stretch
                label = f"turn {t} user message"
                for st, en in _gaps(s, blocks):
                    cid = f"text:{'.'.join(map(str, p[1:]))}@{st}"
                    kids = _line_chunks(cid, label, p, s[st:en], st, pos[p] + st)
                    out.append(Chunk(cid, role, label, s[st:en].strip(), pos[p] + st, spans=((p, st, en),),
                                     children=kids if len(kids) > 1 else []))
                continue
            only_text = isinstance(m.get("content"), str) and not m.get("tool_calls") or (
                isinstance(m.get("content"), list) and all(b.get("type") == "text" for b in m["content"])
                and len(m["content"]) == 1)
            cid = f"msg[{i}]" if only_text else f"text:{'.'.join(map(str, p[1:]))}"
            label = f"turn {t} {'user message' if role == 'user' else 'assistant text'}"
            kids = _line_chunks(cid, label, p, s, 0, pos[p])
            out.append(Chunk(cid, role, label, s.strip(), pos[p],
                             units=(f"msg[{i}]",) if only_text else (),
                             spans=() if only_text else ((p, 0, len(s)),),
                             children=kids if len(kids) > 1 else []))
        # reasoning
        th = _thinking_text(fmt, m)
        if th:
            out.append(Chunk(f"thinking:msg[{i}]", "thinking", f"turn {t} reasoning", th, msg_pos[i],
                             units=(f"thinking:msg[{i}]",)))
        # tool calls with their results
        calls = []
        if fmt == ANTHROPIC and isinstance(m.get("content"), list):
            calls = [(b["id"], b["name"], json.dumps(b.get("input"), ensure_ascii=False))
                     for b in m["content"] if b.get("type") == "tool_use"]
        elif m.get("tool_calls"):
            calls = [(c["id"], (c.get("function") or {}).get("name"), (c.get("function") or {}).get("arguments"))
                     for c in m["tool_calls"]]
        for cid, name, args in calls:
            res = pair_fields.get(cid, [])
            label = f"turn {t} {name}({_short(str(args), 50)})"
            if any(protected(s) for _, s in res):
                continue
            kids = []
            for p, s in res:
                kids += _line_chunks(f"pair:{cid}", label + " result", p, s, 0, pos[p])
            for n, k in enumerate(kids, 1):
                k.id = f"pair:{cid}.{n}"
                k.label = f"{label} result line {n}"
            out.append(Chunk(f"pair:{cid}", "tool call", label + " + result",
                             "\n".join(s for _, s in res), msg_pos[i], units=(f"pair:{cid}",),
                             children=kids if len(kids) > 1 else []))
    out.sort(key=lambda c: c.pos)
    return out


def apply_chunks(fmt: str, body: dict, chunks: list[Chunk]) -> dict:
    """The request with these chunks removed; always a valid request or AblationError."""
    b = copy.deepcopy(body)
    units: list[str] = []
    by_path: dict[tuple, list[tuple[int, int]]] = {}
    for c in chunks:
        units += c.units
        for p, st, en in c.spans:
            by_path.setdefault(tuple(p), []).append((st, en))
    for p, spans in by_path.items():
        spans.sort()
        merged: list[list[int]] = []
        for st, en in spans:
            if merged and st <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], en)
            else:
                merged.append([st, en])
        s = _get(b, p)
        for st, en in reversed(merged):
            s = _cut(s, st, en)
        o = _get(b, p[:-1])
        o[p[-1]] = s
    # tidy what the cuts emptied
    if fmt == ANTHROPIC and isinstance(b.get("system"), list):
        b["system"] = [x for x in b["system"] if not ("text" in x and not x["text"].strip())]
        if not b["system"]:
            del b["system"]
    elif fmt == ANTHROPIC and isinstance(b.get("system"), str) and not b["system"].strip():
        del b["system"]
    for i, m in enumerate(b.get("messages") or []):
        c = m.get("content")
        if isinstance(c, list):
            c = [x for x in c if not (x.get("type") == "text" and not x.get("text", "").strip())]
            m["content"] = c
            if not c:
                units.append(f"msg[{i}]")
        elif isinstance(c, str) and not c.strip() and m.get("role") != "tool" and not m.get("tool_calls"):
            units.append(f"msg[{i}]")
    seen: set[str] = set()
    units = [u for u in units if not (u in seen or seen.add(u))]
    # the first user message cannot go (Anthropic requires the conversation to
    # start with one); keep it as a stub instead
    msgs = b.get("messages") or []
    first = next((i for i, m in enumerate(msgs) if m.get("role") == "user"), None)
    if first is not None and f"msg[{first}]" in units and not any(
            x.get("type") == "tool_result" for x in msgs[first].get("content") or [] if isinstance(x, dict)):
        units.remove(f"msg[{first}]")
        msgs[first] = {**msgs[first], "content": STUB}
    b = remove_units(fmt, b, units) if units else b
    problems = validate(fmt, b)
    if problems:
        raise AblationError("; ".join(problems))
    return b


# ------------------------------------------------------------------ tests


@dataclass
class Outcome:
    k: int
    n: int
    verdict: str  # flipped | kept | unclear | collapsed | rejected | error
    cost: float = 0.0
    dist: list = field(default_factory=list)
    note: str = ""
    k_given: int | None = None
    n_total: int | None = None
    given_verdict: str | None = None  # collapsed | intact | unclear

    @property
    def rate(self) -> float | None:
        return self.k / self.n if self.n else None

    @property
    def given_rate(self) -> float | None:
        return self.k_given / self.n_total if self.k_given is not None and self.n_total else None

    @property
    def flipped(self) -> bool:
        return self.verdict == "flipped"

    @property
    def collapsed(self) -> bool:
        return self.verdict == "collapsed"

    def __str__(self) -> str:
        if self.verdict in ("rejected", "error"):
            return self.verdict
        if self.k_given is not None and self.n_total is not None:
            if self.verdict == "collapsed":
                return f"collapsed (given {self.k_given}/{self.n_total})"
            return f"{self.k}/{self.n} (given {self.k_given}/{self.n_total})"
        return f"{self.k}/{self.n}"


class BudgetStop(Exception):
    pass


Test = Callable[[frozenset], Awaitable[Outcome]]


def decide(k: int, n: int, threshold: float, max_n: int, min_flip_n: int = 1) -> str:
    """flipped / kept / unclear, or "more" (replay more). A flip needs at least
    ``min_flip_n`` replays: false flips mislead the search more than false keeps."""
    lo, hi = wilson(k, n)
    if hi < threshold and n >= min_flip_n:
        return "flipped"
    if lo > threshold:
        return "kept"
    if n >= max_n:  # undecided: never call it a flip (keeps the search conservative)
        return "flipped" if hi < threshold else "kept" if k / n > threshold else "unclear"
    return "more"


def decide_conditional(k_target: int, k_given: int, n_ok: int, cond_threshold: float,
                       given_threshold: float, max_n: int, min_flip_n: int = 1) -> tuple[str, str]:
    """Conditional verdict on P(target | given) plus P(given).

    Returns ``(verdict, given_verdict)`` where ``verdict`` is one of
    ``collapsed | flipped | kept | unclear | more`` and ``given_verdict`` is
    one of ``collapsed | intact | unclear | more``.
    """
    gv_raw = decide(k_given, n_ok, given_threshold, max_n, min_flip_n)
    if gv_raw == "flipped":
        return "collapsed", "collapsed"
    if gv_raw == "more":
        return "more", "more"
    gv = "intact" if gv_raw == "kept" else "unclear"
    if gv == "unclear" and (n_ok == 0 or k_given / n_ok <= given_threshold):
        return "unclear", "unclear"
    if k_given == 0:
        return ("more" if n_ok < max_n else "unclear"), gv
    lo, hi = wilson(k_target, k_given)
    if hi < cond_threshold and k_given >= min_flip_n:
        return "flipped", gv
    if lo > cond_threshold:
        return "kept", gv
    if n_ok >= max_n:
        min_at_cap = max(1, min_flip_n // 2)
        if hi < cond_threshold and k_given >= min_at_cap:
            return "flipped", gv
        return ("kept" if k_target / k_given > cond_threshold else "unclear"), gv
    return "more", gv


def _representative_call(samples: list[Sample], recorded: Decision, matcher: Matcher,
                         target: str) -> ToolCall | None:
    """First tool call matching ``target`` across baseline samples or the recorded reply."""
    for s in samples:
        if not s.ok:
            continue
        for c in sample_decision(s).calls:
            if matcher._one(c) == target:
                return c
    for c in recorded.calls:
        if matcher._one(c) == target:
            return c
    return recorded.calls[0] if recorded.calls else None


def resolve_given(spec: str | None, key_args: list[str], target: str, matcher: Matcher,
                  samples: list[Sample], recorded: Decision,
                  cwd: str | None = None) -> tuple[Matcher | None, str | None]:
    """Build ``(given_matcher, given_target)`` for conditional blame P(target | given).

    - ``--given none`` disables conditioning.
    - When ``spec`` is omitted and ``--key-arg`` is used, automatically picks the
      coarser ``intent`` when it abstracts away the ``--key-arg`` regex (e.g.
      ``run pytest`` for ``command~^python -m pytest``), otherwise tool ``name``.
    - Explicit specs: ``intent``, ``name``, ``intent:<key>``, ``name:<tool>``,
      ``[Tool:]arg~regex``, an intent phrase (contains space), or a tool name.
    """
    if spec is not None and spec.strip().lower() in ("none", "off", ""):
        return None, None
    if spec is None and not key_args:
        return None, None
    any_call = matcher.any_call
    rep = _representative_call(samples, recorded, matcher, target)
    if spec is None:
        if rep is None:
            return None, None
        rep_int = intent(rep, cwd)
        coarser_intent = (
            rep_int != f"call {rep.name}"
            and bool(key_args)
            and all("~" in k and re.search(k.split("~", 1)[1], rep_int) is None for k in key_args)
        )
        if coarser_intent:
            return Matcher("intent", cwd=cwd, any_call=any_call), rep_int
        return Matcher("name", any_call=any_call), rep.name
    s = spec.strip()
    if s == "intent":
        return (Matcher("intent", cwd=cwd, any_call=any_call), intent(rep, cwd)) if rep else (None, None)
    if s == "name":
        return (Matcher("name", any_call=any_call), rep.name) if rep else (None, None)
    if s.startswith("intent:"):
        return Matcher("intent", cwd=cwd, any_call=any_call), s.split(":", 1)[1].strip()
    if s.startswith("name:"):
        return Matcher("name", any_call=any_call), s.split(":", 1)[1].strip()
    if "~" in s:
        head = s.split("~", 1)[0]
        if ":" in head:
            tool_name, arg_spec = s.split(":", 1)
        else:
            if rep is None:
                raise ValueError(f"--given {s!r} needs a tool call or explicit Tool:arg~regex")
            tool_name, arg_spec = rep.name, s
        gtarget = f"{tool_name}({json.dumps({arg_spec: True}, sort_keys=True, ensure_ascii=False)})"
        return Matcher("args", [arg_spec], any_call=any_call), gtarget
    if " " in s:
        return Matcher("intent", cwd=cwd, any_call=any_call), s
    return Matcher("name", any_call=any_call), s


def _tool_names(fmt: str, body: dict) -> list[str]:
    tools = body.get("tools") or []
    if fmt == ANTHROPIC:
        return [t.get("name") for t in tools if isinstance(t, dict)]
    return [(t.get("function") or {}).get("name") for t in tools if isinstance(t, dict)]


def forcing_unavailable(fmt: str, body: dict, given_matcher: Matcher | None, given_target: str | None) -> str | None:
    """Why the action family E cannot be forced with ``tool_choice`` (None = it can).

    ``tool_choice`` forces a tool name, so only a tool-level E (``--given <tool>`` /
    ``name``) is forced; an intent- or argument-level E (a command family) is not
    identifiable this way. Anthropic does not allow a forced tool with extended thinking."""
    if given_matcher is None or given_target is None:
        return "no action family E (unconditional blame)"
    if given_matcher.mode != "name":
        return f"E is {given_matcher.mode}-level ({given_target!r}); tool_choice forces only a tool name"
    if given_target not in _tool_names(fmt, body):
        return f"E's tool {given_target!r} is not among the request's tools"
    if fmt == ANTHROPIC and (body.get("thinking") or {}).get("type") in ("enabled", "adaptive"):
        return "Anthropic does not allow a forced tool with extended thinking"
    return None


def force_tool_choice(fmt: str, body: dict, tool: str) -> dict:
    """The request with ``tool`` forced: do(E) for a tool-level action family."""
    out = dict(body)
    out["tool_choice"] = ({"type": "tool", "name": tool} if fmt == ANTHROPIC
                          else {"type": "function", "function": {"name": tool}})
    return out


FORCED = "\x00forced"  # cache-key marker: the same removal, replayed with E forced


class Tester:
    """Runs one removal test against the API: batches of replays until decided.

    With ``force_tool`` (E is that tool), ``forced=True`` replays each removal with
    E forced by ``tool_choice`` and tests P(A | do(E), do(-S)) against half of the
    equally forced baseline P(A | do(E)), measured once on the full request (6.4).
    Never compared with the unforced P(A | E)."""

    def __init__(self, step: Step, base_url: str, api_key: str, matcher: Matcher, target: str,
                 chunks: dict[str, Chunk], ledger: Ledger, baseline_rate: float,
                 batch: int = 5, max_n: int = 15, concurrency: int = 8,
                 given_matcher: Matcher | None = None, given_target: str | None = None,
                 baseline_given_rate: float | None = None, free: bool = False,
                 force_tool: str | None = None) -> None:
        self.step, self.base, self.key = step, base_url, api_key
        self.matcher, self.target, self.chunks, self.ledger = matcher, target, chunks, ledger
        self.given_matcher, self.given_target = given_matcher, given_target
        self.threshold = baseline_rate / 2
        self.given_threshold = (baseline_given_rate / 2) if baseline_given_rate is not None else None
        self.batch, self.max_n, self.conc = batch, max_n, concurrency
        self.free = free
        self.force_tool = force_tool
        self.forced_base: Outcome | None = None
        self.forced_threshold: float | None = None
        self.force_note = ""
        self.est = estimate_cost(step, base_url, model=step.body.get("model", ""), free=free)
        self.cache: dict[frozenset, Outcome] = {}
        self.samples: dict[frozenset, list] = {}
        self.log: list[dict] = []
        self.replays = 0
        self.usage = {"input_uncached": 0, "input_cache_read": 0, "input_cache_write": 0, "output": 0}

    def ablated(self, chunks: list[Chunk], forced: bool = False) -> dict:
        """The request without ``chunks``; Anthropic cache breakpoints pinned at the frozen prefix."""
        body = apply_chunks(self.step.fmt, self.step.body, chunks)
        body = pin_cache_breakpoints(self.step.body, body) if self.step.fmt == ANTHROPIC else body
        return force_tool_choice(self.step.fmt, body, self.force_tool) if forced else body

    def _count(self, samples: list[Sample], forced: bool) -> tuple[int, int, int]:
        """(A, of n, ok): with E forced, A among the replies that are in E."""
        ok = [s for s in samples if s.ok]
        if forced:
            in_e = [s for s in ok if self.given_matcher.same(sample_decision(s), self.given_target)]
            return sum(self.matcher.same(None, self.target, s.key, s.keys or [s.key]) for s in in_e), len(in_e), len(ok)
        return sum(self.matcher.same(None, self.target, s.key, s.keys or [s.key]) for s in ok), len(ok), len(ok)

    async def can_force(self) -> bool:
        """Forcing is usable: measure the forced baseline P(A | do(E)) once (``max_n``
        replays of the full request). Unusable if the provider ignores tool_choice or
        forcing E changes the choice even with the whole context."""
        if self.force_tool is None:
            return False
        if self.forced_base is None:
            body = self.ablated([], forced=True)
            if self.ledger.remaining() < self.est * self.max_n:
                raise BudgetStop(f"budget left ${self.ledger.remaining():.3f}")
            try:
                got = await self.replayer().run(body, self.max_n, self.matcher)
            except FatalReplayError as e:
                self.forced_base = Outcome(0, 0, "rejected", note=str(e)[:300])
                self.force_tool, self.force_note = None, f"forcing E was rejected: {str(e)[:200]}"
                return False
            self.replays += len(got)
            k, n, n_ok = self._count(got, True)
            self.forced_base = Outcome(k, n, "kept", sum(s.cost for s in got), k_given=n, n_total=n_ok)
            self.log.append({"removed": [], "forced": True, "baseline": True, "outcome": asdict(self.forced_base)})
            if n_ok == 0 or n < 0.8 * n_ok:
                self.force_tool = None
                self.force_note = f"the provider did not honour tool_choice ({n}/{n_ok} replies used it)"
            elif n == 0 or k / n < 0.5:
                self.force_tool = None
                self.force_note = (f"forcing E changes the choice even with the whole context ({k}/{n}): "
                                   "the forced comparison is not informative here")
            else:
                self.forced_threshold = k / n / 2
        return self.force_tool is not None

    def replayer(self) -> Replayer:
        rec = self.step.record["request"]
        return Replayer(self.step.fmt, self.base + rec["path"], build_headers(self.step.fmt, rec.get("headers"),
                                                                              self.key),
                        self.ledger, self.base, self.est, self.conc, free=self.free)

    async def __call__(self, removed: frozenset, extra: list[Chunk] = (), fresh: bool = False,
                       forced: bool = False) -> Outcome:
        """``fresh``: confirm a finding with at least two more batches, deciding on
        all replays of this removal together (with twice the usual cap).
        ``forced``: replay with E forced (see the class docstring)."""
        key = removed | frozenset(c.id for c in extra)
        if forced:
            if not await self.can_force():
                return Outcome(0, 0, "error", note=self.force_note or "E cannot be forced")
            key = key | {FORCED}
        if key in self.cache and not fresh:
            return self.cache[key]
        try:
            body = self.ablated([self.chunks[i] for i in removed - {FORCED}] + list(extra), forced=forced)
        except AblationError as e:
            out = Outcome(0, 0, "error", note=str(e))
            self.cache[key] = out
            return out
        old = self.samples.get(key, []) if fresh else []
        samples, new, out = list(old), 0, None
        min_new = 2 * self.batch if fresh else 0
        max_n = self.max_n * (2 if fresh else 1)
        extended = fresh
        rp = self.replayer()
        while True:
            if self.ledger.remaining() < self.est * self.batch:
                raise BudgetStop(f"budget left ${self.ledger.remaining():.3f}")
            try:
                got = await rp.run(body, self.batch, self.matcher)
            except FatalReplayError as e:
                out = Outcome(0, 0, "rejected", note=str(e)[:300])
                break
            samples += got
            new += len(got)
            for s in got:
                if s.usage:
                    for k_u in self.usage:
                        self.usage[k_u] += s.usage.get(k_u) or 0
            ok = [s for s in samples if s.ok]
            if forced:  # A among the replies in E, at half the forced baseline
                k, n, n_ok = self._count(samples, True)
                v = decide(k, n, self.forced_threshold, max_n, 2 * self.batch) if n else "more"
                if v == "unclear" and not extended:
                    max_n, extended = max_n * 2, True
                    continue
                if new >= min_new and (v != "more" or new >= max_n * 2):
                    dist = Counter(x for s in ok for x in set(s.keys or [s.key])).most_common(4)
                    out = Outcome(k, n, (v if v != "more" else "unclear") if n else "error",
                                  sum(s.cost for s in samples), dist, k_given=n, n_total=n_ok,
                                  note="" if n else "no reply used the forced tool")
                    break
            elif self.given_matcher is not None and self.given_target is not None:
                k_given, k_target = 0, 0
                for s in ok:
                    if self.given_matcher.same(sample_decision(s), self.given_target):
                        k_given += 1
                        if self.matcher.same(None, self.target, s.key, s.keys or [s.key]):
                            k_target += 1
                v, gv = (decide_conditional(k_target, k_given, len(ok), self.threshold,
                                            self.given_threshold or 0.5, max_n, 2 * self.batch)
                         if ok else ("more", "more"))
                if v == "unclear" and not extended:
                    max_n, extended = max_n * 2, True
                    continue
                if new >= min_new and (v != "more" or new >= max_n * 2):
                    dist = Counter(x for s in ok for x in set(s.keys or [s.key])).most_common(4)
                    out = Outcome(k_target, k_given, v if ok else "error", sum(s.cost for s in samples),
                                  dist, k_given=k_given, n_total=len(ok), given_verdict=gv if ok else None)
                    break
            else:
                k = sum(self.matcher.same(None, self.target, s.key, s.keys or [s.key]) for s in ok)
                v = decide(k, len(ok), self.threshold, max_n, 2 * self.batch) if ok else "more"
                if v == "unclear" and not extended:  # borderline: one extension to twice the replays
                    max_n, extended = max_n * 2, True
                    continue
                if new >= min_new and (v != "more" or new >= max_n * 2):
                    dist = Counter(x for s in ok for x in set(s.keys or [s.key])).most_common(4)
                    out = Outcome(k, len(ok), v if ok else "error", sum(s.cost for s in samples), dist)
                    break
        self.replays += new
        self.samples[key] = samples
        self.cache[key] = out
        self.log.append({"removed": sorted(key - {FORCED}), "fresh": fresh, **({"forced": True} if forced else {}),
                         "outcome": asdict(out)})
        return out

    async def audit(self, removed: frozenset, n: int, forced: bool = False) -> Outcome:
        """``n`` fresh replays of this removal, decided once with no peeking. Never
        cached and never read by the search, so the search cannot have selected on them."""
        if forced and not await self.can_force():
            return Outcome(0, 0, "error", note=self.force_note or "E cannot be forced")
        try:
            body = self.ablated([self.chunks[i] for i in removed], forced=forced)
        except AblationError as e:
            return Outcome(0, 0, "error", note=str(e))
        if self.ledger.remaining() < self.est * n:
            raise BudgetStop(f"budget left ${self.ledger.remaining():.3f}")
        try:
            samples = await self.replayer().run(body, n, self.matcher)
        except FatalReplayError as e:
            return Outcome(0, 0, "rejected", note=str(e)[:300])
        self.replays += len(samples)
        for s in samples:
            for k_u in self.usage:
                self.usage[k_u] += (s.usage or {}).get(k_u) or 0
        ok = [s for s in samples if s.ok]
        cost = sum(s.cost for s in samples)
        dist = Counter(x for s in ok for x in set(s.keys or [s.key])).most_common(4)
        same = lambda s: self.matcher.same(None, self.target, s.key, s.keys or [s.key])  # noqa: E731
        if forced:
            k, m, n_ok = self._count(samples, True)
            v = decide(k, m, self.forced_threshold, m, 1) if m else "error"
            out = Outcome(k, m, "unclear" if v == "more" else v, cost, dist, k_given=m, n_total=n_ok)
            self.log.append({"removed": sorted(removed), "audit": True, "forced": True, "outcome": asdict(out)})
            return out
        if self.given_matcher is not None and self.given_target is not None:
            given = [s for s in ok if self.given_matcher.same(sample_decision(s), self.given_target)]
            k_t = sum(same(s) for s in given)
            v, gv = decide_conditional(k_t, len(given), len(ok), self.threshold, self.given_threshold or 0.5,
                                       len(ok), 1) if ok else ("error", None)
            out = Outcome(k_t, len(given), "unclear" if v == "more" else v, cost, dist, k_given=len(given),
                          n_total=len(ok), given_verdict="unclear" if gv == "more" else gv)
        else:
            k = sum(same(s) for s in ok)
            v = decide(k, len(ok), self.threshold, len(ok), 1) if ok else "error"
            out = Outcome(k, len(ok), "unclear" if v == "more" else v, cost, dist)
        self.log.append({"removed": sorted(removed), "audit": True, "outcome": asdict(out)})
        return out

    def p_value(self, o: Outcome, kind: str) -> float:
        return audit_p(o, kind, self.threshold, self.given_threshold or 0.5, self.forced_threshold)


def audit_p(o: Outcome, kind: str, threshold: float, given_threshold: float,
            forced_threshold: float | None = None) -> float:
    """One-sided exact binomial p-value of an audit outcome, at the search's own thresholds.

    flip     H0: P(A | E, removal) >= threshold   (the removal does not flip the choice)
    restore  H0: P(A | E, removal) <= threshold   (keeping the member does not restore it)
    collapse H0: P(E | removal) >= given_threshold
    intact   H0: P(E | removal) <= given_threshold  (keeping the member does not restore E)
    forced_flip     H0: P(A | do(E), removal) >= forced_threshold
    forced_restore  H0: P(A | do(E), removal) <= forced_threshold

    The thresholds come from the baseline replays (forced: the forced baseline),
    which the audit does not reuse, so the tests are exact conditional on them.
    """
    if o.verdict in ("error", "rejected"):
        return 1.0
    if kind in ("forced_flip", "forced_restore"):
        if forced_threshold is None:
            return 1.0
        return (binom_cdf if kind == "forced_flip" else binom_sf)(o.k, o.n, forced_threshold)
    if kind == "flip":
        return binom_cdf(o.k, o.n, threshold)
    if kind == "restore":
        return binom_sf(o.k, o.n, threshold)
    if kind == "collapse":
        return binom_cdf(o.k_given or 0, o.n_total or 0, given_threshold)
    if kind == "intact":
        return binom_sf(o.k_given or 0, o.n_total or 0, given_threshold)
    raise ValueError(kind)


# ------------------------------------------------------------------ search


async def ddmin(items: list[str], test: Callable[[frozenset], Awaitable[Outcome]],
                base: frozenset = frozenset(),
                pred: Callable[[Outcome], bool] | None = None) -> list[str]:
    """Minimal subset S of items with pred(test(base | S)) true, assuming
    pred(test(base | items)) is true. Subsets try suffixes first and complements
    keep prefixes intact first, maximizing KV prompt-cache hits."""
    hit = pred or (lambda o: o.flipped)
    n = 2
    while len(items) >= 2:
        size = -(-len(items) // n)
        parts = [items[i:i + size] for i in range(0, len(items), size)]
        found = False
        for p in reversed(parts):
            if hit(await test(base | frozenset(p))):
                items, n, found = p, 2, True
                break
        if not found and len(parts) > 2:
            for p in parts:  # omit prefix parts first so comp keeps the earliest prefix intact
                comp = [x for x in items if x not in p]
                if hit(await test(base | frozenset(comp))):
                    items, n, found = comp, max(n - 1, 2), True
                    break
        if not found:
            if n >= len(items):
                break
            n = min(len(items), n * 2)
    return items


@dataclass
class Cause:
    members: list[str]  # chunk ids (refined to lines where that helped)
    together: Outcome | None = None  # all members removed
    alone: dict[str, Outcome] = field(default_factory=dict)
    restored: dict[str, Outcome] = field(default_factory=dict)  # C \ {c_i}: keeping c_i alone restores
    controls: list[tuple[str, Outcome]] = field(default_factory=list)
    role: str = "cause"  # cause | precondition
    removal: list[str] = field(default_factory=list)  # what is removed to confirm it (default: members)
    # audit stage (fresh replays): outcome per test, IUT p-value, Holm-adjusted p-value
    audit: dict[str, Outcome] = field(default_factory=dict)
    p_value: float | None = None
    p_adjusted: float | None = None
    certified: bool | None = None  # None = not audited
    # bundle members coupled with E: keeping one while removing the rest of the
    # bundle stops the action family, so whether it restores the choice is untestable
    # (unless E can be forced: then its restoration is tested with E forced)
    coupled: list[str] = field(default_factory=list)
    # a choice claim with E forced (tool_choice): removing the members flips P(A | do(E))
    forced: bool = False
    # a precondition: with E forced, does removing it also change the choice?
    # True = triggers_and_steers (set when its forced cause is confirmed and audited)
    steers: bool | None = None
    steer_test: Outcome | None = None

    @property
    def relation(self) -> str:
        """AND (individually necessary) vs. OR (minimal hitting set of redundant backups)."""
        if self.role == "precondition":
            return "and_precondition" if len(self.members) == 1 else "or_preconditions"
        return "and_cause" if len(self.members) == 1 else "or_carriers"

    @property
    def specific(self) -> bool | None:
        """Do same-size random removals leave the decision (or action family) alone?"""
        if not self.controls:
            return None
        if self.role == "precondition":
            ok = sum((o.given_verdict == "intact") if o.given_verdict is not None else (o.verdict == "kept")
                     for _, o in self.controls)
            return ok > len(self.controls) / 2
        return sum(o.verdict == "kept" for _, o in self.controls) > len(self.controls) / 2


def _tier_kind(cid: str, by_id: dict[str, Chunk]) -> int:
    """0 = tool schemas, 1 = system prompt, 2 = conversation history."""
    c = by_id[cid]
    if c.kind == "tool desc" or cid.startswith("tooldesc:"):
        return 0
    if c.kind == "system" or cid.startswith("sys"):
        return 1
    return 2


def partition_tiers(remaining: list[str], by_id: dict[str, Chunk]) -> list[list[str]]:
    """Partition ``remaining`` into prefix-to-suffix KV-cache tiers:
    [Tool Schemas, System Prompt, Early History, Tail History] (empty tiers omitted).
    For synthetic chunk lists without tool/system kinds, splits into contiguous tiers."""
    if len(remaining) <= 2:
        return [list(remaining)] if remaining else []
    has_structured = any(_tier_kind(cid, by_id) in (0, 1) for cid in remaining)
    if has_structured:
        t0 = [cid for cid in remaining if _tier_kind(cid, by_id) == 0]
        t1 = [cid for cid in remaining if _tier_kind(cid, by_id) == 1]
        hist = [cid for cid in remaining if _tier_kind(cid, by_id) == 2]
        if len(hist) >= 3:
            mid = len(hist) // 2
            tiers = [t0, t1, hist[:mid], hist[mid:]]
        else:
            tiers = [t0, t1, hist]
        return [t for t in tiers if t]
    n_tiers = 4 if len(remaining) >= 4 else 2
    size = -(-len(remaining) // n_tiers)
    return [remaining[i:i + size] for i in range(0, len(remaining), size)]


async def _widen_suffix(tiers: list[list[str]], test, base: frozenset,
                        pred: Callable[[Outcome], bool]) -> tuple[Outcome, int]:
    """Probe cumulative suffix windows from tail to prefix, stopping at the first
    window satisfying ``pred``. Preserves KV-cache hits on untouched prefix tiers."""
    window: list[str] = []
    last_out = Outcome(0, 0, "kept")
    for i in range(len(tiers) - 1, -1, -1):
        window = tiers[i] + window
        last_out = await test(base | frozenset(window))
        if pred(last_out):
            return last_out, i
    return last_out, -1


async def _stratified_ddmin(tiers: list[list[str]], test, pred: Callable[[Outcome], bool],
                            base: frozenset = frozenset()) -> list[str]:
    """Find a minimal hitting subset across suffix-to-prefix ``tiers`` assuming
    ``tiers[0]`` is the earliest newly added tier needed for ``pred`` and
    ``tiers[1:]`` alone did not satisfy ``pred``.

    Shrinks ``tiers[0]`` first (narrowing prefix mutations quickly), then checks
    if it suffices alone; if not, recursively widens/shrinks ``tiers[1:]`` with
    the minimal prefix piece held removed."""
    if not tiers:
        return []
    if len(tiers) == 1:
        return await ddmin(tiers[0], test, base, pred=pred)
    head, tail_tiers = tiers[0], tiers[1:]
    tail_all = [x for t in tail_tiers for x in t]
    # Check if the newly added tier alone suffices (common for single system/tool rules)
    if pred(await test(base | frozenset(head))):
        return await ddmin(head, test, base, pred=pred)
    # Cross-tier redundant bundle: shrink head with tail held removed
    s_head = await ddmin(head, test, base | frozenset(tail_all), pred=pred)
    new_base = base | frozenset(s_head)
    if pred(await test(new_base)):
        return s_head
    # Recursively widen & shrink only the suffix tiers still needed given s_head
    _, hit_idx = await _widen_suffix(tail_tiers, test, new_base, pred)
    if hit_idx < 0:
        return s_head + tail_all
    s_tail = await _stratified_ddmin(tail_tiers[hit_idx:], test, pred, base=new_base)
    return s_head + s_tail


async def _fallback_window(tiers: list[list[str]], test, base: frozenset,
                           pred: Callable[[Outcome], bool]) -> tuple[Outcome, list[str]] | None:
    """When no suffix window hits, the effect can still be non-monotonic: removing
    *everything* may fall back on the model's habit while removing only some tiers
    flips it (e.g. the carriers sit in tool schemas + system prompt, and the kept
    history steers the model elsewhere once they are gone). Try single tiers (tail
    first), then cumulative prefix windows; return the first window that hits."""
    if len(tiers) < 2:
        return None
    windows: list[list[str]] = [t for t in reversed(tiers)]
    windows += [[x for t in tiers[:i] for x in t] for i in range(2, len(tiers))]
    for w in windows:
        out = await test(base | frozenset(w))
        if pred(out):
            return out, w
    return None


async def _flipping_lines(cid: str, by_id: dict[str, Chunk], test, pred: Callable[[Outcome], bool],
                          max_single: int = 12) -> list[str]:
    """Lines inside chunk ``cid`` whose removal alone satisfies ``pred``. Used inside
    a precondition: the chunk as a whole is needed for the action (removing it stops
    the agent), but one of its lines may decide *how* the agent acts."""
    kids = [k.id for k in by_id[cid].children]
    if not kids:  # already a line (one member of a redundant precondition): test it alone
        return [cid] if pred(await test(frozenset([cid]))) else []
    if len(kids) <= max_single:
        found = []
        for k in kids:
            if pred(await test(frozenset([k]))):
                found.append(k)
        return found
    if pred(await test(frozenset(kids))):
        return await ddmin(kids, test, frozenset(), pred=pred)
    return []


async def _prune_bundle(members: list[str], by_id: dict[str, Chunk], test,
                        pred: Callable[[Outcome], bool],
                        notes: list[str] | None = None) -> tuple[list[str], dict[str, Outcome]]:
    """Leave-one-in restoration check (C \\ {c_i}) on a multi-member bundle.

    For each member c_i, holds all other members removed and checks whether
    keeping c_i alone restores the decision / action family (i.e. ``not pred``).
    Members whose omission still satisfies ``pred`` are noisy hitchhikers and
    are pruned, yielding a verified minimal hitting set."""
    if len(members) <= 1:
        return list(members), {}
    ordered = sorted(members, key=lambda cid: getattr(by_id[cid], "pos", 0))
    current = list(ordered)
    restored: dict[str, Outcome] = {}
    pruned: list[str] = []
    for cid in ordered:
        if cid not in current or len(current) <= 1:
            continue
        others = [x for x in current if x != cid]
        out = await test(frozenset(others))
        if pred(out):
            current = others
            pruned.append(cid)
            restored.pop(cid, None)
        else:
            restored[cid] = out
    if pruned and len(current) > 1:
        restored = {}
        for cid in list(current):
            if len(current) <= 1:
                break
            others = [x for x in current if x != cid]
            out = await test(frozenset(others))
            if pred(out):
                current = others
                pruned.append(cid)
            else:
                restored[cid] = out
    elif len(current) <= 1:
        restored = {}
    if pruned and notes is not None:
        notes.append(f"pruned non-essential hitchhiker(s): {', '.join(pruned)}")
    keep = set(current)
    return [m for m in members if m in keep], {k: v for k, v in restored.items() if k in keep}


async def _vet_members(members: list[str], restored: dict[str, Outcome], by_id: dict[str, Chunk], test,
                       strict: bool, n_controls: int, pool: list[Chunk], avoid: set[str],
                       rng: random.Random, notes: list[str]) -> tuple[list[str], dict[str, Outcome]]:
    """Stricter checks on the members of an OR bundle, for models whose decision
    also moves when unrelated context goes (where "keeping c_i alone restores it"
    can hold for a neutral line).

    strict: keeping c_i alone must *clearly* restore the decision (verdict kept,
    confirmed with more replays); unclear or collapsed no longer counts.
    n_controls: c_i must still restore it when a random same-size run of other
    lines is removed as well; a line that only helps by being "some context"
    fails this. At least one member is always kept."""
    if len(members) <= 1:
        return members, restored
    keep, bad = list(members), []
    for cid in members:
        if len(keep) <= 1:
            break
        others = frozenset(x for x in keep if x != cid)
        ok = True
        if strict:
            out = await test(others, fresh=True)
            restored[cid] = out
            ok = out.verdict == "kept"
        if ok and n_controls:
            ctls = pick_controls(pool, by_id[cid].chars, set(members) | avoid, n_controls, rng)
            if ctls:
                outs = [await test(others, extra=ctl) for ctl in ctls]
                ok = sum(o.verdict == "kept" for o in outs) > len(outs) / 2
        if not ok:
            keep.remove(cid)
            bad.append(cid)
    if bad:
        notes.append(f"dropped bundle member(s) that do not restore the decision specifically: {', '.join(bad)}")
    return keep, {k: v for k, v in restored.items() if k in keep}


TRIGGERS_AND_STEERS = "triggers_and_steers suspected: "
TRIGGERS_AND_STEERS_FORCED = "triggers_and_steers (E forced): "


def _forced_test(test):
    """``test`` with E forced, in the search's test interface."""
    async def ft(removed: frozenset, extra: list = (), fresh: bool = False) -> Outcome:
        return await test(removed, extra, fresh, forced=True)
    ft.force_tool = None  # a forced test is not forced again
    return ft


def _intact(o: Outcome) -> bool:
    """The action family E clearly survived this removal."""
    return o.given_verdict == "intact"


async def _stabilizer(items: list[str], test) -> list[str] | None:
    """A minimal set K of ``items`` such that removing ``items \\ K`` keeps the
    action family E intact (None if even removing nothing does not).

    Used when what makes the agent act at all is spread over many chunks (each
    found precondition reveals another): instead of stopping, K is protected and
    the choice search goes on over the rest. K is sufficient, not necessary, so it
    is reported as diffuse context, not as a precondition. The search keeps
    prefix chunks first, so its removals are suffixes (prefix-cache friendly)."""
    full = frozenset(items)

    async def keep(kept: frozenset) -> Outcome:
        return await test(full - kept)

    if not _intact(await keep(full)):
        return None
    if _intact(await keep(frozenset())):
        return []
    kept = await ddmin(list(reversed(items)), keep, pred=_intact)
    return [x for x in items if x in set(kept)]


async def _refine_members(members: list[str], by_id: dict[str, Chunk], test,
                          pred: Callable[[Outcome], bool]) -> list[str]:
    refined: list[str] = []
    for cid in members:
        others = frozenset(x for x in members if x != cid) | frozenset(refined)
        kids = [k.id for k in by_id[cid].children]
        # removing all lines of a text chunk is removing the chunk (known to hit);
        # a tool pair keeps its call, so check that the result alone carries it
        whole_text = not by_id[cid].units or by_id[cid].id.startswith("msg[")
        if kids and (whole_text or pred(await test(others | frozenset(kids)))):
            refined += await ddmin(kids, test, others, pred=pred)
        else:
            refined.append(cid)
    return refined


async def audit_findings(findings: list[Cause], auditor, n: int, alpha: float) -> None:
    """Certify each finding on ``n`` fresh replays per test (search/audit split).

    A cause C is certified when removing C flips the choice *and* (for a bundle)
    keeping each member alone restores it: the composite null is a union, so the
    intersection-union test takes the max of the one-sided p-values with no
    multiplicity penalty inside the bundle (Berger, 1982). A precondition is
    tested the same way on P(E). Holm's step-down across all findings then
    controls the family-wise error rate at ``alpha``, conditional on the
    baseline and on the search's choice of hypotheses (which saw none of these
    replays).

    Two stages for every bundle (more than one member) whose stage-1 removal
    flips: stage 1 only chooses the hypothesis (which members to keep and what to
    test for each), and the p-value comes from stage 2 alone, on new fresh replays
    (sample splitting). Stage 2 runs even when stage 1 changed nothing: letting
    stage 1 certify when it changed nothing and stage 2 when it did gives two
    chances at a false certificate (up to 2 alpha). The family Holm controls is
    one final hypothesis per finding. Stage-1 outcomes are kept as ``stage1:*``.
    A single-member finding needs no choice and is audited once.

    Stage 1 sorts the members of a choice bundle by what their leave-one-in test
    (remove the rest of the bundle, keep the member) showed:
    - restores: P(A | E) back above the threshold.
    - hitchhiker: E clearly intact but the choice not restored; dropped.
    - coupled: E itself stops (collapse test at ``alpha``). The member's restoration
      cannot be tested, because removing the rest of the bundle without it changes
      E. It stays in the bundle, and stage 2 tests the collapse instead, so a
      certified coupled member carries the claim "removing the others while
      keeping it stops E" (``Cause.coupled``; ``triggers_and_steers``-style).
    - undetermined (E neither intact nor clearly stopped): kept and tested as
      restoring; a member is never dropped on a test that says nothing about it.

    When E can be forced (``auditor.can_force()``, 6.4), a coupled member's
    restoration is testable after all: stage 1 replays its leave-one-in removal
    with E forced. If keeping it restores the choice under do(E), stage 2 tests
    that (``forced:<id>``); if the choice is clearly not restored, it is a
    hitchhiker and dropped; otherwise the collapse test above is kept. A
    ``forced`` finding (a choice claim under do(E)) is audited entirely with E
    forced, against the forced baseline."""
    forceable = getattr(auditor, "force_tool", None) is not None  # measured lazily: only a coupled member needs it

    async def run(members: list[str], removal: frozenset, kinds: tuple[str, str], coupled: set[str],
                  forced_restore: set[str], forced: bool):
        audit = {"together": await auditor.audit(removal, n, forced=True) if forced
                 else await auditor.audit(removal, n)}
        p_main = auditor.p_value(audit["together"], kinds[0])
        p_members: dict[str, float] = {}
        if len(members) > 1:
            for cid in members:
                if cid in forced_restore:
                    audit[f"forced:{cid}"] = o = await auditor.audit(removal - {cid}, n, forced=True)
                    p_members[cid] = auditor.p_value(o, "forced_restore")
                    continue
                audit[cid] = await auditor.audit(removal - {cid}, n, forced=True) if forced \
                    else await auditor.audit(removal - {cid}, n)
                p_members[cid] = auditor.p_value(audit[cid], "collapse" if cid in coupled else kinds[1])
        return audit, p_main, p_members

    for f in findings:
        removal = frozenset(f.removal or f.members)
        kinds = (("collapse", "intact") if f.role == "precondition" else
                 ("forced_flip", "forced_restore") if f.forced else ("flip", "restore"))
        audit, p_main, p_members = await run(f.members, removal, kinds, set(), set(), f.forced)
        drop: list[str] = []
        coupled: set[str] = set()
        forced_restore: set[str] = set()
        for cid, p in p_members.items():
            if p <= alpha:
                continue
            o = audit[cid]
            if f.role != "precondition" and not f.forced and o.n_total is not None:  # E observed
                if auditor.p_value(o, "collapse") <= alpha:
                    coupled.add(cid)
                    if forceable and p_main <= alpha and await auditor.can_force():
                        fo = await auditor.audit(removal - {cid}, n, forced=True)
                        audit[f"forced:{cid}"] = fo
                        if auditor.p_value(fo, "forced_restore") <= alpha:
                            forced_restore.add(cid)
                        elif fo.flipped:  # E forced, keeping it does not bring the choice back
                            coupled.discard(cid)
                            drop.append(cid)
                elif o.given_verdict == "intact":
                    drop.append(cid)
            else:
                drop.append(cid)
        if p_main <= alpha and len(f.members) > 1 and len(drop) < len(f.members):
            stage1 = {f"stage1:{k}": o for k, o in audit.items()}
            f.members = [m for m in f.members if m not in drop]
            f.removal = [m for m in (f.removal or []) if m not in drop]
            removal = removal - set(drop)
            audit, p_main, p_members = await run(f.members, removal, kinds, coupled - forced_restore,
                                                 forced_restore & set(f.members), f.forced)
            audit = {**stage1, **audit}
            f.coupled = [m for m in f.members if m in coupled]
        f.audit = audit
        f.p_value = max([p_main, *p_members.values()])
    for f, p in zip(findings, holm([f.p_value for f in findings])):
        f.p_adjusted = p
        f.certified = p <= alpha


async def search(coarse: list[Chunk], test, max_causes: int = 3, refine: bool = True,
                 n_controls: int = 2, rng: random.Random | None = None,
                 control_pool: list[Chunk] = (), max_members: int = 5,
                 notes: list[str] | None = None,
                 preconditions: list[Cause] | None = None,
                 max_preconditions: int = 3, stratify: bool = True,
                 strict_restore: bool = False, member_controls: int = 0,
                 stabilize: bool = True, stabilizers: list[list[str]] | None = None,
                 audit_n: int = 0, alpha: float = 0.05, uncertified: list[Cause] | None = None,
                 force: bool = False) -> tuple[Outcome, list[Cause]]:
    """KV-cache-stratified suffix-first search.

    Probes suffix tiers before prefix tiers to preserve KV prompt-cache hits,
    isolates and auto-protects workflow preconditions (collapsing action family E),
    and prunes noisy hitchhikers via leave-one-in restoration checks (C \\ {c_i}).
    When preconditions keep appearing (``max_preconditions`` reached) or one is
    diffuse (more than ``max_members`` chunks), a minimal stabilizer of E is
    protected instead (once) and the choice search continues (``stabilize``).

    With ``audit_n`` > 0, every finding is then certified on fresh replays
    (``audit_findings``); findings that fail move to ``uncertified``.

    With ``force`` and a tool-level E (``test.force_tool``), each precondition and
    stabilizer is also tested with E forced (6.4): see ``Cause.steers``.

    Returns ``(probe_outcome, causes)``; isolated preconditions are appended to
    ``preconditions``, stabilizers to ``stabilizers`` and search explanations to
    ``notes``."""
    notes = notes if notes is not None else []
    preconds = preconditions if preconditions is not None else []
    stabs = stabilizers if stabilizers is not None else []
    rng = rng or random.Random(0)
    by_id = {c.id: c for c in coarse}
    for c in coarse:
        for k in c.children:
            by_id[k.id] = k
    remaining = [c.id for c in coarse]

    is_collapsed = lambda o: o.collapsed  # noqa: E731
    is_flipped = lambda o: o.flipped  # noqa: E731
    is_hit = lambda o: o.collapsed or o.flipped  # noqa: E731

    protected_ids: set[str] = set()
    raw_preconds: list[Cause] = []
    causes: list[Cause] = []
    first_flip: Outcome | None = None
    last_probe = Outcome(0, 0, "kept")
    stabilized = False

    async def stabilize_rest(why_: str) -> bool:
        """Protect a minimal stabilizer of E among ``remaining``; False = stop searching."""
        nonlocal remaining, stabilized
        if not stabilize:
            notes.append(why_)
            return False
        if stabilized:
            notes.append(why_ + " again with the stabilizer kept; stopped")
            return False
        stabilized = True
        keep = await _stabilizer(list(remaining), test)
        if keep is None:
            notes.append(why_ + "; no stabilizer found (removing nothing does not keep the action family)")
            return False
        stabs.append(keep)
        protected_ids.update(keep)
        remaining = [x for x in remaining if x not in set(keep)]
        notes.append(why_ + f"; kept a minimal stabilizer of the action family ({len(keep)} chunk(s)) "
                     "and searched the rest for the choice")
        return bool(remaining)

    while remaining and len(causes) < max_causes:
        # stratify=False (ablation): one tier, i.e. remove everything first and
        # delta-debug over all chunks, as before the KV-cache-stratified search
        tiers = partition_tiers(remaining, by_id) if stratify else [list(remaining)]
        # After a stabilizer, widen past tiers whose removal stops E and stop at the
        # first flip: the stabilizer showed that removing all the rest keeps E, but a
        # partial removal need not (E is non-monotone in what is removed: a late
        # output without the history that explains it), and there are no more
        # preconditions to protect. The stratified ddmin then counts collapses as
        # "not flipped" and keeps the tier structure that separates the carriers.
        hit = is_flipped if stabilized else is_hit
        probe, hit_idx = await _widen_suffix(tiers, test, frozenset(), hit)
        last_probe = probe
        region = tiers[hit_idx:] if hit_idx >= 0 else []
        if hit_idx < 0:
            alt = await _fallback_window(tiers, test, frozenset(), hit)
            if alt is None:
                if stabilized and not causes and probe.verdict == "kept":
                    notes.append(TRIGGERS_AND_STEERS + "with the stabilizer kept, removing all the rest "
                                 "keeps the choice, so the context that makes the agent act may also steer "
                                 "it (the stabilizer is not split further)")
                break
            probe, window = alt
            region = [window]
            notes.append(f"non-monotonic: removing all of the context keeps the decision, but removing "
                         f"{len(window)} chunk(s) in one tier changes it")

        if probe.collapsed:
            if len(raw_preconds) >= max_preconditions:
                if await stabilize_rest(f"more than {max_preconditions} preconditions"):
                    continue
                break
            s = await _stratified_ddmin(region, test, is_collapsed)
            s, _ = await _prune_bundle(s, by_id, test, is_collapsed, notes)
            if not (await test(frozenset(s))).collapsed:
                break
            if len(s) > max_members:
                if await stabilize_rest(f"diffuse precondition: the smallest removal that stops the action "
                                        f"family has {len(s)} chunks"):
                    continue
                break
            members = await _refine_members(list(s), by_id, test, is_collapsed) if refine else list(s)
            members, restored = await _prune_bundle(members, by_id, test, is_collapsed, notes)
            protected_set = set(members)
            protected_ids |= protected_set
            new_remaining = []
            for cid in remaining:
                if cid in protected_set:
                    continue
                kid_ids = [k.id for k in by_id[cid].children]
                if kid_ids and any(k in protected_set for k in kid_ids):
                    new_remaining.extend(k for k in kid_ids if k not in protected_set)
                else:
                    new_remaining.append(cid)
            remaining = new_remaining
            raw_preconds.append(Cause(members, restored=restored, role="precondition"))
            continue

        # Choice flip
        if first_flip is None:
            first_flip = probe
        s = await _stratified_ddmin(region, test, is_flipped)
        s, _ = await _prune_bundle(s, by_id, test, is_flipped, notes)
        if not (await test(frozenset(s))).flipped:
            break
        if causes:  # a further cause must be small and specific, not "remove lots of anything"
            size = sum(by_id[c].chars for c in s)
            gate = [await test(frozenset(), extra=ctl)
                    for ctl in pick_controls(control_pool, size, set(s) | protected_ids, 2, rng)]
            if len(s) > max_members or sum(o.verdict == "kept" for o in gate) < len(gate) / 2 or not gate:
                notes.append(f"no further specific cause: removing the rest of the context flips the "
                             f"decision only in bulk ({len(s)} chunks, random same-size removals: "
                             f"{', '.join(map(str, gate)) or 'none possible'})")
                break
        elif len(s) > max_members:
            notes.append(f"diffuse: the smallest removal that flips the decision has {len(s)} chunks")
            break
        remaining = [x for x in remaining if x not in s]
        causes.append(Cause(list(s)))

    for pre in raw_preconds:
        pre.together = await test(frozenset(pre.members), fresh=True)
        if not pre.together.collapsed:
            notes.append(f"dropped an unconfirmed precondition ({', '.join(pre.members)}): {pre.together} "
                         "after more replays")
            continue
        if len(pre.members) > 1:
            for cid in pre.members:
                pre.alone[cid] = await test(frozenset([cid]))
        size = sum(by_id[c].chars for c in pre.members)
        for ctl in pick_controls(control_pool, size, set(pre.members), n_controls, rng):
            pre.controls.append((" / ".join(_short(c.text, 40) for c in ctl),
                                 await test(frozenset(), extra=ctl)))
        preconds.append(pre)
    preconds.sort(key=lambda c: c.specific is False)

    # A precondition chunk is needed for the action as a whole, but one of its
    # lines may still decide the choice (a runbook the agent must read to act at
    # all, whose one line says which flag to use): look inside.
    seen = {m for c in causes for m in c.members}
    for pre in preconds:
        for cid in pre.members:
            if len(causes) >= max_causes:
                break
            lines = [x for x in await _flipping_lines(cid, by_id, test, is_flipped) if x not in seen]
            for line in lines[:max_causes - len(causes)]:
                causes.append(Cause([line]))
                seen.add(line)
                notes.append(f"choice carrier inside precondition {cid}: {line}")

    # 6.4: removing a precondition stops E, so P(A | E) says nothing about whether it
    # also steers the choice. With E forced (tool_choice), compare P(A | do(E), do(-S))
    # with the forced baseline P(A | do(E)): a flip makes S triggers_and_steers, and
    # S becomes a choice claim under do(E) (audited like any finding). A stabilizer
    # gets the same test, and if it flips, a forced search for the lines that steer.
    steer_of: dict[int, Cause] = {}
    if force and (preconds or stabs) and getattr(test, "force_tool", None) is not None and await test.can_force():
        ft = _forced_test(test)
        for pre in preconds:
            if len(causes) >= max_causes:
                break
            pre.steer_test = o = await ft(frozenset(pre.members))
            if o.flipped:
                fc = Cause(list(pre.members), forced=True)
                causes.append(fc)
                steer_of[id(fc)] = pre
            elif o.verdict == "kept":
                pre.steers = False
        for keep in stabs:
            if len(causes) >= max_causes:
                break
            if (await ft(frozenset(keep))).flipped:
                s = await ddmin(list(keep), ft, pred=is_flipped)
                causes.append(Cause(list(s), forced=True))
                notes.append(f"{TRIGGERS_AND_STEERS_FORCED}the stabilizer of the action family also steers the "
                             f"choice: with E forced, removing {', '.join(s)} changes it")
    elif force and (preconds or stabs) and getattr(test, "force_note", ""):
        notes.append(f"E not forced: {test.force_note}")

    for cause in causes:
        t_c = _forced_test(test) if cause.forced else test
        if refine:
            cause.members = await _refine_members(cause.members, by_id, t_c, is_flipped)
        cause.members, cause.restored = await _prune_bundle(cause.members, by_id, t_c, is_flipped, notes)
        removal = list(cause.members)  # what is removed to confirm the flip
        cause.removal = removal
        if (strict_restore or member_controls) and not cause.forced:
            # vetted-out members stay in the confirming removal (the flip may need
            # them gone too), but are not reported as carriers
            cause.members, cause.restored = await _vet_members(
                cause.members, cause.restored, by_id, test, strict_restore, member_controls,
                control_pool, protected_ids, rng, notes)
        cause.together = await t_c(frozenset(removal), fresh=True)
        if not cause.together.flipped:
            notes.append(f"dropped an unconfirmed finding ({', '.join(cause.members)}): {cause.together} "
                         "after more replays")
            continue
        if len(cause.members) > 1:
            for cid in cause.members:
                cause.alone[cid] = await t_c(frozenset([cid]))
        size = sum(by_id[c].chars for c in cause.members)
        for ctl in pick_controls(control_pool, size, set(cause.members) | protected_ids, n_controls, rng):
            cause.controls.append((" / ".join(_short(c.text, 40) for c in ctl),
                                   await t_c(frozenset(), extra=ctl)))
    causes = [c for c in causes if c.together and c.together.flipped]
    if audit_n:
        await audit_findings(causes + preconds, test, audit_n, alpha)
        for c in causes + preconds:
            dropped = [k[7:] for k in c.audit if k.startswith("stage1:") and k != "stage1:together"
                       and k[7:] not in c.members]
            if dropped:
                notes.append(f"audit dropped {', '.join(dropped)} (did not restore it with the action family "
                             f"intact); {c.role} re-audited on new fresh replays as {', '.join(c.members)}")
            if c.coupled:
                notes.append(f"audit: {', '.join(c.coupled)} coupled with the action family (keeping it while "
                             "removing the rest of the bundle stops the action), so its restoring role is "
                             "untestable; certified claim for it: that collapse")
        failed = [c for c in causes + preconds if not c.certified]
        for c in failed:
            notes.append(f"not certified on {audit_n} fresh replays per test ({c.role}: {', '.join(c.members)}; "
                         f"p = {c.p_value:.3g}, Holm-adjusted {c.p_adjusted:.3g} > {alpha})")
        if uncertified is not None:
            uncertified.extend(failed)
        causes = [c for c in causes if c.certified]
        preconds[:] = [p for p in preconds if p.certified]
    final = {id(c) for c in causes}
    for fid, pre in steer_of.items():
        if fid in final:
            pre.steers = True
            fc = next(c for c in causes if id(c) == fid)
            notes.append(f"triggers_and_steers: {', '.join(pre.members)}: removing it stops the action family, "
                         f"and with E forced removing {', '.join(fc.members)} also changes the choice "
                         f"({fc.together})")
    causes.sort(key=lambda c: c.specific is False)  # specific causes first
    everything = first_flip if first_flip is not None else last_probe
    return everything, causes


def pick_controls(pool: list[Chunk], size: int, avoid: set[str], n: int, rng: random.Random) -> list[list[Chunk]]:
    """n random runs of consecutive lines (same field) of about ``size`` chars."""
    pool = [c for c in pool if c.id not in avoid and not any(c.id.startswith(a + ".") for a in avoid)
            and not any(a.startswith(c.id + ".") for a in avoid)]
    out, tries = [], 0
    while len(out) < n and tries < 200 and pool:
        tries += 1
        i = rng.randrange(len(pool))
        run, total = [], 0
        for c in pool[i:]:
            if run and c.spans[0][0] != run[0].spans[0][0]:
                break
            run.append(c)
            total += c.chars
            if total >= size * 0.7:
                break
        if size * 0.5 <= total <= size * 1.6 and [c.id for c in run] not in [[x.id for x in r] for r in out]:
            out.append(run)
    return out


# ------------------------------------------------------------------ cli


def add_args(ap) -> None:
    ap.add_argument("trace", type=Path)
    ap.add_argument("--step", type=int, default=None)
    ap.add_argument("-n", type=int, default=10, help="baseline replays (default 10)")
    ap.add_argument("--batch", type=int, default=5, help="replays per batch in each test")
    ap.add_argument("--max-n", type=int, default=15, help="most replays per test")
    ap.add_argument("--match", choices=MODES, default=None)
    ap.add_argument("--key-arg", action="append", default=[])
    ap.add_argument("--first-call", action="store_true",
                    help="compare only the first tool call (default: any of the parallel calls)")
    ap.add_argument("--target", default=None, help="decision to explain (default: the recorded one, or "
                    "the usual one if the recorded one is atypical)")
    ap.add_argument("--given", default=None,
                    help="condition blame on action family E: 'intent', 'name', 'run pytest', 'bash', "
                         "'arg~regex', or 'none' to disable (default: auto when --key-arg is used)")
    ap.add_argument("--protect", action="append", default=[], help="text never to remove")
    ap.add_argument("--no-tool-descs", action="store_true", help="do not consider tool descriptions")
    ap.add_argument("--max-causes", type=int, default=3)
    ap.add_argument("--controls", type=int, default=2)
    ap.add_argument("--no-refine", action="store_true")
    ap.add_argument("--no-stratify", action="store_true",
                    help="ablation: no KV-cache tiers (remove everything first, ddmin over all chunks)")
    ap.add_argument("--strict-restore", action="store_true",
                    help="keep an OR-bundle member only if keeping it alone clearly restores the decision "
                         "(confirmed with more replays); for noisy models")
    ap.add_argument("--member-controls", type=int, default=0, metavar="N",
                    help="each OR-bundle member must still restore the decision when N random same-size "
                         "runs of other lines are removed too (default 0 = off); for noisy models")
    ap.add_argument("--no-stabilize", action="store_true",
                    help="ablation: stop when preconditions run out or are diffuse, instead of keeping a "
                         "minimal stabilizer of the action family and searching on")
    ap.add_argument("--audit-n", type=int, default=20, metavar="N",
                    help="certify each finding on N fresh replays per test, never seen by the search "
                         "(intersection-union within a bundle, Holm across findings); 0 = off (v0.2 behaviour)")
    ap.add_argument("--alpha", type=float, default=0.05,
                    help="family-wise error rate for the audit (default 0.05)")
    ap.add_argument("--no-force", action="store_true",
                    help="ablation: never force the action family with tool_choice; a precondition is then "
                         "not tested for also steering the choice (v0.2.1 behaviour)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--model", default=None, help="override the model name in the replayed request")
    ap.add_argument("--max-tokens", type=int, default=None, help="override max_tokens in the replayed request")
    ap.add_argument("--no-thinking-param", action="store_true",
                    help="strip top-level 'thinking' field from the request body (useful for vLLM / SGLang)")
    ap.add_argument("--extra-body", type=parse_extra_body, default={}, metavar="JSON",
                    help="JSON object merged into every request body, e.g. "
                         "'{\"chat_template_kwargs\": {\"enable_thinking\": false}}' for Qwen3 on vLLM")
    ap.add_argument("--free", action="store_true",
                    help="treat the endpoint as $0/token (skips price-table lookup; API key optional)")
    ap.add_argument("--api-key-env", default=None)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--budget", type=float, default=5.0, help="hard cap on total spend in the ledger (USD)")
    ap.add_argument("--ledger", type=Path, default=Path(".ctxblame/spend.jsonl"))
    ap.add_argument("--out", type=Path, default=Path("runs"))
    ap.add_argument("--json", action="store_true", help="print the JSON report instead of text")


def _serialize_findings(findings: list[Cause], by_id: dict[str, Chunk]) -> list[dict]:
    return [{"relation": c.relation,
             "members": [{"id": m, "kind": by_id[m].kind, "label": by_id[m].label,
                          "text": by_id[m].text} for m in c.members],
             "together": asdict(c.together) if c.together else None,
             "specific": c.specific,
             "alone": {k: asdict(v) for k, v in c.alone.items()},
             "restored": {k: asdict(v) for k, v in c.restored.items()},
             "controls": [{"removed": t, **asdict(o)} for t, o in c.controls],
             "certified": c.certified, "p_value": c.p_value, "p_adjusted": c.p_adjusted,
             "coupled": c.coupled, "forced": c.forced, "steers": c.steers,
             "steer_test": asdict(c.steer_test) if c.steer_test else None,
             "audit": {k: asdict(v) for k, v in c.audit.items()}} for c in findings]


def _certificate(c: Cause) -> str:
    if c.certified is None:
        return ""
    o = c.audit.get("together")
    return f"  certified on fresh replays: {o} (p = {c.p_value:.2g}, Holm {c.p_adjusted:.2g})"


async def why(step: Step, args, api_key: str, base: str, out=None) -> dict:
    step = with_model_override(step, getattr(args, "model", None), getattr(args, "max_tokens", None),
                               bool(getattr(args, "no_thinking_param", False)),
                               getattr(args, "extra_body", None))
    free = bool(getattr(args, "free", False))
    fmt = step.fmt
    mode = args.match or ("args" if args.key_arg else "intent")
    matcher = matcher_for(step, mode, args.key_arg or None, any_call=not args.first_call)
    ledger = Ledger(args.ledger, args.budget)
    start = ledger.total
    recorded_dec = extract_decision(fmt, step.response)
    recorded = matcher.key(recorded_dec)
    report: dict = {"trace": str(args.trace), "step": step.step, "match": mode, "any_call": not args.first_call,
                    "recorded": recorded}

    def say(s=""):
        if not args.json:
            print(s, file=out or sys.stdout, flush=True)

    # 1. baseline
    probe = Tester(step, base, api_key, matcher, recorded, {}, ledger, 1.0, args.n, args.n, args.concurrency,
                   free=free)
    rp = probe.replayer()
    samples = await rp.run(step.body, args.n, matcher)
    target = args.target or recorded
    summ = summarize(samples, target, matcher)
    if not args.target and summ["verdict"] == "atypical":
        target = summ["modal"]
        summ = summarize(samples, target, matcher)
    report.update(target=target, baseline=summ)
    b_rate = summ["same_rate"] or 0.0
    say(f"Decision:  {target}" + ("   (the recorded call was atypical; explaining the usual one)"
                                   if target != recorded and not args.target else ""))
    say(f"Baseline:  {summ['same_decision']}/{summ['n_ok']} replays ({summ['verdict'].replace('_', ' ')})")
    if summ["verdict"] in ("coin_flip", "too_few") or b_rate < 0.5:
        say(f"Stop: {summ['verdict_text']}")
        report.update(result="no_stable_decision", cost=ledger.total - start)
        return report

    notes: list[str] = []
    # 1b. optional conditional action family E (P(target | given))
    given_spec = getattr(args, "given", None)
    given_matcher, given_target = resolve_given(given_spec, args.key_arg, target, matcher, samples,
                                                recorded_dec, matcher.cwd)
    b_given_rate: float | None = None
    b_cond_rate = b_rate
    if given_matcher is not None and given_target is not None:
        ok = [s for s in samples if s.ok]
        b_given_k = sum(given_matcher.same(sample_decision(s), given_target) for s in ok)
        b_cond_k = sum(given_matcher.same(sample_decision(s), given_target)
                       and matcher.same(None, target, s.key, s.keys or [s.key]) for s in ok)
        if not ok or b_given_k / len(ok) < 0.5 or b_given_k == 0 or b_cond_k / b_given_k < 0.5:
            notes.append(f"given {given_target!r} was not reliable at baseline ({b_given_k}/{len(ok)}); "
                         "falling back to unconditional blame")
            given_matcher, given_target = None, None
        else:
            b_given_rate = b_given_k / len(ok)
            b_cond_rate = b_cond_k / b_given_k
            report["given"] = {"mode": given_matcher.mode, "target": given_target,
                               "baseline_given": b_given_k, "baseline_n": len(ok),
                               "baseline_cond": b_cond_k, "baseline_cond_rate": b_cond_rate}
            say(f"Given:     {given_target} ({b_given_k}/{len(ok)} baseline; "
                f"P(decision | given) = {b_cond_k}/{b_given_k})")

    # 2. chunks; can reasoning be removed at all?
    coarse = chunk_request(fmt, step.body, args.protect, not args.no_tool_descs)
    by_id = {c.id: c for c in coarse}
    for c in coarse:
        for k in c.children:
            by_id[k.id] = k
    no_force = forcing_unavailable(fmt, step.body, given_matcher, given_target)
    force = not getattr(args, "no_force", False)
    test = Tester(step, base, api_key, matcher, target, by_id, ledger, b_cond_rate, args.batch, args.max_n,
                  args.concurrency, given_matcher=given_matcher, given_target=given_target,
                  baseline_given_rate=b_given_rate, free=free,
                  force_tool=given_target if force and no_force is None else None)
    think = [c.id for c in coarse if c.kind == "thinking"]
    if think:
        o = await test(frozenset(think))
        if o.verdict == "rejected":
            coarse = [c for c in coarse if c.kind != "thinking"]
            notes.append("reasoning: not removable (the provider requires earlier reasoning to be passed "
                         "back); it is part of the context that cannot be tested")
    say(f"Chunks:    {len(coarse)} ({', '.join(f'{v} {k}' for k, v in Counter(c.kind for c in coarse).items())})")

    # 3-5. search
    pool = [k for c in coarse for k in (c.children or [c]) if c.kind != "thinking" and k.spans]
    preconditions: list[Cause] = []
    stabilizers: list[list[str]] = []
    uncertified: list[Cause] = []
    try:
        everything, causes = await search(coarse, test, args.max_causes, not args.no_refine, args.controls,
                                          random.Random(args.seed), pool, notes=notes,
                                          preconditions=preconditions,
                                          stratify=not getattr(args, "no_stratify", False),
                                          strict_restore=getattr(args, "strict_restore", False),
                                          member_controls=getattr(args, "member_controls", 0),
                                          stabilize=not getattr(args, "no_stabilize", False),
                                          stabilizers=stabilizers,
                                          audit_n=getattr(args, "audit_n", 0),
                                          alpha=getattr(args, "alpha", 0.05), uncertified=uncertified,
                                          force=force)
        stopped = None
    except BudgetStop as e:
        everything, causes, stopped = None, [], str(e)
    report["everything_removed"] = asdict(everything) if everything else None
    if everything is not None:
        if preconditions:
            say(f"Everything else removed (preconditions kept): {everything}" +
                ("  -> the choice comes from the context" if everything.flipped else
                 "  -> given preconditions, no other context carries the choice"))
        else:
            say(f"Everything but the task removed: {everything}" +
                ("  -> the decision comes from the context" if everything.flipped else
                 "  -> the context does not carry it (the task and the model's habits do)"))
    for n, p in enumerate(preconditions, 1):
        together = p.together
        what = "Precondition" if p.specific is not False else "Context needed for action family (not specific)"
        g_lbl = given_target or "action family"
        if len(p.members) == 1:
            say(f"\n{what} {n} (removing it stops {g_lbl}: {together}):")
        else:
            say(f"\n{what} {n} (redundant preconditions for {g_lbl}: {together}):")
        for cid in p.members:
            ch = by_id[cid]
            extra_s = ""
            if cid in p.alone:
                extra_s += f"   alone: {p.alone[cid]}"
            if cid in p.restored:
                extra_s += f"   restores: {p.restored[cid]}"
            say(f"  - {ch.label}: {_short(ch.text, 90)!r}{extra_s}")
        if p.controls:
            say("  controls (random same-size removals): " + ", ".join(str(o) for _, o in p.controls)
                + ("" if p.specific else "  -> NOT specific: random removals stop it too"))
        if p.certified is not None:
            say(_certificate(p))
        if p.steers:
            say(f"  triggers and steers: with {g_lbl} forced, removing it also changes the choice "
                f"({p.steer_test}); see the forced cause below")
        elif p.steers is False:
            say(f"  only a precondition: with {g_lbl} forced, removing it keeps the choice ({p.steer_test})")
    for keep in stabilizers:
        say(f"\nDiffuse context the action family needs (kept while searching the choice; {len(keep)} chunk(s)):")
        for cid in keep:
            say(f"  - {by_id[cid].label}: {_short(by_id[cid].text, 90)!r}")
    for n, c in enumerate(causes, 1):
        together = c.together
        what = "Cause" if c.specific is not False else "Context it needs (not specific)"
        forced_s = f", with {given_target} forced" if c.forced else ""
        if len(c.members) == 1:
            say(f"\n{what} {n} (removing it flips the decision{forced_s}: {together}):")
        else:
            say(f"\n{what} {n} (redundant: only removing all of these flips it{forced_s}: {together}):")
        for cid in c.members:
            ch = by_id[cid]
            extra_s = ""
            if cid in c.alone:
                extra_s += f"   alone: {c.alone[cid]}"
            if cid in c.restored:
                extra_s += f"   restores: {c.restored[cid]}"
            if cid in c.coupled:
                extra_s += "   coupled: keeping it while removing the others stops the action family"
            say(f"  - {ch.label}: {_short(ch.text, 90)!r}{extra_s}")
        if c.controls:
            say("  controls (random same-size removals): " + ", ".join(str(o) for _, o in c.controls)
                + ("" if c.specific else "  -> NOT specific: random removals flip it too"))
        if c.certified is not None:
            say(_certificate(c))
    if not causes and everything is not None and everything.flipped and any("reasoning" in n for n in notes):
        notes.append("removing all removable context flips the decision, but no small set does: the "
                     "reasoning that cannot be removed probably carries it too")
    for note in notes:
        say(f"\nNote: {note}")
    if stopped:
        say(f"\nStopped early: {stopped}")
    cost = ledger.total - start
    usage = dict(test.usage)
    for s in samples:
        if s.usage:
            for k_u in usage:
                usage[k_u] += s.usage.get(k_u) or 0
    total_in = usage["input_uncached"] + usage["input_cache_read"] + usage["input_cache_write"]
    cache_hit_rate = (usage["input_cache_read"] / total_in) if total_in else None
    cache_stats = {**usage, "cache_hit_rate": cache_hit_rate}
    cache_note = f", cache hit {cache_hit_rate:.0%}" if cache_hit_rate is not None else ""
    say(f"\nTests: {len(test.log)}, replays: {test.replays + len(samples)}, cost ${cost:.4f}"
        f"{cache_note} (ledger ${ledger.total:.4f} of ${args.budget:.2f})")
    result = ("causes" if causes else
              "preconditions_only" if preconditions and everything and not everything.flipped else
              "not_in_context" if everything and everything.verdict == "kept" else
              "none_found")
    report.update(result=result,
                  causes=_serialize_findings(causes, by_id),
                  preconditions=_serialize_findings(preconditions, by_id),
                  uncertified=_serialize_findings(uncertified, by_id),
                  audit={"n": getattr(args, "audit_n", 0), "alpha": getattr(args, "alpha", 0.05)},
                  diffuse_preconditions=[[{"id": m, "kind": by_id[m].kind, "label": by_id[m].label,
                                           "text": by_id[m].text} for m in keep] for keep in stabilizers],
                  triggers_and_steers_suspected=any(n.startswith(TRIGGERS_AND_STEERS) for n in notes),
                  forcing={"tool": test.force_tool, "unavailable": no_force if force else "--no-force",
                           "note": test.force_note or None,
                           "baseline": asdict(test.forced_base) if test.forced_base else None,
                           "threshold": test.forced_threshold},
                  cache_stats=cache_stats,
                  notes=notes, stopped=stopped, tests=test.log, cost=cost,
                  replays=test.replays + len(samples))
    return report


def run_cli(args) -> int:
    try:
        step = get_step(load_trace(args.trace), args.step)
    except (LookupError, ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 5
    step = with_model_override(step, args.model, args.max_tokens, args.no_thinking_param, args.extra_body)
    base = (args.base_url or step.record["upstream"]).rstrip("/")
    api_key, key_env = resolve_api_key(step.fmt, base, args.api_key_env, free=args.free)
    if api_key is None:
        print(f"error: set {key_env} in the environment", file=sys.stderr)
        return 2
    resolve_model(step.body.get("model", ""), base, free=args.free)
    try:
        report = asyncio.run(why(step, args, api_key, base))
    except (FatalReplayError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 4
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / f"{args.trace.stem}.step{step.step}.why.json"
    path.write_text(json.dumps(report, indent=1, ensure_ascii=False, default=str))
    if args.json:
        print(json.dumps(report, indent=1, ensure_ascii=False, default=str))
    else:
        print(f"Saved: {path}")
    return 0
