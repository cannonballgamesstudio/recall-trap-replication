$ErrorActionPreference = "Continue"
$G = "data/post-cutoff-branchA\gen"
$S = "code/eval\local_dedup_ab.py"
$env:OPENROUTER_API_KEY = [Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY','User')
$env:LOG_RESPONSE_TEXT = "1"
$env:PYTHONIOENCODING = "utf-8"
$ids = (Get-Content "$G\ids_survivors.txt" -Raw).Trim()
function Log($m) { Add-Content "$G\orchestrate.log" "$(Get-Date -Format HH:mm:ss) $m" }
$common = @("--root","data/post-cutoff-branchA","--instances-file","instances_post.json","--packs-file","post_packs.json","--ids",$ids)
Log "START precache"
python "$G\precache.py" *> "$G\precache.log"
Log "DONE precache rc=$LASTEXITCODE"
# A5 local Qwen3-Coder-30B (GPU) in parallel with gpt (API)
$srv = Start-Process -FilePath "<LLAMA_DIR>\llama-server.exe" -ArgumentList "-m","<LLAMA_DIR>\Qwen3-Coder-30B-A3B-Instruct-UD-Q5_K_XL.gguf","--host","127.0.0.1","--port","8090","-c","16384","--parallel","2","--jinja","-ngl","99" -RedirectStandardOutput "$G\llama_8090.out.log" -RedirectStandardError "$G\llama_8090.err.log" -PassThru -WindowStyle Hidden
Log "llama-server pid $($srv.Id)"
$a5 = Start-Process -FilePath "powershell" -ArgumentList "-NoProfile","-ExecutionPolicy","Bypass","-File","$G\a5.ps1" -PassThru -WindowStyle Hidden
foreach ($seed in @("", "_s2")) {
  $tag = "gpt56sol_post$seed"
  Log "START gpt $tag"
  $p = @()
  foreach ($arm in @("dedupON","dedupOFF")) {
    $a = @($S,"--arm",$arm,"--endpoint","https://openrouter.ai/api/v1","--api-model","openai/gpt-5.6-sol","--api-key-env","OPENROUTER_API_KEY","--model-tag",$tag,"--concurrency","8") + $common
    $p += Start-Process -FilePath "python" -ArgumentList $a -RedirectStandardOutput "$G\gen_${tag}_$arm.log" -RedirectStandardError "$G\gen_${tag}_$arm.err" -PassThru -WindowStyle Hidden
  }
  $p | Wait-Process
  Log "DONE gpt $tag"
}
$a5 | Wait-Process
Log "DONE a5"
Stop-Process -Id $srv.Id -Force
Log "llama-server stopped; ALLDONE"
