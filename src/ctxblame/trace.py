"""Traces: an ordered list of recorded LLM calls ("steps").

On disk a trace is a JSON-lines file, one record per line, each with a
``step`` number (the order the requests were sent). For convenience a single
record (``.json``) or a directory of single records also loads as a trace.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from pathlib import Path

from .formats import detect_format, extract_decision, extract_usage
from .match import Matcher, find_cwd


@dataclass
class Step:
    step: int
    record: dict

    @property
    def fmt(self) -> str:
        return self.record["format"]

    @property
    def body(self) -> dict:
        return self.record["request"]["body"]

    @property
    def response(self) -> dict:
        r = self.record.get("response") or {}
        return (r.get("message") if r.get("streamed") else r.get("body")) or {}


def _prepare(rec: dict, where: str) -> dict:
    req = rec.get("request") or {}
    rec.setdefault("format", detect_format(req.get("path", "")))
    if rec["format"] is None:
        raise ValueError(f"{where}: not an Anthropic or OpenAI chat request")
    return rec


def load_trace(path: Path) -> list[Step]:
    path = Path(path)
    if path.is_dir():
        recs = [(_prepare(json.loads(p.read_text()), str(p)), p.name)
                for p in sorted(path.glob("*.json"))]
        return [Step(i, r) for i, (r, _) in enumerate(recs, 1)]
    text = path.read_text()
    if path.suffix == ".jsonl":
        recs = [_prepare(json.loads(line), f"{path}:{n}")
                for n, line in enumerate(text.splitlines(), 1) if line.strip()]
        recs.sort(key=lambda r: r.get("step", 0))
        return [Step(r.get("step") or i, r) for i, r in enumerate(recs, 1)]
    return [Step(1, _prepare(json.loads(text), str(path)))]


def get_step(steps: list[Step], n: int | None) -> Step:
    if n is None:
        if len(steps) == 1:
            return steps[0]
        raise LookupError(f"trace has {len(steps)} steps; choose one with --step "
                          f"(see `ctxblame steps`)")
    for s in steps:
        if s.step == n:
            return s
    raise LookupError(f"no step {n}; the trace has steps {steps[0].step}-{steps[-1].step}")


def request_text(fmt: str, body: dict) -> str:
    """System prompt plus first user message, as plain text (for cwd detection)."""
    parts = []
    sys_ = body.get("system")
    if isinstance(sys_, str):
        parts.append(sys_)
    elif isinstance(sys_, list):
        parts += [b.get("text", "") for b in sys_ if isinstance(b, dict)]
    for m in (body.get("messages") or [])[:3]:
        c = m.get("content")
        if isinstance(c, str):
            parts.append(c)
        elif isinstance(c, list):
            parts += [b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"]
    return "\n".join(parts)


def matcher_for(step: Step, mode: str = "intent", key_args=None, all_calls: bool = False,
                any_call: bool = False) -> Matcher:
    return Matcher(mode, key_args, all_calls, find_cwd(request_text(step.fmt, step.body)), any_call)


def describe(step: Step, matcher: Matcher | None = None) -> dict:
    """One row for `ctxblame steps`."""
    body, resp = step.body, step.response
    u = extract_usage(step.fmt, resp)
    d = extract_decision(step.fmt, resp)
    m = matcher or matcher_for(step)
    return {
        "step": step.step,
        "time": (step.record.get("started_at") or "")[11:19],
        "format": step.fmt,
        "model": resp.get("model") or body.get("model"),
        "messages": len(body.get("messages") or []),
        "tools": len(body.get("tools") or []),
        "input_tokens": u.input_uncached + u.input_cache_read + u.input_cache_write,
        "output_tokens": u.output,
        "status": (step.record.get("response") or {}).get("status"),
        "decision": m.key(d),
        "n_calls": len(d.calls),
        "error": step.record.get("error"),
    }


class TraceWriter:
    """Appends records to a JSON-lines trace. Steps are numbered when the
    request starts, so concurrent calls keep their send order."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._next = 1
        if self.path.exists():  # continue numbering an existing trace
            steps = [json.loads(l).get("step", 0) for l in self.path.read_text().splitlines() if l.strip()]
            self._next = max(steps, default=0) + 1

    def next_step(self) -> int:
        with self._lock:
            n, self._next = self._next, self._next + 1
            return n

    def save(self, record: dict) -> Path:
        line = json.dumps(record, ensure_ascii=False) + "\n"
        with self._lock, self.path.open("a", encoding="utf-8") as f:
            f.write(line)
        return self.path
