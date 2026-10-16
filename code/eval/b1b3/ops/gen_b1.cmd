@echo off
REM LOCAL-B1B3 B1 generation: ON, OFF (all ids), T (subset-passing ids); 3 seeds each.
set D=work/p5/b1b3
set LOG_RESPONSE_TEXT=1
set PYTHONUNBUFFERED=1
cd /d code/eval
for %%A in (ON OFF) do python local_dedup_ab.py --arm %%A --packs-file b1b3_packs.json --ids-file work/p5\b1b3_ids_all.txt --n-samples 3 --temperature 0.2 --top-p %1 --per-sample-seed --nonce --max-tokens 6000 --max-attempts 3 --timeout 900 --concurrency 2 --model-tag b1b3q30 >> %D%\gen_%%A.log 2>&1
python local_dedup_ab.py --arm T --packs-file b1b3_packs.json --ids-file work/p5\b1b3_ids_T.txt --n-samples 3 --temperature 0.2 --top-p %1 --per-sample-seed --nonce --max-tokens 6000 --max-attempts 3 --timeout 900 --concurrency 2 --model-tag b1b3q30 >> %D%\gen_T.log 2>&1
echo GEN_B1_DONE >> %D%\gen.log
