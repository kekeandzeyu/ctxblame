"""Decision matching: when do two replies count as "the same decision"?

Four modes, from strict to loose:

- ``exact``  tool name + all normalized arguments
- ``args``   tool name + only the named arguments (``--key-arg``; ``arg~regex``
             compares whether the argument matches)
- ``intent`` what the call does, independent of which tool does it:
             ``Read(file_path=src/a.py)`` and ``Bash(cat src/a.py)`` are both
             ``read src/a.py``; ``Bash(cd web && pnpm add x)`` is ``run pnpm add``
- ``name``   tool name only

Intent rules are deliberately simple and agent-agnostic: tools are recognised
by common names (Claude Code, OpenAI/Codex-style, SWE-agent-style), shell
commands by their program and subcommand.
"""

from __future__ import annotations

import posixpath
import re
import shlex
from dataclasses import dataclass

from .formats import Decision, ToolCall

MODES = ("exact", "args", "intent", "name")
NO_CALL = "<no tool call>"


def _canon(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


READ_TOOLS = {"read", "readfile", "view", "viewfile", "openfile", "open", "cat", "readfiles", "fileread"}
LIST_TOOLS = {"ls", "list", "listdir", "listdirectory", "listfiles", "glob", "find", "findfiles", "tree"}
SEARCH_TOOLS = {"grep", "search", "searchfiles", "searchcode", "codesearch", "rg", "ripgrep", "grepsearch"}
EDIT_TOOLS = {"edit", "write", "writefile", "multiedit", "strreplace", "editfile", "createfile",
              "applypatch", "notebookedit", "replaceinfile", "insert", "fileedit", "filewrite"}
SHELL_TOOLS = {"bash", "shell", "sh", "run", "runcommand", "exec", "execute", "terminal",
               "runshellcommand", "executecommand", "localshell", "runterminalcmd", "cmd", "command"}
EDITOR_TOOLS = {"strreplaceeditor", "strreplacebasededittool", "texteditor", "editor"}

PATH_ARGS = ("file_path", "path", "filepath", "file", "filename", "target_file", "notebook_path",
             "absolute_path", "relative_path", "dir", "directory")
CMD_ARGS = ("command", "cmd", "script", "commands", "input")

READ_PROGS = {"cat", "head", "tail", "less", "more", "nl", "bat", "view"}
LIST_PROGS = {"ls", "find", "tree", "fd", "dir"}
SEARCH_PROGS = {"grep", "rg", "ag", "ack", "egrep", "fgrep", "git-grep"}
SUBCOMMAND_PROGS = {"git", "npm", "pnpm", "yarn", "bun", "cargo", "go", "make", "uv", "pip", "pip3",
                    "docker", "kubectl", "poetry", "dotnet", "mvn", "gradle", "deno", "gh", "helm",
                    "terraform", "conda", "brew", "apt", "apt-get", "systemctl", "just", "npx", "pnpx"}
WRAPPERS = {"sudo", "time", "nohup", "env", "command", "exec", "xargs"}
PY = {"python", "python3", "py"}
SHELL_SPLIT = re.compile(r"\s*(?:&&|\|\||;|\||\n)\s*")


def path_of(args: dict, cwd: str | None) -> str | None:
    for k in PATH_ARGS:
        v = args.get(k)
        if isinstance(v, str) and v:
            return norm_path(v, cwd)
    v = args.get("paths")
    if isinstance(v, list) and v and isinstance(v[0], str):
        return norm_path(v[0], cwd)
    return None


def norm_path(p: str, cwd: str | None) -> str:
    p = p.strip().strip("'\"")
    if cwd and p.startswith(cwd.rstrip("/") + "/"):
        p = p[len(cwd.rstrip("/")) + 1:]
    elif cwd and p.rstrip("/") == cwd.rstrip("/"):
        p = "."
    p = posixpath.normpath(p) if p else "."
    return p


def _tokens(segment: str) -> list[str]:
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def _strip_prefix(toks: list[str]) -> list[str]:
    """Drop env assignments and wrappers like sudo/time/timeout N."""
    while toks:
        t = toks[0]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", t) or t in WRAPPERS:
            toks = toks[1:]
        elif t == "timeout" and len(toks) > 1:
            toks = toks[2:]
        else:
            break
    return toks


def _first_arg(toks: list[str]) -> str | None:
    """First non-flag argument (skips '-n 20' style options only for known short forms)."""
    skip_next = False
    for t in toks:
        if skip_next:
            skip_next = False
            continue
        if t in ("-n", "-c", "-e", "-A", "-B", "-C", "-m", "--max-count", "--include", "--exclude"):
            skip_next = True
            continue
        if t.startswith("-") or re.fullmatch(r"[+-]?\d+", t):
            continue
        return t
    return None


def shell_intent(command: str, cwd: str | None) -> str:
    segments = [s for s in SHELL_SPLIT.split(command.strip()) if s]
    # skip leading "cd X" / "source X" / "export" so "cd web && pnpm add" is about pnpm
    for seg in segments:
        toks = _strip_prefix(_tokens(seg))
        if not toks or toks[0] in ("cd", "pushd", "source", ".", "export", "set", "echo") and len(segments) > 1:
            continue
        return _program_intent(toks, cwd)
    toks = _strip_prefix(_tokens(segments[0])) if segments else []
    return _program_intent(toks, cwd) if toks else "run <empty>"


def _program_intent(toks: list[str], cwd: str | None) -> str:
    prog, rest = posixpath.basename(toks[0]), toks[1:]
    if prog in PY and len(rest) >= 2 and rest[0] == "-m":  # python -m pytest -> pytest
        return _program_intent(rest[1:], cwd)
    if prog in ("uv", "poetry", "pdm", "pipenv", "hatch") and rest[:1] == ["run"] and len(rest) > 1:
        return _program_intent(_strip_flags_before_cmd(rest[1:]), cwd)
    if prog in ("npx", "pnpx", "bunx") and rest:
        return _program_intent(_strip_flags_before_cmd(rest), cwd)
    if prog in READ_PROGS:
        a = _first_arg(rest)
        return f"read {norm_path(a, cwd)}" if a else f"run {prog}"
    if prog == "sed":
        if any(t == "-i" or t.startswith("-i") for t in rest):
            files = [t for t in rest if not t.startswith("-")]
            return f"edit {norm_path(files[-1], cwd)}" if len(files) >= 2 else "run sed"
        files = [t for t in rest if not t.startswith("-")]
        return f"read {norm_path(files[-1], cwd)}" if len(files) >= 2 else "run sed"
    if prog in LIST_PROGS:
        a = _first_arg(rest)
        return f"list {norm_path(a, cwd) if a else '.'}"
    if prog in SEARCH_PROGS or (prog == "git" and rest[:1] == ["grep"]):
        if prog == "git":
            rest = rest[1:]
        a = _first_arg(rest)
        return f"search {a}" if a else f"run {prog}"
    if prog in SUBCOMMAND_PROGS:
        sub = _first_arg(rest)
        return f"run {prog} {sub}" if sub else f"run {prog}"
    return f"run {prog}"


def _strip_flags_before_cmd(toks: list[str]) -> list[str]:
    while toks and toks[0].startswith("-"):
        toks = toks[1:]
    return toks or ["<empty>"]


def intent(call: ToolCall, cwd: str | None = None) -> str:
    name = _canon(call.name)
    args = call.args if isinstance(call.args, dict) else {}
    if name in EDITOR_TOOLS:  # one tool, several actions chosen by "command"
        sub = str(args.get("command", ""))
        p = path_of(args, cwd) or "?"
        return f"read {p}" if sub == "view" else f"edit {p}"
    if name in SHELL_TOOLS or (not name and any(k in args for k in CMD_ARGS)):
        cmd = next((args[k] for k in CMD_ARGS if k in args), "")
        if isinstance(cmd, list):
            cmd = " ".join(map(str, cmd[2:] if cmd[:2] in (["bash", "-lc"], ["bash", "-c"]) else cmd))
        return shell_intent(str(cmd), cwd)
    if name in READ_TOOLS:
        return f"read {path_of(args, cwd) or '?'}"
    if name in EDIT_TOOLS:
        return f"edit {path_of(args, cwd) or '?'}"
    if name in LIST_TOOLS:
        p = path_of(args, cwd)
        pat = args.get("pattern")
        return f"list {p or '.'}" + (f" {pat}" if pat and name == "glob" else "")
    if name in SEARCH_TOOLS:
        return f"search {args.get('pattern') or args.get('query') or args.get('regex') or '?'}"
    return f"call {call.name}"


@dataclass
class Matcher:
    mode: str = "intent"
    key_args: list[str] | None = None
    all_calls: bool = False  # compare every call in the reply, not just the first
    cwd: str | None = None

    def __post_init__(self) -> None:
        if self.mode not in MODES:
            raise ValueError(f"unknown match mode {self.mode!r}; choose from {', '.join(MODES)}")

    def key(self, d: Decision) -> str:
        if not d.calls:
            return NO_CALL
        calls = d.calls if self.all_calls else d.calls[:1]
        keys = [self._one(c) for c in calls]
        return " + ".join(sorted(keys)) if self.all_calls else keys[0]

    def _one(self, c: ToolCall) -> str:
        if self.mode == "intent":
            return intent(c, self.cwd)
        if self.mode == "name":
            return c.name
        return Decision([c]).key(self.key_args if self.mode == "args" else None)


CWD_PATTERNS = (
    r"(?:Primary working directory|Working directory|Current working directory|cwd)\s*[:=]\s*(/[^\s<>\"']+)",
    r"<cwd>\s*(/[^\s<]+)\s*</cwd>",
)


def find_cwd(text: str) -> str | None:
    """The agent's working directory, if the prompt states it (Claude Code, Codex and
    most agents do). Lets absolute and relative paths compare equal."""
    for p in CWD_PATTERNS:
        m = re.search(p, text)
        if m:
            return m.group(1).rstrip(".,;")
    return None
