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
#   real5b p5b-real-qwen3-14b      : real again with the 5.2b fix (not in the default RUNS)
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
    real5b) run p5b-real-qwen3-14b real real-qwen3-14b "ctxblame" "" ;;  # 5.2b fix (after a5f5461)
    *) echo "unknown run $r"; exit 2 ;;
  esac
done
