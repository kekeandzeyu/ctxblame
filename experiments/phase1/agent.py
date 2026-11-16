"""A small but real coding agent, used to produce realistic traces for ctxblame.

It works on a copy of this repository with one planted bug, through the
ctxblame recording proxy, with thinking on, in either wire format:

    uv run ctxblame record --upstream https://api.deepseek.com/anthropic --port 8791 --trace a.jsonl &
    DEEPSEEK_API_KEY=... uv run python experiments/phase1/agent.py --format anthropic \
        --base-url http://127.0.0.1:8791 --workspace /tmp/ws

Tools run for real but in a sandbox: file tools are confined to the workspace,
and the shell tool runs one allowlisted command (ls, cat, grep, git status,
pytest, ...) without a shell and without the API key in its environment.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from aiohttp import ClientSession, ClientTimeout

from ctxblame.sse import assemble_message, assemble_openai_chunks, parse_sse

REPO = Path(__file__).resolve().parents[2]
VENV_PY = REPO / ".venv" / "bin" / "python"

TASK = ("Running the test suite shows a failure in tests/test_formats.py. "
        "Find the cause and fix it, then confirm the whole suite passes.")

AGENTS_MD = """# AGENTS.md

Notes for coding agents working in this repository.

## Workflow
- Before editing anything under src/, read docs/ARCHITECTURE.md; it explains
  which module owns which wire format.
- Run the test suite with `python -m pytest -q`. Do not use `uv run`; the
  sandbox has no network.
- Never edit files under tests/. If a test looks wrong, say so instead.
- Keep fixes minimal: change the fewest lines that fix the bug.

## Style
- Python 3.12, type hints on public functions, no new dependencies.
- Do not reformat code you did not change.
"""

ARCHITECTURE_MD = """# Architecture

- `sse.py`: parses server-sent events and reassembles streamed replies for
  both wire formats.
- `formats.py`: everything wire-format specific: format detection, decision
  extraction and token usage (`extract_usage`). Usage is reported as
  uncached input, cache reads, cache writes and output; for OpenAI-format
  replies the cached part is *included* in `prompt_tokens`, so it must be
  subtracted to get the uncached part.
- `pricing.py`: prices per model and the spend ledger.
- `replay.py`, `ablate.py`, `match.py`, `trace.py`: replay, context removal,
  decision matching and traces.
"""

BUG = ("    return Usage(prompt - hit, hit, 0, u.get(\"completion_tokens\") or 0)",
       "    return Usage(prompt, hit, 0, u.get(\"completion_tokens\") or 0)")

SYSTEM = """You are a careful software engineering agent working in a local repository.
You solve the user's task by using the tools provided, one step at a time.

How to work:
- Investigate before you change anything: look at the repository layout, read
  the relevant files, and reproduce the problem when you can.
- Follow the repository's own instructions (AGENTS.md below) exactly. They
  override your general habits.
- Prefer the dedicated file tools (read_file, list_dir, grep, edit_file) over
  shell commands for reading and editing files. Use bash for running programs
  such as the test suite or git.
- The bash tool runs a single command without a shell: no pipes, no &&, no
  redirection. Run one command per call.
- Make the smallest change that solves the task. Do not refactor unrelated code.
- After a change, verify it (for example by running the tests).
- When the task is done, reply with a short summary of what you found and what
  you changed, and do not call any more tools.

Environment:
- Working directory: {cwd}
- Platform: linux
- Python 3.12 with the project's dependencies installed; no network access.

Contents of AGENTS.md (repository instructions):

{agents_md}
"""

TOOLS = [
    {"name": "bash", "description": "Run one shell command in the working directory (no shell operators). "
     "Returns stdout, stderr and the exit code.",
     "schema": {"type": "object", "properties": {
         "command": {"type": "string", "description": "the command line, e.g. `python -m pytest -q`"},
         "description": {"type": "string", "description": "what this command is for, in a few words"}},
         "required": ["command"]}},
    {"name": "read_file", "description": "Read a text file. Returns numbered lines.",
     "schema": {"type": "object", "properties": {
         "path": {"type": "string", "description": "file path, relative to the working directory"},
         "offset": {"type": "integer", "description": "first line to read (1-based)"},
         "limit": {"type": "integer", "description": "maximum number of lines"}},
         "required": ["path"]}},
    {"name": "list_dir", "description": "List a directory (non-recursive).",
     "schema": {"type": "object", "properties": {
         "path": {"type": "string", "description": "directory, relative to the working directory"}},
         "required": ["path"]}},
    {"name": "grep", "description": "Search file contents with a regular expression. Returns file:line: text.",
     "schema": {"type": "object", "properties": {
         "pattern": {"type": "string"},
         "path": {"type": "string", "description": "file or directory to search (default: .)"}},
         "required": ["pattern"]}},
    {"name": "edit_file", "description": "Replace one exact occurrence of old_string with new_string in a file.",
     "schema": {"type": "object", "properties": {
         "path": {"type": "string"}, "old_string": {"type": "string"}, "new_string": {"type": "string"}},
         "required": ["path", "old_string", "new_string"]}},
    {"name": "write_file", "description": "Create or overwrite a file with the given content.",
     "schema": {"type": "object", "properties": {
         "path": {"type": "string"}, "content": {"type": "string"}},
         "required": ["path", "content"]}},
]


# ------------------------------------------------------------------ workspace

def make_workspace(ws: Path) -> None:
    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True)
    for name in ("src", "tests", "pyproject.toml", "README.md", "LICENSE"):
        src = REPO / name
        if src.is_dir():
            shutil.copytree(src, ws / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(src, ws / name)
    f = ws / "src" / "ctxblame" / "formats.py"
    text = f.read_text()
    assert BUG[0] in text, "planted-bug anchor not found; update BUG"
    f.write_text(text.replace(BUG[0], BUG[1]))
    (ws / "AGENTS.md").write_text(AGENTS_MD)
    (ws / "docs").mkdir()
    (ws / "docs" / "ARCHITECTURE.md").write_text(ARCHITECTURE_MD)
    subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
    subprocess.run(["git", "-c", "user.name=agent", "-c", "user.email=agent@example.invalid",
                    "add", "-A"], cwd=ws, check=True)
    subprocess.run(["git", "-c", "user.name=agent", "-c", "user.email=agent@example.invalid",
                    "commit", "-qm", "initial"], cwd=ws, check=True)


# ---------------------------------------------------------------------- tools

class Sandbox:
    ALLOWED = {"ls", "cat", "head", "tail", "wc", "grep", "find", "sed", "git", "python", "python3",
               "pytest", "pwd", "echo", "tree", "diff"}
    GIT_OK = {"status", "diff", "log", "show", "grep", "ls-files"}

    def __init__(self, ws: Path) -> None:
        self.ws = ws.resolve()

    def path(self, p: str) -> Path:
        q = (self.ws / p).resolve() if not os.path.isabs(p) else Path(p).resolve()
        if q != self.ws and self.ws not in q.parents:
            raise ValueError(f"path outside the working directory: {p}")
        return q

    def run(self, name: str, args: dict) -> str:
        try:
            return getattr(self, "t_" + name)(**args)
        except TypeError as e:
            return f"error: bad arguments: {e}"
        except (ValueError, OSError) as e:
            return f"error: {e}"

    def t_read_file(self, path: str, offset: int = 1, limit: int = 400) -> str:
        lines = self.path(path).read_text(errors="replace").splitlines()
        start = max(1, int(offset or 1))
        chunk = lines[start - 1:start - 1 + int(limit or 400)]
        out = "\n".join(f"{i:5d}\t{l}" for i, l in enumerate(chunk, start))
        more = len(lines) - (start - 1 + len(chunk))
        return out + (f"\n... ({more} more lines)" if more > 0 else "")

    def t_list_dir(self, path: str = ".") -> str:
        d = self.path(path)
        items = sorted(d.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        return "\n".join(x.name + ("/" if x.is_dir() else "") for x in items if x.name != ".git")

    def t_grep(self, pattern: str, path: str = ".") -> str:
        rx = re.compile(pattern)
        root = self.path(path)
        files = [root] if root.is_file() else sorted(p for p in root.rglob("*")
                                                     if p.is_file() and ".git" not in p.parts
                                                     and "__pycache__" not in p.parts)
        hits = []
        for f in files:
            try:
                for i, line in enumerate(f.read_text().splitlines(), 1):
                    if rx.search(line):
                        hits.append(f"{f.relative_to(self.ws)}:{i}: {line.strip()[:200]}")
            except (UnicodeDecodeError, OSError):
                continue
        return "\n".join(hits[:200]) or "(no matches)"

    def t_edit_file(self, path: str, old_string: str, new_string: str) -> str:
        f = self.path(path)
        text = f.read_text()
        n = text.count(old_string)
        if n != 1:
            return f"error: old_string occurs {n} times in {path}; it must occur exactly once"
        f.write_text(text.replace(old_string, new_string))
        return f"edited {path}"

    def t_write_file(self, path: str, content: str) -> str:
        f = self.path(path)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content)
        return f"wrote {path} ({len(content)} chars)"

    def t_bash(self, command: str, description: str = "") -> str:
        if re.search(r"[|;&<>`]|\$\(", command):
            return "error: no shell here: pipes, &&, ; and redirection are not supported. Run one command."
        try:
            argv = shlex.split(command)
        except ValueError as e:
            return f"error: {e}"
        if not argv:
            return "error: empty command"
        prog = argv[0]
        if prog not in self.ALLOWED:
            return f"error: `{prog}` is not available in this sandbox"
        if prog == "git" and (len(argv) < 2 or argv[1] not in self.GIT_OK):
            return "error: only read-only git commands are available (status, diff, log, show, grep, ls-files)"
        if prog == "sed" and any(a.startswith("-i") for a in argv):
            return "error: sed -i is not available; use edit_file"
        if prog in ("python", "python3"):
            if argv[1:3] != ["-m", "pytest"]:
                return "error: only `python -m pytest` is available in this sandbox"
            argv = [str(VENV_PY), *argv[1:]]
        elif prog == "pytest":
            argv = [str(VENV_PY), "-m", "pytest", *argv[1:]]
        for a in argv[1:]:  # keep file arguments inside the workspace
            if a.startswith("/") and not a.startswith(str(self.ws)):
                return f"error: path outside the working directory: {a}"
        env = {"PATH": "/usr/bin:/bin", "HOME": str(self.ws), "PYTHONPATH": str(self.ws / "src"),
               "PYTHONDONTWRITEBYTECODE": "1", "LANG": "C.UTF-8"}
        try:
            p = subprocess.run(argv, cwd=self.ws, env=env, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return "error: command timed out after 120s"
        out = (p.stdout + ("\n[stderr]\n" + p.stderr if p.stderr.strip() else ""))[-15000:]
        return f"{out}\n[exit code {p.returncode}]"


# ---------------------------------------------------------------------- agent

def anthropic_tools():
    return [{"name": t["name"], "description": t["description"], "input_schema": t["schema"]} for t in TOOLS]


def openai_tools():
    return [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                              "parameters": t["schema"]}} for t in TOOLS]


async def post_stream(s: ClientSession, url: str, headers: dict, body: dict, fmt: str) -> dict:
    for attempt in range(4):
        async with s.post(url, json=body, headers=headers) as r:
            raw = await r.read()
            if r.status in (429, 500, 502, 503, 504) and attempt < 3:
                await asyncio.sleep(2 ** attempt)
                continue
            if r.status != 200:
                raise RuntimeError(f"HTTP {r.status}: {raw[:400].decode('utf-8', 'replace')}")
            ev = parse_sse(raw)
            msg = assemble_message(ev) if fmt == "anthropic" else assemble_openai_chunks(ev)
            if msg.get("_stream_complete"):
                return msg
    raise RuntimeError("stream did not complete")


async def run_agent(args) -> int:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        print("error: set DEEPSEEK_API_KEY", file=sys.stderr)
        return 2
    ws = Path(args.workspace).resolve()
    if not args.reuse_workspace:
        make_workspace(ws)
    box = Sandbox(ws)
    system = SYSTEM.format(cwd=ws, agents_md=AGENTS_MD.strip())
    base = args.base_url.rstrip("/")
    if args.format == "anthropic":
        url = base + "/v1/messages"
        headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        messages: list = [{"role": "user", "content": TASK}]
    else:
        url = base + "/chat/completions"
        headers = {"authorization": f"Bearer {key}", "content-type": "application/json"}
        messages = [{"role": "system", "content": system}, {"role": "user", "content": TASK}]

    async with ClientSession(timeout=ClientTimeout(total=900)) as s:
        for step in range(1, args.max_steps + 1):
            if args.format == "anthropic":
                body = {"model": args.model, "max_tokens": 16000, "stream": True,
                        "system": [{"type": "text", "text": system}], "tools": anthropic_tools(),
                        "messages": messages, "thinking": {"type": "enabled", "budget_tokens": 8000}}
                msg = await post_stream(s, url, headers, body, "anthropic")
                content = [{k: v for k, v in b.items() if not k.startswith("_")} for b in msg["content"]]
                messages.append({"role": "assistant", "content": content})
                calls = [(b["id"], b["name"], b.get("input") or {}) for b in content if b["type"] == "tool_use"]
                text = "".join(b.get("text", "") for b in content if b["type"] == "text")
            else:
                body = {"model": args.model, "max_tokens": 16000, "stream": True,
                        "stream_options": {"include_usage": True}, "tools": openai_tools(),
                        "messages": messages, "thinking": {"type": "enabled"}}
                resp = await post_stream(s, url, headers, body, "openai")
                m = resp["choices"][0]["message"]
                am = {"role": "assistant", "content": m.get("content") or ""}
                if m.get("reasoning_content"):
                    am["reasoning_content"] = m["reasoning_content"]
                if m.get("tool_calls"):
                    am["tool_calls"] = m["tool_calls"]
                messages.append(am)
                calls = []
                for tc in m.get("tool_calls") or []:
                    try:
                        a = json.loads(tc["function"]["arguments"] or "{}")
                    except json.JSONDecodeError:
                        a = {"_raw": tc["function"]["arguments"]}
                    calls.append((tc["id"], tc["function"]["name"], a))
                text = m.get("content") or ""

            if not calls:
                print(f"[{step}] done: {text.strip()[:600]}")
                return 0
            results = []
            for cid, name, a in calls:
                out = box.run(name, a) if not ("_raw" in a) else "error: arguments were not valid JSON"
                print(f"[{step}] {name}({json.dumps(a)[:150]}) -> {len(out)} chars")
                results.append((cid, out))
            if args.format == "anthropic":
                messages.append({"role": "user", "content": [
                    {"type": "tool_result", "tool_use_id": cid, "content": out} for cid, out in results]})
            else:
                messages += [{"role": "tool", "tool_call_id": cid, "content": out} for cid, out in results]
    print(f"stopped after {args.max_steps} steps")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", choices=["anthropic", "openai"], required=True)
    ap.add_argument("--base-url", required=True, help="the ctxblame proxy, e.g. http://127.0.0.1:8791")
    ap.add_argument("--model", default="deepseek-v4-pro")
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--reuse-workspace", action="store_true")
    ap.add_argument("--max-steps", type=int, default=30)
    return asyncio.run(run_agent(ap.parse_args()))


if __name__ == "__main__":
    sys.exit(main())
