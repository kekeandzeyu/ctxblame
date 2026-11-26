#!/usr/bin/env bash
# Record N real coding-agent runs (experiments/phase1/agent.py) against a local
# vLLM server through the ctxblame proxy. Each run fixes the planted bug in a
# fresh copy of this repository and writes one trace.
#
#   N=6 TEST_CMD="python -m pytest -q -x --tb=line" experiments/phase4/record.sh
#
# Env: N (runs, default 6), TEST_CMD (the convention AGENTS.md and the bash
# tool's example prescribe), MODEL (served name, default Qwen3-8B), UPSTREAM
# (default http://127.0.0.1:8000/v1), EXTRA_BODY (JSON merged into requests),
# OUT (trace dir, default experiments/phase4/traces), PY (python with ctxblame),
# START (first run number, default 1), AGENT_ARGS (extra agent.py flags, e.g. --manual).
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
PY=${PY:-python}
N=${N:-6}
MODEL=${MODEL:-Qwen3-8B}
UPSTREAM=${UPSTREAM:-http://127.0.0.1:8000/v1}
TEST_CMD=${TEST_CMD:-"python -m pytest -q -x --tb=line"}
EXTRA_BODY=${EXTRA_BODY:-'{"chat_template_kwargs": {"enable_thinking": false}, "temperature": 0.7, "top_p": 0.8, "top_k": 20}'}
OUT=${OUT:-$HERE/traces}
mkdir -p "$OUT"
cd "$REPO"

run_one() {
  local i=$1 port=$((8700 + $1))
  local trace="$OUT/run$i.jsonl" ws="/tmp/ctxblame-ws-$i"
  rm -f "$trace"
  "$PY" -m ctxblame.cli record --upstream "$UPSTREAM" --port "$port" --trace "$trace" > "$OUT/proxy$i.log" 2>&1 &
  local proxy=$!
  sleep 3
  "$PY" experiments/phase1/agent.py --format openai --base-url "http://127.0.0.1:$port" --model "$MODEL" \
    --no-thinking --max-tokens 2048 --workspace "$ws" --max-steps 30 \
    --test-cmd "$TEST_CMD" --extra-body "$EXTRA_BODY" ${AGENT_ARGS:-} > "$OUT/agent$i.log" 2>&1
  echo "run $i: exit $? ($(grep -c '^\[' "$OUT/agent$i.log") steps) $(tail -n 1 "$OUT/agent$i.log" | cut -c1-120)"
  kill "$proxy" 2>/dev/null
}

for i in $(seq "${START:-1}" $(( ${START:-1} + N - 1 ))); do run_one "$i" & done
wait
