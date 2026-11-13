"""Parse Anthropic-style SSE streams and rebuild the final Message from them.

Works for Anthropic and Anthropic-compatible endpoints (e.g. DeepSeek). The
raw events are kept as-is by the recorder; this module only derives the
assembled message so later steps can read the decision without re-parsing.
"""

from __future__ import annotations

import codecs
import copy
import json
from dataclasses import dataclass


@dataclass
class SSEEvent:
    event: str | None  # SSE "event:" name; None for unnamed frames
    data: str  # raw "data:" payload (multi-line data joined with "\n")

    def to_json(self) -> dict:
        return {"event": self.event, "data": self.data}


class SSEParser:
    """Incremental SSE parser: feed bytes in any chunking, get whole events."""

    def __init__(self) -> None:
        self._buf = ""
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self._event: str | None = None
        self._data: list[str] = []

    def feed(self, chunk: bytes | str) -> list[SSEEvent]:
        if isinstance(chunk, bytes):
            # incremental: a multi-byte character may be split across chunks
            chunk = self._decoder.decode(chunk)
        self._buf += chunk
        out: list[SSEEvent] = []
        while True:
            idx = self._buf.find("\n")
            if idx < 0:
                break
            line = self._buf[:idx].rstrip("\r")
            self._buf = self._buf[idx + 1 :]
            ev = self._line(line)
            if ev is not None:
                out.append(ev)
        return out

    def flush(self) -> list[SSEEvent]:
        """Call at end of stream to emit a final event lacking a blank line."""
        tail = self._decoder.decode(b"", final=True)
        out = self.feed(tail + "\n") if (self._buf or tail) else []
        ev = self._dispatch()
        if ev is not None:
            out.append(ev)
        return out

    def _line(self, line: str) -> SSEEvent | None:
        if line == "":
            return self._dispatch()
        if line.startswith(":"):  # comment / keep-alive
            return None
        field, _, value = line.partition(":")
        if value.startswith(" "):
            value = value[1:]
        if field == "event":
            self._event = value
        elif field == "data":
            self._data.append(value)
        return None

    def _dispatch(self) -> SSEEvent | None:
        if self._event is None and not self._data:
            return None
        ev = SSEEvent(self._event, "\n".join(self._data))
        self._event, self._data = None, []
        return ev


def parse_sse(text: bytes | str) -> list[SSEEvent]:
    p = SSEParser()
    return p.feed(text) + p.flush()


class StreamError(Exception):
    pass


def assemble_message(events: list[SSEEvent | dict]) -> dict:
    """Rebuild the non-streaming Message object from a list of SSE events.

    Returns a dict shaped like a normal Messages API response, plus
    ``_stream_complete`` (False if ``message_stop`` never arrived) and
    ``_stream_error`` when the stream carried an error frame.
    """
    msg: dict | None = None
    blocks: dict[int, dict] = {}
    partial_json: dict[int, str] = {}
    complete = False
    error = None

    for raw in events:
        if isinstance(raw, dict):
            raw = SSEEvent(raw.get("event"), raw.get("data", ""))
        if not raw.data:
            continue
        try:
            payload = json.loads(raw.data)
        except json.JSONDecodeError:
            continue
        etype = payload.get("type") or raw.event
        if etype is None and "error" in payload:  # DeepSeek unnamed error frame
            error = payload["error"]
            continue

        if etype == "message_start":
            msg = copy.deepcopy(payload["message"])
            msg["content"] = []
        elif etype == "content_block_start":
            i = payload["index"]
            block = copy.deepcopy(payload["content_block"])
            if block.get("type") in ("tool_use", "server_tool_use"):
                partial_json[i] = ""
            blocks[i] = block
        elif etype == "content_block_delta":
            i, d = payload["index"], payload["delta"]
            b = blocks.setdefault(i, {})
            dt = d.get("type")
            if dt == "text_delta":
                b["text"] = b.get("text", "") + d["text"]
            elif dt == "input_json_delta":
                partial_json[i] = partial_json.get(i, "") + d["partial_json"]
            elif dt == "thinking_delta":
                b["thinking"] = b.get("thinking", "") + d["thinking"]
            elif dt == "signature_delta":
                b["signature"] = b.get("signature", "") + d["signature"]
            elif dt == "citations_delta":
                b.setdefault("citations", []).append(d["citation"])
            else:
                b.setdefault("_unknown_deltas", []).append(d)
        elif etype == "content_block_stop":
            i = payload["index"]
            if i in partial_json:
                pj = partial_json.pop(i)
                try:
                    blocks[i]["input"] = json.loads(pj) if pj else blocks[i].get("input", {})
                except json.JSONDecodeError:
                    blocks[i]["_partial_json"] = pj
        elif etype == "message_delta":
            if msg is None:
                msg = {"content": []}
            for k, v in (payload.get("delta") or {}).items():
                msg[k] = v
            usage = payload.get("usage") or {}
            # message_delta usage is cumulative: later non-null values win.
            mu = msg.setdefault("usage", {})
            for k, v in usage.items():
                if v is not None:
                    mu[k] = v
        elif etype == "message_stop":
            complete = True
        elif etype == "error":
            error = payload.get("error", payload)
        # "ping" and unknown event types are ignored

    if msg is None:
        msg = {"content": []}
    msg["content"] = [blocks[i] for i in sorted(blocks)]
    msg["_stream_complete"] = complete
    if error is not None:
        msg["_stream_error"] = error
    return msg
