#!/usr/bin/env bash
# Phase 5.5: re-run Qwen3-14B with the Phase 5 engine on the same oracle-valid cases
# as v0.2 (the v0.2 oracle files are copied, so the case set is identical and the
# oracle is not re-run). Results go to new tags; v0.2 result directories are never touched.
#
#   MODEL=/models/Qwen3-14B-FP8 experiments/phase5/run_p5.sh            # all three runs
#   MODEL=... RUNS="repro" experiments/phase5/run_p5.sh                 # just the environment check
#
#   repro  p5-repro-real-qwen3-14b : v0.2 behaviour (--audit-n 0 --no-stabilize) on `real`;
#                                    must match v0.2's 92% F1 within its CI
#   real   p5-real-qwen3-14b       : Phase 5 engine (defaults), real traces
#   gen    p5-gen-qwen3-14b        : Phase 5 engine (defaults), core + generated cases
#   real5b p5b-real-qwen3-14b      : real again with the 5.2b fix and two-stage audit (not default)
#   gen5b  p5b-gen-qwen3-14b       : gen again with the same fixes (not default)
#   real5c / gen5c  p5c-*          : the 5.5 engine (not default)
#   real5d / gen5d  p5d-*          : with the 5.6 audit (not default; RUNS="real5d gen5d")
#   real64 / gen64  p64-*          : with E forced by tool_choice (6.4, the engine default)
set -euo pipefail
: "${MODEL:?path or HF id of Qwen3-14B-FP8}"
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
P3=$REPO/experiments/phase3
RES=$P3/results
RUNS=${RUNS:-"repro real gen"}
export NAME=Qwen3-14B
export EXTRA_BODY='{"chat_template_kwargs": {"enable_thinking": false}, "temperature": 0.7, "top_p": 0.8, "top_k": 20}'
export SEEDS=${SEEDS:-"0 1 2"}

run() {  # tag suite v0.2-oracle-tag methods blame-args
  local tag=$1 suite=$2 src=$3 methods=$4 blame=$5
  mkdir -p "$RES/$tag"
  [ -f "$RES/$tag/oracle_all.json" ] || cp "$RES/$src/oracle_all.json" "$RES/$tag/oracle_all.json"
  TAG=$tag SUITE=$suite METHODS=$methods BLAME_ARGS=$blame "$P3/run_model.sh"
  export SKIP_SERVE=1  # the server from the first run stays up
}

for r in $RUNS; do
  case $r in
    repro) run p5-repro-real-qwen3-14b real real-qwen3-14b "ctxblame" "--audit-n 0 --no-stabilize" ;;
    real)  run p5-real-qwen3-14b real real-qwen3-14b "ctxblame ctxblame_uncond" "" ;;
    gen)   run p5-gen-qwen3-14b all qwen3-14b-fp8 "ctxblame ctxblame_uncond" "" ;;
    # v0.3 fixes found by the runs above: 5.2b (search after a stabilizer) and the two-stage audit
    real5b) run p5b-real-qwen3-14b real real-qwen3-14b "ctxblame" "" ;;
    gen5b)  run p5b-gen-qwen3-14b all qwen3-14b-fp8 "ctxblame" "" ;;
    # final engine: stratified probe that skips E-collapsing tiers after a stabilizer
    real5c) run p5c-real-qwen3-14b real real-qwen3-14b "ctxblame" "" ;;
    gen5c)  run p5c-gen-qwen3-14b all qwen3-14b-fp8 "ctxblame" "" ;;
    # 5.6: coupled bundle members kept, every bundle re-audited on new replays
    real5d) run p5d-real-qwen3-14b real real-qwen3-14b "ctxblame" "" ;;
    gen5d)  run p5d-gen-qwen3-14b all qwen3-14b-fp8 "ctxblame" "" ;;
    # 6.4: preconditions tested for also steering the choice with E forced (tool_choice)
    real64) run p64-real-qwen3-14b real real-qwen3-14b "ctxblame" "" ;;
    gen64)  run p64-gen-qwen3-14b all qwen3-14b-fp8 "ctxblame" "" ;;
    *) echo "unknown run $r"; exit 2 ;;
  esac
done
