#!/bin/bash
# TRIMMED-BREADTH-PREREG Arm T (473) + T' (27), Qwen3-Coder-30B. Same harness command as the
# qwen30b_{ON,OFF}_rg reference grading (grade_apiside_4arm.sh): princeton-nlp/SWE-bench_Verified,
# --max_workers 8 --cache_level instance --timeout 1800.
cd work/p5
run () {
  local preds=$1 rid=$2
  docker ps -aq --filter "name=${rid}" 2>/dev/null | xargs -r docker rm -f >/dev/null 2>&1 || true
  echo "[$(date +%H:%M:%S)] START $rid  (preds=$preds)"
  python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path "$preds" --run_id "$rid" \
    --max_workers 8 --cache_level instance --timeout 1800 \
    > "eval_${rid}.log" 2>&1
  echo "[$(date +%H:%M:%S)] DONE  $rid  exit=$?"
}
run preds_local_qwen3coder30b_Tprime.jsonl trimT_qwen30b_Tprime
run preds_local_qwen3coder30b_T.jsonl      trimT_qwen30b_T
echo "TRIMT_GRADE_COMPLETE $(date +%H:%M:%S)"
