#!/usr/bin/env python3
"""Run the DENSE-only retriever control at n=500 through the SAME Claude agent
as the fusion headline (swe_bench.py --g-plane packfile, no tools, single-shot).

Waits for prefetch_dense_500.py to fill kpack_dense500_{ON,OFF}.json, then for
each arm sets GPLANE_PACKFILE and predicts in chunks with --resume. Fair within
comparison: identical policy/model/budget, only the retriever (dense vs fusion)
and the dedup knob differ. Grades are a separate step.
"""
import os, sys, json, time, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = Path("work/p5")
INSTANCES = P / "instances_verified.json"
ENDPOINT_FUSION = "http://127.0.0.1:8083"   # any live retrievald; packfile arm ignores retrieval, needs a valid ref resolve
MODEL = "claude-sonnet-5"
CHUNK = 25
CONC = 6
BUDGET = 1.5

ids = sorted(c["instance_id"] for c in json.loads(INSTANCES.read_text(encoding="utf-8")))


def wait_packfile(arm):
    f = P / f"kpack_dense500_{arm}.json"
    while True:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            have = sum(1 for i in ids if i in d)
            if have >= 500:
                print(f"[packfile ready] {arm}: {have}/500", flush=True); return d
            print(f"[waiting] {arm} packfile {have}/500", flush=True)
        except Exception:
            print(f"[waiting] {arm} packfile not readable yet", flush=True)
        time.sleep(60)


def run_arm(arm):
    packfile = P / f"kpack_dense500_{arm}.json"
    store = wait_packfile(arm)
    label = f"g_dense500_{arm}"
    out = P / f"preds_{label}.jsonl"
    env = dict(os.environ, SWE_CLAUDE_MODEL=MODEL, GPLANE_PACKFILE=str(packfile))
    # only run ids that actually have a pack (all 500 expected)
    run_ids = [i for i in ids if i in store]
    for i in range(0, len(run_ids), CHUNK):
        chunk = run_ids[i:i + CHUNK]
        print(f"[chunk] {label} {i}-{i+len(chunk)-1}/{len(run_ids)}", flush=True)
        cmd = [sys.executable, str(HERE / "swe_bench.py"), "predict",
               "--subset", str(INSTANCES), "--mode", "rag", "--g-plane", "packfile",
               "--label", label, "--out", str(out), "--budget", str(BUDGET),
               "--concurrency", str(CONC), "--resume", "--ref-mode", "instance",
               "--endpoint", ENDPOINT_FUSION, "--ids", ",".join(chunk)]
        r = subprocess.run(cmd, env=env, cwd=str(HERE.parent.parent))
        if r.returncode != 0:
            print(f"[FAIL] {label} chunk rc={r.returncode} — resumable", flush=True); return 1
    print(f"[arm-done] {label} n={len(run_ids)}", flush=True)
    return 0


def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    for arm in ("ON", "OFF"):
        if run_arm(arm) != 0:
            return 1
    print("[DENSE500-PREDICT-COMPLETE]", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
