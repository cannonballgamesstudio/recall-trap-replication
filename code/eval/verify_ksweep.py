#!/usr/bin/env python3
"""Verify budget-sweep pack integrity (NEXT-BENCHMARKS-DESIGN Pre-reg 2, G2-rigor).

For every packs_k{K}.json under the p5 dir:
  - coverage: n instances, count with both arms.
  - per-arm n_hits distribution; SHORT packs (n_hits < K) counted (expected when a
    query/repo has < K retrievable chunks or < K distinct files under dedup-ON).
  - DEGENERATE packs (n_hits == 0 or empty pack string) flagged — must be zero.
  - format integrity: number of '### ' chunk headers in the rendered pack == n_hits.
  - dedup shape: dedup-ON chunks/file ~= 1.0 (distinct files == n_hits); dedup-OFF
    chunks/file >= 1.0 (depth). Reports mean distinct-files + chunks/file per arm
    (the ON/OFF divergence the sweep maps as K grows).
Plus a K=12 REPRODUCTION spot-check: re-fetch N instances live at K=12 from the
retrievald daemons and byte-compare the rendered pack to local_packs.json (determinism).
"""
import sys, json, glob, argparse
from pathlib import Path
sys.path.insert(0, "code/eval")
from g_plane_prompts import fetch_pack, format_pack

P = Path("work/p5")
ARMS_EP = {"dedupON": "http://127.0.0.1:8083", "dedupOFF": "http://127.0.0.1:8084"}


def verify_file(fp: Path):
    K = int(fp.stem.split("_k")[1])
    data = json.loads(fp.read_text(encoding="utf-8"))
    both = sum(1 for v in data.values() if "dedupON" in v and "dedupOFF" in v)
    print(f"\n=== {fp.name}  (K={K}) ===")
    print(f"  instances: {len(data)}, with both arms: {both}")
    ok = True
    for arm in ("dedupON", "dedupOFF"):
        nhits, dfiles, hdr_mismatch, degenerate, shortp = [], [], 0, 0, 0
        for iid, v in data.items():
            if arm not in v: continue
            rec = v[arm]
            nh = rec.get("n_hits", 0)
            nfiles = len(rec.get("files", []))
            pack = rec.get("pack", "")
            hdrs = pack.count("\n### ")  # each chunk renders one '### file:line — sym' header
            nhits.append(nh); dfiles.append(nfiles)
            if nh == 0 or not pack.strip(): degenerate += 1
            if hdrs != nh: hdr_mismatch += 1
            if nh < K: shortp += 1
        n = len(nhits)
        mean_h = sum(nhits)/n if n else 0
        mean_f = sum(dfiles)/n if n else 0
        cpf = mean_h/mean_f if mean_f else 0
        atK = sum(1 for h in nhits if h == K)
        print(f"  [{arm:9s}] n={n} mean_hits={mean_h:.2f} mean_distinct_files={mean_f:.2f} "
              f"chunks/file={cpf:.2f} | ==K:{atK} short(<K):{shortp} degenerate:{degenerate} "
              f"header_mismatch:{hdr_mismatch}")
        if degenerate or hdr_mismatch:
            ok = False
            print(f"    !! INTEGRITY FAIL in {arm}: degenerate={degenerate} header_mismatch={hdr_mismatch}")
    return ok


def reproduce_k12(n_sample: int):
    print(f"\n=== K=12 REPRODUCTION spot-check (byte-exact vs local_packs.json), N={n_sample} ===")
    lp = json.loads((P / "local_packs.json").read_text(encoding="utf-8"))
    cells = {c["instance_id"]: c for c in json.loads((P / "instances_verified.json").read_text(encoding="utf-8"))}
    ids = [i for i in sorted(lp) if "dedupON" in lp[i] and "dedupOFF" in lp[i]][:n_sample]
    mism = 0
    for iid in ids:
        c = cells[iid]
        for arm, ep in ARMS_EP.items():
            h = fetch_pack(ep, c["repo"], iid, c["problem_statement"][:6000], 12, mode="hybrid")
            live = format_pack(h, 12)
            stored = lp[iid][arm]["pack"]
            if live != stored:
                mism += 1
                print(f"  MISMATCH {iid} {arm}: live_len={len(live)} stored_len={len(stored)}")
    print(f"  reproduced {len(ids)*2 - mism}/{len(ids)*2} arm-packs byte-exact "
          f"({'OK — daemons deterministic' if mism == 0 else 'DRIFT DETECTED'})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reproduce", type=int, default=8, help="N instances for the K=12 determinism spot-check (0=skip)")
    args = ap.parse_args()
    files = sorted(Path(p) for p in glob.glob(str(P / "packs_k*.json")))
    print(f"found {len(files)} sweep packfiles: {[f.name for f in files]}")
    all_ok = all(verify_file(f) for f in files)
    if args.reproduce:
        reproduce_k12(args.reproduce)
    print(f"\n[VERIFY {'PASS' if all_ok else 'FAIL'}] integrity across {len(files)} packfiles")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
