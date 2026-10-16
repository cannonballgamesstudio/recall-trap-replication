#!/bin/bash
# Branch A gold gate (pre-reg A.4): gold patch of all 108 post-cutoff instances in their SWE-rebench images.
cd data/post-cutoff-branchA/gold || exit 1
<home>/srb/bin/python -m swebench.harness.run_evaluation \
  --dataset_name nebius/SWE-rebench-leaderboard --split test \
  --predictions_path gold_preds_post.jsonl \
  --run_id rebench_post_gold --max_workers 4 --cache_level instance \
  --namespace swerebench >> gold_post.log 2>&1
echo "GOLDPOST_EXIT rc=$? $(date +%H:%M:%S)" >> gold_post.log
