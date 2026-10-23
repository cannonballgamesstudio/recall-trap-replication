"""Analysis 5 (POST HOC): practitioner baseline P.
(a) Same-seed contrasts: P (seed 0, its only seed) against OFF seed 0 and T seed 0, instead of against the 3-seed means.
(b) Pack sizes in characters from the released packs: the SERVED P/TM packs are those in b1b3_packs_b2.json
    (gen_b2.cmd / gen_b3.cmd pass --packs-file b1b3_packs_b2.json); the superseded first build (b1b3/b1b3_packs_build1.json
    in the original run directory, not in the package) is read only to locate the 4,972 figure.
"""
import json
import os
import statistics as st
from pathlib import Path

import numpy as np

from common3 import arm, dvec, repo, P5, all_methods, pp, ci, fp, write_md, dump

T_IDS = sorted(set((P5 / "b1b3_ids_T.txt").read_text(encoding="utf-8").split()))
S8475 = "sphinx-doc__sphinx-8475"
out = {"same_seed": [], "sizes": {}}
L = ["## Analysis 5 — Practitioner baseline P (POST HOC)", "",
     "### (a) Same-seed contrasts (seed 0 only; P has one seed)", "",
     "The paper's Table VI P rows compare P's single seed with the 3-seed mean of OFF/T. Here P seed 0 is compared with OFF seed 0 and T seed 0 on the same instances.", "",
     "| contrast | n | rates A / B | Δ (pp) | b/c | McNemar p | iid 95% CI | wild 95% CI; p | CR2 95% CI; p | flip p | pct-cluster 95% CI |",
     "|---|---|---|---|---|---|---|---|---|---|---|"]
for mode, base in (("scored primary", T_IDS), ("exclude", [i for i in T_IDS if i != S8475])):
    for A, B in (("P", "OFF"), ("P", "T"), ("P", "ON"), ("OFF", "T")):
        a, b = arm(f"b_{A}_s0"), arm(f"b_{B}_s0")
        d, ids = dvec(base, a.res, b.res)
        r = all_methods(d, ids, f"{A}−{B} seed 0, {mode}")
        r["rate_A"], r["rate_B"] = float(np.mean([i in a.res for i in ids])), float(np.mean([i in b.res for i in ids]))
        out["same_seed"].append(r)
        L.append(f"| {r['label']} | {r['n']} | {100*r['rate_A']:.2f}% / {100*r['rate_B']:.2f}% | {pp(r['delta'], 2)} | {r['b']}/{r['c']} | {fp(r['mcnemar_p'])} | "
                 f"{ci(r['iid']['ci95'], 2)} | {ci(r['wild']['ci95'], 2)}; {fp(r['wild']['p'])} | {ci(r['cr2']['ci95'], 2)}; {fp(r['cr2']['p'])} | {fp(r['flip']['p'])} | {ci(r['pct']['ci95'], 2)} |")
L.append("")

# ---------------- sizes
packs = json.loads((P5 / "b1b3_packs_b2.json").read_text(encoding="utf-8"))
packs1 = json.loads((P5 / "b1b3_packs.json").read_text(encoding="utf-8"))
build1 = Path(os.environ.get("RA3_BUILD1", "work/unreleased/b1b3_packs_build1.json"))  # superseded build, not released
pb1 = json.loads(build1.read_text(encoding="utf-8")) if build1.exists() else None


def sizes(pk, arms=("ON", "OFF", "T", "TM", "P"), ids=T_IDS):
    s = {}
    for a in arms:
        L_ = [len(pk[i][a]["pack"]) for i in ids]
        s[a] = dict(mean_chars=st.mean(L_), median_chars=st.median(L_), mean_slots=st.mean(pk[i][a]["n_hits"] for i in ids), n=len(ids))
    return s


S = sizes(packs)
S_all = sizes(packs, arms=("ON", "OFF"), ids=sorted(packs))
ratio = lambda num, den: dict(ratio_of_means=S[num]["mean_chars"] / S[den]["mean_chars"],
                              mean_of_ratios=st.mean(len(packs[i][num]["pack"]) / len(packs[i][den]["pack"]) for i in T_IDS),
                              median_of_ratios=st.median(len(packs[i][num]["pack"]) / len(packs[i][den]["pack"]) for i in T_IDS))
R = {"P/OFF": ratio("P", "OFF"), "P/T": ratio("P", "T"), "P/ON": ratio("P", "ON"), "TM/OFF": ratio("TM", "OFF"), "T/OFF": ratio("T", "OFF")}
out["sizes"] = dict(served_b2_on_478=S, served_b2_ON_OFF_all500=S_all, ratios=R,
                    b1b3_packs_json_on_478=sizes(packs1), build1_on_478=(sizes(pb1) if pb1 else None),
                    identical_P_b2_vs_packs=all(packs[i]["P"]["pack"] == packs1[i]["P"]["pack"] for i in T_IDS),
                    identical_TM_b2_vs_packs=all(packs[i]["TM"]["pack"] == packs1[i]["TM"]["pack"] for i in T_IDS))
L += ["### (b) Pack sizes from the released packs (characters of the rendered pack; 478 gate-passing instances unless stated)", "",
      "| arm | served pack file | mean slots | mean chars | median chars |", "|---|---|---|---|---|"]
for a in ("ON", "OFF", "T", "TM", "P"):
    L.append(f"| {a} | b1b3_packs_b2.json (served) | {S[a]['mean_slots']:.2f} | {S[a]['mean_chars']:,.0f} | {S[a]['median_chars']:,.0f} |")
L.append(f"| ON / OFF, all 500 | b1b3_packs_b2.json | {S_all['ON']['mean_slots']:.2f} / {S_all['OFF']['mean_slots']:.2f} | {S_all['ON']['mean_chars']:,.0f} / {S_all['OFF']['mean_chars']:,.0f} | |")
p1 = out["sizes"]["b1b3_packs_json_on_478"]
L.append(f"| TM (pre-ruling, never generated) | b1b3_packs.json | {p1['TM']['mean_slots']:.2f} | {p1['TM']['mean_chars']:,.0f} | |")
if pb1:
    b1 = out["sizes"]["build1_on_478"]
    L.append(f"| P (superseded first build, never generated; 326 P files unread) | <unreleased>/b1b3/b1b3_packs_build1.json | {b1['P']['mean_slots']:.2f} | **{b1['P']['mean_chars']:,.0f}** | |")
L += ["", f"P pack identical in b1b3_packs_b2.json and b1b3_packs.json: {out['sizes']['identical_P_b2_vs_packs']}; TM identical: {out['sizes']['identical_TM_b2_vs_packs']}.", "",
      "| ratio | ratio of means | mean of per-instance ratios | median of per-instance ratios |", "|---|---|---|---|"]
for k, v in R.items():
    L.append(f"| {k} | {v['ratio_of_means']:.3f} | {v['mean_of_ratios']:.3f} | {v['median_of_ratios']:.3f} |")
L.append("")
write_md("s5_practitioner", "\n".join(L) + "\n")
dump("s5_practitioner", out)
