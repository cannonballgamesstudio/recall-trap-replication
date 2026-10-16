@echo off
for %%A in (gpt56sol_post_dedupON gpt56sol_post_dedupOFF gpt56sol_post_s2_dedupON gpt56sol_post_s2_dedupOFF qwen3coder30b_post_dedupON qwen3coder30b_post_dedupOFF) do (
  wsl -u root -e sh -c "sync; echo 3 > /proc/sys/vm/drop_caches"
  wsl -e bash data/post-cutoff-branchA/grade/grade_one.sh preds_local_%%A.jsonl post_%%A
)
wsl -u root -e sh -c "sync; echo 3 > /proc/sys/vm/drop_caches"
echo ALLGRADED >> data/post-cutoff-branchA\grade\grade.log
