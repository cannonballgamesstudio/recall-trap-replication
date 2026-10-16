#!/bin/bash
# usage: grade_one.sh PREDS_BASENAME RUN_ID   (preds under data/post-cutoff-branchA)
cd data/post-cutoff-branchA/grade || exit 1
docker container prune -f >> grade.log 2>&1
echo "GRADE_START $2 $(date +%H:%M:%S)" >> grade.log
<home>/srb/bin/python -m swebench.harness.run_evaluation \
  --dataset_name nebius/SWE-rebench-leaderboard --split test \
  --predictions_path data/post-cutoff-branchA/$1 \
  --run_id $2 --max_workers 4 --cache_level instance \
  --namespace swerebench >> grade_$2.log 2>&1
echo "GRADE_EXIT $2 rc=$? $(date +%H:%M:%S)" >> grade.log
