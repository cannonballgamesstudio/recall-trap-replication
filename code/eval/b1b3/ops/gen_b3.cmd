@echo off
set D=work/p5/b1b3
set LOG_RESPONSE_TEXT=1
set PYTHONUNBUFFERED=1
cd /d code/eval
python local_dedup_ab.py --arm P --packs-file b1b3_packs_b2.json --ids-file work/p5\b1b3_ids_T.txt --n-samples 1 --temperature 0.2 --top-p %1 --per-sample-seed --nonce --max-tokens 6000 --max-attempts 3 --timeout 900 --concurrency 2 --model-tag b1b3q30 >> %D%\gen_P.log 2>&1
echo GEN_B3_DONE >> %D%\gen.log
