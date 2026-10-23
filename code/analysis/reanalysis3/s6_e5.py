"""Analysis 6 (POST HOC): memorization E5 (Qwen3-Coder-30B local arms qwen30b_{ON,OFF}_rg, local-stack M table).
(a) Interaction on the logit scale (GEE, instance-clustered, exchangeable; off x lowM = log ratio of odds ratios)
    beside the risk-difference scale (two-sample difference of paired d; CR2 by repository), with and without the
    difficulty control. Re-derives reanalysis2 t8 (the reviewer quotes ROR 2.32, p = 0.028 = the UNADJUSTED GEE).
(b) Stratification by gold-file presence in the ON pack (local_packs.json dedupON files vs the instance's gold files):
    a check for the "Low-M is a localization failure" confound (Low-M requires P1 file-path identification to fail).
Sign convention: Low - High (paper's E3 = High - Low).
"""
import json
import math
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

from common3 import arm, repo, P5, DATA, META, VIOL, INST, cr2_bm, wild, mcnemar, pp, ci, fp, write_md, dump

warnings.filterwarnings("ignore")
M = json.loads((DATA / "memorization-branchB" / "M_table_qwen3coder30b_local.json").read_text(encoding="utf-8"))
packs = json.loads((P5 / "local_packs.json").read_text(encoding="utf-8"))
meta = json.loads(META.read_text(encoding="utf-8"))
DMAP = {"<15 min fix": "<15m", "15 min - 1 hour": "15m-1h", "1-4 hours": ">=1h", ">4 hours": ">=1h"}
on, off, T = arm("qc_ON"), arm("qc_OFF"), arm("qc_T")

rows = []
for i in sorted(on.sub & off.sub):
    gold = set(INST[i]["gold_files"])
    fon = set(packs[i]["dedupON"]["files"])
    foff = set(packs[i]["dedupOFF"]["files"])
    rows.append(dict(iid=i, repo=repo(i), lowM=int(M[i]["lowM"]), n_avail=M[i]["n_avail"], p1=M[i]["p1"],
                     diff=DMAP[meta[i]["difficulty"]], gold_on_any=int(bool(gold & fon)), gold_on_all=int(gold <= fon),
                     gold_off_any=int(bool(gold & foff)),
                     y_on=int(i in on.res), y_off=int(i in off.res),
                     y_T=(int(i in T.res) if (i in T.sub and i not in VIOL) else np.nan)))
df = pd.DataFrame(rows)
df["d"] = df.y_off - df.y_on
df["dT"] = df.y_off - df.y_T
out = {"n": len(df)}


def gee(data, f):
    fit = smf.gee(f, groups="iid", data=data, family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
    b, se = fit.params["off:lowM"], fit.bse["off:lowM"]
    return dict(logROR=b, se=se, ROR=math.exp(b), ci=(math.exp(b - 1.96 * se), math.exp(b + 1.96 * se)), p=float(fit.pvalues["off:lowM"]))


def long(dfx, ycol0="y_on", ycol1="y_off"):
    lg = []
    for _, r in dfx.iterrows():
        if pd.isna(r[ycol0]):
            continue
        for a, y in ((0, r[ycol0]), (1, r[ycol1])):
            lg.append(dict(iid=r.iid, off=a, y=int(y), lowM=r.lowM, diff=r["diff"], gold=r.gold_on_any))
    return pd.DataFrame(lg)


def rd(dfx, col="d", X_extra=None):
    s = dfx[~dfx[col].isna()]
    X = [np.ones(len(s)), s.lowM.values]
    if X_extra == "difficulty":
        X += [(s["diff"] == "15m-1h").values, (s["diff"] == ">=1h").values]
    X = np.column_stack(X).astype(float)
    c = np.zeros(X.shape[1]); c[1] = 1
    r = cr2_bm(s[col].values, s.repo.values, X=X, c=c)
    lo, hi = s[s.lowM == 1][col], s[s.lowM == 0][col]
    se_i = math.sqrt(lo.var(ddof=1) / len(lo) + hi.var(ddof=1) / len(hi))
    est = lo.mean() - hi.mean()
    p_i = float(2 * (1 - 0.5 * (1 + math.erf(abs(est / se_i) / math.sqrt(2))))) if se_i > 0 else float("nan")
    return dict(est_crude=est, se_inst=se_i, p_inst=p_i, cr2=r, adjusted=X_extra is not None)


lg = long(df)
lgT = long(df, "y_T", "y_off")
out["gee"] = {"OFF-ON unadjusted": gee(lg, "y ~ off * lowM"),
              "OFF-ON + difficulty, arm x difficulty": gee(lg, "y ~ off * lowM + C(diff) + off:C(diff)"),
              "OFF-T unadjusted": gee(lgT, "y ~ off * lowM")}
out["rd"] = {"OFF-ON crude": rd(df), "OFF-ON + difficulty": rd(df, X_extra="difficulty"), "OFF-T crude": rd(df, "dT")}

# cell rates
cells = {}
for lab, s in (("Low-M", df[df.lowM == 1]), ("High-M", df[df.lowM == 0])):
    cells[lab] = dict(n=len(s), on=s.y_on.mean(), off=s.y_off.mean(), d=s.d.mean(),
                      gold_on_any=s.gold_on_any.mean(), gold_on_all=s.gold_on_all.mean(), gold_off_any=s.gold_off_any.mean(),
                      p1_NA=float((s.p1.isna()).mean()) if s.p1.isna().any() else float((s.n_avail < 3).mean()),
                      n_avail_lt3=float((s.n_avail < 3).mean()))
out["cells"] = cells

# (b) stratify by gold-file presence in the ON pack
strat = {}
for g in (1, 0):
    s = df[df.gold_on_any == g]
    ent = {}
    for lab, ss in (("Low-M", s[s.lowM == 1]), ("High-M", s[s.lowM == 0]), ("all", s)):
        b, c = int((ss.d > 0).sum()), int((ss.d < 0).sum())
        ent[lab] = dict(n=len(ss), on=ss.y_on.mean(), off=ss.y_off.mean(), d=ss.d.mean(), b=b, c=c, mcnemar_p=mcnemar(b, c),
                        dT=ss.dT.mean(), nT=int(ss.dT.notna().sum()))
    ent["interaction_RD"] = rd(s)
    if int((s.d != 0).sum()) == 0:
        ent["interaction_GEE"] = {"error": "not estimable: 0 discordant pairs in this stratum (ON = OFF on every instance)"}
    else:
        ent["interaction_GEE"] = gee(long(s), "y ~ off * lowM")
    strat["gold file in ON pack" if g else "gold file NOT in ON pack"] = ent
out["by_gold_presence"] = strat
# (c) P1-availability (the P1-NA filter: P1 is not applicable where the issue names a gold-file basename)
pstrat = {}
for nm, s in (("P1 available (n_avail = 3)", df[df.n_avail == 3]), ("P1 not applicable (n_avail < 3)", df[df.n_avail < 3])):
    ent = {}
    for lab, ss in (("Low-M", s[s.lowM == 1]), ("High-M", s[s.lowM == 0])):
        b, c = int((ss.d > 0).sum()), int((ss.d < 0).sum())
        ent[lab] = dict(n=len(ss), on=ss.y_on.mean(), off=ss.y_off.mean(), d=ss.d.mean(), b=b, c=c, mcnemar_p=mcnemar(b, c),
                        gold_on_any=ss.gold_on_any.mean())
    ent["interaction_RD"] = rd(s)
    ent["interaction_GEE"] = gee(long(s), "y ~ off * lowM")
    pstrat[nm] = ent
out["by_P1_availability"] = pstrat
# three-way: does adding gold presence (and its interaction with arm) change the off x lowM coefficient?
out["gee_adj_gold"] = gee(lg, "y ~ off * lowM + gold + off:gold")
out["gee_full_gold_x_lowM"] = None
try:
    fit = smf.gee("y ~ off * lowM * gold", groups="iid", data=lg, family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
    out["gee_full_gold_x_lowM"] = {k: dict(b=float(fit.params[k]), se=float(fit.bse[k]), p=float(fit.pvalues[k])) for k in fit.params.index}
except Exception as e:  # noqa
    out["gee_full_gold_x_lowM"] = {"error": str(e)}

# ---------------- markdown
L = ["## Analysis 6 — Memorization E5 (Qwen3-Coder-30B, local M) (POST HOC)", "",
     f"n = {len(df)} (local qwen30b_{{ON,OFF}}_rg; OFF−T on the 473). Interaction signs: Low−High; the paper's E3 = High−Low.", "",
     "### (a) Logit-scale vs risk-difference-scale interaction", "",
     "| scale / model | contrast | estimate | 95% CI | p |", "|---|---|---|---|---|"]
for k, g in out["gee"].items():
    L.append(f"| logit GEE (instance-clustered), {k.split(' ', 1)[1]} | {k.split(' ')[0]} | ROR {g['ROR']:.2f} (log-ROR {g['logROR']:+.3f}, SE {g['se']:.3f}) | [{g['ci'][0]:.2f}, {g['ci'][1]:.2f}] | {fp(g['p'])} |")
for k, r in out["rd"].items():
    c2 = r["cr2"]
    if not r["adjusted"]:
        L.append(f"| RD, instance SE, {k.split(' ', 1)[1]} | {k.split(' ')[0]} | {pp(r['est_crude'], 2)} pp (Low−High) | "
                 f"[{pp(r['est_crude'] - 1.96 * r['se_inst'], 1)}, {pp(r['est_crude'] + 1.96 * r['se_inst'], 1)}] | {fp(r['p_inst'])} |")
    L.append(f"| RD, CR2 by repository (df {c2['df']:.1f}), {k.split(' ', 1)[1]} | {k.split(' ')[0]} | {pp(c2['est'], 2)} pp | {ci(c2['ci95'])} | {fp(c2['p'])} |")
L.append("")
L += ["Why the scales disagree: the OFF−ON effect is a larger *ratio* in Low-M because Low-M's ON rate is lower:", "",
      "| stratum | n | ON | OFF | OFF−ON | odds ratio OFF/ON | gold file in ON pack | in OFF pack | P1 not available (n_avail<3) |", "|---|---|---|---|---|---|---|---|---|"]
for lab, c in cells.items():
    orr = (c["off"] / (1 - c["off"])) / (c["on"] / (1 - c["on"]))
    L.append(f"| {lab} | {c['n']} | {100*c['on']:.1f}% | {100*c['off']:.1f}% | {pp(c['d'])} | {orr:.2f} | {100*c['gold_on_any']:.1f}% | {100*c['gold_off_any']:.1f}% | {100*c['n_avail_lt3']:.1f}% |")
L.append("")
L += ["### (b) E5 stratified by gold-file presence in the ON pack", "",
      "| stratum | cell | n | ON | OFF | OFF−ON (pp) | b/c | McNemar p | OFF−T (pp; n) |", "|---|---|---|---|---|---|---|---|---|"]
for sname, ent in strat.items():
    for lab in ("Low-M", "High-M", "all"):
        e = ent[lab]
        L.append(f"| {sname} | {lab} | {e['n']} | {100*e['on']:.1f}% | {100*e['off']:.1f}% | {pp(e['d'], 1)} | {e['b']}/{e['c']} | {fp(e['mcnemar_p'])} | {pp(e['dT'], 1)}; {e['nT']} |")
    ri, gi = ent["interaction_RD"], ent["interaction_GEE"]
    gtxt = f"ROR {gi['ROR']:.2f} [{gi['ci'][0]:.2f}, {gi['ci'][1]:.2f}], p {fp(gi['p'])}" if "ROR" in gi else gi.get("error", "")
    L.append(f"| {sname} | interaction Low−High | | | | RD {pp(ri['est_crude'], 1)} (inst. p {fp(ri['p_inst'])}; CR2 p {fp(ri['cr2']['p'])}) | | logit: {gtxt} | |")
L.append("")
ga = out["gee_adj_gold"]
L.append(f"GEE off×lowM adjusting for gold presence and arm×gold: ROR {ga['ROR']:.2f} [{ga['ci'][0]:.2f}, {ga['ci'][1]:.2f}], p {fp(ga['p'])}.")
if isinstance(out["gee_full_gold_x_lowM"], dict) and "off:lowM:gold" in out["gee_full_gold_x_lowM"]:
    L.append("A three-way off×lowM×gold GEE term is not interpretable: the gold-absent stratum has 0 discordant pairs (ON = OFF on all 61), "
             "so it carries no information on the arm effect; the fitted value is kept in the JSON only.")
L.append("")
L += ["### (c) E5 stratified by P1 availability (P1 not applicable where the issue names a gold-file basename)", "",
      "| stratum | cell | n | ON | OFF | OFF−ON (pp) | b/c | McNemar p | gold file in ON pack |", "|---|---|---|---|---|---|---|---|---|"]
for sname, ent in pstrat.items():
    for lab in ("Low-M", "High-M"):
        e = ent[lab]
        L.append(f"| {sname} | {lab} | {e['n']} | {100*e['on']:.1f}% | {100*e['off']:.1f}% | {pp(e['d'], 1)} | {e['b']}/{e['c']} | {fp(e['mcnemar_p'])} | {100*e['gold_on_any']:.1f}% |")
    ri, gi = ent["interaction_RD"], ent["interaction_GEE"]
    L.append(f"| {sname} | interaction Low−High | | | | RD {pp(ri['est_crude'], 1)} (inst. p {fp(ri['p_inst'])}; CR2 p {fp(ri['cr2']['p'])}) | | logit ROR {gi['ROR']:.2f} [{gi['ci'][0]:.2f}, {gi['ci'][1]:.2f}], p {fp(gi['p'])} | |")
L.append("")
write_md("s6_e5", "\n".join(L) + "\n")
dump("s6_e5", out)
