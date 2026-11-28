#!/usr/bin/env bash
# One model, end to end: serve it with vLLM, validate the cases (oracle.py), run
# the benchmark for each seed, summarize. Results go to experiments/phase3/results/<tag>/.
#
#   TAG=qwen3-8b MODEL=/models/Qwen3-8B NAME=Qwen3-8B \
#   EXTRA_BODY='{"chat_template_kwargs": {"enable_thinking": false}, "temperature": 0.7, "top_p": 0.8, "top_k": 20}' \
#   SEEDS="0 1 2" experiments/phase3/run_model.sh
#
# Optional: PY (python with ctxblame + vllm), VLLM, TOOL_PARSER (default hermes),
# SERVE_ARGS (extra vllm serve flags, e.g. "--reasoning-parser qwen3"),
# MAX_TOKENS (default 1024), METHODS, PARALLEL (default 8), CONC (default 16),
# ORACLE_N (default 20), SKIP_SERVE=1 to reuse a running server on :8000,
# SUITE (default all; e.g. real, gen-long), BLAME_ARGS (extra ctxblame flags,
# e.g. "--strict-restore --member-controls 2").
set -euo pipefail
: "${TAG:?}" "${MODEL:?}" "${NAME:?}" "${EXTRA_BODY:?}"
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
PY=${PY:-python}
SEEDS=${SEEDS:-"0 1 2"}
MAX_TOKENS=${MAX_TOKENS:-1024}
METHODS=${METHODS:-"ctxblame ctxblame_uncond loo self_explain contextcite"}
SUITE=${SUITE:-all}
OUT=$REPO/experiments/phase3/results/$TAG
LOGS=${LOGS:-$REPO/../logs}
mkdir -p "$OUT" "$LOGS"
cd "$REPO"

if [ -z "${SKIP_SERVE:-}" ]; then
  pkill -f "[v]llm serve" || true
  # wait for the old server's memory to come back (containers may not list GPU processes)
  for _ in $(seq 120); do
    free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1 | tr -d ' ')
    [ "$free" -ge "${MIN_FREE_MB:-30000}" ] && break
    sleep 5
  done
  EXTRA_ARGS="${SERVE_ARGS:-}" nohup "$HERE/serve_vllm.sh" "$MODEL" 8000 "$NAME" > "$LOGS/vllm_$TAG.log" 2>&1 &
  sleep 20  # let serve_vllm.sh exec into vllm before checking it is alive
  until curl -sf http://127.0.0.1:8000/v1/models > /dev/null; do
    if ! pgrep -f "[v]llm serve" > /dev/null; then echo "vllm died; see $LOGS/vllm_$TAG.log"; exit 1; fi
    sleep 5
  done
fi
echo "[$TAG] server ready"

COMMON=(--model "$NAME" --free --no-thinking-param --extra-body "$EXTRA_BODY")
if [ ! -f "$OUT/oracle_all.json" ]; then
  "$PY" experiments/phase3/oracle.py --suite "$SUITE" "${COMMON[@]}" -n "${ORACLE_N:-20}" --max-tokens "$MAX_TOKENS" \
    --parallel-cases 8 --out "$OUT/oracle_all.json" > "$LOGS/oracle_$TAG.log" 2>&1
fi
tail -n 2 "$LOGS/oracle_$TAG.log" 2>/dev/null || true  # absent when oracle_all.json was supplied

for s in $SEEDS; do
  [ -f "$OUT/seed$s/benchmark.json" ] && continue
  # shellcheck disable=SC2086
  "$PY" experiments/phase3/benchmark.py --suite "$SUITE" --valid-from "$OUT/oracle_all.json" "${COMMON[@]}" \
    --max-tokens "$MAX_TOKENS" --methods $METHODS --parallel-cases "${PARALLEL:-8}" --concurrency "${CONC:-16}" \
    --seed "$s" --blame-args="${BLAME_ARGS:-}" --budget 1 --ledger "$LOGS/ledger_${TAG}_$s.jsonl" --out-dir "$OUT/seed$s" \
    > "$LOGS/bench_${TAG}_$s.log" 2>&1
  echo "[$TAG] seed $s done"
done
"$PY" experiments/phase3/analyze.py "$OUT" > /dev/null && echo "[$TAG] summary: $OUT/summary.md"
