"""Benchmark cases for Phase 3 evaluation (ctxblame vs. LOO vs. LLM self-explanation).

Combines:
- Existing Phase 0 single-carrier OpenAI records
- Existing Phase 1 real 20k-token coding-agent OpenAI trace steps (single, 2-OR, 3-OR + precondition)
- Five self-contained Phase 3 OpenAI stress cases covering:
  * workflow preconditions + 2-way and 3-way redundant OR-carriers
  * long-context (~14k chars) tail-only carrier (KV-cache hit-rate benchmark)
  * 2-way redundant OR-carrier with distractor tool descriptions
  * negative control (task/habit only -> tests self-explanation hallucination rate)
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from ctxblame.trace import Step, get_step, load_trace

HERE = Path(__file__).parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "experiments" / "phase0"))
sys.path.insert(0, str(REPO / "experiments" / "phase1"))

from scenarios import SCENARIOS  # noqa: E402
import ablations as P1  # noqa: E402

P0_RECORDS = REPO / "experiments" / "phase0" / "results" / "deepseek-v4-pro" / "records"
P1_TRACES = REPO / "experiments" / "phase1" / "results" / "traces"


@dataclass
class BenchCase:
    name: str
    category: str  # single | or_redundant | precondition_or | tail_long_ctx | negative
    step: Step
    argv: list[str]
    carriers: list[str]  # ground-truth choice carriers ("pair:<id>" or text substring)
    preconditions: list[str] = field(default_factory=list)  # expected workflow preconditions
    protect: list[str] = field(default_factory=list)
    expect: str = ""


def _oai_step(model: str, system: str, tools: list[dict], messages: list[dict],
              rec_tool: str, rec_args: dict) -> Step:
    body = {
        "model": model,
        "max_tokens": 1024,
        "messages": [{"role": "system", "content": system}, *messages],
        "tools": [{"type": "function", "function": t} for t in tools],
    }
    resp = {
        "id": "chatcmpl-bench",
        "object": "chat.completion",
        "model": model,
        "choices": [{
            "index": 0,
            "finish_reason": "tool_calls",
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call_rec",
                    "type": "function",
                    "function": {"name": rec_tool, "arguments": json.dumps(rec_args)},
                }],
            },
        }],
        "usage": {"prompt_tokens": len(json.dumps(body)) // 4, "completion_tokens": 64},
    }
    record = {
        "step": 1,
        "format": "openai",
        "upstream": "http://127.0.0.1:8000/v1",
        "request": {"path": "/chat/completions", "headers": {}, "body": body},
        "response": {"status": 200, "streamed": False, "body": resp},
    }
    return Step(1, record)


def _base_tools(bash_example: str = "e.g. `git status`") -> list[dict]:
    return [
        {
            "name": "bash",
            "description": "Run one shell command in the repository working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": f"the command line, {bash_example}"},
                    "description": {"type": "string", "description": "short summary of what the command does"},
                },
                "required": ["command"],
            },
        },
        {
            "name": "read_file",
            "description": "Read a text file from the repository and return numbered lines.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "relative file path"},
                    "limit": {"type": "integer", "description": "maximum number of lines to return"},
                },
                "required": ["path"],
            },
        },
        {
            "name": "edit_file",
            "description": "Replace one exact occurrence of old_string with new_string in a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "relative file path"},
                    "old_string": {"type": "string", "description": "exact existing text"},
                    "new_string": {"type": "string", "description": "replacement text"},
                },
                "required": ["path", "old_string", "new_string"],
            },
        },
        {
            "name": "list_dir",
            "description": "List files and subdirectories in a directory.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "directory path"}},
                "required": ["path"],
            },
        },
    ]


def _p0_openai_cases() -> list[BenchCase]:
    out: list[BenchCase] = []
    # Skip system_rule_make_clean (known 0% baseline even on DeepSeek v4-pro)
    for sc in SCENARIOS:
        if sc.name == "system_rule_make_clean":
            continue
        path = P0_RECORDS / f"{sc.name}.openai.json"
        if not path.exists():
            continue
        step = get_step(load_trace(path), None)
        carriers = [f"pair:{sc.plant_pair}"] if sc.plant_pair else [sc.plant]
        if sc.name == "system_section_deploy_freeze":
            # Decision is tool choice (calling check_calendar instead of deploy)
            argv = ["--target", "call check_calendar"]
        else:
            target = f"{sc.target}({json.dumps({k: True for k in sc.key_args}, sort_keys=True)})"
            argv = [x for k in sc.key_args for x in ("--key-arg", k)] + ["--target", target]
        out.append(BenchCase(
            name=f"p0/{sc.name}",
            category="single",
            step=step,
            argv=argv,
            carriers=carriers,
            protect=list(sc.protect),
            expect="single planted carrier",
        ))
    return out


def _p1_openai_cases() -> list[BenchCase]:
    trace_path = P1_TRACES / "openai-1.jsonl"
    if not trace_path.exists():
        return []
    steps = load_trace(trace_path)
    arch_argv = ["--target", "read docs/ARCHITECTURE.md"]
    pyt_argv = ["--key-arg", f"command~{P1.PYTEST_RX}",
                "--target", f'bash({{"command~{P1.PYTEST_RX}": true}})']
    rule_arch, rule_test, example = P1.RULE_ARCH, P1.RULE_TEST, P1.EXAMPLE.strip(", ")

    st5 = get_step(steps, 5)
    hist_pytest = [f"pair:{p}" for p in P1.pair_ids(st5, "pytest")]
    edit_pairs = [f"pair:{p}" for p in P1.pair_ids(st5, "formats.py") if p not in [h[5:] for h in hist_pytest]]
    # Explicitly find edit_file pair id on step 5
    from ctxblame.ablate import list_units
    edit_pre = [u.id for u in list_units(st5.fmt, st5.body)
                if u.kind == "tool pair" and u.label.startswith("edit_file(")]

    return [
        BenchCase(
            name="p1/arch/step2",
            category="single",
            step=get_step(steps, 2),
            argv=arch_argv,
            carriers=[rule_arch],
            expect="system rule line in 20k-token agent trace",
        ),
        BenchCase(
            name="p1/pytest/step1",
            category="or_redundant",
            step=get_step(steps, 1),
            argv=pyt_argv,
            carriers=[rule_test, example],
            expect="2-way redundant OR-carriers (AGENTS.md + tool schema example)",
        ),
        BenchCase(
            name="p1/pytest/step5",
            category="precondition_or",
            step=st5,
            argv=pyt_argv,
            carriers=[rule_test, example, *hist_pytest],
            preconditions=edit_pre or edit_pairs[:1],
            expect="edit_file precondition separated from 3-way redundant pytest OR-carriers",
        ),
    ]


def _p3_synthetic_cases() -> list[BenchCase]:
    cases: list[BenchCase] = []

    # 1. Precondition (edit_file) + 2 redundant OR-carriers (pnpm --frozen-lockfile)
    rule_pnpm = "- Always install dependencies with `pnpm install --frozen-lockfile`; never run `npm install`."
    ex_pnpm = "e.g. `pnpm install --frozen-lockfile`"
    sys_pnpm = (
        "You are a careful coding agent working in a TypeScript monorepo.\n"
        "Inspect files before editing, apply minimal edits, and verify your changes.\n\n"
        "## Repository Rules\n"
        "- TypeScript strict mode is enabled across all packages.\n"
        f"{rule_pnpm}\n"
        "- Do not commit build artifacts under dist/.\n"
    )
    msgs_pnpm = [
        {"role": "user", "content": "Add `zod` `^3.23.0` to package.json and install dependencies."},
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": "call_read_pkg", "type": "function",
             "function": {"name": "read_file", "arguments": json.dumps({"path": "package.json"})}}]},
        {"role": "tool", "tool_call_id": "call_read_pkg",
         "content": '{\n  "name": "web-app",\n  "dependencies": {\n    "react": "^19.0.0"\n  }\n}'},
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": "call_edit_pkg", "type": "function",
             "function": {"name": "edit_file", "arguments": json.dumps({
                 "path": "package.json",
                 "old_string": '"react": "^19.0.0"',
                 "new_string": '"react": "^19.0.0",\n    "zod": "^3.23.0"',
             })}}]},
        {"role": "tool", "tool_call_id": "call_edit_pkg", "content": "edited package.json"},
    ]
    cases.append(BenchCase(
        name="p3/precond_2or_pnpm",
        category="precondition_or",
        step=_oai_step("local", sys_pnpm, _base_tools(ex_pnpm), msgs_pnpm,
                       "bash", {"command": "pnpm install --frozen-lockfile"}),
        argv=["--key-arg", r"command~pnpm\s+install.*--frozen-lockfile", "--given", "bash"],
        carriers=[rule_pnpm, ex_pnpm],
        preconditions=["pair:call_edit_pkg"],
        expect="edit_file precondition + 2 redundant pnpm carriers",
    ))

    # 2. Precondition (edit_file) + 3 redundant OR-carriers (python -m unittest -v)
    rule_ut = "- Run the test suite with `python -m unittest -v`; do not use pytest."
    ex_ut = "e.g. `python -m unittest -v`"
    sys_ut = (
        "You are a software engineering agent fixing a Python library bug.\n"
        "After editing code, always re-run the test suite to verify the fix.\n\n"
        "## Workflow\n"
        "- Keep diffs minimal and well-typed.\n"
        f"{rule_ut}\n"
        "- Never modify files under tests/.\n"
    )
    msgs_ut = [
        {"role": "user", "content": "A unit test in tests/test_calc.py is failing on divide(). Fix src/calc.py and re-run tests."},
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": "call_ut1", "type": "function",
             "function": {"name": "bash", "arguments": json.dumps({"command": "python -m unittest -v"})}}]},
        {"role": "tool", "tool_call_id": "call_ut1",
         "content": "test_divide (tests.test_calc.TestCalc) ... FAIL\nAssertionError: 2 != 2.5\nFAILED (failures=1)"},
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": "call_read_calc", "type": "function",
             "function": {"name": "read_file", "arguments": json.dumps({"path": "src/calc.py"})}}]},
        {"role": "tool", "tool_call_id": "call_read_calc",
         "content": "1\tdef divide(a: float, b: float) -> float:\n2\t    return a // b\n"},
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": "call_edit_calc", "type": "function",
             "function": {"name": "edit_file", "arguments": json.dumps({
                 "path": "src/calc.py", "old_string": "return a // b", "new_string": "return a / b",
             })}}]},
        {"role": "tool", "tool_call_id": "call_edit_calc", "content": "edited src/calc.py"},
    ]
    cases.append(BenchCase(
        name="p3/precond_3or_unittest",
        category="precondition_or",
        step=_oai_step("local", sys_ut, _base_tools(ex_ut), msgs_ut,
                       "bash", {"command": "python -m unittest -v"}),
        argv=["--key-arg", r"command~^python -m unittest", "--given", "bash"],
        carriers=[rule_ut, ex_ut, "pair:call_ut1"],
        preconditions=["pair:call_edit_calc"],
        expect="edit_file precondition + 3 redundant unittest carriers",
    ))

    # 3. Long-context (~14k chars) tail-only carrier (KV-cache benchmark)
    filler_doc = "\n".join(
        f"- Module service_{i:02d}: handles internal telemetry batch {i} with retry window {10 + i}s and JSON logging."
        for i in range(45)
    )
    sys_long = (
        "You are an operations agent working inside a service monorepo.\n"
        "Read the relevant runbooks before invoking CLI commands.\n\n"
        "## Service Catalog\n"
        f"{filler_doc}\n\n"
        "## General Guidelines\n"
        "- Never expose credentials in logs.\n"
        "- Keep command invocations concise and auditable.\n"
    )
    tail_rule = "Always include `--dry-run` when running `deploy_cli` for staging verification."
    msgs_long: list[dict] = [
        {"role": "user", "content": "Run staging verification for api-gateway using deploy_cli."},
    ]
    for i in range(4):
        cid = f"call_early_{i}"
        msgs_long.append({"role": "assistant", "content": None, "tool_calls": [
            {"id": cid, "type": "function",
             "function": {"name": "read_file", "arguments": json.dumps({"path": f"docs/service_{i}.md"})}}]})
        msgs_long.append({"role": "tool", "tool_call_id": cid, "content": (
            f"# Service {i} Notes\n" + "\n".join(
                f"line {j}: standard healthcheck endpoint /healthz returns 200 OK for replica group {i}-{j}."
                for j in range(18)
            )
        )})
    msgs_long.append({"role": "assistant", "content": None, "tool_calls": [
        {"id": "call_tail_runbook", "type": "function",
         "function": {"name": "read_file", "arguments": json.dumps({"path": "docs/RELEASE.md"})}}]})
    msgs_long.append({"role": "tool", "tool_call_id": "call_tail_runbook", "content": (
        "# Release Runbook\n"
        "Staging environment uses cluster `stg-us-west`.\n"
        f"{tail_rule}\n"
        "Notify #releases after production cutover.\n"
    )})
    cases.append(BenchCase(
        name="p3/tail_carrier_long_ctx",
        category="tail_long_ctx",
        step=_oai_step("local", sys_long, _base_tools(), msgs_long,
                       "bash", {"command": "deploy_cli --service api-gateway --env staging --dry-run"}),
        argv=["--key-arg", r"command~--dry-run"],
        carriers=[tail_rule],
        expect="tail-only carrier in ~14k-char prompt (benchmarks suffix-first KV cache hit rate)",
    ))

    # 4. 2-way redundant OR-carrier with distractor tools (ruff check --fix)
    rule_ruff = "- Lint and auto-fix Python files using `ruff check --fix src/`; do not use flake8."
    ex_ruff = "e.g. `ruff check --fix src/`"
    sys_ruff = (
        "You are a careful Python coding agent.\n\n"
        "## Code Quality\n"
        "- Use Python 3.12 type annotations.\n"
        f"{rule_ruff}\n"
        "- Keep pull requests small.\n"
    )
    msgs_ruff = [
        {"role": "user", "content": "Lint the Python files under src/ and apply safe auto-fixes."},
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": "call_ls_src", "type": "function",
             "function": {"name": "list_dir", "arguments": json.dumps({"path": "src"})}}]},
        {"role": "tool", "tool_call_id": "call_ls_src", "content": "__init__.py\napp.py\nutils.py"},
    ]
    cases.append(BenchCase(
        name="p3/two_carrier_ruff",
        category="or_redundant",
        step=_oai_step("local", sys_ruff, _base_tools(ex_ruff), msgs_ruff,
                       "bash", {"command": "ruff check --fix src/"}),
        argv=["--key-arg", r"command~ruff\s+check\s+--fix", "--given", "bash"],
        carriers=[rule_ruff, ex_ruff],
        expect="2-way redundant ruff carriers with neutral distractor tool descriptions",
    ))

    # 5. Negative control: decision comes purely from task + model prior (no context cause)
    sys_neg = (
        "You are a helpful coding assistant.\n\n"
        "## Notes\n"
        "- The repository license is MIT.\n"
        "- Documentation is written in Markdown.\n"
    )
    msgs_neg = [
        {"role": "user", "content": "Run `git status` using the bash tool to inspect the working tree."},
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": "call_readme", "type": "function",
             "function": {"name": "read_file", "arguments": json.dumps({"path": "README.md"})}}]},
        {"role": "tool", "tool_call_id": "call_readme",
         "content": "# Demo Project\nA small utility library for parsing timestamps.\n"},
    ]
    cases.append(BenchCase(
        name="p3/negative_habit_only",
        category="negative",
        step=_oai_step("local", sys_neg, _base_tools("e.g. `ls -la`"), msgs_neg,
                       "bash", {"command": "git status"}),
        argv=["--target", "run git status"],
        carriers=[],
        expect="not_in_context (negative control: catches LLM self-explanation hallucinations)",
    ))

    return cases


def core_cases() -> list[BenchCase]:
    return _p0_openai_cases() + _p1_openai_cases() + _p3_synthetic_cases()


SUITES = ("core", "gen", "gen-open", "gen-long", "real", "all")


def all_cases(suite: str = "core", gen_n: int = 64, gen_seed: int = 0) -> list[BenchCase]:
    """``core`` = the 12 hand-written cases, ``gen`` = generated cases (direct
    style), ``gen-open`` = generated cases (open style), ``all`` = core + gen."""
    out = []
    if suite in ("core", "all"):
        out += core_cases()
    if suite in ("gen", "all", "gen-open", "gen-long"):
        from gen_cases import generated_cases
        style = {"gen-open": "open", "gen-long": "long"}.get(suite, "direct")
        out += generated_cases(gen_n, gen_seed, style=style)
    if suite == "real":
        sys.path.insert(0, str(REPO / "experiments" / "phase4"))
        from real_cases import real_cases
        out += real_cases()
    return out
