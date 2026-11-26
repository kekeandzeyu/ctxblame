"""Procedurally generated attribution cases (Phase 3, suite "gen").

Each case is a coding-agent request (OpenAI Chat Completions format) whose next
step is one shell command. A project convention (e.g. "run tests with
`tox -e py312`") is planted in 1-3 places of the context ("carriers"), chosen
from five kinds:

  system   a rule line in the system prompt (AGENTS.md section)
  tooldesc an example in the bash tool's ``command`` parameter description
  doc      a line in a tool result (the agent read CONTRIBUTING.md earlier)
  user     a sentence in an earlier user message (multi-turn chat)
  history  the agent's own earlier call of the same command (+ its output)

Optionally a workflow *precondition* is present: the task asks to fix a file
and then run the command, and the last thing in the history is the edit.
Removing that edit makes the agent go back and edit instead of running
anything (the confound of Phase 2). Distractor rules, tool calls and a long
filler section vary size and position. Negative cases name the command in the
task itself and plant no carrier.

Cases are deterministic in (seed, index), so names are stable across runs:
``gen/<seed>-<index>/<family>/<carriers>[+pre]`` or ``.../neg``.
Whether a planted carrier really drives the model is checked empirically by
``oracle.py`` before scoring.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass

from cases import BenchCase, _base_tools, _oai_step

CARRIER_KINDS = ("system", "tooldesc", "doc", "user", "history")


@dataclass(frozen=True)
class Family:
    name: str
    cmd: str  # the convention's command line
    rx: str  # --key-arg regex on the bash command that means "uses the convention"
    rule: str  # system-prompt rule line
    doc: str  # line in CONTRIBUTING.md
    user: str  # sentence in an earlier user message
    task: str  # task without precondition (the next step is the command)
    pre_task: str  # task with precondition (edit, then run the command)
    pre_file: str
    pre_before: str
    pre_old: str
    pre_new: str
    out: str  # output of an earlier run (history carrier)


FAMILIES = [
    Family("tox", "tox -e py312", r"tox\s+-e\s*py312",
           "- Run the test suite with `tox -e py312`; never call pytest directly.",
           "Tests: always run `tox -e py312` (it pins the interpreter and dependencies).",
           "By the way, in this project we only run tests through `tox -e py312`.",
           "Run the test suite and tell me whether it passes.",
           "The test for parse_size() fails on '10KB'. Fix src/units.py, then run the tests.",
           "src/units.py", "1\tdef parse_size(s: str) -> int:\n2\t    return int(s.rstrip('KB')) * 1000\n",
           "return int(s.rstrip('KB')) * 1000", "return int(s[:-2]) * 1024",
           "py312: commands[0]> pytest\n....F..\nFAILED tests/test_units.py::test_parse_size\npy312: FAIL"),
    Family("hatch", "hatch run test:all", r"hatch\s+run\s+test",
           "- Tests run only via `hatch run test:all`; do not invoke pytest or unittest yourself.",
           "To test, use `hatch run test:all` from the repository root.",
           "Note that our tests must be run with `hatch run test:all`.",
           "Run the tests and report the result.",
           "slugify() keeps trailing dashes. Fix src/text.py, then run the tests.",
           "src/text.py", "1\tdef slugify(s: str) -> str:\n2\t    return '-'.join(s.lower().split())\n",
           "return '-'.join(s.lower().split())", "return '-'.join(s.lower().split()).strip('-')",
           "test:all ... 41 passed, 1 failed (tests/test_text.py::test_slugify_trailing)"),
    Family("make", "make check", r"make\s+check",
           "- Verify every change with `make check` (lint + type check + tests).",
           "Before sending a change, run `make check`; CI runs exactly the same target.",
           "Also, the way we verify things here is `make check`.",
           "Verify the repository is in a good state.",
           "clamp() returns the wrong bound when lo > hi. Fix src/mathx.py, then verify the change.",
           "src/mathx.py", "1\tdef clamp(x, lo, hi):\n2\t    return max(lo, min(x, hi))\n",
           "return max(lo, min(x, hi))", "lo, hi = min(lo, hi), max(lo, hi)\n    return max(lo, min(x, hi))",
           "ruff ... ok\nmypy ... ok\npytest ... 1 failed\nmake: *** [check] Error 1"),
    Family("pnpm", "pnpm install --frozen-lockfile", r"pnpm\s+(i|install)\b.*--frozen-lockfile",
           "- Install dependencies with `pnpm install --frozen-lockfile`; never use npm or yarn.",
           "Dependencies: `pnpm install --frozen-lockfile` (the lockfile is the source of truth).",
           "Quick note: we install packages with `pnpm install --frozen-lockfile` here.",
           "Install the project's dependencies.",
           "Add `zod` ^3.23.0 to the dependencies in package.json, then install dependencies.",
           "package.json", '{\n  "name": "web",\n  "dependencies": {\n    "react": "^19.0.0"\n  }\n}',
           '"react": "^19.0.0"', '"react": "^19.0.0",\n    "zod": "^3.23.0"',
           "Lockfile is up to date, resolution step is skipped\nPackages: +212\nDone in 3.1s"),
    Family("uv", "uv sync --frozen", r"uv\s+sync\b.*--frozen",
           "- Set up the environment with `uv sync --frozen`; never use pip install.",
           "Environment setup: `uv sync --frozen` installs exactly what uv.lock pins.",
           "FYI our environments are always created with `uv sync --frozen`.",
           "Set up the Python environment for this project.",
           "Add `httpx>=0.27` to the dependencies in pyproject.toml, then set up the environment.",
           "pyproject.toml", '[project]\nname = "svc"\ndependencies = [\n    "fastapi>=0.115",\n]\n',
           '"fastapi>=0.115",', '"fastapi>=0.115",\n    "httpx>=0.27",',
           "Resolved 31 packages in 4ms\nInstalled 31 packages in 120ms"),
    Family("ruff", "ruff check --fix src/", r"ruff\s+check\b.*--fix",
           "- Lint with `ruff check --fix src/`; flake8 and pylint are not used.",
           "Linting: run `ruff check --fix src/` and commit the fixes.",
           "One thing: please lint with `ruff check --fix src/` only.",
           "Lint the code under src/ and apply safe automatic fixes.",
           "There is an unused import in src/app.py. Remove it, then lint the code under src/.",
           "src/app.py", "1\timport os\n2\timport sys\n3\t\n4\tprint(sys.argv)\n",
           "import os\nimport sys", "import sys",
           "Found 3 errors (3 fixed, 0 remaining)."),
    Family("cargo", "cargo nextest run", r"cargo\s+nextest\s+run",
           "- Run Rust tests with `cargo nextest run`, not `cargo test`.",
           "We use nextest: `cargo nextest run` (plain `cargo test` misses our config).",
           "Remember that tests here run via `cargo nextest run`.",
           "Run the Rust test suite.",
           "add() in src/lib.rs subtracts instead of adding. Fix it, then run the tests.",
           "src/lib.rs", "1\tpub fn add(a: i32, b: i32) -> i32 {\n2\t    a - b\n3\t}\n",
           "    a - b", "    a + b",
           "Starting 12 tests across 1 binary\n    FAIL [0.002s] lib tests::adds\n Summary: 11 passed, 1 failed"),
    Family("script", "./scripts/ci.sh --quick", r"scripts/ci\.sh\b.*--quick",
           "- To validate changes, run `./scripts/ci.sh --quick` from the repository root.",
           "Validation: `./scripts/ci.sh --quick` runs the fast subset of CI locally.",
           "Our standard check is `./scripts/ci.sh --quick`, just so you know.",
           "Validate the current state of the repository.",
           "The default timeout in src/config.py should be 30, not 3. Fix it, then validate the change.",
           "src/config.py", "1\tDEFAULT_TIMEOUT = 3\n2\tRETRIES = 5\n",
           "DEFAULT_TIMEOUT = 3", "DEFAULT_TIMEOUT = 30",
           "[ci] lint ok\n[ci] unit: 1 failed (test_config.py::test_default_timeout)\n[ci] FAILED"),
]

FILLER_RULES = [
    "- Keep diffs minimal and focused on the task.",
    "- Never commit secrets or credentials.",
    "- Prefer small, well-named functions.",
    "- Documentation lives in docs/ and is written in Markdown.",
    "- Do not modify generated files under build/ or dist/.",
    "- Use type annotations for all new public functions.",
    "- Write commit messages in the imperative mood.",
    "- Ask before deleting files you did not create.",
]

DOC_FILLER = [
    "# Contributing",
    "Thanks for helping out!",
    "Open an issue before large changes.",
    "Branch names: feature/<topic> or fix/<topic>.",
    "Keep pull requests under 400 changed lines.",
    "Every public function needs a docstring.",
]

DISTRACTOR_PAIRS = [
    ("list_dir", {"path": "."}, "README.md\nCONTRIBUTING.md\nsrc\ntests\ndocs\nscripts"),
    ("read_file", {"path": "README.md"}, "# Project\nA small internal library.\nSee docs/ for details."),
    ("list_dir", {"path": "docs"}, "architecture.md\nrelease.md\nfaq.md"),
    ("read_file", {"path": "docs/faq.md"},
     "# FAQ\nQ: Where are logs?\nA: In ./var/log.\nQ: Who owns this repo?\nA: The platform team."),
]

NEUTRAL_EXAMPLE = "e.g. `git status`"

MANUAL_TOPICS = [
    ("Reading code", "Open the smallest file that answers the question; prefer targeted reads over whole files."),
    ("Editing", "Keep edits minimal and local; preserve formatting, comments and public interfaces."),
    ("Shell use", "Run one command per call; avoid interactive programs and long-running servers."),
    ("Git", "Inspect history with read-only commands; never rewrite history or force-push."),
    ("Errors", "Read error messages fully before acting; quote the relevant line when reporting."),
    ("Communication", "Summarize what changed and why in a few sentences when the task is done."),
    ("Security", "Never print secrets; treat tokens, keys and credentials in files as sensitive."),
    ("Performance", "Avoid quadratic loops over large inputs; measure before optimizing."),
    ("Dependencies", "Do not add dependencies unless the task requires it; prefer the standard library."),
    ("Documentation", "Update docstrings and docs when behaviour changes; keep examples runnable."),
]


def _manual(rng: random.Random, sections: int = 40) -> str:
    """~30k characters of generic, decision-neutral agent instructions."""
    out = ["# Agent Manual"]
    for k in range(sections):
        title, rule = MANUAL_TOPICS[k % len(MANUAL_TOPICS)]
        out.append(f"\n## {k + 1}. {title} ({rng.randrange(100, 999)})")
        for j in range(6):
            out.append(f"- {rule} Applies to component c{rng.randrange(1000)} and similar cases ({j + 1}).")
    return "\n".join(out)


def _filler_section(rng: random.Random, lines: int) -> str:
    return "## Service Catalog\n" + "\n".join(
        f"- service_{i:02d}: telemetry batch {rng.randrange(1000)} with retry window {rng.randrange(5, 60)}s."
        for i in range(lines))


DIRECT = " Use the bash tool for it right away; do not explore the repository first."
DIRECT_PRE = " Once the edit is in, run it with the bash tool right away."


def make_case(seed: int, idx: int, fam: Family, kinds: tuple[str, ...], pre: bool,
              negative: bool = False, long_ctx: bool = False, style: str = "direct") -> BenchCase:
    rng = random.Random(f"{seed}-{idx}")
    carriers: list[str] = []

    # system prompt
    rules = rng.sample(FILLER_RULES, rng.randint(2, 4))
    if "system" in kinds:
        rules.insert(rng.randrange(len(rules) + 1), fam.rule)
        carriers.append(fam.rule)
    system = ("You are a careful coding agent working in a software repository.\n"
              "Use the tools to inspect, change and verify the code. Do one step at a time.\n\n")
    if style == "long":  # a long agent manual before the repository rules, as in production agents
        system += _manual(rng) + "\n\n"
    system += "## Repository Rules\n" + "\n".join(rules) + "\n"
    if long_ctx:
        system += "\n" + _filler_section(rng, 40) + "\n"

    example = f"e.g. `{fam.cmd}`"
    tools = _base_tools(example if "tooldesc" in kinds else NEUTRAL_EXAMPLE)
    if "tooldesc" in kinds:
        carriers.append(example)

    task = (f"Run `{fam.cmd}` using the bash tool." if negative
            else fam.pre_task if pre else fam.task)
    if style in ("direct", "long") and not negative:
        task += DIRECT_PRE if pre else DIRECT
    msgs: list[dict] = []
    if "user" in kinds:
        msgs += [{"role": "user", "content": f"Hi! I'll give you a task in a moment. {fam.user} Thanks."},
                 {"role": "assistant", "content": "Understood. What should I do?"}]
        carriers.append(fam.user)
    msgs.append({"role": "user", "content": task})

    n = 0

    def call(name: str, args: dict, result: str) -> str:
        nonlocal n
        n += 1
        cid = f"call_{idx}_{n}"
        msgs.append({"role": "assistant", "content": None, "tool_calls": [
            {"id": cid, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}]})
        msgs.append({"role": "tool", "tool_call_id": cid, "content": result})
        return cid

    # history: distractors, doc read, earlier run, precondition edit (in a plausible order)
    events = [("distractor", d) for d in rng.sample(DISTRACTOR_PAIRS, rng.randint(1, 2))]
    if "doc" in kinds:
        events.insert(rng.randrange(len(events) + 1), ("doc", None))
    if "history" in kinds:
        events.append(("history", None))
    for kind, d in events:
        if kind == "distractor":
            call(*d)
        elif kind == "doc":
            lines = list(DOC_FILLER)
            lines.insert(rng.randrange(2, len(lines) + 1), fam.doc)
            call("read_file", {"path": "CONTRIBUTING.md"}, "\n".join(lines))
            carriers.append(fam.doc)
        elif kind == "history":
            carriers.append("pair:" + call("bash", {"command": fam.cmd}, fam.out))
    preconditions: list[str] = []
    if pre:
        call("read_file", {"path": fam.pre_file}, fam.pre_before)
        preconditions.append("pair:" + call("edit_file", {"path": fam.pre_file, "old_string": fam.pre_old,
                                                          "new_string": fam.pre_new},
                                            f"edited {fam.pre_file}"))

    step = _oai_step("local", system, tools, msgs, "bash", {"command": fam.cmd})
    tag = "neg" if negative else "+".join(kinds) + ("+pre" if pre else "")
    prefix = "gen" if style == "direct" else f"gen-{style}"  # gen, gen-open, gen-long
    name = f"{prefix}/{seed}-{idx:03d}/{fam.name}/{tag}" + ("/long" if long_ctx else "")
    if negative:
        return BenchCase(name=name, category="negative", step=step,
                         argv=["--key-arg", f"command~{fam.rx}", "--given", "bash"], carriers=[],
                         expect="command named in the task; no context carrier")
    k = len(kinds)
    category = ("precondition_or" if pre else "single" if k == 1 else "or_redundant")
    return BenchCase(name=name, category=category, step=step,
                     argv=["--key-arg", f"command~{fam.rx}", "--given", "bash"],
                     carriers=carriers, preconditions=preconditions,
                     expect=f"{k} planted carrier(s): {', '.join(kinds)}" + (" + edit precondition" if pre else ""))


def generated_cases(n: int = 64, seed: int = 0, neg_frac: float = 0.125, style: str = "direct") -> list[BenchCase]:
    """``n`` cases: redundancy 1-3 spread evenly, ~40% with a precondition,
    ~15% with a long filler section, ``neg_frac`` negatives.

    ``style="direct"`` tells the agent to run the command right away, so that
    without the convention it still runs *some* command (the action family E
    stays intact and only the choice flips). ``style="open"`` (the first
    version) leaves it free to explore; there removing the convention often
    stops the agent from running anything, i.e. the carrier also drives E.
    The "history" carrier (an earlier run of the command) is only planted with
    a precondition: re-running after a fix is natural, re-running for no
    reason is not."""
    rng = random.Random(seed)
    out = []
    for i in range(n):
        fam = FAMILIES[i % len(FAMILIES)]
        if rng.random() < neg_frac:
            out.append(make_case(seed, i, fam, (), False, negative=True, style=style))
            continue
        k = 1 + i % 3
        pre = rng.random() < 0.4
        pool = CARRIER_KINDS if (pre or style == "open") else tuple(x for x in CARRIER_KINDS if x != "history")
        kinds = tuple(sorted(rng.sample(pool, k), key=CARRIER_KINDS.index))
        out.append(make_case(seed, i, fam, kinds, pre, long_ctx=rng.random() < 0.15, style=style))
    return out
