"""Task 10: numeric fixes.
(a) fusion x dense +2.6: decomposition, and the version against the logged re-run.
(b) fusion x BM25 against the logged re-run (expected ~ +8.6).
(c) gpt logged re-run wild CI: inversion on a 0.01pp grid, several seeds / B.
(d) Which Qwen3-Coder K=12 ON/OFF run feeds which table: fingerprint each candidate pair
    (rates, b/c, fix-locality cells, anchor-class B->C cell) against the paper's printed values.
"""
import json
import sys

import numpy as np

from ra2 import arm, paired, did, dvec, wild_pfun, repo, P5, cra, pp, ci, fp, write_md, dump

sys.path.insert(0, str(__import__("ra2").PKG / "code" / "eval"))
import contam_common as cc  # noqa: E402

out = {}
L = ["## Task 10 — Numeric fixes", ""]

# ---------------- (a)/(b) interactions
hl_on, hl_off, lr_on, lr_off = arm("gpt_hl_ON"), arm("gpt_hl_OFF"), arm("gpt_lr_ON"), arm("gpt_lr_OFF")
de_on, de_off, bm_on, bm_off = arm("gpt_dense_ON"), arm("gpt_dense_OFF"), arm("gpt_bm25_ON"), arm("gpt_bm25_OFF")
d_hl = dvec(hl_on.sub & hl_off.sub, hl_off.res, hl_on.res)
d_lr = dvec(lr_on.sub & lr_off.sub, lr_off.res, lr_on.res)
d_de = dvec(de_on.sub & de_off.sub, de_off.res, de_on.res)
d_bm = dvec(bm_on.sub & bm_off.sub, bm_off.res, bm_on.res)
mean = lambda d, ids: 100 * np.mean([d[i] for i in ids])
L += ["(a)/(b) Retriever interactions = instance-paired DiD of OFF−ON on instances paired in both arms (n=494 with dense: dense has 3 never-submitted per side; n=500 with BM25).", "",
      "| interaction | n | fusion Δ on these n | other Δ on these n | marginal difference (Table II Δs) | DiD Δ | inst. 95% CI; p | wild 95% CI; p | CR2 95% CI; p | flip p |",
      "|---|---|---|---|---|---|---|---|---|---|"]
for lab, dA, dB, margA, margB in (("fusion(discovery) × dense", d_hl, d_de, 7.60, 5.67), ("fusion(logged re-run) × dense", d_lr, d_de, 5.40, 5.67),
                                  ("fusion(discovery) × BM25", d_hl, d_bm, 7.60, -3.20), ("fusion(logged re-run) × BM25", d_lr, d_bm, 5.40, -3.20),
                                  ("dense × BM25", d_de, d_bm, 5.67, -3.20)):
    ids = sorted(set(dA) & set(dB))
    r = did(ids, dA, dB, lab)
    out[lab] = r
    L.append(f"| {lab} | {r['n']} | {mean(dA, ids):+.2f} | {mean(dB, ids):+.2f} | {margA - margB:+.2f} | {pp(r['delta'], 2)} | {ci(r['inst_ci95'])}; {fp(r['inst_p'])} | "
             f"{ci(r['wild_ci95'])}; {fp(r['wild_p'])} | {ci(r['cr2_ci95'])}; {fp(r['cr2_p'])} | {fp(r['flip_p'])} |")
excl = sorted(set(d_hl) - set(d_de))
L.append("")
L.append(f"Explanation of +2.6: the 6 instances excluded by the dense arm's never-submitted ({', '.join(excl)}) carry fusion-discovery d = "
         f"{[d_hl[i] for i in excl]}; on the remaining 494 the fusion discovery Δ is {mean(d_hl, sorted(set(d_hl)&set(d_de))):+.2f}pp (not +7.60), so the paired DiD is "
         f"{mean(d_hl, sorted(set(d_hl)&set(d_de))):+.2f} − {mean(d_de, sorted(set(d_hl)&set(d_de))):+.2f} = {out['fusion(discovery) × dense']['delta']*100:+.2f}pp, while Table II's marginal Δs differ by only 7.60 − 5.67 = +1.93.")
L.append("")

# ---------------- (c) re-run wild CI
ids = sorted(lr_on.sub & lr_off.sub)
d = np.array([d_lr[i] for i in ids], float)
cl = [repo(i) for i in ids]
L += ["(c) gpt logged re-run (n=500, +5.40pp): WCR wild-cluster CI by test inversion on a 0.01pp grid (Webb, CR1 t).", "",
      "| seed | B | wild p | 95% CI (0.01pp grid) | pieces | 90% CI |", "|---|---|---|---|---|---|"]
grid = np.arange(-0.10, 0.25, 0.0001)
curves = {}
import os
SEEDS = ((20261014, 9999), (20261014, 99999), (1, 99999), (2, 99999), (3, 99999)) if not os.environ.get("FAST") else ((20261014, 9999),)
for seed, B in SEEDS:
    pval, est = wild_pfun(d, cl, B=B, seed=seed)
    ps = np.array([pval(b) for b in grid])
    if seed == 20261014 and B == 9999:
        curves["paper"] = ps
    acc = grid[ps > 0.05]
    idx = np.where(ps > 0.05)[0]
    acc90 = grid[ps > 0.10]
    pieces = 1 + int((np.diff(idx) > 1).sum())
    out[f"wild seed={seed} B={B}"] = dict(p=pval(0.0), lo=float(acc.min()), hi=float(acc.max()), pieces=pieces,
                                          lo90=float(acc90.min()), hi90=float(acc90.max()))
    L.append(f"| {seed} | {B:,} | {pval(0.0):.4f} | [{100*acc.min():+.2f}, {100*acc.max():+.2f}] | {pieces} | [{100*acc90.min():+.2f}, {100*acc90.max():+.2f}] |")
# shape diagnostic
ps = curves["paper"]
sel = [0.025, 0.030, 0.031, 0.032, 0.033, 0.035, 0.040, 0.054, 0.08, 0.10, 0.11, 0.113, 0.115, 0.12]
L.append("")
L.append("p(δ0) along the grid (seed 20261014, B=9,999): " + ", ".join(f"{100*x:.1f}pp→{ps[int(round((x+0.10)/0.0001))]:.3f}" for x in sel))
cr1 = cra.cr2_bm(d, cl)
S_y, n = cra._cluster_sums(d, cl)
lab_ = sorted(set(cl))
share = {lab_[k].split('/')[1]: (int(n[k]), int(S_y[k])) for k in range(len(lab_))}
L.append("")
L.append(f"Why asymmetric: the bootstrap-t null distribution is re-generated at each δ0 from restricted residuals d−δ0, and with 12 clusters of very unequal size (django n={share['django'][0]}, "
         f"cluster sums of d: " + ", ".join(f"{k} {v[1]:+d}/{v[0]}" for k, v in share.items()) + "), the studentized statistic's distribution is not symmetric in δ0: "
         "below the estimate the p-curve drops from >0.3 to <0.05 within ~1pp (δ0 between +3.2 and +4.0), above it decays slowly. The asymmetry is genuine, not a bisection artefact: "
         "the fine grid, five seeds and B up to 99,999 reproduce [+3.2, +11.3] to within MC error, and the acceptance region is a single interval.")
L.append("")

# ---------------- (d) Qwen3-Coder K=12 pairs
gold = json.loads((P5 / "gold_patches.json").read_text(encoding="utf-8"))
packs = json.loads((P5 / "local_packs.json").read_text(encoding="utf-8"))
cls = {i: cc.anchor_class(gold[i], packs[i]["dedupON"]["pack"]) + ">" + cc.anchor_class(gold[i], packs[i]["dedupOFF"]["pack"]) for i in packs}
nfile = {i: len(cc.gold_files(gold[i])) for i in gold}
cands = [("qwen30b_*_rg (local GGUF, regraded)", "qc_ON", "qc_OFF"), ("qwen3or_k12 (OpenRouter, budget sweep)", "qor_k12_ON", "qor_k12_OFF"),
         ("coder30b_c12k (local, 12k ctx)", "c12k_ON", "c12k_OFF"), ("local_dedup (87-instance pilot)", "qc87_ON", "qc87_OFF")]
L += ["(d) Qwen3-Coder-30B-A3B K=12 ON/OFF candidates, fingerprinted against the paper's printed values.", "",
      "| pair (report files) | n | ON / OFF resolve | Δ; b/c; p | single-file: n, Δ, b/c | multi-file: n, Δ, b/c | B→C: n, Δ, b/c | error_instances ON/OFF |",
      "|---|---|---|---|---|---|---|---|"]
for lab, on, off in cands:
    a, b = arm(on), arm(off)
    ids = sorted(a.sub & b.sub)
    r = paired(ids, b.res, a.res, cluster=False)
    s1 = paired([i for i in ids if nfile[i] == 1], b.res, a.res, cluster=False)
    sm = paired([i for i in ids if nfile[i] > 1], b.res, a.res, cluster=False)
    bc = paired([i for i in ids if cls.get(i) == "B>C"], b.res, a.res, cluster=False)
    out["qc pair " + lab] = dict(all=r, single=s1, multi=sm, BC=bc, files=(a.file, b.file))
    L.append(f"| {lab}: {a.file} / {b.file} | {r['n']} | {100*r['B_rate']:.1f}% ({r['B']}) / {100*r['A_rate']:.1f}% ({r['A']}) | {pp(r['delta'], 1)}; {r['b']}/{r['c']}; {fp(r['mcnemar_p'])} | "
             f"{s1['n']}, {pp(s1['delta'])}, {s1['b']}/{s1['c']} | {sm['n']}, {pp(sm['delta'])}, {sm['b']}/{sm['c']} | {bc['n']}, {pp(bc['delta'])}, {bc['b']}/{bc['c']} | {a.n_err}/{b.n_err} |")
L += ["", "Anchor-transition table (paper Table VII, QC column: B→C +31.2 (26/1), B→B +0.4, C→C −5.7, A→A −1.7, B→A 0.0) recomputed for each full-500 candidate:", "",
      "| pair | B→C | B→B | C→C | A→A | B→A |", "|---|---|---|---|---|---|"]
for lab, on, off in cands[:3]:
    a, b = arm(on), arm(off)
    ids = sorted(a.sub & b.sub)
    cells = []
    for t in ("B>C", "B>B", "C>C", "A>A", "B>A"):
        r = paired([i for i in ids if cls.get(i) == t], b.res, a.res, cluster=False)
        cells.append(f"{pp(r['delta'])} ({r['b']}/{r['c']}, n={r['n']})")
    L.append(f"| {lab} | " + " | ".join(cells) + " |")
L += ["", "Mapping to the paper (matched on printed values):", "",
      "| paper location | printed values | feeding pair |", "|---|---|---|",
      "| Table V (Arm T references), Fig. 1 caption | ON 7.0%, OFF 12.9% on the 473; G +5.9, 38/10 | qwen30b_{ON,OFF}_rg (M1 in inclusion table) |",
      "| §V within-file selection (random-chunk control) | 'own ON and OFF runs (6.6%, 12.4%)' | qwen30b_{ON,OFF}_rg (33/500, 62/500) |",
      "| §V-D E5 (Branch B on Qwen3-Coder), Table VIII E5 OFF−ON rows | full +5.8; low +8.6 / high +3.6 | qwen30b_{ON,OFF}_rg (contam_common.T_ARM) |",
      "| Table VIII E5 'K=4/12/40 Δlow (proxy M)' and §V-D proxy-M sentence | +3.2 / +7.7 / +7.2 | qwen3or_k{4,12,40} (contam_common.ARMS['qwen3coder']) |",
      "| §RQ2 Budget K (exploratory Qwen3-Coder sweep) | +2.0 (26/16), +4.2 (33/12), +6.2 (42/11); 'budget sweep's (7.4%, 11.6%)' | qwen3or_k{4,12,40} |",
      "| Table MDE 'Qwen3-Coder-A3B K=4' | 500, +2.0, 26/16 | qwen3or_k4 |",
      "| Fix locality (§RQ2 'six arms'; earlier t3 row 'Qwen3-Coder-30B-A3B' 429, +6.3, 37/10 / 71, +2.8, 2/0) | single +6.3 (37/10), multi +2.8 (2/0) | qwen30b_{ON,OFF}_rg |",
      "| **Anchor table (Table VII) QC column** | **B→C +31.2 (26/1)** | **qwen3or_k12 (OpenRouter budget-sweep pair), NOT the local pair that feeds Table V / E5 (local pair gives B→C +30.0, 24/0)** |",
      "| coder30b_c12k pair (35/59) | — | not cited in v2 main.tex (no printed value matches); earlier Gate-1/cap2 program |", ""]
write_md("t10_numeric", "\n".join(L) + "\n")
dump("t10_numeric", out)
