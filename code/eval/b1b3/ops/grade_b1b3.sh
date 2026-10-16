#!/bin/bash
# LOCAL-B1B3 grading: one Docker session for the arm-seeds given as args (e.g. ON_s00 OFF_s01 ...).
# Authenticated pulls (verified by caller). Retry passes until error_instances==0 (max 6; stops early
# only if a pass makes no progress -> caller inspects; never scored).
PY=python
D=work/p5
LOG=$D/b1b3/grade.out
errs(){ python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['error_instances'])" "$1" 2>/dev/null || echo 999; }
cd $D || exit 9
for as in "$@"; do
  preds=preds_local_b1b3q30_${as}.jsonl; rid=b1b3_${as}; report=local_b1b3q30_${as}.${rid}.json; prev=99999
  for pass in 1 2 3 4 5 6; do
    echo "[$(date +%F' '%H:%M:%S)] $rid pass $pass" >> $LOG
    "$PY" -m swebench.harness.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified \
      --predictions_path "$preds" --run_id "$rid" --max_workers 6 --cache_level instance \
      > "b1b3/eval_${rid}_p${pass}.log" 2>&1
    docker container prune -f >/dev/null 2>&1
    e=$(errs "$report"); echo "[$(date +%F' '%H:%M:%S)] $rid pass $pass errors=$e" >> $LOG
    [ "$e" = "0" ] && break; [ "$e" -ge "$prev" ] && { echo "NO_PROGRESS $rid errors=$e" >> $LOG; break; }; prev=$e
  done
done
echo "GRADE_BATCH_COMPLETE $* $(date +%F' '%H:%M:%S)" >> $LOG
