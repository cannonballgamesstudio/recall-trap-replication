@echo off
rem Qwen3-Embedding-8B on GPU, :8082, for contamination Branch A indexing.
rem -np 4 with -c 32768 = 8192 ctx per slot (the -c 8192 shared-KV config hit GGML_ASSERT(task) on 2026-10-14).
:loop
<LLAMA_DIR>\llama-server.exe -m <LLAMA_DIR>\Qwen3-Embedding-8B-Q8_0.gguf --embeddings --host 127.0.0.1 --port 8082 -ngl 99 -np 4 -c 32768 -b 8192 -ub 8192 >> data/post-cutoff-branchA\embed_8082.log 2>&1
echo [%date% %time%] llama-server exited, restarting in 10s >> data/post-cutoff-branchA\embed_8082.restarts.log
timeout /t 10 /nobreak > nul
goto loop
