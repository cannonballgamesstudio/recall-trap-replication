#!/usr/bin/env python3
"""Prefetch retrieval packs for the 500 SWE-bench Verified instances.

Default (no args): the original two-arm run — dedupON from :8083, dedupOFF from
:8084, hybrid, limit 12, merged into local_packs.json (resumable; reuses
anything already fetched).

Parameterized (Track B §2): a single named arm from one endpoint, e.g. a cap
arm against a fleet instance on a spare port:

  py -3 prefetch_500.py --arm cap2 --endpoint http://127.0.0.1:8085 \
        --max-chunks-per-file 2 --packs-file cap_packs.json

NEVER point a cap run at local_packs.json — cap packs go to a NEW file; the
original pack file is a frozen eval input.
"""
import argparse, json, sys, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, "code/eval")
from g_plane_prompts import fetch_pack, format_pack

P = Path("work/p5")

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--arm", default=None, help="single arm name (e.g. cap2); default: dedupON+dedupOFF pair")
ap.add_argument("--endpoint", default=None, help="retrievald endpoint for --arm")
ap.add_argument("--max-chunks-per-file", type=int, default=None,
                help="send max_chunks_per_file with every query (cap arms)")
ap.add_argument("--packs-file", default="local_packs.json", help="output packs json under the p5 dir")
ap.add_argument("--limit", type=int, default=12)
ap.add_argument("--max-instances", type=int, default=None, help="smoke-test slice (default: all)")
args = ap.parse_args()

if args.arm and not args.endpoint:
    sys.exit("--arm requires --endpoint")
if args.arm:
    ARMS = [(args.arm, args.endpoint)]
    if args.packs_file == "local_packs.json":
        sys.exit("refusing to write a custom arm into local_packs.json — pass --packs-file")
else:
    ARMS = [("dedupON", "http://127.0.0.1:8083"), ("dedupOFF", "http://127.0.0.1:8084")]
EXTRA = ({"max_chunks_per_file": args.max_chunks_per_file}
         if args.max_chunks_per_file is not None else None)
PACKS = P / args.packs_file

cells = json.loads((P / "instances_verified.json").read_text())
cmap = {c["instance_id"]: c for c in cells}
ids = sorted(cmap)
if args.max_instances:
    ids = ids[: args.max_instances]

out = {}
try:
    out = json.loads(PACKS.read_text())
except Exception:
    pass

lock = threading.Lock()
done = {"n": 0}
todo = [(iid, arm, ep) for iid in ids for arm, ep in ARMS
        if arm not in out.get(iid, {})]
print(f"to fetch: {len(todo)} (already have {sum(len(v) for v in out.values())})", flush=True)


def work(job):
    iid, arm, ep = job
    c = cmap[iid]
    try:
        h = fetch_pack(ep, c["repo"], iid, c["problem_statement"][:6000], args.limit,
                       mode="hybrid", extra=EXTRA)
    except Exception as e:
        print(f"  fail {iid} {arm}: {str(e)[:40]}", flush=True); return
    with lock:
        out.setdefault(iid, {})[arm] = {
            "pack": format_pack(h, args.limit),
            "files": sorted({x.get("file", "") for x in h if x.get("file")}),
            "n_hits": len(h)}
        done["n"] += 1
        if done["n"] % 100 == 0:
            PACKS.write_text(json.dumps(out), encoding="utf-8")
            print(f"  {done['n']}/{len(todo)} (saved)", flush=True)


with ThreadPoolExecutor(max_workers=6) as ex:
    list(ex.map(work, todo))
PACKS.write_text(json.dumps(out), encoding="utf-8")
per_arm = {a: sum(1 for v in out.values() if a in v) for a, _ in ARMS}
print(f"[PREFETCH-DONE] {len(out)} instances, per-arm {per_arm}", flush=True)
