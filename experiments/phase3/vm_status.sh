#!/usr/bin/env bash
# Health and progress of benchmark runs on a GPU box. Run it ON the box (over ssh):
#
#   experiments/phase3/vm_status.sh            # all tags
#   experiments/phase3/vm_status.sh p5-        # tags starting with p5-
#
# Prints one status line (machine-readable) then details. Exit 0 = healthy or
# idle, 1 = something needs attention (driver died while seeds remain, vLLM down
# while a benchmark runs, errors in a benchmark or vLLM log).
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
LOGS=${LOGS:-$REPO/../logs}
RES=$REPO/experiments/phase3/results
P=${1:-}

up() { "$@" > /dev/null 2>&1 && echo up || echo DOWN; }
job=$(up pgrep -f "run_model.sh|run_p5.sh")
bench=$(up pgrep -f "benchmark.py|oracle.py")
vllm=$(up curl -sf -m 10 http://127.0.0.1:8000/v1/models)
gpu=$(nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d ' ')
berr=$(cat "$LOGS"/bench_"$P"*.log "$LOGS"/oracle_"$P"*.log 2>/dev/null | grep -ciE "traceback|exception|error")
verr=$(cat "$LOGS"/vllm_"$P"*.log 2>/dev/null | grep -cE "ERROR|Traceback")
echo "job=$job bench=$bench vllm=$vllm gpu=${gpu:-none} benchErr=$berr vllmErr=$verr"

echo "-- seeds finished (benchmark.json) / cases started per running log"
incomplete=0
for d in "$RES"/"$P"*/; do
  [ -d "$d" ] || continue
  t=$(basename "$d"); done_=$(ls "$d"/seed*/benchmark.json 2>/dev/null | wc -l)
  # a tag this box started (it has a bench log here) but has not summarized
  ls "$LOGS"/bench_"$t"_*.log > /dev/null 2>&1 && [ ! -f "$d/summary.md" ] && incomplete=1
  printf "%-32s seeds_done=%s%s\n" "$t" "$done_" "$([ -f "$d/summary.md" ] && echo " summary")"
done
for f in "$LOGS"/bench_"$P"*.log; do
  [ -f "$f" ] && printf "%-40s cases_started=%s\n" "$(basename "$f")" "$(grep -c '^== ' "$f")"
done
echo "-- driver log tails"
for f in "$LOGS"/p5.log "$LOGS"/run_*.log; do [ -f "$f" ] && { echo "[$f]"; tail -n 3 "$f"; }; done
[ "$berr$verr" != "00" ] && { echo "-- errors"; grep -iE "traceback|exception|error" "$LOGS"/bench_"$P"*.log "$LOGS"/oracle_"$P"*.log 2>/dev/null | tail -5; grep -E "ERROR|Traceback" "$LOGS"/vllm_"$P"*.log 2>/dev/null | tail -5; }

bad=0
if [ "$berr" -gt 0 ] || [ "$verr" -gt 0 ]; then bad=1; fi
if [ "$bench" = up ] && [ "$vllm" = DOWN ]; then bad=1; fi
if [ "$job" = DOWN ] && [ "$incomplete" = 1 ]; then bad=1; fi  # driver died mid-run
exit $bad
