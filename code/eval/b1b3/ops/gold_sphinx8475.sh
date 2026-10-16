#!/bin/bash
cd work/p5/b1b3
python -m swebench.harness.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified \
  --predictions_path gold --instance_ids sphinx-doc__sphinx-8475 --run_id b1b3_gold_sphinx8475 \
  --max_workers 1 --cache_level instance > gold_sphinx8475.log 2>&1
echo "GOLD_DONE rc=$?" >> gold_sphinx8475.log
