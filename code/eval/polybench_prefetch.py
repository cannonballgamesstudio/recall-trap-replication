#!/usr/bin/env python3
"""Prefetch dedup-ON/OFF PolyBench packs at K=12 (NEXT-BENCHMARKS-DESIGN Pre-reg 1).

Runs AFTER polybench_index.py has registered the per-instance PolyBench indexes in
<EVAL_ROOT>\\registry.db (the live retrievald daemons resolve repo+branch=instance_id there).
Same construction as the SWE-Verified headline (prefetch_500.py): mode=hybrid,
query=problem_statement[:6000], k=12, format_pack — only the manifest + output root
differ. Writes polybench_packs.json under <EVAL_ROOT>\\polybench, the shape
local_dedup_ab.py --root <EVAL_ROOT>/polybench --packs-file polybench_packs.json expects.

Only instances whose index is registered (i.e. survived the R2 file-budget) are
fetched; the rest are skipped and counted (report the per-language inclusion rate).

  python polybench_prefetch.py                     # k=12, all registered instances
  python polybench_prefetch.py --mode keyword --out polybench_packs_bm25.json   # BM25 arm (A3)
"""
import sys, json, threading, argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, "code/eval")
from g_plane_prompts import fetch_pack, format_pack

ROOT = Path(r"<EVAL_ROOT>\polybench")
MANIFEST = ROOT / "instances_polybench.json"
ARMS = [("dedupON", "http://127.0.0.1:8083"), ("dedupOFF", "http://127.0.0.1:8084")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=12)
    ap.add_argument("--mode", default="hybrid", help="hybrid (fusion, default) or keyword (BM25 arm A3)")
    ap.add_argument("--out", default="polybench_packs.json")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    K = args.k
    dest = ROOT / args.out

    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cmap = {x["instance_id"]: x for x in man}
    ids = sorted(cmap)

    out = {}
    if dest.exists():
        try: out = json.loads(dest.read_text(encoding="utf-8"))
        except Exception: out = {}

    lock = threading.Lock()
    done = {"n": 0}
    skipped = {"n": 0}
    todo = [(iid, arm, ep) for iid in ids for arm, ep in ARMS if arm not in out.get(iid, {})]
    print(f"PolyBench prefetch k={K} mode={args.mode}: to fetch {len(todo)}", flush=True)

    def work(job):
        iid, arm, ep = job
        c = cmap[iid]
        try:
            h = fetch_pack(ep, c["repo"], iid, c["problem_statement"][:6000], K, mode=args.mode)
        except Exception as e:
            # RefNotFound => instance not indexed (excluded by R2 budget or index failed) — expected, count it
            with lock: skipped["n"] += 1
            print(f"  skip {iid} {arm}: {str(e)[:60]}", flush=True); return
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
    # per-language inclusion (B-5)
    from collections import Counter
    langtot = Counter(x["language"] for x in man)
    langgot = Counter(cmap[i]["language"] for i in out if "dedupON" in out[i] and "dedupOFF" in out[i])
    print(f"[POLYBENCH-PREFETCH-DONE] {dest.name}: {full}/500 with both arms; skipped-fetches={skipped['n']}", flush=True)
    for lang in sorted(langtot):
        print(f"  {lang}: {langgot.get(lang,0)}/{langtot[lang]} included", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
