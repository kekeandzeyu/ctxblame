#!/usr/bin/env bash
# Phase 6 on a GPU box, one model: coalition tables (the truth), then ctxblame on
# the same cases, then the score. Results go to experiments/phase6/results/<tag>/.
#
#   MODEL=/models/Qwen3-14B-FP8 NAME=Qwen3-14B TAG=pilot-qwen3-14b LIMIT=10 experiments/phase6/run_p6.sh
#   MODEL=... NAME=... TAG=qwen3-14b CASES=250 experiments/phase6/run_p6.sh
#
# Optional: PY, VLLM, TOOL_PARSER, SERVE_ARGS, EXTRA_BODY (default: Qwen3 non-thinking
# sampling), N (replays per cell, default 50), CASES (suite size, default 250),
# LIMIT (first N cases only, the 6.2 pilot), SEEDS (ctxblame seeds, default "0 1 2";
# empty = tables only), CONC (tables: requests in flight, default 128), SKIP_SERVE=1,
# PORT (default 8000) and CUDA_VISIBLE_DEVICES to run one server per GPU side by side.
#
# 6.4: FORCED_FROM=<tag of finished tables> replays those tables' gated cases with E forced
# by tool_choice (<tag>/forced/), runs ctxblame (forcing on by default) on all of FORCED_FROM's
# cases, and scores it on the truth recomputed with E forced. Two comparison summaries are
# written next to summary.md: the FORCED_FROM engine on the forced truth, and this engine on
# the unforced truth, so engine and truth changes can be told apart.
#   FORCED_FROM=qwen3-14b MODEL=... NAME=Qwen3-14B TAG=p64-qwen3-14b experiments/phase6/run_p6.sh
set -euo pipefail
: "${TAG:?}" "${MODEL:?}" "${NAME:?}"
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
PY=${PY:-python}
N=${N:-50}
CASES=${CASES:-250}
LIMIT=${LIMIT:-0}
SEEDS=${SEEDS-"0 1 2"}
EXTRA_BODY=${EXTRA_BODY:-'{"chat_template_kwargs": {"enable_thinking": false}, "temperature": 0.7, "top_p": 0.8, "top_k": 20}'}
OUT=$REPO/experiments/phase6/results/$TAG
LOGS=${LOGS:-$REPO/../logs}
PORT=${PORT:-8000}
GPU_IDX=${CUDA_VISIBLE_DEVICES:-0}; GPU_IDX=${GPU_IDX%%,*}
SERVER="[v]llm serve .* --port $PORT( |$)"
mkdir -p "$OUT" "$LOGS"
cd "$REPO"

echo $$ > "$LOGS/driver_$TAG.pid"  # vm_status.sh: is this tag's driver alive

if [ -z "${SKIP_SERVE:-}" ]; then
  pkill -f "$SERVER" || true  # only the server on our port
  for _ in $(seq 120); do
    free=$(nvidia-smi -i "$GPU_IDX" --query-gpu=memory.free --format=csv,noheader,nounits | tr -d ' ')
    [ "$free" -ge "${MIN_FREE_MB:-30000}" ] && break
    sleep 5
  done
  EXTRA_ARGS="${SERVE_ARGS:-}" nohup "$REPO/experiments/phase3/serve_vllm.sh" "$MODEL" "$PORT" "$NAME" \
    > "$LOGS/vllm_$TAG.log" 2>&1 &
  sleep 20
  until curl -sf "http://127.0.0.1:$PORT/v1/models" > /dev/null; do
    if ! pgrep -f "$SERVER" > /dev/null; then echo "vllm died; see $LOGS/vllm_$TAG.log"; exit 1; fi
    sleep 5
  done
fi
echo "[$TAG] server ready"

COMMON=(--base-url "http://127.0.0.1:$PORT/v1" --model "$NAME" --free --no-thinking-param --extra-body "$EXTRA_BODY")
FORCED_FROM=${FORCED_FROM:-}
if [ -n "$FORCED_FROM" ]; then
  TABLES=$REPO/experiments/phase6/results/$FORCED_FROM/tables
  [ -d "$TABLES" ] || { echo "no tables at $TABLES"; exit 1; }
  TARGS=(--forced --base-tables "$TABLES")
  FORCED_DIR=$OUT/forced
else
  TABLES=$OUT/tables
  TARGS=()
  FORCED_DIR=
fi
t0=$(date +%s)
"$PY" experiments/phase6/tables.py "${COMMON[@]}" -n "$N" --cases "$CASES" --limit "$LIMIT" \
  --concurrency "${CONC:-128}" --budget 1 --ledger "$LOGS/ledger_${TAG}_tables.jsonl" --out "$OUT" "${TARGS[@]}" \
  > "$LOGS/tables_$TAG.log" 2>&1
wall=$(( $(date +%s) - t0 ))
tail -n 1 "$LOGS/tables_$TAG.log"
echo "[$TAG] tables done (${wall}s)"

# ctxblame (defaults) on exactly the tabled cases, no oracle filter
mapfile -t names < <(ls "$TABLES" | sed 's/\.json$//; s#__#/#g')
for s in $SEEDS; do
  [ -f "$OUT/seed$s/benchmark.json" ] && continue
  "$PY" experiments/phase3/benchmark.py --suite phase6 --gen-n "$CASES" --only "${names[@]}" "${COMMON[@]}" \
    --methods ctxblame --parallel-cases "${PARALLEL:-8}" --concurrency "${BCONC:-16}" --seed "$s" \
    --budget 1 --ledger "$LOGS/ledger_${TAG}_$s.jsonl" --out-dir "$OUT/seed$s" > "$LOGS/bench_${TAG}_$s.log" 2>&1
  echo "[$TAG] seed $s done"
done
FARGS=(${FORCED_DIR:+--forced "$FORCED_DIR"})
if [ -n "$SEEDS" ]; then
  if [ -n "$FORCED_FROM" ]; then  # comparisons first: summary.md is the run's milestone
    "$PY" experiments/phase6/score6.py "$TABLES" "$REPO/experiments/phase6/results/$FORCED_FROM"/seed*/benchmark.json \
      "${FARGS[@]}" --out "$OUT/score_${FORCED_FROM}_engine.json" > "$OUT/summary_${FORCED_FROM}_engine.md"
    "$PY" experiments/phase6/score6.py "$TABLES" "$OUT"/seed*/benchmark.json \
      --out "$OUT/score_unforced_truth.json" > "$OUT/summary_unforced_truth.md"
  fi
  "$PY" experiments/phase6/score6.py "$TABLES" "$OUT"/seed*/benchmark.json "${FARGS[@]}" --out "$OUT/score.json" \
    > "$OUT/summary.md"
else  # tables only (the 6.2 pilot): regimes, throughput and the full suite's estimated time
  "$PY" experiments/phase6/score6.py "${FORCED_DIR:-$OUT/tables}" --wall-seconds "$wall" --suite "$CASES" \
    --out "$OUT/tables_summary.json" > "$OUT/summary.md"
fi
echo "[$TAG] summary: $OUT/summary.md"
