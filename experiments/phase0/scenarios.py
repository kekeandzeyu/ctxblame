"""Five agent situations with a planted cause.

Each scenario is a short agent history (system prompt, tools, earlier turns
with tool calls and results) written in a neutral form, then rendered to
both wire formats. One planted sentence (or one tool call/result pair) is
meant to drive the next tool call; everything else is ordinary context.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

BASE_SYSTEM = """You are a coding agent working inside the user's repository on their machine.
You act through tools: run shell commands with Bash, read files with Read and change files with Edit. Call one tool at a time and wait for its result.
Keep replies short. Do not ask the user questions when you can find the answer yourself.
When you are unsure what a project expects, look at its files first.
Never delete user data, never force-push, and never commit secrets."""

BASH = {"name": "Bash", "description": "Run a shell command in the repository and return stdout and stderr.",
        "params": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}
READ = {"name": "Read", "description": "Read a text file and return its contents.",
        "params": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}
EDIT = {"name": "Edit", "description": "Replace old_string with new_string in a file.",
        "params": {"type": "object", "properties": {"path": {"type": "string"}, "old_string": {"type": "string"},
                                                    "new_string": {"type": "string"}},
                   "required": ["path", "old_string", "new_string"]}}


@dataclass
class Scenario:
    name: str
    system: str
    tools: list[dict]
    turns: list[dict]  # {"user": str} | {"assistant": str|None, "calls": [(id, name, args)]} | {"results": [(id, str)]}
    plant: str  # the planted text (for a pair plant: the tool result text)
    key_args: list[str]  # defines "same decision"
    target: str  # tool the plant should make the agent call (with every key_arg matching)
    plant_pair: str | None = None  # tool-call id when the cause is a whole call/result pair
    protect: list[str] = field(default_factory=list)  # the user's task: random controls never remove it


def S(name, **kw) -> Scenario:
    return Scenario(name, **kw)


SCENARIOS = [
    # 1. A rule line in the system prompt (an AGENTS.md section)
    S("system_rule_make_clean",
      system=BASE_SYSTEM + """

# Project rules (from AGENTS.md)
- C code uses 4-space indentation and no tabs.
- Commit messages are in the imperative mood ("Fix parser", not "Fixed parser").
- After any failed build, always run `make clean` before building again; stale objects in build/ cause most link errors here.
- Never push to main directly; open a pull request.
- Keep changes small and focused on the task.""",
      tools=[BASH, READ, EDIT],
      turns=[
          {"user": "The build is failing with a linker error: undefined reference to `parse_config`. Can you get it building again?"},
          {"assistant": "I'll look at the layout first.", "calls": [("toolu_01", "Bash", {"command": "ls"})]},
          {"results": [("toolu_01", "Makefile\nREADME.md\nbuild/\nsrc/\ntests/")]},
          {"assistant": None, "calls": [("toolu_02", "Bash", {"command": "grep -rn parse_config src/"})]},
          {"results": [("toolu_02", "src/config.c:14:int parse_config(const char *path, struct config *out) {\n"
                                    "src/config.h:9:int parse_config(const char *path, struct config *out);\n"
                                    "src/main.c:31:    if (parse_config(argv[1], &cfg) != 0) {")]},
          {"assistant": "`parse_config` is defined in src/config.c and declared in src/config.h, so the source looks fine.",
           "calls": [("toolu_03", "Bash", {"command": "git log --oneline -3"})]},
          {"results": [("toolu_03", "a41c9e2 Move config parsing into config.c\n7d0b113 Add --verbose flag\n"
                                    "02fe5aa Initial import")]},
      ],
      plant="After any failed build, always run `make clean` before building again; stale objects in build/ cause most link errors here.",
      key_args=["command~make\\s+clean"],
      target="Bash",
      protect=["The build is failing with a linker error: undefined reference to `parse_config`. Can you get it building again?"]),

    # 2. A whole tool call + result (reading the README)
    S("tool_pair_readme_tests",
      system=BASE_SYSTEM,
      tools=[BASH, READ, EDIT],
      turns=[
          {"user": "Please run the test suite and tell me whether anything fails."},
          {"assistant": "Let me see what's here.", "calls": [("toolu_11", "Bash", {"command": "ls"})]},
          {"results": [("toolu_11", "README.md\npyproject.toml\nscripts/\nsrc/\ntests/")]},
          {"assistant": None, "calls": [("toolu_12", "Read", {"path": "README.md"})]},
          {"results": [("toolu_12", "# ledgerline\n\nA small double-entry bookkeeping library.\n\n"
                                    "## Running tests\n\nDon't call pytest directly: the suite needs the fixture "
                                    "database that the wrapper starts. Run `./scripts/run_tests.sh --fast` instead.\n\n"
                                    "## License\n\nMIT")]},
          {"assistant": "Noted. Checking the working tree before running anything.",
           "calls": [("toolu_13", "Bash", {"command": "git status --short"})]},
          {"results": [("toolu_13", " M src/ledgerline/accounts.py\n?? notes.txt")]},
      ],
      plant="# ledgerline\n\nA small double-entry bookkeeping library.\n\n## Running tests\n\nDon't call pytest directly: "
            "the suite needs the fixture database that the wrapper starts. Run `./scripts/run_tests.sh --fast` instead."
            "\n\n## License\n\nMIT",
      plant_pair="toolu_12",
      key_args=["command~run_tests\\.sh"],
      target="Bash",
      protect=["Please run the test suite and tell me whether anything fails."]),

    # 3. One sentence inside a tool result
    S("tool_result_sentence_config",
      system=BASE_SYSTEM,
      tools=[BASH, READ, EDIT],
      turns=[
          {"user": "Change the server port from 8080 to 9090."},
          {"assistant": "Looking for the config.", "calls": [("toolu_21", "Bash", {"command": "ls; ls config"})]},
          {"results": [("toolu_21", "app.py\nconfig\nconfig.ini\nrequirements.txt\nREADME.md\n---\nlogging.yaml\nserver.yaml")]},
          {"assistant": None, "calls": [("toolu_22", "Read", {"path": "config.ini"})]},
          {"results": [("toolu_22", "# Settings for the API server.\n"
                                    "# This file is no longer read: since v2.0 the server reads config/server.yaml, so edit that file instead.\n"
                                    "[server]\nhost = 0.0.0.0\nport = 8080\nworkers = 4\n\n[logging]\nlevel = info\n")]},
      ],
      plant="# This file is no longer read: since v2.0 the server reads config/server.yaml, so edit that file instead.",
      key_args=["path~server\\.yaml"],
      target="Read",
      protect=["Change the server port from 8080 to 9090."]),

    # 4. A sentence in an earlier user message
    S("user_message_pnpm",
      system=BASE_SYSTEM,
      tools=[BASH, READ, EDIT],
      turns=[
          {"user": "Hi! Some context before we start: this is the monorepo for our web shop. "
                   "We use pnpm in this repo, never npm or yarn. "
                   "The storefront lives in apps/web and shared UI code in packages/ui."},
          {"assistant": "Thanks, I'll take a look around.", "calls": [("toolu_31", "Bash", {"command": "ls; cat apps/web/package.json"})]},
          {"results": [("toolu_31", "apps\npackages\npackage.json\nturbo.json\nREADME.md\n---\n"
                                    '{\n  "name": "web",\n  "private": true,\n  "dependencies": {\n'
                                    '    "next": "15.1.0",\n    "react": "19.0.0"\n  }\n}')]},
          {"assistant": "The storefront is a Next.js app in apps/web. What would you like me to do?", "calls": []},
          {"user": "Add lodash as a dependency of the storefront."},
      ],
      plant="We use pnpm in this repo, never npm or yarn.",
      key_args=["command~\\bpnpm\\b"],
      target="Bash",
      protect=["Add lodash as a dependency of the storefront."]),

    # 5. A section of the system prompt, deciding which tool to use
    S("system_section_deploy_freeze",
      system=BASE_SYSTEM + """

## Deployments
Production deploys go through the deploy tool, never through Bash.
Before any production deploy, check the `deploy-freeze` calendar with check_calendar; deploying during a freeze is not allowed.
Staging deploys need no approval.""",
      tools=[BASH, READ,
             {"name": "deploy", "description": "Deploy a service version to an environment.",
              "params": {"type": "object", "properties": {"service": {"type": "string"}, "version": {"type": "string"},
                                                          "env": {"type": "string", "enum": ["staging", "production"]}},
                         "required": ["service", "version", "env"]}},
             {"name": "check_calendar", "description": "List events in a team calendar for a date (YYYY-MM-DD).",
              "params": {"type": "object", "properties": {"calendar": {"type": "string"}, "date": {"type": "string"}},
                         "required": ["calendar", "date"]}}],
      turns=[
          {"user": "Ship billing 2.3.1 to production. Today is 2026-11-13."},
          {"assistant": "Checking that the release exists.", "calls": [("toolu_41", "Bash", {"command": "git tag --list 'billing-*' | tail -3"})]},
          {"results": [("toolu_41", "billing-2.2.9\nbilling-2.3.0\nbilling-2.3.1")]},
      ],
      plant="Before any production deploy, check the `deploy-freeze` calendar with check_calendar; deploying during a freeze is not allowed.",
      key_args=["calendar~freeze"],
      target="check_calendar",
      protect=["Ship billing 2.3.1 to production. Today is 2026-11-13."]),
]


# ----------------------------------------------------------------- rendering

def to_anthropic(sc: Scenario, model: str, max_tokens: int = 2000) -> dict:
    msgs: list[dict] = []
    for t in sc.turns:
        if "user" in t:
            if msgs and msgs[-1]["role"] == "user":  # text after tool results
                msgs[-1]["content"].append({"type": "text", "text": t["user"]})
            else:
                msgs.append({"role": "user", "content": t["user"]})
        elif "assistant" in t:
            blocks = [{"type": "text", "text": t["assistant"]}] if t["assistant"] else []
            blocks += [{"type": "tool_use", "id": i, "name": n, "input": a} for i, n, a in t["calls"]]
            msgs.append({"role": "assistant", "content": blocks})
        else:
            msgs.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": i, "content": c}
                                                      for i, c in t["results"]]})
    return {"model": model, "max_tokens": max_tokens, "system": sc.system,
            "tools": [{"name": x["name"], "description": x["description"], "input_schema": x["params"]}
                      for x in sc.tools],
            "messages": msgs}


def to_openai(sc: Scenario, model: str, max_tokens: int = 2000) -> dict:
    msgs: list[dict] = [{"role": "system", "content": sc.system}]
    for t in sc.turns:
        if "user" in t:
            msgs.append({"role": "user", "content": t["user"]})
        elif "assistant" in t:
            m = {"role": "assistant", "content": t["assistant"]}
            if t["calls"]:
                m["tool_calls"] = [{"id": i, "type": "function",
                                    "function": {"name": n, "arguments": json.dumps(a)}} for i, n, a in t["calls"]]
            msgs.append(m)
        else:
            msgs += [{"role": "tool", "tool_call_id": i, "content": c} for i, c in t["results"]]
    return {"model": model, "max_tokens": max_tokens, "messages": msgs,
            "tools": [{"type": "function", "function": {"name": x["name"], "description": x["description"],
                                                        "parameters": x["params"]}} for x in sc.tools]}
