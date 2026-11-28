"""Phase 6 cases: generated coding-agent steps with m <= 5 planted *elements*.

An element is a span the coalition table removes as a unit: a choice carrier, a
workflow precondition, or a neutral *probe*. Probes are lines already in the case
(a filler repository rule, a filler line of CONTRIBUTING.md, a distractor tool
call), not new text, so the table shows directly whether "neutral" context
matters to the model (Phase 6.3, Llama's padded bundles).

The design tag says what was planted and is used only to stratify the suite;
the truth label always comes from the table (``truth.py``):

  single / or     1-3 carriers of the convention (gen "direct" style), +-precondition
  e_coupled       gen "open" style: without the convention the agent may not act at all
  and             the command split into two facts in two places (tool + flag/target),
                  so the exact command needs both
  conflict        the convention plus a stale doc line naming another command
  habit_negative  no carrier; the target is the model's habitual command (``pytest``)

Cases are deterministic in (seed, index).
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "phase3"))

from cases import BenchCase, _base_tools, _oai_step  # noqa: E402
from gen_cases import (CARRIER_KINDS, DISTRACTOR_PAIRS, DOC_FILLER, FAMILIES, FILLER_RULES,  # noqa: E402
                       make_case)

MAX_ELEMENTS = 5

# (tool fact, flag/target fact) per family: the exact command needs both
AND_PARTS = {
    "tox": ("- Run the test suite with tox; never call pytest directly.",
            "The tox environment for tests is named `py312`; always pass it with `-e`."),
    "hatch": ("- Tests run only through hatch; do not invoke pytest or unittest yourself.",
              "The hatch test script is `test:all` (`hatch run <script>`)."),
    "make": ("- Verify every change with the Makefile, never with ad-hoc commands.",
             "The Makefile target that runs lint, type check and tests is `check`."),
    "pnpm": ("- Install JavaScript dependencies with pnpm only.",
             "Installs must not touch the lockfile: always pass `--frozen-lockfile`."),
    "uv": ("- Manage the Python environment with uv (`uv sync`).",
           "Environment syncs must leave uv.lock untouched: always pass `--frozen`."),
    "ruff": ("- Lint Python code with `ruff check`.",
             "Lint runs must apply the safe fixes: always pass `--fix`."),
    "cargo": ("- Run Rust tests with cargo, using the nextest runner.",
              "The test subcommand is `cargo nextest run`, not `cargo test`."),
    "script": ("- CI checks run through `./scripts/ci.sh`; do not call the tools it wraps.",
               "For a fast local check pass `--quick` to the CI script."),
}

STALE_DOC = "Legacy note (2019): tests used to run with `python setup.py test`."


@dataclass
class TableCase:
    case: BenchCase
    elements: dict[str, str]  # element name -> chunk spec ("pair:<id>" or a text span)
    kinds: dict[str, str]  # element name -> carrier | precondition | probe | conflict
    design: str
    meta: dict = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.case.name


def _replace(obj, old: str, new: str):
    if isinstance(obj, str):
        return obj.replace(old, new)
    if isinstance(obj, list):
        return [_replace(x, old, new) for x in obj]
    if isinstance(obj, dict):
        return {k: _replace(v, old, new) for k, v in obj.items()}
    return obj


def _rewrite(case: BenchCase, old: str, new: str) -> BenchCase:
    case.step.record["request"]["body"] = _replace(case.step.body, old, new)
    case.carriers = [new if c == old else c for c in case.carriers]
    return case


def _probe_candidates(case: BenchCase) -> list[str]:
    """Neutral spans present in this case: filler rules, filler doc lines, distractor calls."""
    body = case.step.body
    system = body["messages"][0]["content"]
    out = [r for r in FILLER_RULES if r in system]
    taken = set(case.carriers) | set(case.preconditions)
    for m in body["messages"]:
        for tc in m.get("tool_calls") or []:
            f = tc["function"]
            if (f["name"], f["arguments"]) in {(n, __import__("json").dumps(a)) for n, a, _ in DISTRACTOR_PAIRS}:
                if "pair:" + tc["id"] not in taken:
                    out.append("pair:" + tc["id"])
        if m.get("role") == "tool" and "# Contributing" in (m.get("content") or ""):
            out += [d for d in DOC_FILLER[2:] if d in m["content"]]  # skip the heading and the greeting
    return out


def _with_probes(case: BenchCase, design: str, rng: random.Random, extra: dict | None = None,
                 n_probes: int = 2) -> TableCase:
    elements: dict[str, str] = {}
    kinds: dict[str, str] = {}
    for i, c in enumerate(case.carriers, 1):
        elements[f"c{i}"], kinds[f"c{i}"] = c, "carrier"
    for i, p in enumerate(case.preconditions, 1):
        elements[f"pre{i}" if len(case.preconditions) > 1 else "pre"] = p
        kinds[f"pre{i}" if len(case.preconditions) > 1 else "pre"] = "precondition"
    for k, (spec, kind) in (extra or {}).items():
        elements[k], kinds[k] = spec, kind
    room = MAX_ELEMENTS - len(elements)
    cands = _probe_candidates(case)
    for i, p in enumerate(rng.sample(cands, min(n_probes, room, len(cands))), 1):
        elements[f"p{i}"], kinds[f"p{i}"] = p, "probe"
    return TableCase(case, elements, kinds, design)


def _habit_case(seed: int, idx: int, rng: random.Random) -> BenchCase:
    rules = rng.sample(FILLER_RULES, rng.randint(3, 4))
    system = ("You are a careful coding agent working in a Python repository.\n"
              "Use the tools to inspect, change and verify the code. Do one step at a time.\n\n"
              "## Repository Rules\n" + "\n".join(rules) + "\n")
    msgs: list[dict] = [{"role": "user", "content": "Run the test suite and tell me whether it passes. "
                         "Use the bash tool for it right away; do not explore the repository first."}]
    for n, (name, args, result) in enumerate(rng.sample(DISTRACTOR_PAIRS, 2), 1):
        cid = f"call_h{idx}_{n}"
        msgs += [{"role": "assistant", "content": None, "tool_calls": [
            {"id": cid, "type": "function", "function": {"name": name, "arguments": __import__("json").dumps(args)}}]},
            {"role": "tool", "tool_call_id": cid, "content": result}]
    step = _oai_step("local", system, _base_tools(), msgs, "bash", {"command": "python -m pytest"})
    return BenchCase(name=f"p6/{seed}-{idx:03d}/habit/neg", category="negative", step=step,
                     argv=["--key-arg", r"command~\bpytest\b", "--given", "bash"], carriers=[],
                     expect="no carrier: the model's habit decides")


def phase6_cases(n: int = 250, seed: int = 0) -> list[TableCase]:
    """``n`` cases, designs in fixed proportions (single/or 40%, precondition-gated
    20%, and 12%, e_coupled 10%, conflict 10%, habit_negative 8%)."""
    rng = random.Random(f"p6-{seed}")
    plan = (["or"] * 40 + ["pre"] * 20 + ["and"] * 12 + ["open"] * 10 + ["conflict"] * 10 + ["habit"] * 8)
    out: list[TableCase] = []
    for i in range(n):
        d = plan[i % len(plan)] if n >= len(plan) else rng.choice(plan)
        fam = FAMILIES[i % len(FAMILIES)]
        crng = random.Random(f"p6-{seed}-{i}")
        if d == "habit":
            out.append(_with_probes(_habit_case(seed, i, crng), "habit_negative", crng, n_probes=3))
            continue
        if d == "and":
            c = make_case(seed, 1000 + i, fam, ("system", "doc"), False)
            a, b = AND_PARTS[fam.name]
            c = _rewrite(_rewrite(c, fam.rule, a), fam.doc, b)
            c.name = c.name.replace("gen/", "p6/", 1) + "/and"
            c.category = "and"
            out.append(_with_probes(c, "and", crng))
            continue
        pre = d == "pre"
        k = 1 + crng.randrange(3 if not pre else 2)  # m <= 5 with a precondition and >= 1 probe
        pool = CARRIER_KINDS if pre else tuple(x for x in CARRIER_KINDS if x != "history")
        kinds = tuple(sorted(crng.sample(pool, k), key=CARRIER_KINDS.index))
        c = make_case(seed, 1000 + i, fam, kinds, pre, style="open" if d == "open" else "direct")
        c.name = c.name.replace("gen/", "p6/", 1).replace("gen-open/", "p6/", 1) + (
            "/open" if d == "open" else "")
        design = "e_coupled" if d == "open" else ("precondition_gated" if pre else "single" if k == 1 else "or")
        extra = None
        if d == "conflict":
            c = make_case(seed, 1000 + i, fam, ("system",), False)
            c.name = c.name.replace("gen/", "p6/", 1) + "/conflict"
            body = c.step.body
            for m in body["messages"]:
                if m.get("role") == "tool" and "# Contributing" in (m.get("content") or ""):
                    m["content"] += "\n" + STALE_DOC
                    break
            else:  # no CONTRIBUTING.md read yet: put the stale line in the system prompt
                body["messages"][0]["content"] += "\n" + STALE_DOC.replace("Legacy note", "- Legacy note") + "\n"
            design, extra = "conflict", {"x1": (STALE_DOC, "conflict")}
        out.append(_with_probes(c, design, crng, extra))
    return out
