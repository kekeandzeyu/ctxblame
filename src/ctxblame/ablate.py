"""Remove pieces of a recorded request while keeping it a valid request.

Removable units:
  system / system[i]   the system prompt, or one block of it (Anthropic)
  msg[i]               one message (OpenAI system messages are messages too)
  pair:<id>            a tool call together with its result
  tool:<name>          a tool definition
  thinking:msg[i]      the reasoning of one assistant message (thinking blocks,
                       or OpenAI-format ``reasoning_content``); ``thinking`` = all
plus exact text spans (``remove_text``) and a random same-size span of
whole sentences/lines (``remove_random_span``) as a control.

Removing reasoning also gives the tool calls of those messages fresh ids
(and their results). Some providers (seen with DeepSeek) keep earlier
reasoning server-side and silently restore it when they see their own call
ids, so without this the "removed" reasoning still reaches the model. With
fresh ids such a provider refuses the request instead, which is honest.

Rule: a tool call and its result are never separated. Removing either one
(directly or by removing the message holding it) removes both. Messages left
empty are dropped and neighbours with the same role are merged, so the
request stays valid.
"""

from __future__ import annotations

import copy
import json
import random
import re
from dataclasses import dataclass

from .formats import ANTHROPIC


class AblationError(ValueError):
    pass


@dataclass
class Unit:
    id: str
    kind: str
    label: str
    chars: int


# ------------------------------------------------------------------ helpers

def _short(s: str, n: int = 70) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _text_of(content) -> str:
    if isinstance(content, str):
        return content
    out = []
    for b in content or []:
        if isinstance(b, dict):
            if "text" in b:
                out.append(b["text"])
            elif b.get("type") == "tool_result":
                out.append(_text_of(b.get("content")))
            elif b.get("type") == "tool_use":
                out.append(str(b.get("input")))
    return " ".join(out)


def _tool_ids(fmt: str, msg: dict) -> set[str]:
    ids: set[str] = set()
    if fmt == ANTHROPIC:
        for b in msg.get("content") if isinstance(msg.get("content"), list) else []:
            if b.get("type") in ("tool_use", "server_tool_use"):
                ids.add(b["id"])
            elif b.get("type") == "tool_result":
                ids.add(b["tool_use_id"])
    else:
        for c in msg.get("tool_calls") or []:
            ids.add(c["id"])
        if msg.get("role") == "tool":
            ids.add(msg["tool_call_id"])
    return ids


# ------------------------------------------------------------------ listing

def list_units(fmt: str, body: dict) -> list[Unit]:
    units: list[Unit] = []
    if fmt == ANTHROPIC and body.get("system"):
        sysv = body["system"]
        if isinstance(sysv, str):
            units.append(Unit("system", "system", _short(sysv), len(sysv)))
        else:
            for i, b in enumerate(sysv):
                units.append(Unit(f"system[{i}]", "system", _short(b.get("text", "")), len(b.get("text", ""))))
    pairs: dict[str, Unit] = {}
    for i, m in enumerate(body.get("messages") or []):
        text = _text_of(m.get("content"))
        if not text and m.get("tool_calls"):  # OpenAI: show what the turn called
            text = " ".join(f"{(c.get('function') or {}).get('name')}"
                            f"({(c.get('function') or {}).get('arguments')})" for c in m["tool_calls"])
        units.append(Unit(f"msg[{i}]", m.get("role", "?"), _short(text), len(text)))
        if fmt == ANTHROPIC:
            for b in m.get("content") if isinstance(m.get("content"), list) else []:
                if b.get("type") == "tool_use":
                    pairs[b["id"]] = Unit(f"pair:{b['id']}", "tool pair",
                                          _short(f"{b['name']}({b.get('input')})"), 0)
                elif b.get("type") == "tool_result" and b["tool_use_id"] in pairs:
                    pairs[b["tool_use_id"]].chars = len(_text_of(b.get("content")))
        else:
            for c in m.get("tool_calls") or []:
                fn = c.get("function") or {}
                pairs[c["id"]] = Unit(f"pair:{c['id']}", "tool pair",
                                      _short(f"{fn.get('name')}({fn.get('arguments')})"), 0)
            if m.get("role") == "tool" and m.get("tool_call_id") in pairs:
                pairs[m["tool_call_id"]].chars = len(_text_of(m.get("content")))
    units.extend(pairs.values())
    thinking = [(i, _thinking_text(fmt, m)) for i, m in enumerate(body.get("messages") or [])]
    thinking = [(i, s) for i, s in thinking if s]
    if thinking:
        units.append(Unit("thinking", "thinking", f"all reasoning ({len(thinking)} messages)",
                          sum(len(s) for _, s in thinking)))
        units += [Unit(f"thinking:msg[{i}]", "thinking", _short(s), len(s)) for i, s in thinking]
    for t in body.get("tools") or []:
        name = t.get("name") or (t.get("function") or {}).get("name")
        units.append(Unit(f"tool:{name}", "tool def", _short(_tool_description(t)), len(json.dumps(t))))
    return units


def _tool_description(t: dict) -> str:
    return str(t.get("description") or (t.get("function") or {}).get("description") or "")


def _thinking_text(fmt: str, m: dict) -> str:
    if m.get("role") != "assistant":
        return ""
    if fmt == ANTHROPIC:
        c = m.get("content")
        return "\n".join(b.get("thinking", "") for b in c if isinstance(b, dict) and b.get("type") == "thinking") \
            if isinstance(c, list) else ""
    return m.get("reasoning_content") or ""


def _drop_thinking(fmt: str, m: dict) -> dict:
    if fmt == ANTHROPIC:
        c = m.get("content")
        if isinstance(c, list):
            m = {**m, "content": [b for b in c if b.get("type") not in ("thinking", "redacted_thinking")]}
        return m
    return {k: v for k, v in m.items() if k != "reasoning_content"}


# ------------------------------------------------------------------ removal

_UNIT = re.compile(r"^(system|system\[(\d+)\]|msg\[(\d+)\]|pair:(.+)|tool:(.+)|thinking(?::msg\[(\d+)\])?)$")


def remove_units(fmt: str, body: dict, unit_ids: list[str]) -> dict:
    b = copy.deepcopy(body)
    msgs = b.get("messages") or []
    drop_msgs: set[int] = set()
    tool_ids: set[str] = set()
    drop_tools: set[str] = set()
    drop_thinking: set[int] = set()
    for uid in unit_ids:
        m = _UNIT.match(uid)
        if not m:
            raise AblationError(f"unknown unit {uid!r}")
        if uid == "system":
            if "system" not in b:
                raise AblationError("request has no top-level system prompt")
            del b["system"]
        elif m.group(2) is not None:
            i = int(m.group(2))
            if not isinstance(b.get("system"), list) or i >= len(b["system"]):
                raise AblationError(f"no {uid}")
            b["system"][i] = None
        elif m.group(3) is not None:
            i = int(m.group(3))
            if i >= len(msgs):
                raise AblationError(f"no {uid}")
            drop_msgs.add(i)
            tool_ids |= _tool_ids(fmt, msgs[i])
        elif uid.startswith("thinking"):
            if m.group(6) is None:
                drop_thinking |= {i for i, x in enumerate(msgs) if _thinking_text(fmt, x)}
            else:
                i = int(m.group(6))
                if i >= len(msgs) or not _thinking_text(fmt, msgs[i]):
                    raise AblationError(f"msg[{i}] has no reasoning to remove")
                drop_thinking.add(i)
        elif m.group(4) is not None:
            if not any(m.group(4) in _tool_ids(fmt, x) for x in msgs):
                raise AblationError(f"no tool call with id {m.group(4)!r}")
            tool_ids.add(m.group(4))
        else:
            drop_tools.add(m.group(5))
    if isinstance(b.get("system"), list):
        b["system"] = [x for x in b["system"] if x is not None]
        if not b["system"]:
            del b["system"]
    if drop_tools:
        names = lambda t: t.get("name") or (t.get("function") or {}).get("name")  # noqa: E731
        missing = drop_tools - {names(t) for t in b.get("tools") or []}
        if missing:
            raise AblationError(f"no tool definition named {sorted(missing)}")
        b["tools"] = [t for t in b["tools"] if names(t) not in drop_tools]
        if not b["tools"]:
            del b["tools"]

    kept = [_drop_thinking(fmt, m) if i in drop_thinking else m
            for i, m in enumerate(msgs) if i not in drop_msgs]
    renames = {cid: f"{'toolu' if fmt == ANTHROPIC else 'call'}_ctxb{n:04d}"
               for n, cid in enumerate(sorted({c for i in drop_thinking if i not in drop_msgs
                                               for c in _tool_ids(fmt, msgs[i])} - tool_ids))}
    if renames:
        kept = [_rename_ids(fmt, m, renames) for m in kept]
    kept = _strip_tool_ids(fmt, kept, tool_ids)
    b["messages"] = _merge_same_role(fmt, kept)
    problems = validate(fmt, b)
    if problems:
        raise AblationError("ablation left an invalid request: " + "; ".join(problems))
    return b


def _rename_ids(fmt: str, m: dict, renames: dict[str, str]) -> dict:
    if fmt == ANTHROPIC:
        c = m.get("content")
        if not isinstance(c, list):
            return m
        out = []
        for b in c:
            if b.get("type") in ("tool_use", "server_tool_use") and b.get("id") in renames:
                b = {**b, "id": renames[b["id"]]}
            elif b.get("type") == "tool_result" and b.get("tool_use_id") in renames:
                b = {**b, "tool_use_id": renames[b["tool_use_id"]]}
            out.append(b)
        return {**m, "content": out}
    m = dict(m)
    if m.get("tool_calls"):
        m["tool_calls"] = [{**c, "id": renames.get(c["id"], c["id"])} for c in m["tool_calls"]]
    if m.get("tool_call_id") in renames:
        m["tool_call_id"] = renames[m["tool_call_id"]]
    return m


def _strip_tool_ids(fmt: str, msgs: list[dict], ids: set[str]) -> list[dict]:
    out = []
    for m in msgs:
        if fmt == ANTHROPIC:
            c = m.get("content")
            if isinstance(c, list):
                c = [x for x in c if not (
                    (x.get("type") in ("tool_use", "server_tool_use") and x.get("id") in ids)
                    or (x.get("type") == "tool_result" and x.get("tool_use_id") in ids))]
                if not c or all(x.get("type") in ("thinking", "redacted_thinking") for x in c):
                    continue
                m = {**m, "content": c}
        else:
            if m.get("role") == "tool" and m.get("tool_call_id") in ids:
                continue
            if m.get("tool_calls"):
                calls = [c for c in m["tool_calls"] if c["id"] not in ids]
                if len(calls) != len(m["tool_calls"]):
                    m = dict(m)
                    if calls:
                        m["tool_calls"] = calls
                    else:
                        del m["tool_calls"]
                        if not m.get("content"):
                            continue
        out.append(m)
    return out


def _as_blocks(content) -> list:
    return [{"type": "text", "text": content}] if isinstance(content, str) else list(content)


def _merge_same_role(fmt: str, msgs: list[dict]) -> list[dict]:
    out: list[dict] = []
    for m in msgs:
        prev = out[-1] if out else None
        if prev is None or prev.get("role") != m.get("role") or m.get("role") not in ("user", "assistant"):
            out.append(m)
            continue
        if fmt == ANTHROPIC:
            blocks = _as_blocks(prev["content"]) + _as_blocks(m["content"])
            if m["role"] == "user":  # tool_result blocks must come first
                blocks.sort(key=lambda x: x.get("type") != "tool_result")
            out[-1] = {**prev, "content": blocks}
        else:
            if prev.get("tool_calls") and m["role"] == "assistant":
                out.append(m)  # keep call/result adjacency rather than merge
                continue
            merged = dict(prev)
            a, c = prev.get("content"), m.get("content")
            if isinstance(a, list) or isinstance(c, list):
                merged["content"] = _as_blocks(a or "") + _as_blocks(c or "")
            else:
                merged["content"] = "\n\n".join(x for x in (a, c) if x)
            if m.get("tool_calls"):
                merged["tool_calls"] = m["tool_calls"]
            out[-1] = merged
    return out


def validate(fmt: str, body: dict) -> list[str]:
    msgs = body.get("messages") or []
    problems = []
    if not msgs:
        return ["no messages left"]
    if fmt == ANTHROPIC:
        if msgs[0].get("role") != "user":
            problems.append("first message is not from the user")
        for i, m in enumerate(msgs):
            if m.get("role") != "assistant" or not isinstance(m.get("content"), list):
                continue
            calls = {b["id"] for b in m["content"] if b.get("type") == "tool_use"}
            if not calls:
                continue
            nxt = msgs[i + 1] if i + 1 < len(msgs) else None
            got = set()
            if nxt and isinstance(nxt.get("content"), list):
                got = {b["tool_use_id"] for b in nxt["content"] if b.get("type") == "tool_result"}
            if calls - got:
                problems.append(f"msg[{i}] tool calls without results: {sorted(calls - got)}")
    else:
        open_calls: set[str] = set()
        for i, m in enumerate(msgs):
            if m.get("role") == "tool":
                if m.get("tool_call_id") not in open_calls:
                    problems.append(f"msg[{i}] result for unknown call {m.get('tool_call_id')}")
                open_calls.discard(m.get("tool_call_id"))
            else:
                if open_calls:
                    problems.append(f"calls without results before msg[{i}]: {sorted(open_calls)}")
                    open_calls = set()
                open_calls |= {c["id"] for c in m.get("tool_calls") or []}
        if open_calls:
            problems.append(f"calls without results: {sorted(open_calls)}")
    return problems


# --------------------------------------------------------- prompt caching

MAX_BREAKPOINTS = 4  # Anthropic allows at most 4 cache_control breakpoints per request
_NO_CACHE_MARK = ("thinking", "redacted_thinking")


def _blocks(body: dict) -> list[tuple[tuple, dict | str]]:
    """Every cacheable block of an Anthropic request in prompt order (tools,
    system, messages) as (path, block); string system / content is one block."""
    out: list[tuple[tuple, dict | str]] = [(("tools", i), t) for i, t in enumerate(body.get("tools") or [])]
    s = body.get("system")
    if isinstance(s, str):
        out.append((("system",), s))
    elif isinstance(s, list):
        out += [(("system", i), b) for i, b in enumerate(s)]
    for i, m in enumerate(body.get("messages") or []):
        c = m.get("content")
        if isinstance(c, str):
            out.append((("messages", i, "content"), c))
        elif isinstance(c, list):
            out += [(("messages", i, "content", j), b) for j, b in enumerate(c)]
    return out


def _bare(b) -> object:
    return {k: v for k, v in b.items() if k != "cache_control"} if isinstance(b, dict) else b


def pin_cache_breakpoints(original: dict, ablated: dict, limit: int = MAX_BREAKPOINTS) -> dict:
    """Anthropic ``cache_control`` for an ablated replay of ``original``.

    The ablated request shares a byte-identical prefix with the original up to
    the first changed block. Breakpoints after that point would only write cache
    entries for a body that changes from test to test, so they are removed; one
    is pinned on the last unchanged block (the frozen prefix every test shares),
    in the style of the recorded ones (e.g. a ``ttl``), keeping at most ``limit``.
    Requests recorded without prompt caching are returned unchanged."""
    orig = _blocks(original)
    marks = [b["cache_control"] for _, b in orig if isinstance(b, dict) and "cache_control" in b]
    if not marks:
        return ablated
    b = copy.deepcopy(ablated)
    new = _blocks(b)
    k = 0
    while k < min(len(orig), len(new)) and _bare(orig[k][1]) == _bare(new[k][1]):
        k += 1
    if k == len(orig) == len(new):  # nothing removed
        return b

    def node(path: tuple):
        o = b
        for p in path[:-1]:
            o = o[p]
        return o, path[-1]

    for path, blk in new[k:]:  # stale breakpoints in the changed region
        if isinstance(blk, dict) and "cache_control" in blk:
            parent, key = node(path)
            parent[key] = _bare(blk)
    pin = next((i for i in range(k - 1, -1, -1)
                if not (isinstance(new[i][1], dict) and new[i][1].get("type") in _NO_CACHE_MARK)
                and not (isinstance(new[i][1], str) and not new[i][1].strip())), None)
    if pin is not None:
        path, blk = new[pin]
        style = next((blk2["cache_control"] for _, blk2 in reversed(new[:pin + 1])
                      if isinstance(blk2, dict) and "cache_control" in blk2), marks[-1])
        parent, key = node(path)
        if isinstance(blk, str):  # string system / content: one text block carrying the mark
            parent[key] = [{"type": "text", "text": blk, "cache_control": dict(style)}]
        else:
            parent[key] = {**blk, "cache_control": dict(style)}
    marked = [p for p, blk in _blocks(b) if isinstance(blk, dict) and "cache_control" in blk]
    for path in marked[:max(0, len(marked) - limit)]:  # over the limit: drop the earliest
        parent, key = node(path)
        parent[key] = _bare(parent[key])
    return b


# --------------------------------------------------------------------- text

def text_fields(fmt: str, body: dict) -> list[tuple[tuple, str]]:
    """Every editable text span as (path, text)."""
    out: list[tuple[tuple, str]] = []
    if fmt == ANTHROPIC:
        s = body.get("system")
        if isinstance(s, str):
            out.append((("system",), s))
        elif isinstance(s, list):
            out += [(("system", i, "text"), b["text"]) for i, b in enumerate(s) if "text" in b]
    for i, m in enumerate(body.get("messages") or []):
        c = m.get("content")
        if isinstance(c, str):
            out.append((("messages", i, "content"), c))
        elif isinstance(c, list):
            for j, b in enumerate(c):
                if b.get("type") == "text":
                    out.append((("messages", i, "content", j, "text"), b["text"]))
                elif b.get("type") == "tool_result":
                    rc = b.get("content")
                    if isinstance(rc, str):
                        out.append((("messages", i, "content", j, "content"), rc))
                    elif isinstance(rc, list):
                        out += [(("messages", i, "content", j, "content", k, "text"), x["text"])
                                for k, x in enumerate(rc) if x.get("type") == "text"]
    for i, t in enumerate(body.get("tools") or []):  # tool and parameter descriptions
        out += _descriptions(t, ("tools", i))
    return out


def _descriptions(o, path: tuple) -> list[tuple[tuple, str]]:
    out: list[tuple[tuple, str]] = []
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "description" and isinstance(v, str):
                out.append((path + (k,), v))
            elif isinstance(v, (dict, list)):
                out += _descriptions(v, path + (k,))
    elif isinstance(o, list):
        for j, v in enumerate(o):
            out += _descriptions(v, path + (j,))
    return out


def _set(body: dict, path: tuple, value: str) -> None:
    o = body
    for p in path[:-1]:
        o = o[p]
    o[path[-1]] = value


def _cut(s: str, start: int, end: int) -> str:
    """Remove s[start:end] and tidy the seam (no double space, no empty line)."""
    left, right = s[:start], s[end:]
    if left.endswith((" ", "\t")) and right.startswith((" ", "\t", "\n")):
        left = left.rstrip(" \t")
    elif (left == "" or left.endswith("\n")) and right.startswith((" ", "\t")):
        right = right.lstrip(" \t")
    if (left == "" or left.endswith("\n")) and right.startswith("\n"):
        right = right[1:]
    return left + right


def remove_text(fmt: str, body: dict, text: str) -> dict:
    b = copy.deepcopy(body)
    found = 0
    for path, s in text_fields(fmt, b):
        while text in s:
            i = s.index(text)
            s = _cut(s, i, i + len(text))
            found += 1
        _set(b, path, s)
    if not found:
        raise AblationError(f"text not found in request: {_short(text)!r}")
    return b


_SEG = re.compile(r"[^\n]*?(?:[.!?](?=\s)|\n|$)\s*")


def _segments(s: str) -> list[tuple[int, int]]:
    """Sentence/line spans (start, end), covering s."""
    segs, pos = [], 0
    for m in _SEG.finditer(s):
        if m.end() > pos:
            segs.append((m.start(), m.end()))
            pos = m.end()
        if m.end() >= len(s):
            break
    return segs


def remove_random_span(fmt: str, body: dict, size: int, rng: random.Random,
                       protect: list[str] = (), tolerance: float = 0.5) -> tuple[dict, str]:
    """Remove a random run of whole sentences/lines about ``size`` chars long
    (within ``tolerance``), never touching any ``protect`` text."""
    candidates = []
    for fi, (path, s) in enumerate(text_fields(fmt, body)):
        blocked = [(m.start(), m.end()) for p in protect if p for m in re.finditer(re.escape(p), s)]
        segs = _segments(s)
        for a in range(len(segs)):
            for z in range(a, len(segs)):
                st, en = segs[a][0], segs[z][1]
                n = len(s[st:en].strip())
                if n > size * (1 + tolerance):
                    break
                if n >= size * (1 - tolerance) and not any(st < be and bs < en for bs, be in blocked):
                    candidates.append((abs(n - size), fi, path, st, en))
    if not candidates:
        raise AblationError(f"no removable span of ~{size} chars outside the protected text")
    # uniform over spans within 30% of the size, so controls spread over the
    # whole context; fall back to the closest sizes if none is that close
    pool = [c for c in candidates if c[0] <= size * 0.3]
    if not pool:
        best = min(c[0] for c in candidates)
        pool = [c for c in candidates if c[0] <= best + max(10, size * 0.2)]
    _, _, path, st, en = rng.choice(pool)
    b = copy.deepcopy(body)
    s = dict(text_fields(fmt, b))[path]
    removed = s[st:en]
    _set(b, path, _cut(s, st, en))
    return b, removed
