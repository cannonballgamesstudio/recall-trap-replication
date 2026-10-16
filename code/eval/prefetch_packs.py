#!/usr/bin/env python3
"""Pre-fetch the dedup-ON and dedup-OFF packs for the 100-slice, save to JSON.

Separating retrieval (needs the :8080 embedder + retrievald) from generation (needs the
local coder model in VRAM) so they don't fight over the 24GB card. Run this while
the embedder is up; then the local-model generation phase reads packs from disk.
"""
import sys, json
sys.path.insert(0, "code/eval")
from g_plane_prompts import fetch_pack, format_pack
from pathlib import Path

P = Path("work/p5")
cells = {c["instance_id"]: c for c in json.loads((P / "instances_verified.json").read_text(encoding="utf-8"))}
ids = [i for i in (P / "oracle_slice.txt").read_text().split(",") if i in cells]

ARMS = {"dedupON": "http://127.0.0.1:8083", "dedupOFF": "http://127.0.0.1:8084"}
out = {}
for arm, ep in ARMS.items():
    got = 0
    for iid in ids:
        c = cells[iid]
        try:
            hits = fetch_pack(ep, c["repo"], iid, c["problem_statement"][:6000], 12)
        except Exception as e:
            print(f"  {arm} FAIL {iid}: {str(e)[:60]}"); continue
        out.setdefault(iid, {})[arm] = {
            "pack": format_pack(hits, 12),
            "files": sorted({h.get("file", "") for h in hits if h.get("file")}),
            "n_hits": len(hits),
        }
        got += 1
    print(f"{arm}: {got}/{len(ids)} packs")

dest = P / "local_packs.json"
dest.write_text(json.dumps(out, indent=1), encoding="utf-8")
print(f"wrote {dest}  ({len(out)} instances)")
