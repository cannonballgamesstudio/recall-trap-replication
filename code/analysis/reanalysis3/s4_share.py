"""Analysis 4 (POST HOC): uncertainty for the depth share (OFF-T)/(OFF-ON).

share = depth / G with depth = mean(OFF-T), G = mean(OFF-ON) on the same instances; 1 - share = trim / G.
Bootstraps resample the joint per-instance vector (y_ON, y_OFF, y_T) so numerator and denominator move together:
  instance-paired: resample instances (B = 10,000);  repository cluster: resample the 12 repositories (B = 10,000).
Percentile 95% CIs; also the share of draws with G* <= 0 (where the ratio is undefined / sign-flipped), and Fieller
95% intervals (instance covariance; and CR1 repository covariance with t(11)) as analytic cross-checks.
Replication: seed-averaged y per arm (3 seeds), primary = sphinx-8475 Class-P cells scored unresolved (n = 478);
exclude mode (n = 477) shown because the paper's "92%" was computed there.
"""
import math

import numpy as np
from scipy import stats

from common3 import arm, repo, P5, VIOL, pp, write_md, dump

T_IDS = set((P5 / "b1b3_ids_T.txt").read_text(encoding="utf-8").split())
S8475 = "sphinx-doc__sphinx-8475"
B = 10000


def seedavg(a, ids):
    rs = [arm(f"b_{a}_s{s}").res for s in range(3)]
    return np.array([np.mean([i in r for r in rs]) for i in ids], float)


def fieller(a, b, Vaa, Vbb, Vab, q):
    """CI for a/b given var/cov of the estimators a, b (Fieller). Returns (lo, hi, bounded)."""
    A = b * b - q * q * Vbb
    Bq = a * b - q * q * Vab
    C = a * a - q * q * Vaa
    disc = Bq * Bq - A * C
    if A <= 0 or disc < 0:
        return (float("nan"), float("nan"), False)
    r1, r2 = (Bq - math.sqrt(disc)) / A, (Bq + math.sqrt(disc)) / A
    return (min(r1, r2), max(r1, r2), True)


def share_ci(y_on, y_off, y_t, ids, label):
    ids = list(ids)
    dep = y_off - y_t
    g = y_off - y_on
    n = len(ids)
    est = dep.mean() / g.mean()
    rng = np.random.default_rng(20261016)
    # instance-paired bootstrap
    k = rng.integers(0, n, size=(B, n))
    Gs, Ds = g[k].mean(1), dep[k].mean(1)
    with np.errstate(divide="ignore", invalid="ignore"):
        sh_i = Ds / Gs
    # repository-cluster bootstrap (sums per repo)
    labs = sorted({repo(i) for i in ids})
    gi = np.array([labs.index(repo(i)) for i in ids])
    Sg = np.bincount(gi, weights=g, minlength=len(labs))
    Sd = np.bincount(gi, weights=dep, minlength=len(labs))
    nn = np.bincount(gi, minlength=len(labs)).astype(float)
    kc = rng.integers(0, len(labs), size=(B, len(labs)))
    Gc, Dc = Sg[kc].sum(1) / nn[kc].sum(1), Sd[kc].sum(1) / nn[kc].sum(1)
    with np.errstate(divide="ignore", invalid="ignore"):
        sh_c = Dc / Gc
    # Fieller, instance covariance
    C = np.cov(np.vstack([dep, g]), ddof=1) / n
    fi = fieller(dep.mean(), g.mean(), C[0, 0], C[1, 1], C[0, 1], 1.959964)
    # Fieller, CR1 repository covariance, t(G-1)
    G = len(labs)
    rd = Sd - nn * dep.mean()
    rg = Sg - nn * g.mean()
    c1 = G / (G - 1)
    Vdd, Vgg, Vdg = c1 * (rd ** 2).sum() / n ** 2, c1 * (rg ** 2).sum() / n ** 2, c1 * (rd * rg).sum() / n ** 2
    fc = fieller(dep.mean(), g.mean(), Vdd, Vgg, Vdg, stats.t.ppf(0.975, G - 1))
    return dict(label=label, n=n, G_pp=100 * g.mean(), depth_pp=100 * dep.mean(), trim_pp=100 * (y_t - y_on).mean(), share=est,
                inst_boot_ci95=tuple(np.quantile(sh_i[Gs > 0], [0.025, 0.975])), inst_frac_G_le0=float(np.mean(Gs <= 0)),
                inst_P_share_ge_0p6=float(np.mean((Gs > 0) & (Ds >= 0.6 * Gs))),
                clus_boot_ci95=tuple(np.quantile(sh_c[Gc > 0], [0.025, 0.975])), clus_frac_G_le0=float(np.mean(Gc <= 0)),
                clus_P_share_ge_0p6=float(np.mean((Gc > 0) & (Dc >= 0.6 * Gc))),
                fieller_inst=fi, fieller_cr1=fc)


rows = []
for mode, base in (("scored primary", sorted(T_IDS)), ("exclude (paper's 92%)", sorted(T_IDS - {S8475}))):
    rows.append(share_ci(seedavg("ON", base), seedavg("OFF", base), seedavg("T", base), base, f"replication, 3 seeds, {mode}"))
for lab, onk, offk, tk in (("Qwen3-Coder-30B headline arms, 1 draw (paper: 104%)", "qc_ON", "qc_OFF", "qc_T"),
                           ("gpt vs discovery draw (paper: 81%)", "gpt_hl_ON", "gpt_hl_OFF", "gpt_T"),
                           ("gpt vs logged re-run (paper: 100%)", "gpt_lr_ON", "gpt_lr_OFF", "gpt_T")):
    A_on, A_off, A_t = arm(onk), arm(offk), arm(tk)
    ids = sorted((A_on.sub & A_off.sub & A_t.sub) - set(VIOL))
    f = lambda A: np.array([i in A.res for i in ids], float)
    rows.append(share_ci(f(A_on), f(A_off), f(A_t), ids, lab))


def pc(t):
    return f"[{100*t[0]:.0f}%, {100*t[1]:.0f}%]"


L = ["## Analysis 4 — CI for the depth share (OFF−T)/(OFF−ON) (POST HOC)", "",
     "Bootstraps resample the joint per-instance outcomes so numerator and denominator move together (B = 10,000 each). "
     "The ratio is undefined when G* <= 0; percentile CIs are over the draws with G* > 0 and the share of excluded draws is reported (when it exceeds 2.5% the 95% interval is effectively unbounded on one side). P(share* >= 60%) counts draws with G* > 0 and depth* >= 0.6 G*. Fieller intervals are analytic cross-checks "
     "(instance covariance with z; CR1 repository covariance with t(11)).", "",
     "| row | n | G (pp) | depth (pp) | trim (pp) | **share** | instance-paired boot 95% CI | P(G*≤0) inst | repo-cluster boot 95% CI | P(G*≤0) cluster | Fieller (inst.) | Fieller (CR1, t11) | P(share* ≥ 60%) inst / cluster |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    L.append(f"| {r['label']} | {r['n']} | {r['G_pp']:+.2f} | {r['depth_pp']:+.2f} | {r['trim_pp']:+.2f} | **{100*r['share']:.1f}%** | {pc(r['inst_boot_ci95'])} | {r['inst_frac_G_le0']:.4f} | "
             f"{pc(r['clus_boot_ci95'])} | {r['clus_frac_G_le0']:.4f} | {pc(r['fieller_inst'][:2]) if r['fieller_inst'][2] else 'unbounded'} | "
             f"{pc(r['fieller_cr1'][:2]) if r['fieller_cr1'][2] else 'unbounded'} | {r['inst_P_share_ge_0p6']:.3f} / {r['clus_P_share_ge_0p6']:.3f} |")
L.append("")
write_md("s4_share", "\n".join(L) + "\n")
dump("s4_share", rows)
