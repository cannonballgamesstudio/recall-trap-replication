#!/bin/bash
# Third consecutive pass (addendum §6 / SPHINX8475 ruling §5.1) for TM arm-seeds given as args.
PY=python
D=work/p5
cd $D
for as in "$@"; do
  "$PY" -m swebench.harness.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path preds_local_b1b3q30_${as}.jsonl --run_id b1b3_${as} --max_workers 1 --cache_level instance \
    > b1b3/eval_b1b3_${as}_p3.log 2>&1 &
done
wait
echo "PASS3_TM_DONE $* $(date +%F' '%H:%M:%S)" >> $D/b1b3/grade.out
