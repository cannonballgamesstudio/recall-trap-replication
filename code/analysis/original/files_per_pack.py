#!/usr/bin/env python3
"""FREE control for the -18.2pp dedup finding: is it DEDUP, or just FEWER FILES?

At a fixed 12-slot budget, vary k = number of distinct files the pack is allowed to
span, filling the remaining slots with more chunks from those top-k files (depth).
Measure LINE-level coverage of the gold patch hunks -- the quantity that actually
predicts resolve (our taxonomy: 82% of failures are gold-file-present-lines-absent).

  k=12 -> up to 12 files, 1 chunk each  == the DEDUP-ON pack (64.9% resolved)
  k~=3 -> 3 files, ~4 chunks each        == the DEDUP-OFF depth pack (83.2% resolved)

If line-coverage rises monotonically as k falls, the mechanism is ALLOCATION
(depth), and "dedup vs not" is just the k=12 vs k<=4 endpoints of one curve.

Retrieval only. No agent, no API cost. Needs a dedup-OFF retrieval-service (:8084) so the raw
ranking keeps multiple chunks per file.
"""
from __future__ import annotations
import argparse, json, statistics, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from g_plane_prompts import fetch_pack
from oracle_pack import parse_gold_hunks

P = Path(r"data/swe-verified")
BUDGET = 12
KS = (1, 2, 3, 4, 6, 12)


def _norm(p): return p.replace("\\", "/").lower().lstrip("./")


def pack_at_k(hits, k, budget=BUDGET):
    """Keep chunks from only the top-k distinct files (first-seen order = rank),
    filling up to `budget` slots, depth-first within those files."""
    order, seen = [], set()
    for h in hits:
        f = _norm(h.get("file", ""))
        if f and f not in seen:
            seen.add(f)
            order.append(f)
        if len(seen) >= k and f not in seen:
            continue
    topk = set(order[:k])
    return [h for h in hits if _norm(h.get("file", "")) in topk][:budget]


def line_cov(pack, gold_lines):
    """Fraction of gold hunk-lines that fall inside some packed chunk's span."""
    covered = 0
    total = sum(len(v) for v in gold_lines.values())
    if not total:
        return None
    for f, lines in gold_lines.items():
        hit = set()
        for h in pack:
            if _norm(h.get("file", "")) != f:
                continue
            start = int(h.get("line") or 0)
            span = len((h.get("snippet") or "").splitlines()) or 1
            hit |= set(range(start, start + span))
        covered += len(lines & hit)
    return covered / total


def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default="http://127.0.0.1:8084", help="MUST be a dedup-OFF retrieval-service")
    ap.add_argument("--mode", default="hybrid")
    args = ap.parse_args()

    cells = {c["instance_id"]: c for c in json.loads((P / "instances_verified.json").read_text(encoding="utf-8"))}
    gold_patches = json.loads((P / "gold_patches.json").read_text(encoding="utf-8"))
    ids = [i for i in (P / "oracle_slice.txt").read_text().split(",") if i in cells]

    rows = []
    for n, iid in enumerate(ids, 1):
        c = cells[iid]
        gl = {}
        for path, s, ln in parse_gold_hunks(gold_patches[iid]):
            gl.setdefault(_norm(path), set()).update(range(s, s + ln))
        if not gl:
            continue
        try:
            hits = fetch_pack(args.endpoint, c["repo"], iid, c["problem_statement"][:6000], 40, mode=args.mode)
        except Exception as e:
            print(f"  FAIL {iid}: {str(e)[:70]}"); continue
        r = {"iid": iid}
        for k in KS:
            r[k] = line_cov(pack_at_k(hits, k), gl)
        rows.append(r)
        if n % 25 == 0:
            print(f"  {n}/{len(ids)}", flush=True)

    (P / "files_per_pack.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"\nn={len(rows)}  LINE-level gold coverage at a fixed {BUDGET}-slot budget:")
    print("%-8s %14s" % ("k files", "line-cov@12"))
    for k in KS:
        vals = [r[k] for r in rows if r[k] is not None]
        tag = "  <- dedup-ON" if k == 12 else ("  <- ~dedup-OFF" if k == 3 else "")
        print("%-8d %13.3f%s" % (k, statistics.mean(vals), tag))
    c12 = statistics.mean(r[12] for r in rows if r[12] is not None)
    c3 = statistics.mean(r[3] for r in rows if r[3] is not None)
    print(f"\nk=3 vs k=12 line-coverage: {c3:.3f} vs {c12:.3f}  ({100*(c3-c12):+.1f}pp)")
    print("If this gap is large and monotonic, the mechanism is DEPTH ALLOCATION,")
    print("and dedup is just the k=12 endpoint of it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
