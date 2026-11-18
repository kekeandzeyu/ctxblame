"""ctxblame command line.

    ctxblame record --upstream https://api.deepseek.com/anthropic   # proxy; writes traces/<id>.jsonl
    ctxblame steps traces/<id>.jsonl                               # what is in the trace
    ctxblame replay traces/<id>.jsonl --step 14 -n 10              # does step 14 reproduce?
    ctxblame why traces/<id>.jsonl --step 14                       # which context caused it?
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import blame, proxy, replay
from .match import MODES
from .trace import describe, load_trace, matcher_for


def steps_cmd(args) -> int:
    try:
        steps = load_trace(args.trace)
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 5
    rows = [describe(s, matcher_for(s, args.match)) for s in steps]
    if args.json:
        print(json.dumps(rows, indent=1, ensure_ascii=False))
        return 0
    print(f"{'step':>4}  {'time':8}  {'format':9} {'model':18} {'msgs':>4} {'in_tok':>7} {'out':>5}  decision")
    for r in rows:
        dec = r["decision"] + (f"  (+{r['n_calls'] - 1} more)" if r["n_calls"] > 1 else "")
        if r["error"] or (r["status"] and r["status"] != 200):
            dec = f"[HTTP {r['status']}] {r['error'] or ''}".strip()
        print(f"{r['step']:>4}  {r['time']:8}  {r['format']:9} {str(r['model'])[:18]:18} {r['messages']:>4} "
              f"{r['input_tokens']:>7} {r['output_tokens']:>5}  {dec[:90]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ctxblame", description="git blame for LLM agent decisions")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("record", help="run the recording proxy")
    proxy.add_args(p)
    p.set_defaults(func=proxy.run)

    p = sub.add_parser("steps", help="list the steps (LLM calls) in a trace")
    p.add_argument("trace", type=Path)
    p.add_argument("--match", choices=MODES, default="intent", help="how decisions are labelled")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=steps_cmd)

    p = sub.add_parser("replay", help="replay one step N times (optionally with context removed)")
    replay.add_args(p)
    p.set_defaults(func=replay.run_cli)

    p = sub.add_parser("why", help="find the context chunks that caused the decision at one step")
    blame.add_args(p)
    p.set_defaults(func=blame.run_cli)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
