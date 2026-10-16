#!/usr/bin/env python3
"""Budget-sweep prefetch: build dedup-ON/OFF packs at an arbitrary slot budget K.

Pre-registered in docs/paper/NEXT-BENCHMARKS-DESIGN.md (Pre-reg 2, rule B-1/B-2).
Identical construction to prefetch_500.py (the K=12 headline) EXCEPT the slot
budget is a CLI arg. The retrievald daemons apply file-dedup internally, so requesting
limit=K from :8083 (dedup-ON) and :8084 (dedup-OFF) yields the correct per-arm
K-budget packs: ON = up to K distinct files (post-filtered before the top-K cut),
OFF = the raw top-K chunks. Everything else (mode=hybrid, query=problem_statement
[:6000], code_only, rendering order, format_pack) is held byte-identical to the
headline so the sweep is comparable to the K=12 primary arm.

Writes packs_k{K}.json under the p5 dir, keyed by instance_id with per-arm
{pack, files, n_hits} — the exact shape local_dedup_ab.py --packs-file expects.

  python prefetch_ksweep.py --k 4
  python prefetch_ksweep.py --k 8
  python prefetch_ksweep.py --k 20
  python prefetch_ksweep.py --k 40
"""
import sys, json, threading, argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, "code/eval")
from g_plane_prompts import fetch_pack, format_pack

P = Path("work/p5")
ARMS = [("dedupON", "http://127.0.0.1:8083"), ("dedupOFF", "http://127.0.0.1:8084")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, required=True, help="slot budget for this sweep point")
    ap.add_argument("--out", default=None, help="output filename under p5 (default packs_k{K}.json)")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    K = args.k
    dest = P / (args.out or f"packs_k{K}.json")

    cells = json.loads((P / "instances_verified.json").read_text(encoding="utf-8"))
    cmap = {c["instance_id"]: c for c in cells}
    ids = sorted(cmap)

    out = {}
    if dest.exists():                       # resumable: a timeout can't wipe progress
        try: out = json.loads(dest.read_text(encoding="utf-8"))
        except Exception: out = {}

    lock = threading.Lock()
    done = {"n": 0}
    todo = [(iid, arm, ep) for iid in ids for arm, ep in ARMS
            if arm not in out.get(iid, {})]
    print(f"K={K}: to fetch {len(todo)} (already have {sum(len(v) for v in out.values())})", flush=True)

    def work(job):
        iid, arm, ep = job
        c = cmap[iid]
        try:
            h = fetch_pack(ep, c["repo"], iid, c["problem_statement"][:6000], K, mode="hybrid")
        except Exception as e:
            print(f"  fail {iid} {arm}: {str(e)[:50]}", flush=True); return
        with lock:
            out.setdefault(iid, {})[arm] = {
                "pack": format_pack(h, K),
                "files": sorted({x.get("file", "") for x in h if x.get("file")}),
                "n_hits": len(h)}
            done["n"] += 1
            if done["n"] % 100 == 0:
                dest.write_text(json.dumps(out), encoding="utf-8")
                print(f"  {done['n']}/{len(todo)} (saved)", flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        list(ex.map(work, todo))
    dest.write_text(json.dumps(out), encoding="utf-8")
    full = sum(1 for v in out.values() if "dedupON" in v and "dedupOFF" in v)
    print(f"[KSWEEP-DONE K={K}] {dest.name}: {len(out)} instances, {full} with both arms", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
