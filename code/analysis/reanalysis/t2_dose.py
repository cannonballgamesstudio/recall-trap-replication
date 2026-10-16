"""Task 2 (EXPLORATORY): Qwen3.6-27B dose-response at K=4, 12, 40, pairwise exclusion of never-submitted.

Per K: n, raw McNemar (b, c, p), empty and fin=length rates per arm, exact product decomposition,
both-non-truncated and both-non-empty secondaries. Then instance-paired DeltaDelta(40-4), (40-12) with
an instance-level paired SE and wild-cluster CI; and an ordinal trend test (K coded 0/1/2) by GEE
clustered by instance.
"""
from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

from common_ra import (OUT, load_table, paired_rows, mcnemar_exact, cr2_bm, wild_cluster, signflip, fmt_p,
                       repo_of)

warnings.filterwarnings("ignore")
KS = [("K=4", 0, "B1_qwen36_K4"), ("K=12", 1, "P3_qwen36_fusion_K12"), ("K=40", 2, "B1_qwen36_K40")]


def is_empty(r):
    return r["status"] == "empty"


def is_trunc(r):
    return r["raw_finish_reason"] == "length"


def sub_mcnemar(rows):
    n = len(rows)
    b = sum(1 for r in rows if r["y_off"] and not r["y_on"])
    c = sum(1 for r in rows if r["y_on"] and not r["y_off"])
    d = 100 * (sum(r["y_off"] for r in rows) - sum(r["y_on"] for r in rows)) / n if n else float("nan")
    return dict(n=n, b=b, c=c, d=d, p=mcnemar_exact(b, c))


def decomp(rows):
    n = len(rows)
    att_on = sum(1 for r in rows if not is_empty(r["on"]))
    att_off = sum(1 for r in rows if not is_empty(r["off"]))
    A_on, A_off = att_on / n, att_off / n
    Q_on = sum(r["y_on"] for r in rows) / att_on
    Q_off = sum(r["y_off"] for r in rows) / att_off
    dA, dQ = A_off - A_on, Q_off - Q_on
    dR = A_off * Q_off - A_on * Q_on
    return dict(A_on=A_on, A_off=A_off, Q_on=Q_on, Q_off=Q_off, dA=100 * dA, dQ=100 * dQ, dR=100 * dR,
                prod=100 * Q_on * dA, qual=100 * A_on * dQ, inter=100 * dA * dQ)


def main():
    tab = load_table()
    per_k, dmap = [], {}
    for lab, kc, arm in KS:
        rows = paired_rows(tab, arm)
        n_np_on = sum(1 for v in tab[(arm, "ON")].values() if v["status"] == "never_predicted")
        n_np_off = sum(1 for v in tab[(arm, "OFF")].values() if v["status"] == "never_predicted")
        m = sub_mcnemar(rows)
        n = m["n"]
        e_on = sum(is_empty(r["on"]) for r in rows) / n
        e_off = sum(is_empty(r["off"]) for r in rows) / n
        t_on = sum(is_trunc(r["on"]) for r in rows) / n
        t_off = sum(is_trunc(r["off"]) for r in rows) / n
        nt = sub_mcnemar([r for r in rows if not is_trunc(r["on"]) and not is_trunc(r["off"])])
        ne = sub_mcnemar([r for r in rows if not is_empty(r["on"]) and not is_empty(r["off"])])
        dec = decomp(rows)
        per_k.append(dict(K=lab, kc=kc, arm=arm, never_on=n_np_on, never_off=n_np_off, **m,
                          res_on=sum(r["y_on"] for r in rows), res_off=sum(r["y_off"] for r in rows),
                          empty_on=e_on, empty_off=e_off, empty_p=mcnemar_exact(
                              sum(1 for r in rows if is_empty(r["on"]) and not is_empty(r["off"])),
                              sum(1 for r in rows if is_empty(r["off"]) and not is_empty(r["on"]))),
                          trunc_on=t_on, trunc_off=t_off, nt=nt, ne=ne, **dec))
        dmap[lab] = {r["iid"]: (r["y_on"], r["y_off"]) for r in rows}

    # DeltaDelta, instance-paired on instances paired at both K
    dd_res = []
    for hi, lo in (("K=40", "K=4"), ("K=40", "K=12"), ("K=12", "K=4")):
        ids = sorted(set(dmap[hi]) & set(dmap[lo]))
        dd = np.array([(dmap[hi][i][1] - dmap[hi][i][0]) - (dmap[lo][i][1] - dmap[lo][i][0]) for i in ids], float)
        cl = [repo_of(i) for i in ids]
        n = len(dd)
        est = dd.mean()
        se = dd.std(ddof=1) / np.sqrt(n)
        z = est / se
        p_inst = 2 * stats.norm.sf(abs(z))
        wb = wild_cluster(dd, cl)
        cr = cr2_bm(dd, cl)
        sf = signflip(dd, cl)
        marg = np.mean([v[1] - v[0] for v in dmap[hi].values()]) - np.mean([v[1] - v[0] for v in dmap[lo].values()])
        dd_res.append(dict(contrast=f"ΔΔ({hi[2:]}−{lo[2:]})", n=n, est=100 * est, se_inst=100 * se, p_inst=p_inst,
                           lo_inst=100 * (est - 1.96 * se), hi_inst=100 * (est + 1.96 * se),
                           wild_lo=100 * wb["lo"], wild_hi=100 * wb["hi"], wild_p=wb["p"],
                           cr2_lo=100 * cr["lo"], cr2_hi=100 * cr["hi"], cr2_p=cr["p"], cr2_df=cr["df"],
                           signflip_p=sf["p"], marginal=100 * marg))

    # Ordinal trend test: GEE, clustered by instance
    recs = []
    for lab, kc, arm in KS:
        for iid, (yon, yoff) in dmap[lab].items():
            recs.append(dict(iid=iid, kc=kc, off=0, y=yon))
            recs.append(dict(iid=iid, kc=kc, off=1, y=yoff))
    df = pd.DataFrame(recs)
    trend = {}
    for cs_name, cs in (("exchangeable", sm.cov_struct.Exchangeable()), ("independence", sm.cov_struct.Independence())):
        mod = smf.gee("y ~ C(kc) + off + off:kc", groups="iid", data=df, family=sm.families.Binomial(), cov_struct=cs)
        fit = mod.fit()
        b = fit.params["off:kc"]; s = fit.bse["off:kc"]
        trend[f"logit_{cs_name}"] = dict(beta=float(b), se=float(s), p=float(fit.pvalues["off:kc"]),
                                         OR=float(np.exp(b)), lo=float(np.exp(b - 1.96 * s)), hi=float(np.exp(b + 1.96 * s)),
                                         beta_off=float(fit.params["off"]))
    # risk-difference trend: d_ik ~ kc, Gaussian GEE clustered by instance
    drecs = [dict(iid=iid, kc=kc, d=yoff - yon) for lab, kc, arm in KS for iid, (yon, yoff) in dmap[lab].items()]
    ddf = pd.DataFrame(drecs)
    fit = smf.gee("d ~ kc", groups="iid", data=ddf, family=sm.families.Gaussian(),
                  cov_struct=sm.cov_struct.Exchangeable()).fit()
    trend["rd_exchangeable"] = dict(beta=100 * float(fit.params["kc"]), se=100 * float(fit.bse["kc"]),
                                    p=float(fit.pvalues["kc"]))
    # conditional logistic (paired, discordant pairs only): logit P(OFF wins | discordant) = a + b*kc
    disc = ddf[ddf.d != 0].copy()
    disc["w"] = (disc.d > 0).astype(int)
    fit = smf.gee("w ~ kc", groups="iid", data=disc, family=sm.families.Binomial(),
                  cov_struct=sm.cov_struct.Independence()).fit()
    trend["clogit_discordant"] = dict(beta=float(fit.params["kc"]), se=float(fit.bse["kc"]), p=float(fit.pvalues["kc"]),
                                      n_disc=int(len(disc)))

    out = dict(per_k=per_k, dd=dd_res, trend=trend)
    (OUT / "t2_dose.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")

    L = ["## Task 2 — Qwen3.6-27B dose-response, K = 4 / 12 / 40 (EXPLORATORY)", "",
         "All three K ran at 32k completion budget, reasoning on. Never-submitted instances excluded pairwise. "
         "Δ = OFF − ON (pp). Empty = empty patch (counted as failure). fin=length = raw finish_reason 'length' "
         "(truncated generation), rate over the paired n.", "",
         "| K | never-sub ON/OFF | n | ON | OFF | Δ (pp) | b/c (OFF/ON) | McNemar p | empty ON/OFF (%) | empty-asym p | fin=length ON/OFF (%) |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in per_k:
        L.append(f"| {r['K']} | {r['never_on']}/{r['never_off']} | {r['n']} | {r['res_on']} ({100*r['res_on']/r['n']:.1f}%) | "
                 f"{r['res_off']} ({100*r['res_off']/r['n']:.1f}%) | {r['d']:+.2f} | {r['b']}/{r['c']} | {fmt_p(r['p'])} | "
                 f"{100*r['empty_on']:.1f}/{100*r['empty_off']:.1f} | {fmt_p(r['empty_p'])} | {100*r['trunc_on']:.1f}/{100*r['trunc_off']:.1f} |")
    L += ["", "Product decomposition (A = attempt = 1 − empty, Q = resolved | attempted; ΔR = Q_on·ΔA + A_on·ΔQ + ΔA·ΔQ).", "",
          "| K | A ON/OFF | Q ON/OFF | ΔA (pp) | ΔQ (pp) | ΔR | producibility Q_on·ΔA | quality A_on·ΔQ | interaction ΔA·ΔQ |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in per_k:
        sh = lambda x: f"{x:+.2f} ({100*x/r['dR']:.0f}%)"
        L.append(f"| {r['K']} | {r['A_on']:.3f}/{r['A_off']:.3f} | {r['Q_on']:.3f}/{r['Q_off']:.3f} | {r['dA']:+.2f} | {r['dQ']:+.2f} | "
                 f"{r['dR']:+.2f} | {sh(r['prod'])} | {sh(r['qual'])} | {sh(r['inter'])} |")
    L += ["", "Secondaries.", "",
          "| K | both-non-truncated: n, Δ, b/c, p | both-non-empty: n, Δ, b/c, p |", "|---|---|---|"]
    for r in per_k:
        a, b = r["nt"], r["ne"]
        L.append(f"| {r['K']} | n={a['n']}, {a['d']:+.2f}, {a['b']}/{a['c']}, p={fmt_p(a['p'])} | "
                 f"n={b['n']}, {b['d']:+.2f}, {b['b']}/{b['c']}, p={fmt_p(b['p'])} |")
    L += ["", "Growth tests (instance-paired on instances paired at both K; wild = WCR Webb B=9,999; CR2 with BM df).", "",
          "| contrast | n overlap | ΔΔ (pp) | instance SE | inst. 95% CI | inst. p | wild 95% CI | wild p | CR2 95% CI (df) | CR2 p | sign-flip p | marginal ΔΔ (own sets) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in dd_res:
        L.append(f"| {r['contrast']} | {r['n']} | {r['est']:+.2f} | {r['se_inst']:.2f} | [{r['lo_inst']:+.1f}, {r['hi_inst']:+.1f}] | "
                 f"{fmt_p(r['p_inst'])} | [{r['wild_lo']:+.1f}, {r['wild_hi']:+.1f}] | {fmt_p(r['wild_p'])} | "
                 f"[{r['cr2_lo']:+.1f}, {r['cr2_hi']:+.1f}] ({r['cr2_df']:.1f}) | {fmt_p(r['cr2_p'])} | {fmt_p(r['signflip_p'])} | {r['marginal']:+.2f} |")
    t = trend
    L += ["", "Ordinal trend (K coded 0/1/2), clustered by instance:", "",
          "| model | trend coefficient | SE | p |", "|---|---|---|---|",
          f"| GEE logit, y ~ C(K) + off + off×K, exchangeable | log-OR per K step {t['logit_exchangeable']['beta']:+.3f} (OR {t['logit_exchangeable']['OR']:.2f} [{t['logit_exchangeable']['lo']:.2f}, {t['logit_exchangeable']['hi']:.2f}]) | {t['logit_exchangeable']['se']:.3f} | {fmt_p(t['logit_exchangeable']['p'])} |",
          f"| same, independence working corr. | {t['logit_independence']['beta']:+.3f} (OR {t['logit_independence']['OR']:.2f}) | {t['logit_independence']['se']:.3f} | {fmt_p(t['logit_independence']['p'])} |",
          f"| GEE identity, d ~ K (risk-difference trend) | {t['rd_exchangeable']['beta']:+.2f} pp per K step | {t['rd_exchangeable']['se']:.2f} | {fmt_p(t['rd_exchangeable']['p'])} |",
          f"| conditional (discordant pairs, n={t['clogit_discordant']['n_disc']}): logit P(OFF wins) ~ K | {t['clogit_discordant']['beta']:+.3f} | {t['clogit_discordant']['se']:.3f} | {fmt_p(t['clogit_discordant']['p'])} |"]
    txt = "\n".join(L) + "\n"
    (OUT / "t2_dose.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
