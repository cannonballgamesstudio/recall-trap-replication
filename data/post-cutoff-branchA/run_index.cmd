@echo off
rem Contamination pre-reg Branch A: detached index job (pinned stack 4fab615, embedder :8082).
rem Three resumable passes: a pass retries any instance that FAILed on a transient embedder error.
set OPENAI_BASE_URL=http://127.0.0.1:8082
set OPENAI_API_KEY=sk-noauth
set PYTHONIOENCODING=utf-8
set SRCLIGHT_EMBED_REQUEST_TIMEOUT=120
cd /d <repo>
for %%P in (1 2 3) do (
  echo [pass %%P start %date% %time%] >> data/post-cutoff-branchA\index.log
  python -u code/eval\contam_post_index.py --max-files 15000 >> data/post-cutoff-branchA\index.log 2>&1
)
