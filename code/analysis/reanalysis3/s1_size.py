"""Analysis 1 (POST HOC): size of the wild cluster bootstrap (and CR2-BM, sign-flip, the registered percentile
cluster bootstrap, McNemar, iid z) under the ACTUAL cluster structure of the confirmatory contrasts (G=12,
django 231/500), plus a diagnosis of why the wild CI's lower bound is tighter than the iid one.

Null DGPs (both keep the observed instance-level |d| pattern and cluster sizes; true mean difference = 0):
  A (requested): ON/OFF labels swapped at random WITHIN INSTANCE -> d*_i = s_i d_i, s_i iid +-1.  R = 2,000.
  B (harsher, added): labels swapped for WHOLE REPOSITORIES -> d*_g = s_g d_g; keeps any within-repository
    heterogeneity of the effect. Exact enumeration of all 2^12 = 4,096 patterns (no Monte Carlo for the outer loop).
Per replicate: WCR-Webb wild with B=999 fresh weights (the paper's procedure, smaller B); CR2-BM t-test (df fixed
by the cluster sizes); exact sign-flip; registered percentile bootstrap (999 reps; reject if 95% CI excludes 0);
exact McNemar; iid z. Rejection = p < 0.05 (pct: CI excludes 0).
"""
import itertools
import math

import numpy as np
from scipy import stats

from common3 import (arm, dvec, repo, cluster_sums, webb_weights, wild_pfun_sums, wild, cr2_bm, cr2_fast_factory,
                     iid, mcnemar, signflip, pp, ci, fp, write_md, dump)

R_A = 2000
B_SIM = 999
ALPHA = 0.05
import os
SIZE_SEED = int(os.environ.get("RA3_SIZE_SEED", "20261016"))
rng = np.random.default_rng(SIZE_SEED)
B_SIM = int(os.environ.get("RA3_BSIM", "999"))
OUTNAME = "s1_size" if (SIZE_SEED == 20261016 and B_SIM == 999) else f"s1_size_seed{SIZE_SEED}_B{B_SIM}"

STRUCT = {
    "Qwen3.6-27B K=12 (n=499)": ("q36_k12_OFF", "q36_k12_ON"),
    "gpt re-run (n=500)": ("gpt_lr_OFF", "gpt_lr_ON"),
    "gpt discovery draw (n=500)": ("gpt_hl_OFF", "gpt_hl_ON"),
}
FLIPS = np.array(list(itertools.product([1, -1], repeat=12)), float)


def one_rep(S, n, W, cr2f, d_inst=None):
    """p-values for one null data set given cluster sums S (and instance d for McNemar/iid)."""
    out = {}
    pf = wild_pfun_sums(S, n, W)
    out["wild"] = pf(0.0)
    out["cr2"] = cr2f(S)[2]
    out["flip"] = float(np.mean(np.abs(FLIPS @ S) >= abs(S.sum()) - 1e-9))
    k = rng.integers(0, len(n), size=(B_SIM, len(n)))
    v = np.sort(S[k].sum(1) / n[k].sum(1))
    lo, hi = v[int(0.025 * B_SIM)], v[int(0.975 * B_SIM) - 1]
    out["pct_reject"] = bool(lo > 0 or hi < 0)
    if d_inst is not None:
        b, c = int((d_inst > 0).sum()), int((d_inst < 0).sum())
        out["mcnemar"] = mcnemar(b, c)
        out["iid"] = iid(d_inst)["p"]
    return out


res = {}
L = ["## Analysis 1 — Wild-bootstrap size check under the actual cluster structure (POST HOC)", "",
     "Null data are generated from each confirmatory contrast's own instances: the observed paired differences d_i, "
     "repository labels and cluster sizes are kept and the ON/OFF labels are randomised, so the true mean difference is 0. "
     "DGP A (requested) swaps labels within instance (d*_i = s_i·d_i), R = 2,000 replicates. "
     "DGP B (added; harsher) swaps labels for whole repositories (d*_g = s_g·d_g), all 4,096 patterns enumerated, which keeps "
     "between-repository effect heterogeneity. Each replicate runs the paper's WCR-Webb wild bootstrap-t (B = 999 fresh weights), "
     "CR2 with BM df, the exact repository sign-flip, the registered percentile repository bootstrap (999 reps; reject if the 95% CI excludes 0), "
     "exact McNemar and an iid z-test. Nominal α = 0.05. MC SE of a rate near 0.05 at R = 2,000 is ≈ 0.005.", ""]

for lab, (offk, onk) in STRUCT.items():
    A_off, A_on = arm(offk), arm(onk)
    ids = sorted(A_on.sub & A_off.sub)
    d, ids = dvec(ids, A_off.res, A_on.res)
    cl = np.array([repo(i) for i in ids])
    S0, n, labs = cluster_sums(d, cl)
    cr2f = cr2_fast_factory(n)
    # check the fast CR2 against the general implementation on the observed data
    chk_fast = cr2f(S0)
    chk_full = cr2_bm(d, cl)
    assert abs(chk_fast[1] - chk_full["se"]) < 1e-12 and abs(cr2f.df - chk_full["df"]) < 1e-9, (chk_fast, chk_full)
    gidx = np.array([labs.index(c) for c in cl])
    # ---- DGP A
    rejA = {k: [] for k in ("wild", "cr2", "flip", "pct_reject", "mcnemar", "iid")}
    for r in range(R_A):
        s = rng.choice([-1.0, 1.0], size=len(d))
        dstar = s * d
        S = np.bincount(gidx, weights=dstar, minlength=len(n))
        W = webb_weights(len(n), B_SIM, seed=int(rng.integers(1 << 31)))
        o = one_rep(S, n, W, cr2f, dstar)
        for k in rejA:
            rejA[k].append(o[k] if k == "pct_reject" else o[k] < ALPHA)
    rateA = {k: float(np.mean(v)) for k, v in rejA.items()}
    # ---- DGP B (exact enumeration of the 4,096 repository sign patterns)
    rejB = {k: [] for k in ("wild", "cr2", "flip", "pct_reject")}
    for s in FLIPS:
        S = s * S0
        W = webb_weights(len(n), B_SIM, seed=int(rng.integers(1 << 31)))
        o = one_rep(S, n, W, cr2f)
        for k in rejB:
            rejB[k].append(o[k] if k == "pct_reject" else o[k] < ALPHA)
    rateB = {k: float(np.mean(v)) for k, v in rejB.items()}
    disc = int((d != 0).sum())
    dj = labs.index("django/django")
    res[lab] = dict(n=len(d), G=len(n), discordant=disc, cluster_sizes=dict(zip(labs, n.tolist())),
                    discordant_by_repo={labs[g]: int(((d != 0) & (gidx == g)).sum()) for g in range(len(n))},
                    cr2_df=cr2f.df, rate_A=rateA, rate_B=rateB, R_A=R_A, B_sim=B_SIM,
                    django_share_n=float(n[dj] / n.sum()), django_share_disc=float(((d != 0) & (gidx == dj)).sum() / disc))

L += ["| instance structure | n | discordant (django) | CR2 df | DGP | wild (WCR-Webb) | CR2-BM | sign-flip | registered pct bootstrap | McNemar | iid z |",
      "|---|---|---|---|---|---|---|---|---|---|---|"]
for lab, r in res.items():
    a, b = r["rate_A"], r["rate_B"]
    dj = r["discordant_by_repo"]["django/django"]
    L.append(f"| {lab} | {r['n']} | {r['discordant']} ({dj}) | {r['cr2_df']:.2f} | A: within-instance swap, R=2,000 | **{a['wild']:.3f}** | **{a['cr2']:.3f}** | {a['flip']:.3f} | {a['pct_reject']:.3f} | {a['mcnemar']:.3f} | {a['iid']:.3f} |")
    L.append(f"| | | | | B: whole-repository swap, all 4,096 | **{b['wild']:.3f}** | **{b['cr2']:.3f}** | {b['flip']:.3f} | {b['pct_reject']:.3f} | — | — |")
L.append("")

# =============================================================== why is the wild lower bound tighter than iid?
A_off, A_on = arm("gpt_lr_OFF"), arm("gpt_lr_ON")
d, ids = dvec(sorted(A_on.sub & A_off.sub), A_off.res, A_on.res)
cl = [repo(i) for i in ids]
S0, n, labs = cluster_sums(d, cl)
w = wild(d, cl, B=9999, alphas=(0.05,), step=0.0001, hw=0.12)
pf = w["_pf"]
ii = iid(d)
c2 = cr2_bm(d, cl)
G = len(n)
se1 = pf.se_cr1
tq = stats.t.ppf(0.975, G - 1)
# unrestricted wild (WCU) percentile-t: bootstrap t built from residuals around the estimate (not null-imposed)
Wm = webb_weights(G, 9999)
resid = S0 - n * pf.est
c1 = G / (G - 1)
m_u = (Wm * resid).sum(1) / n.sum()
se_u = np.sqrt(c1 * ((Wm * resid - np.outer(m_u, n)) ** 2).sum(1)) / n.sum()
t_u = m_u / se_u
q_u = np.quantile(np.abs(t_u), 0.95)
q_lo, q_hi = np.quantile(t_u, [0.025, 0.975])
probe = [0.0, 0.010, 0.020, 0.030, 0.0319, 0.035, 0.040, pf.est, 0.08, 0.10, 0.1131, 0.12]
tab = []
for b0 in probe:
    ts = pf.tstar(b0)
    S = S0 - b0 * n
    share = float(S[labs.index("django/django")] ** 2 / (S ** 2).sum())
    tab.append(dict(b0=b0, t_obs=(pf.est - b0) / se1, c95=float(np.quantile(np.abs(ts), 0.95)), p=pf(b0), django_share_sq=share,
                    frac_abs_t_star_in_0p9_1p1=float(np.mean((np.abs(ts) > 0.9) & (np.abs(ts) < 1.1)))))
ex = dict(est=pf.est, se_iid=ii["se"], se_cr1=se1, se_cr2=c2["se"], cr2_df=c2["df"], iid_ci=ii["ci95"],
          cr1_normal_ci=(pf.est - 1.96 * se1, pf.est + 1.96 * se1), cr1_t11_ci=(pf.est - tq * se1, pf.est + tq * se1),
          cr2_ci=c2["ci95"], wild_ci=w["ci95"], wild_pieces=w.get("ci95_pieces"), wcu_sym_ci=(pf.est - q_u * se1, pf.est + q_u * se1),
          wcu_eqtail_ci=(pf.est - q_hi * se1, pf.est - q_lo * se1), probe=tab,
          cluster=[dict(repo=labs[g], n=int(n[g]), sum_d=float(S0[g]), mean_d=float(S0[g] / n[g])) for g in range(G)])
res["ci_diagnosis_gpt_rerun"] = ex

L += ["### Why the re-run's wild 95% CI [+3.2, +11.3] has a tighter lower bound than the iid CI", "",
      f"Re-run, n = {len(d)}: Δ = {pp(pf.est, 2)}. Interval constructions (all 95%):", "",
      "| construction | SE (pp) | 95% CI |", "|---|---|---|",
      f"| iid (instance) normal | {100*ii['se']:.2f} | {ci(ii['ci95'], 2)} |",
      f"| CR1 (repository) SE, normal | {100*se1:.2f} | {ci(ex['cr1_normal_ci'], 2)} |",
      f"| CR1 SE, t(G−1 = 11) | {100*se1:.2f} | {ci(ex['cr1_t11_ci'], 2)} |",
      f"| CR2 SE, t(BM df = {c2['df']:.2f}) | {100*c2['se']:.2f} | {ci(c2['ci95'], 2)} |",
      f"| wild WCU (unrestricted), symmetric percentile-t | {100*se1:.2f} | {ci(ex['wcu_sym_ci'], 2)} |",
      f"| wild WCU, equal-tailed percentile-t | {100*se1:.2f} | {ci(ex['wcu_eqtail_ci'], 2)} |",
      f"| **wild WCR (the paper's), test inversion, 0.01pp grid** | {100*se1:.2f} (observed t uses CR1) | **{ci(w['ci95'], 2)}** ({w.get('ci95_pieces')} piece) |", "",
      "Test inversion: at each candidate b0 the WCR bootstrap imposes Δ = b0 when building the bootstrap samples and keeps b0 in the CI iff p(b0) > 0.05. "
      "The observed statistic t(b0) = (Δ̂ − b0)/SE_CR1 uses one fixed CR1 SE; only the bootstrap reference distribution changes with b0:", "",
      "| b0 (pp) | observed t(b0) | 95% quantile of abs(t*) under b0 | p(b0) | django share of Σ(restricted cluster sum)² | share of abs(t*) in (0.9, 1.1) |", "|---|---|---|---|---|---|"]
for t in tab:
    L.append(f"| {100*t['b0']:+.2f} | {t['t_obs']:+.2f} | {t['c95']:.2f} | {t['p']:.4f} | {t['django_share_sq']:.2f} | {t['frac_abs_t_star_in_0p9_1p1']:.2f} |")
L.append("")
# (a) exact repository sign-flip CI by inversion (H0: Δ = b0 on restricted sums S_g - b0 n_g)
grid = np.arange(-0.02, 0.16, 0.0001)
pflip = np.array([float(np.mean(np.abs(FLIPS @ (S0 - b * n)) >= abs((S0 - b * n).sum()) - 1e-9)) for b in grid])
acc = grid[pflip > 0.05]
ex["flip_inversion_ci"] = (float(acc.min()), float(acc.max()))
# (b) size of the WCR test AT the CI endpoints under a repository-symmetric null centred at b0:
#     S*_g = b0 n_g + s_g (S_g - b0 n_g), all 4,096 s; reject if WCR p(b0) < 0.05 (B = 999 fresh weights)
endp = {}
for nm, b0 in (("lower", w["ci95"][0]), ("upper", w["ci95"][1]), ("zero", 0.0)):
    r0 = S0 - b0 * n
    rej = rej_c = 0
    cr2f = cr2_fast_factory(n)
    for s in FLIPS:
        S = b0 * n + s * r0
        W = webb_weights(G, B_SIM, seed=int(rng.integers(1 << 31)))
        pfx = wild_pfun_sums(S, n, W)
        rej += pfx(b0) < 0.05
        est, se, _ = cr2f(S)
        rej_c += 2 * stats.t.sf(abs((est - b0) / se), cr2f.df) < 0.05
    endp[nm] = dict(b0=b0, wild=rej / len(FLIPS), cr2=rej_c / len(FLIPS))
ex["endpoint_size_repo_symmetric"] = endp
L += [f"Exact repository sign-flip test inverted (0.01pp grid): 95% CI {ci(ex['flip_inversion_ci'], 2)}.", "",
      "Rejection rate of the test of H0: Δ = b0 when the truth is Δ = b0 and the 12 restricted repository sums are sign-symmetric "
      "(all 4,096 patterns S*_g = b0·n_g ± (S_g − b0·n_g); inner WCR B = 999):", "",
      "| b0 | wild WCR | CR2-BM |", "|---|---|---|"]
for nm, e in endp.items():
    L.append(f"| {nm} ({100*e['b0']:+.2f}pp) | {e['wild']:.3f} | {e['cr2']:.3f} |")
L.append("")
L += ["Per-repository contributions (re-run):", "", "| repository | n | Σd | mean d (pp) |", "|---|---|---|---|"]
for c in ex["cluster"]:
    L.append(f"| {c['repo']} | {c['n']} | {c['sum_d']:+.0f} | {100*c['mean_d']:+.1f} |")
L.append("")
L.append(f"Outer-loop seed: {SIZE_SEED}.")
write_md(OUTNAME, "\n".join(L) + "\n")
dump(OUTNAME, res)
