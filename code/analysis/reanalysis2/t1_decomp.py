"""Task 1: gpt decomposition against the pre-registered LOGGED RE-RUN on the same 473 instances.
Task 12: T-ON 95% CIs (gpt, Qwen3-Coder). Also reproduces the paper's headline-draw decomposition.

Instance set = pairwise-attempted (ON & OFF & T submitted) minus the 27 subset-gate violators (= 473).
Rule (TRIMMED-BREADTH-PREREG §4): depth if share_depth >= 60% and McNemar p(OFF-T) < .05;
trim if share_trim >= 60% and McNemar p(T-ON) < .05; else 'both contribute / not resolved'.
"""
from ra2 import arm, paired, VIOL, pp, ci, fp, write_md, dump


def decomp(model, on, off, T):
    A_on, A_off, A_T = arm(on), arm(off), arm(T)
    ids = (A_on.sub & A_off.sub & A_T.sub) - set(VIOL)
    G = paired(ids, A_off.res, A_on.res, "G = OFF−ON", alpha_wild=(0.10, 0.05))
    D = paired(ids, A_off.res, A_T.res, "OFF−T (depth)", alpha_wild=(0.10, 0.05))
    Tr = paired(ids, A_T.res, A_on.res, "T−ON (trim)", alpha_wild=(0.10, 0.05))
    g = G["delta"]
    sd, st = D["delta"] / g, Tr["delta"] / g
    if sd >= 0.6 and D["mcnemar_p"] < 0.05:
        v = "depth carries the effect"
    elif st >= 0.6 and Tr["mcnemar_p"] < 0.05:
        v = "file trimming carries the effect"
    else:
        v = "both contribute; partition not resolved"
    return dict(model=model, n=len(ids), rows=[G, D, Tr], share_depth=sd, share_trim=st, verdict=v,
                identity=D["delta"] + Tr["delta"] - g, rates=(A_on, A_T, A_off))


res = {
    "gpt_rerun": decomp("gpt-5.6-sol, logged re-run refs", "gpt_lr_ON", "gpt_lr_OFF", "gpt_T"),
    "gpt_headline": decomp("gpt-5.6-sol, discovery-draw refs (paper Table V)", "gpt_hl_ON", "gpt_hl_OFF", "gpt_T"),
    "qwen3coder": decomp("Qwen3-Coder-30B (paper Table V)", "qc_ON", "qc_OFF", "qc_T"),
}

L = ["## Task 1 — gpt decomposition against the pre-registered logged re-run (same 473 instances)", "",
     "Same 473 instances as Table V (ON, OFF and T all submitted; 27 subset-gate violators removed). T is the same T draw in both gpt rows; only the ON/OFF reference arms change. Δ in pp; b/c = first-arm-only / second-arm-only wins; McNemar exact two-sided; wild = WCR Webb B=9,999 (G=12); CR2 = Bell–McCaffrey; flip = exact repository sign-flip (4,096 assignments).", "",
     "| reference arms | contrast | n | first/second resolved | Δ | b/c | McNemar p | wild 95% CI | wild p | CR2 p | flip p | share of G |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for key in ("gpt_rerun", "gpt_headline", "qwen3coder"):
    r = res[key]
    for row, sh in zip(r["rows"], (1.0, r["share_depth"], r["share_trim"])):
        L.append(f"| {r['model']} | {row['label']} | {row['n']} | {row['A']}/{row['B']} | "
                 f"{pp(row['delta'], 2)} | {row['b']}/{row['c']} | {fp(row['mcnemar_p'])} | {ci(row['wild_ci95'])} | {fp(row['wild_p'])} | "
                 f"{fp(row['cr2_p'])} | {fp(row['flip_p'])} | {100*sh:.0f}% |")
L.append("")
L.append("| reference arms | ON / T / OFF resolve on the 473 | depth share | trim share | identity check | 60%-rule verdict |")
L.append("|---|---|---|---|---|---|")
for key in ("gpt_rerun", "gpt_headline", "qwen3coder"):
    r = res[key]
    G = r["rows"][0]
    D = r["rows"][1]
    on_rate = G["B_rate"]; off_rate = G["A_rate"]; t_rate = D["B_rate"]
    L.append(f"| {r['model']} | {100*on_rate:.1f}% / {100*t_rate:.1f}% / {100*off_rate:.1f}% | {100*r['share_depth']:.1f}% | "
             f"{100*r['share_trim']:.1f}% | {pp(r['identity'], 3)} | {r['verdict']} |")
L.append("")

L.append("## Task 12 — T−ON 95% CIs (and 90% for reference)")
L.append("")
L.append("| model / refs | n | T−ON Δ | b/c | instance-paired 95% CI | wild-cluster 95% CI | CR2 95% CI | instance 90% CI | wild 90% CI |")
L.append("|---|---|---|---|---|---|---|---|---|")
for key in ("gpt_headline", "gpt_rerun", "qwen3coder"):
    t = res[key]["rows"][2]
    L.append(f"| {res[key]['model']} | {t['n']} | {pp(t['delta'], 2)} | {t['b']}/{t['c']} | {ci(t['inst_ci95'], 2)} | {ci(t['wild_ci95'], 2)} | "
             f"{ci(t['cr2_ci95'], 2)} | {ci(t['inst_ci90'], 2)} | {ci(t['wild_ci90'], 2)} |")
L.append("")
write_md("t1_decomp", "\n".join(L) + "\n")
dump("t1_decomp", {k: {kk: vv for kk, vv in v.items() if kk != "rates"} for k, v in res.items()})
