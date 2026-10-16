#!/bin/bash
# TRIMMED-BREADTH Arm T (473) + T' (27) on gpt-5.6-sol, and CONTAMINATION Tier-1 P2 (gpt-5.6-sol).
# Same official harness command as the headline gpt-5.6-sol grading (grade_local_gpt56sol_dedupON.sh):
# princeton-nlp/SWE-bench_Verified, --max_workers 4 --cache_level instance. Sequential (no overlap).
PY=python
run () {
  local dir=$1 preds=$2 rid=$3
  cd "$dir" || exit 9
  echo "[$(date +%H:%M:%S)] START $rid  (preds=$preds)"
  "$PY" -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path "$preds" --run_id "$rid" \
    --max_workers 4 --cache_level instance \
    > "eval_${rid}.log" 2>&1
  echo "[$(date +%H:%M:%S)] DONE  $rid  exit=$?"
}
run work/p5 preds_local_gpt56sol_Tprime.jsonl trimT_gpt56sol_Tprime
run work/p5 preds_local_gpt56sol_T.jsonl      trimT_gpt56sol_T
run data/memorization-branchB preds_P2_gpt56sol.jsonl       contamP2_gpt56sol
echo "TRIMT_GPT_P2_GRADE_COMPLETE $(date +%H:%M:%S)"
