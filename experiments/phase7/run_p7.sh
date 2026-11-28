#!/usr/bin/env bash
# Phase 7.1 on a GPU box, one model: raw data for the baselines (baselines.py) on the
# Phase 6 suite, then the estimates (estimate.py) and the scores next to ctxblame's 6.4
# run on the same truth (score7.py). Results go to experiments/phase7/results/<tag>/.
#
#   MODEL=/root/autodl-tmp/models/Qwen3-14B-FP8 NAME=Qwen3-14B TAG=p71pilot-qwen3-14b LIMIT=10 \
#     FROM=qwen3-14b experiments/phase7/run_p7.sh                # pilot: 10 cases, throughput
#   MODEL=... NAME=Qwen3-14B TAG=p71-qwen3-14b FROM=qwen3-14b experiments/phase7/run_p7.sh
#
# FROM: the Phase 6 model tag. Truth = results/<FROM>/tables with the forced tables of
# results/p64c-<FROM>/forced; ctxblame = results/p64c-<FROM>/seed*/benchmark.json.
# Optional: PY, SEEDS (default "0"), DESIGNS (default: baselines.py's), M (rows per design,
# default 512), CC (ContextCite prefills, default 512), LIMIT, CONC (requests in flight,
# default 128), PARALLEL (cases at once, default 8), EXTRA_BODY, TOOL_PARSER, SERVE_ARGS,
# SKIP_SERVE=1, PORT (default 8000) and CUDA_VISIBLE_DEVICES, as run_p6.sh.
set -euo pipefail
: "${TAG:?}" "${MODEL:?}" "${NAME:?}" "${FROM:?}"
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
PY=${PY:-python}
SEEDS=${SEEDS-"0"}
LIMIT=${LIMIT:-0}
EXTRA_BODY=${EXTRA_BODY:-'{"chat_template_kwargs": {"enable_thinking": false}, "temperature": 0.7, "top_p": 0.8, "top_k": 20}'}
OUT=$REPO/experiments/phase7/results/$TAG
P6=$REPO/experiments/phase6/results
TABLES=$P6/$FROM/tables
FORCED=$P6/p64c-$FROM/forced
LOGS=${LOGS:-$REPO/../logs}
PORT=${PORT:-8000}
GPU_IDX=${CUDA_VISIBLE_DEVICES:-0}; GPU_IDX=${GPU_IDX%%,*}
SERVER="[v]llm serve .* --port $PORT( |$)"
[ -d "$TABLES" ] || { echo "no tables at $TABLES"; exit 1; }
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
DARGS=(${DESIGNS:+--designs $DESIGNS})
for s in $SEEDS; do
  [ -f "$OUT/seed$s/benchmark.json" ] && continue
  t0=$(date +%s)
  "$PY" experiments/phase7/baselines.py "${COMMON[@]}" --tables "$TABLES" --limit "$LIMIT" --seed "$s" \
    -m "${M:-512}" --cc-masks "${CC:-512}" "${DARGS[@]}" --concurrency "${CONC:-128}" \
    --parallel-cases "${PARALLEL:-8}" --budget 1 --ledger "$LOGS/ledger_${TAG}_$s.jsonl" --out "$OUT/seed$s" \
    > "$LOGS/base_${TAG}_$s.log" 2>&1
  echo "[$TAG] seed $s raw data done ($(( $(date +%s) - t0 ))s)"
  "$PY" experiments/phase7/estimate.py "$OUT/seed$s" >> "$LOGS/base_${TAG}_$s.log" 2>&1
  echo "[$TAG] seed $s estimated"
done
CTX=("$P6/p64c-$FROM"/seed*/benchmark.json)
"$PY" experiments/phase7/score7.py "$OUT"/seed* --tables "$TABLES" --forced "$FORCED" --ctxblame "${CTX[@]}" \
  --out "$OUT/score.json" > "$OUT/summary.md"
echo "[$TAG] summary: $OUT/summary.md"
