#!/usr/bin/env python3
"""LOCAL-B1B3-ADDENDUM-PREREG §3-§4: build ON/OFF/T/TM/P packs from b1b3_prov.json and run the gates.

CPU only. Reads work/p5/b1b3_prov.json (from b1b3_prefetch.py), renders with the
PINNED format_pack (code/eval/g_plane_prompts.py), writes
  b1b3_gates.json            gate + size + concordance + prefix report (always)
  b1b3_packs.json            arm keys ON, OFF, T, TM, P (only if gates 1 and 2 pass)
  b1b3_build_log.json        per-instance TM / P construction details
  b1b3_ids_all.txt / b1b3_ids_T.txt   instance sets for generation
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

PIN = Path(__file__).resolve().parents[1]   # code/eval (scripts/eval of the pinned revision)
sys.path.insert(0, str(PIN))
import g_plane_prompts as gp  # noqa: E402
assert str(Path(gp.__file__).resolve()).lower().startswith(str(PIN).lower()), gp.__file__

import os
P = Path(os.environ.get("B1B3_ROOT", Path(__file__).resolve().parents[3] / "work" / "p5"))
WORK = Path(os.environ.get("EVAL_ROOT", "<EVAL_ROOT>")) / "swebench"   # bare repo caches


def key(h):
    return (h["file"], h["line"], (h.get("snippet") or "").rstrip("\n"))


def render(hits):
    return gp.format_pack(hits, len(hits))


def snip(h):
    return (h.get("snippet") or "").rstrip("\n")


_src_cache: dict = {}


def source(repo, commit, f):
    k = (repo, commit, f)
    if k not in _src_cache:
        cache = WORK / (repo.replace("/", "__") + ".cache")
        r = subprocess.run(["git", "-C", str(cache), "show", f"{commit}:{f}"],   # works for bare and non-bare caches
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        _src_cache[k] = r.stdout if r.returncode == 0 else None
    return _src_cache[k]


def widen(h, target, src):
    """§3 P rule. Returns (hit, status)."""
    s0 = snip(h)
    if len(s0) >= target:
        return h, "unchanged_already_ge_target"
    if src is None:
        return h, "unlocated_no_source"
    occ, i = [], src.find(s0)
    while i != -1 and s0:
        occ.append(i)
        i = src.find(s0, i + 1)
    if not occ:
        return h, "unlocated_not_verbatim"
    # occurrence whose line is nearest the declared start line
    best = min(occ, key=lambda o: abs(src.count("\n", 0, o) + 1 - h["line"]))
    lines = src.split("\n")
    a = src.count("\n", 0, best)                      # 0-based first line
    b = src.count("\n", 0, best + len(s0) - 1)        # 0-based last line
    cur = "\n".join(lines[a:b + 1])
    turn_below = True
    while True:
        can_below, can_above = b + 1 < len(lines), a - 1 >= 0
        if not (can_below or can_above):
            break
        go_below = (turn_below and can_below) or not can_above
        nxt = lines[b + 1] if go_below else lines[a - 1]
        if len(cur) + 1 + len(nxt) > target:
            break
        if go_below:
            b += 1; cur = cur + "\n" + nxt
        else:
            a -= 1; cur = nxt + "\n" + cur
        turn_below = not turn_below
    out = dict(h)
    out["line"] = a + 1
    out["snippet"] = cur
    return out, ("widened" if len(cur) > len(s0) else "located_not_widened")


def main() -> int:
    prov = json.loads((P / "b1b3_prov.json").read_text(encoding="utf-8"))
    cells = {c["instance_id"]: c for c in json.loads((P / "instances_verified.json").read_text(encoding="utf-8"))}
    packs, blog = {}, {}
    n_all = 0
    subset_ok, violators = [], []
    ident_tot = ident_ok = 0
    conc_tot = conc_top = conc_any = 0
    prefix_eq = prefix_n = 0
    tm_pad_in_on = 0
    tm_short = []
    p_status: dict = {}
    sizes = {a: {"slots": [], "chars": []} for a in ("ON", "OFF", "T", "TM", "P")}
    tm_ratio, p_ratio = [], []
    missing = []
    for iid in sorted(cells):
        rec = prov.get(iid, {})
        if not all(q in rec for q in ("ON12", "OFF12", "ON48", "OFF48")):
            missing.append(iid); continue
        n_all += 1
        c = cells[iid]
        on, off, on48 = rec["ON12"]["hits"], rec["OFF12"]["hits"], rec["ON48"]["hits"]
        packs[iid] = {}
        for arm, hits in (("ON", on), ("OFF", off)):
            packs[iid][arm] = {"pack": render(hits), "files": sorted({h["file"] for h in hits if h.get("file")}),
                               "n_hits": len(hits)}
        on_files = [h["file"] for h in on]
        assert len(on_files) == len(set(on_files)), f"ON not deduped {iid}"
        on_by_file = {h["file"]: h for h in on}
        off_files = []
        for h in off:
            if h["file"] not in off_files:
                off_files.append(h["file"])
        # prefix consistency
        prefix_n += 1
        if [(h["file"], h["line"]) for h in on48[:12]] == [(h["file"], h["line"]) for h in on]:
            prefix_eq += 1
        # concordance over files(OFF) ∩ files(ON)
        for f in off_files:
            if f not in on_by_file:
                continue
            conc_tot += 1
            offs = [h for h in off if h["file"] == f]
            if key(offs[0]) == key(on_by_file[f]):
                conc_top += 1
            if any(key(x) == key(on_by_file[f]) for x in offs):
                conc_any += 1
        sizes["ON"]["slots"].append(len(on)); sizes["ON"]["chars"].append(len(packs[iid]["ON"]["pack"]))
        sizes["OFF"]["slots"].append(len(off)); sizes["OFF"]["chars"].append(len(packs[iid]["OFF"]["pack"]))
        if not set(off_files) <= set(on_by_file):
            violators.append({"instance_id": iid, "missing_files": [f for f in off_files if f not in on_by_file],
                              "gold_missing": [f for f in off_files if f not in on_by_file and f in c.get("gold_files", [])]})
            continue
        subset_ok.append(iid)
        # T
        T = [on_by_file[f] for f in off_files]
        on_keys = {key(h) for h in on}
        for h in T:
            ident_tot += 1
            ident_ok += key(h) in on_keys
        # TM
        target = len(packs[iid]["OFF"]["pack"])
        tfiles = set(off_files)
        cands = [h for h in on48 if h["rank"] >= 13 and h["file"] not in tfiles]
        TM, pads = list(T), []
        cur = len(render(TM))
        exhausted = True
        for h in cands:
            nxt = len(render(TM + [h]))
            if abs(nxt - target) < abs(cur - target):
                TM.append(h); pads.append(h); cur = nxt
            else:
                exhausted = False
                break
        if exhausted and cur < target:
            tm_short.append(iid)
        tm_pad_in_on += sum(1 for h in pads if h["file"] in on_by_file)
        # P
        Pk, pst = [], []
        for f in off_files:
            tgt = sum(len(snip(h)) for h in off if h["file"] == f)
            src = source(c["repo"], c["base_commit"], f)
            ph, st = widen(on_by_file[f], tgt, src)
            Pk.append(ph); pst.append({"file": f, "status": st, "target": tgt,
                                       "on_len": len(snip(on_by_file[f])), "p_len": len(snip(ph)), "p_line": ph["line"]})
            p_status[st] = p_status.get(st, 0) + 1
        for arm, hits in (("T", T), ("TM", TM), ("P", Pk)):
            packs[iid][arm] = {"pack": render(hits), "files": sorted({h["file"] for h in hits}), "n_hits": len(hits)}
            sizes[arm]["slots"].append(len(hits)); sizes[arm]["chars"].append(len(packs[iid][arm]["pack"]))
        tm_ratio.append(len(packs[iid]["TM"]["pack"]) / target)
        p_ratio.append(len(packs[iid]["P"]["pack"]) / target)
        blog[iid] = {"T_files": off_files, "TM_pads": [{"file": h["file"], "line": h["line"], "rank": h["rank"],
                                                        "score": h.get("score")} for h in pads],
                     "TM_chars": len(packs[iid]["TM"]["pack"]), "OFF_chars": target, "P": pst}

    mean = lambda xs: round(sum(xs) / len(xs), 3) if xs else None
    within = lambda xs: round(sum(1 for x in xs if 0.9 <= x <= 1.1) / len(xs), 4) if xs else None
    subset_rate = len(subset_ok) / n_all if n_all else 0.0
    ident_rate = ident_ok / ident_tot if ident_tot else 0.0
    gates = {
        "n_instances_with_all_queries": n_all, "missing_queries": missing,
        "gate1_subset": {"pass_n": len(subset_ok), "n": n_all, "rate": round(subset_rate, 4),
                         "threshold": 0.95, "PASS": subset_rate >= 0.95, "violators": violators},
        "gate2_chunk_identity_T": {"ok": ident_ok, "n": ident_tot, "rate": ident_rate, "PASS": ident_rate == 1.0},
        "concordance": {"n_files": conc_tot, "on_eq_top_off": conc_top,
                        "rate_top": round(conc_top / conc_tot, 4) if conc_tot else None,
                        "on_among_off": conc_any, "rate_any": round(conc_any / conc_tot, 4) if conc_tot else None},
        "sizes": {a: {"mean_slots": mean(v["slots"]), "mean_chars": mean(v["chars"]), "n": len(v["slots"])}
                  for a, v in sizes.items()},
        "TM_over_OFF_chars": {"mean": mean(tm_ratio), "share_within_10pct": within(tm_ratio),
                              "n_ran_out_of_candidates": len(tm_short), "ran_out": tm_short},
        "P_over_OFF_chars": {"mean": mean(p_ratio), "share_within_10pct": within(p_ratio)},
        "P_file_status_counts": p_status,
        "prefix_consistency": {"on48_top12_eq_on12": prefix_eq, "n": prefix_n,
                               "rate": round(prefix_eq / prefix_n, 4) if prefix_n else None,
                               "tm_pad_files_in_files_ON": tm_pad_in_on},
    }
    (P / "b1b3_gates.json").write_text(json.dumps(gates, indent=1), encoding="utf-8")
    (P / "b1b3_build_log.json").write_text(json.dumps(blog), encoding="utf-8")
    g1, g2 = gates["gate1_subset"]["PASS"], gates["gate2_chunk_identity_T"]["PASS"]
    print(json.dumps({k: v for k, v in gates.items() if k not in ("missing_queries",)}, indent=1)[:6000])
    if not (g1 and g2):
        print("STOP: gate failed -> packs NOT written"); return 3
    # ON/OFF for all; T/TM/P only for subset-passing instances (built above only for those)
    dest = P / "b1b3_packs.json"
    data = json.dumps(packs, indent=1).encode("utf-8")
    dest.write_bytes(data)
    (P / "b1b3_ids_all.txt").write_text("\n".join(sorted(packs)) + "\n", encoding="utf-8")
    (P / "b1b3_ids_T.txt").write_text("\n".join(sorted(subset_ok)) + "\n", encoding="utf-8")
    print(f"wrote {dest} sha256={hashlib.sha256(data).hexdigest()}  all={len(packs)} T-set={len(subset_ok)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
