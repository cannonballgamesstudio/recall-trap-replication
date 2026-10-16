$G = "data/memorization-branchB\local_run"
$env:PYTHONIOENCODING = "utf-8"
function Log($m) { Add-Content "$G\probes.log" "$(Get-Date -Format HH:mm:ss) $m" }
$srv = Start-Process -FilePath "<LLAMA_DIR>\llama-server.exe" -ArgumentList "-m","<LLAMA_DIR>\Qwen3-Coder-30B-A3B-Instruct-UD-Q5_K_XL.gguf","--host","127.0.0.1","--port","8090","-c","16384","--parallel","2","--jinja","-ngl","99" -RedirectStandardOutput "$G\llama_8090.out.log" -RedirectStandardError "$G\llama_8090.err.log" -PassThru -WindowStyle Hidden
Log "llama-server pid $($srv.Id)"
for ($i=0; $i -lt 120; $i++) { try { $r = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8090/health -TimeoutSec 5; if ($r.StatusCode -eq 200) { break } } catch {}; Start-Sleep 5 }
Log "server healthy"
Set-Location <repo>
foreach ($p in @("P3","P2")) {
  Log "START $p"
  python scripts/eval/contam_probe.py run --probe $p --tag qwen3coder30b_local --endpoint http://127.0.0.1:8090 --concurrency 2 --max-tokens 6000 *> "$G\run_${p}_resume.log"
  Log "DONE $p rc=$LASTEXITCODE"
}
Stop-Process -Id $srv.Id -Force
Log "llama-server stopped; PROBES_DONE"
