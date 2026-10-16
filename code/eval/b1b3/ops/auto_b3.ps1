# Wait for B3 generation, stop llama-server (GPU), then grade P (Docker) -- never overlapping.
$D = "work/p5/b1b3"
while (-not (Select-String -Path "$D\gen.log" -Pattern "GEN_B3_DONE" -Quiet)) { Start-Sleep 30 }
Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 10
"[$(Get-Date -Format s)] llama-server stopped; starting P grading" | Out-File -Append -Encoding utf8 "$D\grade.out"
& cmd /c "$D\grade_b3.cmd"
"AUTO_B3_DONE $(Get-Date -Format s)" | Out-File -Append -Encoding utf8 "$D\grade.out"
