"""Task 8: E5 (Qwen3-Coder-30B, local-GGUF proxy M) Low-M vs High-M interaction with a difficulty control.

Outcome pairs: OFF-ON (primary E5 cell, refs qwen30b_{ON,OFF}_rg, n=500) and OFF-T (n=473, secondary).
Covariates: SWE-bench Verified `difficulty` (3 levels: <15 min, 15 min-1 h, >=1 h [1-4 h + >4 h merged, n=45]),
gold-patch added lines, gold-file count (distinct files in the gold diff).
(a) MH-style stratified Low-High interaction: within stratum s, I_s = D_low,s - D_high,s, weight
    w_s = n_low,s*n_high,s/(n_low,s+n_high,s); SE from within-cell variances of the paired d; plus an
    instance bootstrap (B=10,000, resampling within cells) for the CI.
(b) GEE logit, long format (instance x arm), exchangeable, clustered by instance:
    y ~ off*lowM + C(diff) + off:C(diff)  [and an extended model adding log(1+added) and multi-file with arm interactions].
(c) Risk-difference regression of d on lowM + covariates, CR2 by repository.
Sign convention: Low-High (positive = larger effect in Low-M). The paper's E3 is High-Low = -(Low-High).
"""
import json
import math
import re
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

from ra2 import arm, VIOL, CONTAM, repo, cra, pp, ci, fp, write_md, dump

warnings.filterwarnings("ignore")
PQ = "<HF_HOME>/hub/datasets--princeton-nlp--SWE-bench_Verified/snapshots/c104f840cc67f8b6eec6f759ebc8b2693d585d4a/data/test-00000-of-00001.parquet"
dfv = pd.DataFrame.from_dict(json.loads(open(__import__("ra2").PKG / "data" / "swe-verified" / "inputs" / "verified_meta.json", encoding="utf-8").read()), orient="index")  # exported from PQ by export_verified_meta.py


def added_lines(p):
    return sum(1 for l in p.splitlines() if l.startswith("+") and not l.startswith("+++"))


def n_files(p):
    return len(set(re.findall(r"^diff --git a/(\S+) b/", p, re.M)))


DMAP = {"<15 min fix": "<15m", "15 min - 1 hour": "15m-1h", "1-4 hours": ">=1h", ">4 hours": ">=1h"}
M = json.loads((CONTAM / "M_table_qwen3coder30b_local.json").read_text(encoding="utf-8"))
on, off, T = arm("qc_ON"), arm("qc_OFF"), arm("qc_T")

rows = []
for i in sorted(on.sub & off.sub):
    p = dfv.loc[i, "patch"]
    rows.append(dict(iid=i, repo=repo(i), lowM=int(M[i]["lowM"]), diff=DMAP[dfv.loc[i, "difficulty"]],
                     added=added_lines(p), nfiles=n_files(p),
                     y_on=int(i in on.res), y_off=int(i in off.res), y_T=(int(i in T.res) if i in T.sub and i not in VIOL else np.nan)))
df = pd.DataFrame(rows)
df["d"] = df.y_off - df.y_on
df["dT"] = df.y_off - df.y_T
df["logadd"] = np.log1p(df.added)
df["multi"] = (df.nfiles > 1).astype(int)
df["diff2"] = np.where(df["diff"] == "<15m", "<15m", ">=15m")
df["add_t"] = pd.qcut(df.added, 3, labels=["A1", "A2", "A3"]).astype(str)

L = ["## Task 8 — E5 (Qwen3-Coder-30B) Low-M vs High-M with a difficulty control", "",
     "Primary cell OFF−ON (n=500, one draw); secondary OFF−T (n=473). Interaction reported as **Low−High** (paper's E3 = High−Low, so the paper's −5.0 is +5.0 here).", ""]

# --- balance table
L += ["Covariate balance (is Low-M easier?):", "",
      "| stratum | n | <15m | 15m–1h | ≥1h | mean added lines | median added | multi-file share | ON resolve | OFF resolve |",
      "|---|---|---|---|---|---|---|---|---|---|"]
for lab, s in (("Low-M", df[df.lowM == 1]), ("High-M", df[df.lowM == 0])):
    vc = s["diff"].value_counts(normalize=True)
    L.append(f"| {lab} | {len(s)} | {100*vc.get('<15m',0):.1f}% | {100*vc.get('15m-1h',0):.1f}% | {100*vc.get('>=1h',0):.1f}% | {s.added.mean():.1f} | {s.added.median():.0f} | "
             f"{100*s.multi.mean():.1f}% | {100*s.y_on.mean():.1f}% | {100*s.y_off.mean():.1f}% |")
L.append("")


def strat(dfx, col, strata_cols, B=10000, seed=20261014):
    dfx = dfx[~dfx[col].isna()].copy()
    dfx["cell"] = dfx[strata_cols].astype(str).agg("|".join, axis=1)
    cells = []
    for c, g in dfx.groupby("cell"):
        lo, hi = g[g.lowM == 1][col].values, g[g.lowM == 0][col].values
        if len(lo) == 0 or len(hi) == 0:
            continue
        w = len(lo) * len(hi) / (len(lo) + len(hi))
        v = (lo.var(ddof=1) / len(lo) if len(lo) > 1 else 0) + (hi.var(ddof=1) / len(hi) if len(hi) > 1 else 0)
        cells.append(dict(cell=c, n_low=len(lo), n_high=len(hi), d_low=lo.mean(), d_high=hi.mean(), w=w, v=v, lo=lo, hi=hi))
    W = sum(c["w"] for c in cells)
    est = sum(c["w"] * (c["d_low"] - c["d_high"]) for c in cells) / W
    se = math.sqrt(sum(c["w"] ** 2 * c["v"] for c in cells)) / W
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(B):
        num = 0.0
        for c in cells:
            l = c["lo"][rng.integers(0, len(c["lo"]), len(c["lo"]))].mean()
            h = c["hi"][rng.integers(0, len(c["hi"]), len(c["hi"]))].mean()
            num += c["w"] * (l - h)
        bs.append(num / W)
    bs = np.sort(bs)
    used = sum(c["n_low"] + c["n_high"] for c in cells)
    return dict(est=est, se=se, z_p=2 * (1 - 0.5 * (1 + math.erf(abs(est / se) / math.sqrt(2)))),
                boot_ci=(bs[int(0.025 * (B - 1))], bs[int(0.975 * (B - 1))]),
                boot_p_one_low_gt_high=float(np.mean(bs <= 0)), n_cells=len(cells), n_used=used,
                cells=[{k: v for k, v in c.items() if k not in ("lo", "hi")} for c in cells])


def crude(dfx, col):
    dfx = dfx[~dfx[col].isna()]
    lo, hi = dfx[dfx.lowM == 1][col], dfx[dfx.lowM == 0][col]
    est = lo.mean() - hi.mean()
    se = math.sqrt(lo.var(ddof=1) / len(lo) + hi.var(ddof=1) / len(hi))
    return dict(est=est, se=se, z_p=2 * (1 - 0.5 * (1 + math.erf(abs(est / se) / math.sqrt(2)))), d_low=lo.mean(), d_high=hi.mean(),
                n_low=len(lo), n_high=len(hi))


out = {}
L += ["(a) Stratified Low−High interaction (MH-style weights n_l·n_h/(n_l+n_h); SE from within-cell variances; bootstrap CI resamples within cells, B=10,000):", "",
      "| contrast | stratification | cells used | n used | Low−High (pp) | SE | 95% CI (normal) | 95% CI (bootstrap) | two-sided p |",
      "|---|---|---|---|---|---|---|---|---|"]
for col, name in (("d", "OFF−ON"), ("dT", "OFF−T")):
    c0 = crude(df, col)
    out[(name, "crude")] = c0
    L.append(f"| {name} | none (crude; Δlow {pp(c0['d_low'])} n={c0['n_low']}, Δhigh {pp(c0['d_high'])} n={c0['n_high']}) | 1 | {c0['n_low']+c0['n_high']} | {pp(c0['est'], 2)} | {100*c0['se']:.2f} | "
             f"{ci((c0['est']-1.96*c0['se'], c0['est']+1.96*c0['se']))} | — | {fp(c0['z_p'])} |")
    for sc, lab in ((["diff"], "difficulty (3)"), (["diff", "multi"], "difficulty × multi-file (6)"),
                    (["diff", "multi", "add_t"], "difficulty × multi-file × added-lines tercile (18)")):
        r = strat(df, col, sc)
        out[(name, lab)] = r
        L.append(f"| {name} | {lab} | {r['n_cells']} | {r['n_used']} | {pp(r['est'], 2)} | {100*r['se']:.2f} | "
                 f"{ci((r['est']-1.96*r['se'], r['est']+1.96*r['se']))} | {ci(r['boot_ci'])} | {fp(r['z_p'])} |")
L.append("")
L.append("Per-difficulty cells, OFF−ON:")
L.append("")
L.append("| difficulty | n low / high | Δlow | Δhigh | Low−High |")
L.append("|---|---|---|---|---|")
for c in out[("OFF−ON", "difficulty (3)")]["cells"]:
    L.append(f"| {c['cell']} | {c['n_low']} / {c['n_high']} | {pp(c['d_low'])} | {pp(c['d_high'])} | {pp(c['d_low']-c['d_high'])} |")
L.append("")

# --- (b) GEE logit
long = []
for _, r in df.iterrows():
    for armv, y in ((0, r.y_on), (1, r.y_off)):
        long.append(dict(iid=r.iid, off=armv, y=y, lowM=r.lowM, diff=r["diff"], diff2=r["diff2"], logadd=r.logadd, multi=r.multi))
lg = pd.DataFrame(long)
lgT = []
for _, r in df[~df.y_T.isna()].iterrows():
    for armv, y in ((0, r.y_T), (1, r.y_off)):
        lgT.append(dict(iid=r.iid, off=armv, y=y, lowM=r.lowM, diff=r["diff"], diff2=r["diff2"], logadd=r.logadd, multi=r.multi))
lgT = pd.DataFrame(lgT)
forms = [("unadjusted", "y ~ off * lowM"),
         ("+ difficulty, arm×difficulty (requested)", "y ~ off * lowM + C(diff) + off:C(diff)"),
         ("+ difficulty, log(1+added), multi-file, each × arm", "y ~ off * lowM + C(diff) + off:C(diff) + logadd + off:logadd + multi + off:multi")]
L += ["(b) GEE logit, instance-clustered, exchangeable. Coefficient = off×lowM (log ratio of odds ratios, Low vs High); >0 = larger OFF effect in Low-M.", "",
      "| contrast | model | off×lowM log-ROR | SE | ROR [95% CI] | p |", "|---|---|---|---|---|---|"]
for nm, data in (("OFF−ON", lg), ("OFF−T", lgT)):
    for lab, f in forms:
        fit = smf.gee(f, groups="iid", data=data, family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
        b, se = fit.params["off:lowM"], fit.bse["off:lowM"]
        if not np.isfinite(se):   # quasi-separation: T resolves 0/45 in the >=1h stratum -> 2-level difficulty
            f = f.replace("C(diff)", "C(diff2)")
            lab = lab + " [difficulty collapsed to <15m / >=15m: T resolves 0 in >=1h]"
            fit = smf.gee(f, groups="iid", data=data, family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
            b, se = fit.params["off:lowM"], fit.bse["off:lowM"]
        out[(nm, "GEE " + lab)] = dict(b=b, se=se, p=fit.pvalues["off:lowM"])
        L.append(f"| {nm} | {lab} | {b:+.3f} | {se:.3f} | {math.exp(b):.2f} [{math.exp(b-1.96*se):.2f}, {math.exp(b+1.96*se):.2f}] | {fp(fit.pvalues['off:lowM'])} |")
L.append("")

# --- (c) RD regression with CR2 by repository
L += ["(c) Risk-difference regression of the paired d on lowM + covariates, CR2 (Bell–McCaffrey) by repository (G=12):", "",
      "| contrast | covariates | lowM coef = Low−High (pp) | CR2 SE | df | 95% CI | p |", "|---|---|---|---|---|---|---|"]
for nm, col in (("OFF−ON", "d"), ("OFF−T", "dT")):
    s = df[~df[col].isna()]
    for lab, X in (("none", np.column_stack([np.ones(len(s)), s.lowM])),
                   ("difficulty", np.column_stack([np.ones(len(s)), s.lowM, (s["diff"] == "15m-1h"), (s["diff"] == ">=1h")]).astype(float)),
                   ("difficulty + log(1+added) + multi", np.column_stack([np.ones(len(s)), s.lowM, (s["diff"] == "15m-1h"), (s["diff"] == ">=1h"), s.logadd, s.multi]).astype(float))):
        c = np.zeros(X.shape[1]); c[1] = 1
        r = cra.cr2_bm(s[col].values, s.repo.values, X=X, c=c)
        out[(nm, "RD " + lab)] = r
        L.append(f"| {nm} | {lab} | {pp(r['est'], 2)} | {100*r['se']:.2f} | {r['df']:.1f} | {ci((r['lo'], r['hi']))} | {fp(r['p'])} |")
L.append("")
write_md("t8_e5_difficulty", "\n".join(L) + "\n")
dump("t8_e5_difficulty", {" | ".join(k): v for k, v in out.items()})
