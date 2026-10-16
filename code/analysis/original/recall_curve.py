#!/usr/bin/env python3
"""Where does gold sit in the ranked list? The diagnostic that picks the technique.

The oracle arm (2026-07-14) showed a 9.8pp resolve gap between our fusion pack
(76.1%) and a perfect pack (85.9%) at the SAME 12-slot budget. That gap is a
retrieval gap. This script asks the question that determines what kind of fix is
even possible:

  recall@12  (the pack budget)  vs  recall@50 / @100 (the candidate pool)

  - pool recall HIGH, @12 LOW  -> gold IS retrieved, ranked below the cutline.
    A RANKING problem. Reranking / small-model sifting can convert it.
  - pool recall LOW too        -> gold is not in the pool at all.
    A RETRIEVAL problem. Only query expansion / new signals can convert it.

Free: one retrieval-service query per instance, no agent, no API cost.

  python recall_curve.py --slice data/swe-verified/oracle_slice.txt
  python recall_curve.py --all --mode hybrid
"""
from __future__ import annotations
import argparse, json, statistics, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from g_plane_prompts import fetch_pack

INSTANCES = Path(r"data/swe-verified/instances_verified.json")
KS = (1, 5, 12, 25, 50, 100)


def _norm(p: str) -> str:
    return p.replace("\\", "/").lower().lstrip("./")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default="http://127.0.0.1:8083")
    ap.add_argument("--slice", default=None, help="comma-file of instance_ids")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--mode", default="hybrid")
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--out", default=r"data/swe-verified/recall_curve.json")
    args = ap.parse_args()

    cells = {c["instance_id"]: c for c in json.loads(INSTANCES.read_text(encoding="utf-8"))}
    if args.slice:
        ids = [i for i in Path(args.slice).read_text().split(",") if i in cells]
    elif args.all:
        ids = sorted(cells)
    else:
        ap.error("need --slice or --all")

    rows, fails = [], []
    for n, iid in enumerate(ids, 1):
        c = cells[iid]
        gold = {_norm(g) for g in c.get("gold_files", [])}
        if not gold:
            continue
        try:
            hits = fetch_pack(args.endpoint, c["repo"], iid, c["problem_statement"][:6000],
                              args.limit, mode=args.mode)
        except Exception as e:
            fails.append((iid, str(e)[:80]))
            continue
        # rank of FILES (dedup, first occurrence wins) -- the pack is file-oriented
        seen, ranked = set(), []
        for h in hits:
            f = _norm(h.get("file", ""))
            if f and f not in seen:
                seen.add(f)
                ranked.append(f)
        r = {"instance_id": iid, "n_gold": len(gold), "n_hits": len(hits), "n_files": len(ranked)}
        for k in KS:
            found = len(gold & set(ranked[:k]))
            r[f"recall@{k}"] = found / len(gold)
            r[f"any@{k}"] = 1.0 if found else 0.0
        rows.append(r)
        if n % 25 == 0:
            print(f"  {n}/{len(ids)} ...", flush=True)

    Path(args.out).write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"\nn={len(rows)}  (fetch failures: {len(fails)})")
    for iid, e in fails[:5]:
        print(f"   FAIL {iid}: {e}")
    print(f"\nmode={args.mode}  endpoint={args.endpoint}")
    print("%-10s %10s %10s" % ("k", "recall@k", "any-gold@k"))
    for k in KS:
        rc = statistics.mean(r[f"recall@{k}"] for r in rows)
        an = statistics.mean(r[f"any@{k}"] for r in rows)
        star = "  <- PACK BUDGET" if k == 12 else ""
        print("%-10d %10.3f %10.3f%s" % (k, rc, an, star))
    r12 = statistics.mean(r["recall@12"] for r in rows)
    r100 = statistics.mean(r["recall@100"] for r in rows)
    head = r100 - r12
    print(f"\nRANKING headroom (recall@100 - recall@12) = {head:+.3f}")
    print(f"POOL   ceiling (recall@100)                = {r100:.3f}")
    print("\ninterpretation:")
    if r100 >= 0.85 and head >= 0.10:
        print("  -> RANKING problem. Gold is in the pool but below the 12-slot cutline.")
        print("     Sifting/reranking the pool is the indicated fix.")
    elif r100 < 0.85:
        print("  -> RETRIEVAL problem. Gold is missing from the pool entirely at k=100.")
        print("     Reranking CANNOT fix this. Query expansion / new signals are the only lever.")
    else:
        print("  -> pool ~= pack. Little ranking headroom; gains must come from the pool.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
