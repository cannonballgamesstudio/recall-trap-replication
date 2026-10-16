#!/usr/bin/env python3
"""R0.5 — is the 9.8pp oracle gap even a RETRIEVAL problem?

Partition the fusion-pack arm's outcomes against what its pack actually contained:

  (A) gold-absent            gold FILE not in the 12-slot pack        -> recall problem
  (B) gold-present, under-resolved
                             gold file IS in the pack, but the gold
                             PATCH LINES are not inside any packed
                             chunk's line span                        -> allocation/shape problem
  (C) gold fully covered     gold file present AND gold lines inside a
                             packed chunk -- and it STILL failed       -> NOT retrieval-addressable

If (C) dominates the failures, the entire retrieval-optimization program is a
mirage and the gap is a GENERATION gap. This costs nothing and must be run before
any technique is built.

Free: one retrieval-service query per instance, no agent, no API cost.
"""
from __future__ import annotations
import argparse, json, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from g_plane_prompts import fetch_pack
from oracle_pack import parse_gold_hunks

P = Path(r"data/swe-verified")
PACK_LIMIT = 12


def _norm(p: str) -> str:
    return p.replace("\\", "/").lower().lstrip("./")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default="http://127.0.0.1:8083")
    ap.add_argument("--mode", default="hybrid")
    ap.add_argument("--arm", default="g_pack", help="which graded arm's outcomes to explain")
    ap.add_argument("--reports", nargs="*", default=["g_pack.g_pack.json", "g_pack.g500_pack.json"])
    args = ap.parse_args()

    cells = {c["instance_id"]: c for c in json.loads((P / "instances_verified.json").read_text(encoding="utf-8"))}
    gold_patches = json.loads((P / "gold_patches.json").read_text(encoding="utf-8"))
    ids = [i for i in (P / "oracle_slice.txt").read_text().split(",") if i in cells]

    resolved, completed = set(), set()
    for r in args.reports:
        f = P / r
        if not f.exists():
            continue
        d = json.loads(f.read_text())
        resolved |= set(d.get("resolved_ids", []))
        completed |= set(d.get("completed_ids", []))

    rows = []
    for iid in ids:
        if iid not in completed:
            continue
        c = cells[iid]
        # gold: file -> set of patched line numbers (pre-image, matches the checkout)
        gold_lines: dict[str, set[int]] = {}
        for path, start, length in parse_gold_hunks(gold_patches[iid]):
            gold_lines.setdefault(_norm(path), set()).update(range(start, start + length))
        if not gold_lines:
            continue
        try:
            hits = fetch_pack(args.endpoint, c["repo"], iid, c["problem_statement"][:6000],
                              PACK_LIMIT, mode=args.mode)
        except Exception as e:
            print(f"  FETCH FAIL {iid}: {e}")
            continue

        pack_files = {_norm(h.get("file", "")) for h in hits if h.get("file")}
        # a chunk covers gold if its [line, line+snippet_lines) span intersects a gold line
        covered: dict[str, bool] = {g: False for g in gold_lines}
        for h in hits:
            f = _norm(h.get("file", ""))
            if f not in gold_lines:
                continue
            start = int(h.get("line") or 0)
            span = len((h.get("snippet") or "").splitlines()) or 1
            if set(range(start, start + span)) & gold_lines[f]:
                covered[f] = True

        gold_present = [g for g in gold_lines if g in pack_files]
        n_gold = len(gold_lines)
        n_present = len(gold_present)
        n_covered = sum(1 for g in gold_lines if covered[g])
        distractors = len(pack_files - set(gold_lines))

        if n_present == 0:
            cls = "A_gold_absent"
        elif n_covered < n_gold:
            cls = "B_under_resolved"
        else:
            cls = "C_fully_covered"
        rows.append({"instance_id": iid, "class": cls, "resolved": iid in resolved,
                     "n_gold": n_gold, "n_present": n_present, "n_covered": n_covered,
                     "distractor_files": distractors, "pack_files": len(pack_files)})

    (P / "failure_taxonomy.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    n = len(rows)
    res = [r for r in rows if r["resolved"]]
    fails = [r for r in rows if not r["resolved"]]
    print(f"arm={args.arm}  graded n={n}   resolved {len(res)} ({100*len(res)/n:.1f}%)   failed {len(fails)}\n")

    print("ALL INSTANCES — pack content vs outcome")
    print("%-18s %6s %9s %9s" % ("class", "n", "resolved", "rate"))
    cc = Counter(r["class"] for r in rows)
    for cls in ("A_gold_absent", "B_under_resolved", "C_fully_covered"):
        sub = [r for r in rows if r["class"] == cls]
        if not sub:
            continue
        rr = sum(1 for r in sub if r["resolved"])
        print("%-18s %6d %9d %8.1f%%" % (cls, len(sub), rr, 100 * rr / len(sub)))

    print(f"\nTHE FAILURES (n={len(fails)}) — what would have had to change:")
    fc = Counter(r["class"] for r in fails)
    for cls in ("A_gold_absent", "B_under_resolved", "C_fully_covered"):
        k = fc.get(cls, 0)
        if not fails:
            break
        print("  %-18s %3d  (%4.1f%% of failures)" % (cls, k, 100 * k / len(fails)))

    a, b, cnt = fc.get("A_gold_absent", 0), fc.get("B_under_resolved", 0), fc.get("C_fully_covered", 0)
    tot = max(1, len(fails))
    print("\nVERDICT:")
    if cnt / tot >= 0.5:
        print("  -> (C) DOMINATES. Most failures had the gold code IN THE PACK, fully covered,")
        print("     and failed anyway. The gap is a GENERATION gap, not a retrieval gap.")
        print("     Retrieval optimization CANNOT close it. Say so and stop building retrievers.")
    elif b >= a:
        print("  -> (B) DOMINATES. Gold file is in the pack but the gold LINES are not.")
        print("     This is an ALLOCATION problem: file-dedup spends 12 slots on 12 files,")
        print("     shallow. Depth-over-breadth packing is the indicated fix — free, no new model.")
    else:
        print("  -> (A) DOMINATES. Gold file is missing from the pack entirely.")
        print("     A ranking/recall problem: better ranking or expansion is the indicated fix.")
    print(f"\nmean distractor files in pack: {sum(r['distractor_files'] for r in rows)/n:.1f} of "
          f"{sum(r['pack_files'] for r in rows)/n:.1f} slots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
