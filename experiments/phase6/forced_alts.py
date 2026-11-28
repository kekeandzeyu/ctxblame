"""What replaces A under do(E) (6.4, $0, offline): for each steer set of a forced table
that touches a precondition set, what did the forced replies in E do instead of A?

  step: inspect   read / list / search, git status | diff | log | show | branch
  step: edit      edit a file, git add | commit | apply | checkout | stash, sed, patch, echo
  same program    A's program at another step (pnpm add for pnpm install)
  competing tool  any other program (flake8 for ruff, npm for pnpm)

The classes are a heuristic over ``match.intent`` labels and only describe the
flips; the truth itself is unchanged (a flip of A among E, as for carriers). Needs
forced tables that record ``replies`` (tables.py since 6.4b).

    python experiments/phase6/forced_alts.py experiments/phase6/results/p64b-qwen3-14b
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

INSPECT = {"git status", "git diff", "git log", "git show", "git branch"}
EDIT = {"git add", "git commit", "git apply", "git checkout", "git stash"}
EDIT_PROGS = {"edit_file", "edit", "sed", "patch", "echo"}


def kind_of(intent: str, a_progs: set[str]) -> str:
    words = intent.split()
    if not words:
        return "competing tool"
    sub = " ".join(words[1:3])
    if words[0] in ("read", "list", "search") or sub in INSPECT:
        return "step: inspect"
    if words[0] == "edit" or sub in EDIT or words[1:2] and words[1] in EDIT_PROGS:
        return "step: edit"
    prog = words[1] if words[0] == "run" and len(words) > 1 else intent
    return "same program" if prog in a_progs else "competing tool"


def case_rows(d: dict) -> list[tuple[str, str, Counter]]:
    """(planted kinds of the steer set, main class, intents instead of A) per steer set."""
    t = d["truth"]
    if not (t.get("forced") or {}).get("used"):
        return []
    cells = {frozenset(c["removed"]): c for c in d["forced_cells"]}
    a_progs = {i.split()[1] for c in d["forced_cells"] for a, i, _ in c.get("replies", [])
               if a and i.startswith("run ") and len(i.split()) > 1}
    pre = set().union(*map(set, t["precondition_sets"])) if t["precondition_sets"] else set()
    out = []
    for s in t["steer_sets"]:
        if not set(s) & pre:
            continue
        alts = Counter({i: n for a, i, n in cells[frozenset(s)].get("replies", []) if not a})
        by = Counter()
        for i, n in alts.items():
            by[kind_of(i, a_progs)] += n
        out.append(("+".join(sorted({t["kinds"][x] for x in s})), by.most_common(1)[0][0] if by else "none", alts))
    return out


def summarize(results: Path) -> dict:
    rows: Counter = Counter()
    eg: dict = defaultdict(Counter)
    for f in sorted((results / "forced").glob("*.json")):
        for kinds, main, alts in case_rows(json.loads(f.read_text())):
            rows[(kinds, main)] += 1
            eg[(kinds, main)].update(alts)
    return {"rows": [{"kinds": k, "instead": m, "steer_sets": v, "examples": eg[(k, m)].most_common(3)}
                     for (k, m), v in sorted(rows.items())]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("results", type=Path, nargs="+")
    args = ap.parse_args(argv)
    for r in args.results:
        print(f"## {r.name}\n\n| planted kinds | instead of A | steer sets | most common |\n|---|---|---:|---|")
        for row in summarize(r)["rows"]:
            ex = ", ".join(f"`{i}` {n}" for i, n in row["examples"])
            print(f"| {row['kinds']} | {row['instead']} | {row['steer_sets']} | {ex} |")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
