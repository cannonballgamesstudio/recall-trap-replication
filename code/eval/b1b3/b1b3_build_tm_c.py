#!/usr/bin/env python3
"""LOCAL-B1B3 D-TM (TM-RULING-2026-10-15 option (c)): rebuild TM only -> p5/b1b3_packs_b2.json.

TM padding candidates = Q-ON48 hits whose file is not in files(ON12), in Q-ON48 rank order (no rank
cutoff). Everything else as in b1b3_build.py (T prefix, greedy closest-match on rendered chars vs
len(format_pack(OFF)), whole chunks). ON/OFF/T/P are copied from p5/b1b3_packs.json (never rewritten)
and asserted byte-identical. Prints the ruling's check numbers.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from b1b3_build import P, render  # noqa: E402  (pinned format_pack)


def main() -> int:
    prov = json.loads((P / "b1b3_prov.json").read_text(encoding="utf-8"))
    src_bytes = (P / "b1b3_packs.json").read_bytes()
    assert hashlib.sha256(src_bytes).hexdigest().startswith("80382193"), "B1 packs file changed!"
    b1 = json.loads(src_bytes)
    t_ids = (P / "b1b3_ids_T.txt").read_text(encoding="utf-8").split()
    out = json.loads(src_bytes)               # deep copy; only TM entries are replaced
    ratios, pads_n, cands_n, short, pad_low, pad_in_on, rank_sum = [], 0, [], [], 0, 0, []
    log = {}
    for iid in t_ids:
        rec = prov[iid]
        on, off, on48 = rec["ON12"]["hits"], rec["OFF12"]["hits"], rec["ON48"]["hits"]
        on_files = {h["file"] for h in on}
        on_by_file = {h["file"]: h for h in on}
        off_files = []
        for h in off:
            if h["file"] not in off_files:
                off_files.append(h["file"])
        T = [on_by_file[f] for f in off_files]
        assert render(T) == b1[iid]["T"]["pack"], f"T mismatch {iid}"
        target = len(b1[iid]["OFF"]["pack"])
        cands = [h for h in on48 if h["file"] not in on_files]
        cands_n.append(len(cands))
        TM, pads, cur, exhausted = list(T), [], len(render(T)), True
        for h in cands:
            nxt = len(render(TM + [h]))
            if abs(nxt - target) < abs(cur - target):
                TM.append(h); pads.append(h); cur = nxt
            else:
                exhausted = False
                break
        if exhausted and cur < target:
            short.append(iid)
        pads_n += len(pads)
        pad_low += sum(1 for h in pads if h["rank"] <= 12)
        pad_in_on += sum(1 for h in pads if h["file"] in on_files)
        rank_sum += [h["rank"] for h in pads]
        out[iid]["TM"] = {"pack": render(TM), "files": sorted({h["file"] for h in TM}), "n_hits": len(TM)}
        ratios.append(len(out[iid]["TM"]["pack"]) / target)
        log[iid] = [{"file": h["file"], "line": h["line"], "rank": h["rank"]} for h in pads]
    # identity assertion for ON/OFF/T/P on every instance
    for iid, arms in b1.items():
        for a in ("ON", "OFF", "T", "P"):
            if a in arms:
                assert json.dumps(arms[a], sort_keys=True) == json.dumps(out[iid][a], sort_keys=True), (iid, a)
        assert set(arms) == set(out[iid]), iid
    n = len(t_ids)
    rs = sorted(rank_sum)
    chk = {"n": n, "mean_ratio": round(sum(ratios) / n, 4),
           "within_10pct": round(sum(1 for r in ratios if 0.9 <= r <= 1.1) / n, 4),
           "pads_per_inst": round(pads_n / n, 2), "pads_total": pads_n,
           "cands_per_inst_mean": round(sum(cands_n) / n, 1), "cands_min": min(cands_n),
           "short": short, "pads_in_files_ON": pad_in_on,
           "pads_rank_le12": pad_low, "pads_rank_le12_share": round(pad_low / pads_n, 3),
           "pad_rank_mean": round(sum(rs) / len(rs), 1), "pad_rank_median": rs[len(rs) // 2]}
    print(json.dumps(chk, indent=1))
    expect = {"mean_ratio": 0.9997, "within_10pct": 1.0, "pads_per_inst": 7.25, "cands_per_inst_mean": 35.1,
              "cands_min": 7, "short": ["psf__requests-5414"], "pads_in_files_ON": 0}
    bad = {k: (chk[k], v) for k, v in expect.items() if chk[k] != v}
    if bad:
        print("STOP: does not reproduce ruling (c) row:", bad); return 3
    data = json.dumps(out, indent=1).encode("utf-8")
    (P / "b1b3_packs_b2.json").write_bytes(data)
    (P / "b1b3" / "tm_c_build.json").write_text(json.dumps({"check": chk, "pads": log}), encoding="utf-8")
    print(f"wrote b1b3_packs_b2.json sha256={hashlib.sha256(data).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
