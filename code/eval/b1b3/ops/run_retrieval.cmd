@echo off
REM LOCAL-B1B3 addendum: embedder (:8082, -ngl 99) + pinned retrievald (:8083) + prefetch, then stop both.
set D=work/p5/b1b3
set PYTHONUNBUFFERED=1
echo [%date% %time%] start >> %D%\retrieval.log
start "b1b3_embed" /b <LLAMA_DIR>\llama-server.exe -m <LLAMA_DIR>\Qwen3-Embedding-8B-Q8_0.gguf --embeddings --host 127.0.0.1 --port 8082 -ngl 99 -c 8192 > %D%\embed_8082.log 2>&1
set PYTHONPATH=code/retrieval
set RETRIEVALD_BACKEND=fusion
set RETRIEVALD_REGISTRY_DB=<EVAL_ROOT>\registry.db
set RETRIEVALD_EMBED_MODEL=openai:Qwen/Qwen3-Embedding-8B
set RETRIEVALD_DIMS=4096
set OPENAI_BASE_URL=http://127.0.0.1:8082
set OPENAI_API_KEY=sk-noauth
set RETRIEVALD_DEFAULT_IDENTITY=local
set RETRIEVALD_QUERY_DEDUP_FILE=
cd /d code/retrieval
start "b1b3_retrievald" /b python -m uvicorn ragfusion.retrievald.server:build_app --factory --host 127.0.0.1 --port 8083 > %D%\retrievald_8083.log 2>&1
python code/eval/b1b3/b1b3_waitup.py >> %D%\retrieval.log 2>&1
if errorlevel 1 goto stop
cd /d <repo>
python code/eval/b1b3/b1b3_prefetch.py >> %D%\retrieval.log 2>&1
echo PREFETCH_EXIT=%ERRORLEVEL% >> %D%\retrieval.log
:stop
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'llama-server.exe' -or $_.Name -eq 'python.exe') -and ($_.CommandLine -match 'port 808[23]') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >> %D%\retrieval.log 2>&1
echo [%date% %time%] RETRIEVAL_DONE >> %D%\retrieval.log
