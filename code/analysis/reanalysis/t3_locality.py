"""Task 3: fix-locality without the random-effects meta-analysis.

Per arm: single-file and multi-file strata (distinct pre-image gold files; patches touching only new
files are dropped, same rule as code/analysis_original/stratify_locality.py), McNemar per stratum, and an
arm x stratum interaction test: GEE logistic y ~ off + multi + off:multi clustered by instance
(exchangeable), plus the risk-difference-scale contrast Delta_multi - Delta_single.
A pooled model over the four original locality arms (arm-specific main effects, common off:multi,
clustered by instance) is reported as a supplement.
"""
from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

from common_ra import OUT, load_table, paired_rows, mcnemar_exact, gold_file_counts, fmt_p

warnings.filterwarnings("ignore")
ARMS = [  # the four arms of the paper's locality paragraph first, then two extra rows
    ("gpt-5.6-sol fusion", "P1_gpt_fusion", True),
    ("DENSE-1", "P4_DENSE1_gpt_dense", True),
    ("DeepSeek-v4", "P2_deepseek_fusion", True),
    ("Qwen3-Coder-30B-A3B", "M1_qwen3coder30b_AC", True),
    ("Qwen3.6-27B K=12", "P3_qwen36_fusion_K12", False),
    ("gpt logged re-run", "F1_gpt_logged_replication", False),
]


def strat(rows):
    n = len(rows)
    b = sum(1 for r in rows if r["y_off"] and not r["y_on"])
    c = sum(1 for r in rows if r["y_on"] and not r["y_off"])
    d = np.array([r["y_off"] - r["y_on"] for r in rows], float)
    return dict(n=n, b=b, c=c, d=100 * d.mean(), var=d.var(ddof=1) / n, p=mcnemar_exact(b, c))


def main():
    tab = load_table()
    nf = gold_file_counts()
    valid = [i for i, k in nf.items() if k > 0]
    n_single = sum(1 for i in valid if nf[i] == 1)
    out, pooled = [], []
    for lab, arm, in_pool in ARMS:
        rows = [r for r in paired_rows(tab, arm) if nf.get(r["iid"], 0) > 0]
        s = strat([r for r in rows if nf[r["iid"]] == 1])
        m = strat([r for r in rows if nf[r["iid"]] >= 2])
        recs = []
        for r in rows:
            mult = int(nf[r["iid"]] >= 2)
            recs.append(dict(iid=r["iid"], off=0, multi=mult, y=r["y_on"], arm=arm))
            recs.append(dict(iid=r["iid"], off=1, multi=mult, y=r["y_off"], arm=arm))
        df = pd.DataFrame(recs)
        if in_pool:
            pooled += recs
        fit = smf.gee("y ~ off * multi", groups="iid", data=df, family=sm.families.Binomial(),
                      cov_struct=sm.cov_struct.Exchangeable()).fit()
        b, se = fit.params["off:multi"], fit.bse["off:multi"]
        rd = (m["d"] - s["d"]); rd_se = 100 * np.sqrt(m["var"] + s["var"])
        out.append(dict(arm=lab, arm_id=arm, single=s, multi=m,
                        gee_beta=float(b), gee_se=float(se), gee_p=float(fit.pvalues["off:multi"]),
                        ror=float(np.exp(b)), ror_lo=float(np.exp(b - 1.96 * se)), ror_hi=float(np.exp(b + 1.96 * se)),
                        rd=rd, rd_se=rd_se, rd_p=float(2 * stats.norm.sf(abs(rd / rd_se)))))
    dfp = pd.DataFrame(pooled)
    fitp = smf.gee("y ~ C(arm) * off + C(arm) * multi + off:multi", groups="iid", data=dfp,
                   family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
    pooled_res = dict(beta=float(fitp.params["off:multi"]), se=float(fitp.bse["off:multi"]),
                      p=float(fitp.pvalues["off:multi"]), n_obs=int(len(dfp)), n_inst=int(dfp.iid.nunique()))
    json.dump(dict(per_arm=out, pooled=pooled_res, n_valid=len(valid), n_single=n_single),
              open(OUT / "t3_locality.json", "w"), indent=1, default=float)

    L = ["## Task 3 — Fix locality (per arm; no cross-arm meta-analysis)", "",
         f"Gold patches with ≥1 pre-image file: {len(valid)}; single-file {n_single} ({100*n_single/len(valid):.1f}%), "
         f"multi-file {len(valid)-n_single}. Never-submitted excluded pairwise. Interaction = GEE logistic "
         "y ~ off + multi + off×multi, clustered by instance (exchangeable); ratio of odds ratios multi/single. "
         "RD-scale = Δ_multi − Δ_single with independent-strata SE (strata are disjoint instances).", "",
         "| arm | single-file: n, Δ (pp), b/c, p | multi-file: n, Δ (pp), b/c, p | RD-scale Δ_multi−Δ_single (SE), p | GEE off×multi: ROR [95% CI], p |",
         "|---|---|---|---|---|"]
    for r in out:
        s, m = r["single"], r["multi"]
        L.append(f"| {r['arm']} | {s['n']}, {s['d']:+.1f}, {s['b']}/{s['c']}, {fmt_p(s['p'])} | "
                 f"{m['n']}, {m['d']:+.1f}, {m['b']}/{m['c']}, {fmt_p(m['p'])} | {r['rd']:+.1f} ({r['rd_se']:.1f}), {fmt_p(r['rd_p'])} | "
                 f"{r['ror']:.2f} [{r['ror_lo']:.2f}, {r['ror_hi']:.2f}], {fmt_p(r['gee_p'])} |")
    L += ["", f"Supplement — pooled over the paper's four locality arms (gpt fusion, DENSE-1, DeepSeek, A3B), arm-specific "
          f"main effects, common off×multi, clustered by instance ({pooled_res['n_inst']} instances, {pooled_res['n_obs']} obs): "
          f"log-ROR {pooled_res['beta']:+.3f} (SE {pooled_res['se']:.3f}), ROR {np.exp(pooled_res['beta']):.2f}, p = {fmt_p(pooled_res['p'])}."]
    txt = "\n".join(L) + "\n"
    (OUT / "t3_locality.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
