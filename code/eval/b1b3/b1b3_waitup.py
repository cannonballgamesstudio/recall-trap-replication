#!/usr/bin/env python3
"""LOCAL-B1B3: wait for embedder :8082 and pinned retrievald :8083, verify provenance, one smoke query.

Exit 0 when both are up and retrievald's `ragfusion` is the pinned worktree; non-zero otherwise.
Smoke: ON12 for the first manifest instance vs headline local_packs.json dedupON (reported, not gated).
"""
import json, os, subprocess, sys, time, urllib.request
from pathlib import Path


def get(url, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())


def wait(url, label, limit=900):
    t0 = time.time()
    while time.time() - t0 < limit:
        try:
            get(url); print(f"[up] {label} after {time.time()-t0:.0f}s", flush=True); return True
        except Exception:
            time.sleep(5)
    print(f"[TIMEOUT] {label}", flush=True); return False


def main():
    if not wait("http://127.0.0.1:8082/v1/models", "embedder :8082"):
        return 2
    print("[embed models]", json.dumps(get("http://127.0.0.1:8082/v1/models"))[:300], flush=True)
    if not wait("http://127.0.0.1:8083/healthz", "retrievald :8083"):
        return 3
    origin = subprocess.run([sys.executable, "-c", "import ragfusion;print(ragfusion.__file__)"],
                            capture_output=True, text=True, env=os.environ).stdout.strip()
    print(f"[ragfusion origin under PYTHONPATH] {origin}", flush=True)
    if not origin.lower().startswith(r"code/retrieval"):
        print("[ABORT] ragfusion not from pinned worktree"); return 4
    sha = subprocess.run(["git", "-C", r"code/retrieval", "rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", r"code/retrieval", "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True).stdout.strip()
    print(f"[pin] HEAD={sha} dirty={bool(dirty)}", flush=True)
    if not sha.startswith("4fab615") or dirty:
        print("[ABORT] pinned worktree not at clean 4fab615"); return 5
    P = Path("work/p5")
    c = json.loads((P / "instances_verified.json").read_text(encoding="utf-8"))[0]
    body = json.dumps({"repo": c["repo"], "branch": c["instance_id"], "text": c["problem_statement"][:6000],
                       "mode": "hybrid", "limit": 12, "code_only": True, "dedup": True}).encode()
    req = urllib.request.Request("http://127.0.0.1:8083/v1/query", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        hits = json.loads(r.read())["hits"]
    ref = json.loads((P / "local_packs.json").read_text(encoding="utf-8"))[c["instance_id"]]["dedupON"]
    print(f"[smoke] {c['instance_id']} ON12 hits={len(hits)} files_match_headline="
          f"{sorted({h['file'] for h in hits}) == ref['files']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
