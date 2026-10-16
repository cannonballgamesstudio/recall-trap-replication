@echo off
wsl -e bash data/post-cutoff-branchA/grade/grade_one.sh preds_local_gpt56sol_post_dedupOFF.jsonl post_gpt56sol_post_dedupOFF
wsl -u root -e sh -c "sync; echo 3 > /proc/sys/vm/drop_caches"
echo REGRADE_OFF_DONE >> E:val\swe-rebench-post\grade\grade.log
