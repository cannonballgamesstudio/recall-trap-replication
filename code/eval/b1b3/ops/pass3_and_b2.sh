#!/bin/bash
# Third consecutive pass for the four B1 arm-seeds with a sphinx-8475 timeout (addendum §6), in parallel,
# alongside B2 grading in the same Docker session.
PY=python
D=work/p5
cd $D
for as in ON_s00 OFF_s02 T_s00 T_s01; do
  "$PY" -m swebench.harness.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path preds_local_b1b3q30_${as}.jsonl --run_id b1b3_${as} --max_workers 1 --cache_level instance \
    > b1b3/eval_b1b3_${as}_p3.log 2>&1 &
done
bash $D/b1b3/grade_b1b3.sh TM_s00 TM_s01 TM_s02
wait
echo "PASS3_DONE $(date +%F' '%H:%M:%S)" >> $D/b1b3/grade.out
