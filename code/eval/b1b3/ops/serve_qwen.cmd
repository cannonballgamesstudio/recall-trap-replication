@echo off
REM LOCAL-B1B3 reference serving for Qwen3-Coder-30B-A3B (addendum S5).
set D=work/p5/b1b3
start "b1b3_qwen" /b <LLAMA_DIR>\llama-server.exe -m <LLAMA_DIR>\Qwen3-Coder-30B-A3B-Instruct-UD-Q5_K_XL.gguf -c 16384 --parallel 2 --jinja -ngl 99 --host 127.0.0.1 --port 8090 > %D%\qwen_8090.log 2>&1
python %D%\wait_props.py >> %D%\serve.log 2>&1
echo SERVE_DONE >> %D%\serve.log
