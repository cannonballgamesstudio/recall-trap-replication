#!/bin/bash
cd data/memorization-branchB || exit 1
docker container prune -f > /dev/null 2>&1
echo "P2GRADE_START $(date +%H:%M:%S)" >> local_run/grade_p2.status
python -m swebench.harness.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified \
  --predictions_path preds_P2_qwen3coder30b_local.jsonl --run_id contamP2_qwen3coder30b_local \
  --max_workers 4 --cache_level instance >> eval_contamP2_qwen3coder30b_local.log 2>&1
echo "P2GRADE_EXIT rc=$? $(date +%H:%M:%S)" >> local_run/grade_p2.status
