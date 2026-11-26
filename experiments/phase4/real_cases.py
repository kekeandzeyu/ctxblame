"""Benchmark cases from real recorded agent runs (Phase 4, suite "real").

Each trace in ``results/traces/run*.jsonl`` is one run of experiments/phase1/agent.py
against a local model, with AGENTS.md and the bash tool's example prescribing
the test command (default ``python -m pytest -q -x --tb=line``). Every step
whose recorded reply runs that command becomes a case:

  carriers       the AGENTS.md rule line, the tool example, and every earlier
                 call of the command (the agent's own history)
  preconditions  the edit_file calls since the previous test run (re-running
                 the tests only makes sense after an edit)
  decision       the command uses the convention's distinctive flag
                 (``--key-arg command~--tb=line``); the action family is
                 conditioned automatically (``run pytest``)

As with the generated cases, oracle.py decides which planted carriers really
drive the model before anything is scored.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "experiments" / "phase3"))

from cases import BenchCase  # noqa: E402
from ctxblame.formats import extract_decision  # noqa: E402
from ctxblame.trace import load_trace  # noqa: E402

TEST_CMD = "python -m pytest -q -x --tb=line"
FLAG_RX = r"--tb=line"


def _calls(msg: dict) -> list[tuple[str, str, dict]]:
    out = []
    for tc in msg.get("tool_calls") or []:
        try:
            a = json.loads(tc["function"]["arguments"] or "{}")
        except json.JSONDecodeError:
            a = {}
        out.append((tc["id"], tc["function"]["name"], a))
    return out


def cases_from_trace(path: Path, test_cmd: str = TEST_CMD) -> list[BenchCase]:
    rule = f"Run the test suite with `{test_cmd}`"
    example = f"e.g. `{test_cmd}`"
    out = []
    for st in load_trace(path):
        if st.fmt != "openai":
            continue
        dec = extract_decision(st.fmt, st.response)
        if not any(c.name == "bash" and re.search(FLAG_RX, str(c.args.get("command", ""))) for c in dec.calls):
            continue
        history, edits_since = [], []
        for m in st.body["messages"]:
            for cid, name, a in _calls(m):
                if name == "bash" and "pytest" in str(a.get("command", "")):
                    history.append(f"pair:{cid}")
                    edits_since = []
                elif name in ("edit_file", "write_file"):
                    edits_since.append(f"pair:{cid}")
        hist_ok = list(history)  # the agent's earlier runs of the command back the rule up
        category = "precondition_or" if edits_since else "or_redundant"
        out.append(BenchCase(
            name=f"real/{path.stem}/step{st.step}",
            category=category,
            step=st,
            argv=["--key-arg", f"command~{FLAG_RX}"],
            carriers=[rule, example, *hist_ok],
            preconditions=edits_since,
            expect=f"real agent run: rule + tool example + {len(hist_ok)} earlier run(s)"
                   + (f" + {len(edits_since)} edit precondition(s)" if edits_since else ""),
        ))
    return out


def real_cases(trace_dir: Path | None = None) -> list[BenchCase]:
    """All cases, minus exact duplicates (step 1 is the same request in every run)."""
    if trace_dir is None:  # published traces; record.sh writes to traces/ by default
        trace_dir = HERE / "results" / "traces"
        if not any(trace_dir.glob("run*.jsonl")):
            trace_dir = HERE / "traces"
    out, seen = [], set()
    for p in sorted(trace_dir.glob("run*.jsonl"), key=lambda p: int(re.sub(r"\D", "", p.stem) or 0)):
        for c in cases_from_trace(p):
            key = re.sub(r"/tmp/ctxblame-ws-\d+", "WS", json.dumps(c.step.body["messages"], sort_keys=True))
            if key not in seen:
                seen.add(key)
                out.append(c)
    return out
