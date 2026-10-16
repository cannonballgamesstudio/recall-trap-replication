"""Task 2: TOST equivalence for T-ON (both models), margin +-3pp; sensitivity margin 0.4*G.
90% CIs, instance-paired (Wald, paired SE) and wild-cluster (WCR Webb, inversion at alpha=0.10).
TOST at level 0.05 <=> 90% CI inside (-m, +m). Also: m* = smallest margin that would pass.
Same 'not detected; CI' treatment for the agentic nulls and the fusion x dense interaction.
"""
import math

from scipy import stats

from ra2 import arm, paired, did, dvec, VIOL, pp, ci, fp, write_md, dump


def tost_inst(est, se, m):
    p_lo = stats.norm.sf((est + m) / se)   # H0: delta <= -m
    p_hi = stats.norm.sf((m - est) / se)   # H0: delta >= +m
    return max(p_lo, p_hi)


def verdict(ci90, m):
    return "PASS (equivalent)" if (ci90[0] > -m and ci90[1] < m) else "fail"


rows = []


def t_row(model, on, off, T):
    A_on, A_off, A_T = arm(on), arm(off), arm(T)
    ids = (A_on.sub & A_off.sub & A_T.sub) - set(VIOL)
    G = paired(ids, A_off.res, A_on.res, "G", cluster=False)
    t = paired(ids, A_T.res, A_on.res, "T-ON", alpha_wild=(0.10, 0.05))
    return dict(model=model, contrast="T−ON (trim)", Gref=G["delta"], **t)


rows.append(t_row("gpt-5.6-sol (discovery-draw refs, Table V)", "gpt_hl_ON", "gpt_hl_OFF", "gpt_T"))
rows.append(t_row("gpt-5.6-sol (logged re-run refs)", "gpt_lr_ON", "gpt_lr_OFF", "gpt_T"))
rows.append(t_row("Qwen3-Coder-30B (Table V)", "qc_ON", "qc_OFF", "qc_T"))

# agentic nulls (OFF-ON), pairwise attempted
for lab, on, off in (("agentic sonnet-5, fusion", "ag_fus_ON", "ag_fus_OFF"),
                     ("agentic sonnet-5, dense", "ag_dense_ON", "ag_dense_OFF")):
    A_on, A_off = arm(on), arm(off)
    ids = A_on.sub & A_off.sub
    r = paired(ids, A_off.res, A_on.res, "OFF-ON", alpha_wild=(0.10, 0.05))
    rows.append(dict(model=lab, contrast="OFF−ON", Gref=None, **r))

# fusion x dense interaction (instance-paired DiD on the overlap)
hl_on, hl_off, lr_on, lr_off = arm("gpt_hl_ON"), arm("gpt_hl_OFF"), arm("gpt_lr_ON"), arm("gpt_lr_OFF")
de_on, de_off = arm("gpt_dense_ON"), arm("gpt_dense_OFF")
d_hl = dvec(hl_on.sub & hl_off.sub, hl_off.res, hl_on.res)
d_lr = dvec(lr_on.sub & lr_off.sub, lr_off.res, lr_on.res)
d_de = dvec(de_on.sub & de_off.sub, de_off.res, de_on.res)
ix = []
for lab, dA in (("fusion(discovery draw) − dense", d_hl), ("fusion(logged re-run) − dense", d_lr)):
    r = did(set(dA) & set(d_de), dA, d_de, lab)
    ix.append(r)

L = ["## Task 2 — TOST equivalence (α = 0.05 per side ⇔ 90% CI inside ±m)", "",
     "Primary margin m = ±3pp; sensitivity margin m = 0.4·G, with G = OFF−ON on the same 473 for that model and reference pair. "
     "m* = smallest symmetric margin the 90% CI would pass. Instance = Wald paired SE; wild = WCR Webb B=9,999 inverted at α=0.10 on a 0.05pp grid (G=12).", "",
     "| model / refs | contrast | n | Δ | b/c | inst. 90% CI | wild 90% CI | TOST p (inst., ±3) | ±3pp: inst. / wild | 0.4·G | 0.4·G: inst. / wild | m* inst. / wild |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    m1 = 0.03
    tp = tost_inst(r["delta"], r["inst_se"], m1)
    mstar_i = max(abs(r["inst_ci90"][0]), abs(r["inst_ci90"][1]))
    mstar_w = max(abs(r["wild_ci90"][0]), abs(r["wild_ci90"][1]))
    if r["Gref"] is not None:
        m2 = 0.4 * r["Gref"]
        sens = f"{100*m2:.2f} | {verdict(r['inst_ci90'], m2)} / {verdict(r['wild_ci90'], m2)}"
    else:
        sens = "— | —"
    r.update(tost_p_inst_3=tp, mstar_inst=mstar_i, mstar_wild=mstar_w)
    L.append(f"| {r['model']} | {r['contrast']} | {r['n']} | {pp(r['delta'], 2)} | {r['b']}/{r['c']} | {ci(r['inst_ci90'], 2)} | {ci(r['wild_ci90'], 2)} | "
             f"{fp(tp)} | {verdict(r['inst_ci90'], m1)} / {verdict(r['wild_ci90'], m1)} | {sens} | {100*mstar_i:.2f} / {100*mstar_w:.2f} |")
L.append("")
L.append("95% CIs for the same rows (\"not detected; CI\" wording):")
L.append("")
L.append("| model / refs | contrast | Δ | McNemar p | inst. 95% CI | wild 95% CI | wild p | CR2 95% CI | flip p |")
L.append("|---|---|---|---|---|---|---|---|---|")
for r in rows:
    L.append(f"| {r['model']} | {r['contrast']} | {pp(r['delta'], 2)} | {fp(r['mcnemar_p'])} | {ci(r['inst_ci95'], 2)} | {ci(r['wild_ci95'], 2)} | {fp(r['wild_p'])} | {ci(r['cr2_ci95'], 2)} | {fp(r['flip_p'])} |")
L.append("")
L.append("Fusion × dense interaction (instance-paired DiD of OFF−ON on instances paired in both arms):")
L.append("")
L.append("| interaction | n | Δ | inst. 95% CI | inst. p | inst. 90% CI | wild 95% CI | wild 90% CI | wild p | CR2 95% CI | CR2 p | flip p | ±3pp TOST (inst./wild) | m* inst./wild |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for r in ix:
    mi = max(map(abs, r["inst_ci90"])); mw = max(map(abs, r["wild_ci90"]))
    r.update(mstar_inst=mi, mstar_wild=mw)
    L.append(f"| {r['label']} | {r['n']} | {pp(r['delta'], 2)} | {ci(r['inst_ci95'], 2)} | {fp(r['inst_p'])} | {ci(r['inst_ci90'], 2)} | {ci(r['wild_ci95'], 2)} | "
             f"{ci(r['wild_ci90'], 2)} | {fp(r['wild_p'])} | {ci(r['cr2_ci95'], 2)} | {fp(r['cr2_p'])} | {fp(r['flip_p'])} | "
             f"{verdict(r['inst_ci90'], 0.03)} / {verdict(r['wild_ci90'], 0.03)} | {100*mi:.2f} / {100*mw:.2f} |")
L.append("")
write_md("t2_tost", "\n".join(L) + "\n")
dump("t2_tost", {"rows": rows, "interaction": ix})
