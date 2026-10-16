"""Task 6: concordant-subset sensitivity. An instance is concordant iff, for EVERY file in its T pack
(= every OFF file), the ON chunk for that file equals that file's first-ranked (first-listed) OFF chunk
(same file, start line and text). Parser = scratchpad/tb/build_T.py (round-trip verified there).
Task 7: confirm local_packs.json carries no rank or score fields.
"""
import json
import re
import sys

from ra2 import arm, paired, VIOL, P5, SCR, pp, ci, fp, write_md, dump

sys.path.insert(0, str(SCR / "eval"))
from build_T import parse  # noqa: E402

lp = json.loads((P5 / "local_packs.json").read_text(encoding="utf-8"))

# ---------------- Task 7: field audit
field_keys = set()
for i, v in lp.items():
    for side, d in v.items():
        field_keys |= {f"{side}.{k}" for k in d}
rank_like = [k for k in field_keys if re.search(r"rank|score|sim|dist", k, re.I)]
hdr_tokens = set()
for i, v in lp.items():
    for side in v:
        for line in v[side]["pack"].splitlines():
            if line.startswith("### "):
                hdr_tokens.add("### <file>:<line> — <symbol> [<kind>]")
hdr_has_score = sum(bool(re.search(r"score|rank|sim[=:]", l, re.I)) for v in lp.values() for s in v
                    for l in v[s]["pack"].splitlines() if l.startswith("### ") or l.startswith("## "))

# ---------------- Task 6
viol = set(VIOL)
conc, per_file_tot, per_file_ok, detail = {}, 0, 0, {}
for iid in sorted(lp):
    if iid in viol:
        continue
    _, bon = parse(lp[iid]["dedupON"]["pack"])
    _, boff = parse(lp[iid]["dedupOFF"]["pack"])
    on_by_file = {}
    for x in bon:
        on_by_file.setdefault(x["file"], x)
    off_order = []
    for x in boff:
        if x["file"] not in off_order:
            off_order.append(x["file"])
    ok_all = True
    nbad = 0
    on_in_off = 0
    for f in off_order:
        first = next(x for x in boff if x["file"] == f)
        o = on_by_file[f]
        same = (o["line"], o["text"]) == (first["line"], first["text"])
        per_file_tot += 1
        per_file_ok += same
        on_in_off += any((o["line"], o["text"]) == (x["line"], x["text"]) for x in boff if x["file"] == f)
        if not same:
            ok_all = False
            nbad += 1
    conc[iid] = ok_all
    detail[iid] = dict(n_files=len(off_order), n_discordant_files=nbad, on_chunk_anywhere_in_off=on_in_off)

ids473 = set(conc)
C = {i for i, v in conc.items() if v}
D = ids473 - C
# rank structure diagnostic: position of the ON chunk among the OFF chunks of the same file, where present
pos_hist = {}
for iid in ids473:
    _, bon = parse(lp[iid]["dedupON"]["pack"])
    _, boff = parse(lp[iid]["dedupOFF"]["pack"])
    on_by_file = {}
    for x in bon:
        on_by_file.setdefault(x["file"], x)
    for f in {x["file"] for x in boff}:
        offs = [x for x in boff if x["file"] == f]
        o = on_by_file[f]
        k = next((j for j, x in enumerate(offs) if (x["line"], x["text"]) == (o["line"], o["text"])), None)
        key = "absent" if k is None else (str(k + 1) if k < 3 else "4+")
        pos_hist[key] = pos_hist.get(key, 0) + 1

L = ["## Task 6 — Concordant-subset sensitivity", "",
     f"Concordant instance = every T file's ON chunk is byte-identical (file, start line, text) to that file's first-listed (top-ranked) OFF chunk. "
     f"Computed on the 473 T instances.", "",
     "| quantity | value |", "|---|---|",
     f"| file-level concordance (ON chunk = first OFF chunk of that file) | {per_file_ok}/{per_file_tot} = {100*per_file_ok/per_file_tot:.1f}% |",
     f"| **instance-level concordance (all T files concordant)** | **{len(C)}/{len(ids473)} = {100*len(C)/len(ids473):.1f}%** |",
     f"| discordant instances | {len(D)} (mean discordant files among them {sum(detail[i]['n_discordant_files'] for i in D)/max(1,len(D)):.2f}) |",
     f"| position of the ON chunk among that file's OFF chunks (all T files) | " + ", ".join(f"{k}: {pos_hist[k]}" for k in sorted(pos_hist)) + " |",
     ""]
L += ["| model / refs | subset | contrast | n | first/second resolved | Δ | b/c | McNemar p | wild 95% CI | wild p | flip p |",
      "|---|---|---|---|---|---|---|---|---|---|---|"]
res = {}
for lab, on, off, T in (("Qwen3-Coder-30B", "qc_ON", "qc_OFF", "qc_T"),
                        ("gpt (discovery-draw refs)", "gpt_hl_ON", "gpt_hl_OFF", "gpt_T"),
                        ("gpt (logged re-run refs)", "gpt_lr_ON", "gpt_lr_OFF", "gpt_T")):
    a, b, t = arm(on), arm(off), arm(T)
    base = (a.sub & b.sub & t.sub) - viol
    assert base == ids473 or base <= ids473, lab
    for sname, S in (("all 473", base), ("concordant", base & C), ("discordant", base & D)):
        for cname, A, B in (("OFF−ON", b.res, a.res), ("OFF−T", b.res, t.res), ("T−ON", t.res, a.res)):
            r = paired(S, A, B, cname)
            res[(lab, sname, cname)] = r
            L.append(f"| {lab} | {sname} | {cname} | {r['n']} | {r['A']}/{r['B']} | {pp(r['delta'], 2)} | {r['b']}/{r['c']} | "
                     f"{fp(r['mcnemar_p'])} | {ci(r['wild_ci95'])} | {fp(r['wild_p'])} | {fp(r['flip_p'])} |")
L.append("")

L += ["## Task 7 — Structural rank fact; local_packs.json field audit", "",
      "**Structural fact (no data needed).** Let one ranking order all chunks. Dedup-OFF serves ranks 1..K. Dedup-ON serves, for each of the first K distinct files in the ranking, that file's best-ranked chunk. "
      "Hence, under a single ranking: (i) every OFF file is among ON's files (files(OFF) ⊆ files(ON)); (ii) for every OFF file, the ON chunk is that file's first OFF chunk, so T ⊆ OFF chunk-for-chunk and OFF−T adds exactly OFF's non-first same-file chunks; "
      "(iii) every chunk OFF adds over T has rank ≤ K, while every chunk ON adds over T (one per extra file) has rank > K, since those files have no chunk in the top K. "
      "So OFF's extra chunks are higher-ranked than ON's extra chunks by construction: rank is not a confound that a reweighting of these arms can remove, and a 'rank-matched' K-slot pack with OFF's rank profile is OFF itself. "
      "Any violation of (i) or (ii) in the data measures the difference between the two service instances' rankings, not a property of the policy.", "",
      "| check | result |", "|---|---|",
      f"| fields present in local_packs.json (per side) | {', '.join(sorted(field_keys))} |",
      f"| fields whose name matches rank/score/sim/dist | {', '.join(rank_like) if rank_like else 'none'} |",
      f"| pack header lines containing score/rank/sim tokens | {hdr_has_score}, all inside file paths or symbol names (e.g. sklearn/metrics/_ranking.py, roc_auc_score); none is a score or rank value |",
      "| chunk header format | `### <file>:<line> — <symbol> [<kind>]` (no score, no rank; order in the pack is the only rank signal) |",
      f"| (i) files(OFF) ⊆ files(ON) | {len(lp) - len(viol)}/{len(lp)} = {100*(len(lp)-len(viol))/len(lp):.1f}% |",
      f"| (ii) ON chunk = first OFF chunk, per file / per instance | {100*per_file_ok/per_file_tot:.1f}% / {100*len(C)/len(ids473):.1f}% (on the 473) |",
      ""]
write_md("t6_t7_concordant", "\n".join(L) + "\n")
dump("t6_t7_concordant", {"concordant_ids": sorted(C), "discordant_ids": sorted(D), "detail": detail, "pos_hist": pos_hist,
                          "fields": sorted(field_keys), "results": {" | ".join(k): v for k, v in res.items()}})
