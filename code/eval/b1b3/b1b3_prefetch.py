#!/usr/bin/env python3
"""LOCAL-B1B3-ADDENDUM-PREREG §2: prefetch the four queries per instance from ONE pinned daemon.

Daemon: code/retrieval retrievald on :8083 (RETRIEVALD_BACKEND=fusion, 4fab615 defaults, no
RETRIEVALD_QUERY_DEDUP_FILE), embedder :8082. Per instance, POST /v1/query with an explicit per-request
`dedup`:
  ON12  dedup=true  limit 12   OFF12 dedup=false limit 12
  ON48  dedup=true  limit 48   OFF48 dedup=false limit 48
hybrid, code_only=true, text=problem_statement[:6000], branch=instance_id (same body as the pinned
fetch_pack plus `dedup`). Raw hits (file, line, symbol, kind, score, snippet) + rank are stored in
work/p5/b1b3_prov.json. Resumable. Refuses to run unless the addendum is committed.
"""
from __future__ import annotations
import json, subprocess, sys, time, urllib.request
from pathlib import Path

P = Path("work/p5")
OUT = P / "b1b3_prov.json"
EP = "http://127.0.0.1:8083"
QUERIES = {"ON12": (True, 12), "OFF12": (False, 12), "ON48": (True, 48), "OFF48": (False, 48)}
REPO_ROOT = Path(__file__).resolve().parents[2]


def committed() -> bool:
    r = subprocess.run(["git", "-C", str(REPO_ROOT), "log", "--format=%h", "-1", "--",
                        "docs/paper/LOCAL-B1B3-ADDENDUM-PREREG.md"], capture_output=True, text=True)
    return bool(r.stdout.strip())


def query(repo, iid, text, dedup, limit):
    body = json.dumps({"repo": repo, "branch": iid, "text": text, "mode": "hybrid",
                       "limit": limit, "code_only": True, "dedup": dedup}).encode("utf-8")
    req = urllib.request.Request(f"{EP}/v1/query", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        resp = json.loads(r.read())
    hits = resp["hits"]
    if not isinstance(hits, list):
        raise RuntimeError("malformed hits")
    return [{"rank": i + 1, **h} for i, h in enumerate(hits)], resp.get("served_ref")


def main() -> int:
    if not committed():
        print("REFUSE: addendum not committed"); return 1
    cells = json.loads((P / "instances_verified.json").read_text(encoding="utf-8"))
    out = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    fails = {}
    t0 = time.time()
    for n, c in enumerate(cells, 1):
        iid = c["instance_id"]
        rec = out.setdefault(iid, {})
        for q, (dedup, limit) in QUERIES.items():
            if q in rec:
                continue
            for attempt in range(3):
                try:
                    hits, served = query(c["repo"], iid, c["problem_statement"][:6000], dedup, limit)
                    rec[q] = {"dedup": dedup, "limit": limit, "hits": hits, "served_ref": served}
                    break
                except Exception as e:
                    print(f"[FAIL] {iid} {q} try{attempt}: {str(e)[:120]}", flush=True)
                    time.sleep(2)
            else:
                fails.setdefault(iid, []).append(q)
        if n % 10 == 0 or n == len(cells):
            OUT.write_text(json.dumps(out), encoding="utf-8")
            print(f"[{n}/{len(cells)}] {time.time()-t0:.0f}s fails={len(fails)}", flush=True)
    OUT.write_text(json.dumps(out), encoding="utf-8")
    (P / "b1b3_prefetch_fails.json").write_text(json.dumps(fails, indent=1), encoding="utf-8")
    print(f"[prefetch-done] {len(out)} instances, {len(fails)} with failed queries", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
