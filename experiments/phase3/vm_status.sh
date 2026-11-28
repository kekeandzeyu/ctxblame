#!/usr/bin/env bash
# Health and progress of benchmark runs on a GPU box. Run it ON the box (over ssh):
#
#   experiments/phase3/vm_status.sh            # all tags
#   experiments/phase3/vm_status.sh p5-        # tags starting with p5-
#   PORT=8001 experiments/phase3/vm_status.sh pilot-   # a second server, on another GPU
#
# Prints one status line (machine-readable) then details. Exit 0 = healthy or
# idle, 1 = something needs attention (driver died while seeds remain, vLLM down
# while a benchmark runs, errors in a benchmark or vLLM log). With a tag prefix, the
# benchmark check only counts that prefix's processes; a driver that wrote
# $LOGS/driver_<tag>.pid is checked by its pid, so two runs side by side are told apart.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
LOGS=${LOGS:-$REPO/../logs}
RES=$REPO/experiments/phase3/results
RES6=$REPO/experiments/phase6/results
P=${1:-}
PORT=${PORT:-8000}

up() { "$@" > /dev/null 2>&1 && echo up || echo DOWN; }
job=$(up pgrep -f "run_model.sh|run_p5.sh|run_p6.sh")
bench=$(up pgrep -f "(benchmark|oracle|tables)\.py.*results/$P")
vllm=$(up curl -sf -m 10 "http://127.0.0.1:$PORT/v1/models")
gpu=$(nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits 2>/dev/null | tr -d ' ' | paste -sd ';' -)  # per GPU
berr=$(cat "$LOGS"/bench_"$P"*.log "$LOGS"/oracle_"$P"*.log "$LOGS"/tables_"$P"*.log 2>/dev/null | grep -ciE "traceback|exception|error")
# a malformed tool call from the model is logged by vLLM's tool parser as an ERROR
# traceback but returned as text (HTTP 200, scored as "no tool call"): count apart
verr=$(cat "$LOGS"/vllm_"$P"*.log 2>/dev/null | grep -E "ERROR|Traceback" | grep -vc "tool_parser")
tperr=$(cat "$LOGS"/vllm_"$P"*.log 2>/dev/null | grep -c "Error in extracting tool call")
echo "job=$job bench=$bench vllm=$vllm gpu=${gpu:-none} benchErr=$berr vllmErr=$verr toolParseFail=$tperr"

echo "-- seeds finished (benchmark.json) / cases started per running log"
incomplete=0; dead=0
for d in "$RES"/"$P"*/ "$RES6"/"$P"*/; do
  [ -d "$d" ] || continue
  t=$(basename "$d"); done_=$(ls "$d"/seed*/benchmark.json 2>/dev/null | wc -l)
  # a tag this box started (it has a bench log here) but has not summarized
  if ls "$LOGS"/bench_"$t"_*.log "$LOGS"/tables_"$t".log > /dev/null 2>&1 && [ ! -f "$d/summary.md" ]; then
    pidf=$LOGS/driver_$t.pid
    if [ -f "$pidf" ]; then kill -0 "$(cat "$pidf")" 2> /dev/null || { dead=1; echo "driver of $t is gone"; }
    else incomplete=1; fi
  fi
  tabs=$(ls "$d"/tables/*.json 2>/dev/null | wc -l)
  printf "%-32s seeds_done=%s%s%s\n" "$t" "$done_" "$([ "$tabs" -gt 0 ] && echo " tables=$tabs")" \
    "$([ -f "$d/summary.md" ] && echo " summary")"
done
for f in "$LOGS"/bench_"$P"*.log; do
  [ -f "$f" ] && printf "%-40s cases_started=%s\n" "$(basename "$f")" "$(grep -c '^== ' "$f")"
done
for f in "$LOGS"/tables_"$P"*.log; do
  [ -f "$f" ] && printf "%-40s tables_done=%s errors=%s\n" "$(basename "$f")" "$(grep -c '^done ' "$f")" \
    "$(grep -c '^ERROR ' "$f")"
done
echo "-- driver log tails"
for f in "$LOGS"/p5.log "$LOGS"/p6.log "$LOGS"/run_*.log; do [ -f "$f" ] && { echo "[$f]"; tail -n 3 "$f"; }; done
[ "$berr$verr" != "00" ] && { echo "-- errors"; grep -iE "traceback|exception|error" "$LOGS"/bench_"$P"*.log "$LOGS"/oracle_"$P"*.log "$LOGS"/tables_"$P"*.log 2>/dev/null | tail -5; grep -E "ERROR|Traceback" "$LOGS"/vllm_"$P"*.log 2>/dev/null | grep -v tool_parser | tail -5; }

bad=0
if [ "$berr" -gt 0 ] || [ "$verr" -gt 0 ]; then bad=1; fi
if [ "$bench" = up ] && [ "$vllm" = DOWN ]; then bad=1; fi
if [ "$job" = DOWN ] && [ "$incomplete" = 1 ]; then bad=1; fi  # driver died mid-run
if [ "$dead" = 1 ]; then bad=1; fi  # this tag's driver died while another one runs
exit $bad
