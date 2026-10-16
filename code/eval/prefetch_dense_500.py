#!/usr/bin/env python3
"""Build DENSE-only (mode=semantic) packs for all 500, both dedup arms.

Powers the retriever-generality control to n=500: the n=100 dense arm was an
underpowered null (6 discordant pairs). Same pipeline as prefetch_500.py but
mode='semantic' (strips graph/trigram/priors/lex to plain cosine). dedup-ON from
:8083, dedup-OFF from :8084. Writes packfiles the g-plane packfile arm consumes:
  kpack_dense500_ON.json / kpack_dense500_OFF.json  (keyed by instance_id)
"""
import sys, json, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, "code/eval")
from g_plane_prompts import fetch_pack, format_pack

P = Path("work/p5")
cells = {c["instance_id"]: c for c in json.loads((P / "instances_verified.json").read_text())}
ids = sorted(cells)
ARMS = [("ON", "http://127.0.0.1:8083"), ("OFF", "http://127.0.0.1:8084")]

out = {"ON": {}, "OFF": {}}
for arm, _ in ARMS:
    f = P / f"kpack_dense500_{arm}.json"
    if f.exists():
        try: out[arm] = json.loads(f.read_text())
        except Exception: pass

lock = threading.Lock()
done = {"n": 0}
todo = [(iid, arm, ep) for iid in ids for arm, ep in ARMS if iid not in out[arm]]
print(f"to fetch: {len(todo)} (have ON={len(out['ON'])} OFF={len(out['OFF'])})", flush=True)


def save():
    for arm, _ in ARMS:
        (P / f"kpack_dense500_{arm}.json").write_text(json.dumps(out[arm]), encoding="utf-8")


def work(job):
    iid, arm, ep = job
    c = cells[iid]
    try:
        h = fetch_pack(ep, c["repo"], iid, c["problem_statement"][:6000], 12, mode="semantic")
    except Exception as e:
        print(f"  fail {iid} {arm}: {str(e)[:40]}", flush=True); return
    with lock:
        out[arm][iid] = format_pack(h, 12)
        done["n"] += 1
        if done["n"] % 100 == 0:
            save(); print(f"  {done['n']}/{len(todo)} (saved)", flush=True)


with ThreadPoolExecutor(max_workers=6) as ex:
    list(ex.map(work, todo))
save()
full = sum(1 for i in ids if i in out["ON"] and i in out["OFF"])
print(f"[DENSE-500-DONE] ON={len(out['ON'])} OFF={len(out['OFF'])} both={full}", flush=True)
