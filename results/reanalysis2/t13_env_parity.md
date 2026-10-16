## Task 13 — Environment-parity spot check: SKIPPED (precondition not met)

Precondition: Docker only if no other Docker job is running AND the GPU model server is down.

State checked 2026-10-15 before any Docker use:

| check | result |
|---|---|
| `docker ps` | no running containers (Docker Desktop up, idle) |
| GPU model server | **UP**: `<LLAMA_DIR>\llama-server.exe -m Qwen3-Coder-30B-A3B-Instruct-UD-Q5_K_XL.gguf --port 8091 -np 32 -c 311296` (PID 75660), 23.8 GB VRAM in use, 37% GPU util |
| other host job | `python scripts\eval\fanout_calibrate.py --model a3b --np 8,16,32 --force` (PID 42088) is driving that server |

Because the GPU model server is up (and a calibration run is using it), the regrade was not started and WSL caches were not dropped.
No Docker command was issued. To run it later: stop the calibration and :8091, confirm `docker ps` is empty, drop WSL caches,
then regrade a seeded 5% sample (seed 20261014; ~25 instances per arm) of gpt_hl_{ON,OFF} and qc_{ON,OFF} under new run_ids
and compare per-instance `resolved` against the original reports.
