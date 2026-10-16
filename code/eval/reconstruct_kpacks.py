#!/usr/bin/env python3
"""Build max-files=k reconstruction packs for the dose-response (E3).

From the dedup-OFF ranking (:8084, multiple chunks per file), keep only the top-k
DISTINCT files and fill the 12-slot budget depth-first within them. Varying k at a
FIXED budget isolates the files-per-pack knob:

  k=2  -> deepest  (2 files, ~6 chunks each)
  k=5  ~= the measured dedup-OFF depth pack (83.2%)
  k=8  -> mild
  k=12 ~= the measured dedup-ON breadth pack (64.9%)

If resolve rises monotonically as k falls, the mechanism is DEPTH ALLOCATION and
dedup is just the k=12 endpoint. If flat until the last distractors vanish, it is
distractor-count (a noise story). Writes one JSON {instance_id: packtext} per k.
"""
import sys, json
sys.path.insert(0, "code/eval")
from g_plane_prompts import fetch_pack, format_pack
from pathlib import Path

P = Path("work/p5")
EP = "http://127.0.0.1:8084"   # dedup-OFF daemon (depth ranking)
BUDGET = 12
KS = (2, 8)                     # the two NEW points; 5 and 12 already graded

cells = {c["instance_id"]: c for c in json.loads((P / "instances_verified.json").read_text(encoding="utf-8"))}
ids = [i for i in (P / "oracle_slice.txt").read_text().split(",") if i in cells]


def norm(p): return p.replace("\\", "/").lower()


def kpack(hits, k):
    seen, keep = [], []
    for h in hits:
        f = norm(h.get("file", ""))
        if f and f not in seen:
            if len(seen) >= k:
                continue          # new file beyond the k-cap: skip
            seen.append(f)
        keep.append(h)
    return keep[:BUDGET]


for k in KS:
    out, empty = {}, 0
    for iid in ids:
        c = cells[iid]
        try:
            hits = fetch_pack(EP, c["repo"], iid, c["problem_statement"][:6000], 40)
        except Exception as e:
            print(f"  k={k} FAIL {iid}: {str(e)[:50]}"); continue
        kp = kpack(hits, k)
        if not kp:
            empty += 1; continue
        out[iid] = format_pack(kp, BUDGET)
    dest = P / f"kpack_k{k}.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8")
    nfiles = sum(len({l.split(":")[0] for l in p.split("### ")[1:]}) for p in out.values()) / max(1, len(out))
    print(f"k={k}: {len(out)} packs, mean distinct files ~{nfiles:.1f}  -> {dest.name}")
