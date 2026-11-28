#!/usr/bin/env bash
# Serve a local model with vLLM for $0 ctxblame runs (prefix caching + tool calls).
#
#   experiments/phase3/serve_vllm.sh /path/to/Qwen3-8B [port] [served-name]
#
# GPU_UTIL (fraction of *total* GPU memory) defaults to what is free right now
# minus a margin, so it also works on a GPU shared with other processes. Pin a GPU
# with CUDA_VISIBLE_DEVICES; its free memory is the one read.
set -euo pipefail
MODEL=${1:?model path or HF id}
PORT=${2:-8000}
NAME=${3:-$(basename "$MODEL")}
VLLM=${VLLM:-vllm}
GPU_IDX=${CUDA_VISIBLE_DEVICES:-0}; GPU_IDX=${GPU_IDX%%,*}
if [ -z "${GPU_UTIL:-}" ]; then
  read -r free total < <(nvidia-smi -i "$GPU_IDX" --query-gpu=memory.free,memory.total --format=csv,noheader,nounits | head -1 | tr -d ,)
  GPU_UTIL=$(python3 -c "print(round(max(0.3, ($free - 2048) / $total), 2))" 2>/dev/null \
             || awk -v f="$free" -v t="$total" 'BEGIN{u=(f-2048)/t; if(u<0.3)u=0.3; printf "%.2f", u}')
fi
echo "serving $MODEL as $NAME on :$PORT (gpu-memory-utilization $GPU_UTIL)"
exec "$VLLM" serve "$MODEL" \
  --served-model-name "$NAME" \
  --host 127.0.0.1 --port "$PORT" \
  --enable-prefix-caching \
  --enable-prompt-tokens-details \
  --enable-auto-tool-choice --tool-call-parser "${TOOL_PARSER:-hermes}" \
  --max-model-len "${MAX_LEN:-32768}" \
  --gpu-memory-utilization "$GPU_UTIL" \
  ${EXTRA_ARGS:-}
