"""Task 4: recompute every MDE by exact-McNemar power at 80% (alpha = 0.05 two-sided).

Unconditional power: D ~ Binom(n, psi) discordant pairs, b | D ~ Binom(D, p_b/psi); reject if the exact
McNemar p <= 0.05. Power is computed exactly by enumeration over (D, b) and confirmed by Monte-Carlo
simulation (200,000 replicate trials at the MDE). Three assumptions are reported:
  (C) the paper's convention: D fixed at the observed discordant count (conditional power);
  (A) total discordance rate psi = observed (b+c)/n held fixed, D random;  MDE must be <= psi;
  (B) the ON-only (breadth-wins) discordance rate p_c held at its observed value, p_b = p_c + Delta.
Power at observed |Delta| uses the observed p_b, p_c (assumption A at the observed split).
"""
from __future__ import annotations

import json

import numpy as np
from scipy import stats

from common_ra import OUT, fmt_p

ROWS = [  # label, n, observed delta pp, b (OFF-only), c (ON-only), raw p (paper), paper MDE
    ("agentic fusion (sonnet-5)", 499, -1.4, 28, 35, 0.45, 4.5),
    ("agentic dense (sonnet-5)", 499, -1.8, 18, 27, 0.23, 3.8),
    ("Qwen2.5-Coder-32B", 98, +2.0, 4, 2, 0.69, 5.7),
    ("agentic BM25 (opus-4-8)", 100, -2.0, 2, 4, 0.69, 5.6),
    ("agentic dense (opus-4-8)", 100, -2.0, 2, 4, 0.69, 5.6),
    ("A3B K=4 (text, §5.9)", 500, +2.0, 26, 16, 0.164, 3.6),
    ("SWE-PolyBench pooled (text, §5.10)", 617, +2.59, 39, 23, 0.056, 3.6),
]
ALPHA = 0.05
_rej_cache = {}


def rejection(D):
    """Boolean array over b = 0..D: exact two-sided McNemar p <= alpha."""
    if D not in _rej_cache:
        b = np.arange(D + 1)
        k = np.minimum(b, D - b)
        p = np.minimum(1.0, 2 * stats.binom.cdf(k, D, 0.5)) if D > 0 else np.ones(1)
        _rej_cache[D] = p <= ALPHA + 1e-12
    return _rej_cache[D]


def power_cond(D, pi):
    if D == 0:
        return 0.0
    return float((stats.binom.pmf(np.arange(D + 1), D, pi) * rejection(D)).sum())


def power_uncond(n, pb, pc):
    psi = pb + pc
    if psi <= 0:
        return 0.0
    pi = pb / psi
    PD = stats.binom.pmf(np.arange(n + 1), n, psi)
    tot = 0.0
    for D in range(n + 1):
        if PD[D] < 1e-14:
            continue
        tot += PD[D] * power_cond(D, pi)
    return tot


def simulate(n, pb, pc, reps=200_000, seed=20261014):
    rng = np.random.default_rng(seed)
    cnt = rng.multinomial(n, [pb, pc, 1 - pb - pc], size=reps)
    b, c = cnt[:, 0], cnt[:, 1]
    D = b + c
    k = np.minimum(b, c)
    p = np.where(D > 0, np.minimum(1.0, 2 * stats.binom.cdf(k, np.maximum(D, 1), 0.5)), 1.0)
    return float((p <= ALPHA + 1e-12).mean())


def mde_search(fn, hi, step=0.0005):
    """Smallest Delta on the grid with power >= 0.8 (and power stays >= 0.8 at the next 4 grid points)."""
    grid = np.arange(step, hi + 1e-12, step)
    pw = [fn(x) for x in grid]
    for i, (x, p) in enumerate(zip(grid, pw)):
        if p >= 0.8 and all(q >= 0.8 for q in pw[i:i + 5]):
            return float(x)
    return None


def main():
    out = []
    for lab, n, dobs, b, c, praw, mde_paper in ROWS:
        D = b + c
        psi = D / n
        pc_rate = c / n
        # (C) conditional on observed D, Delta = psi*(2*pi-1)
        mC = mde_search(lambda x: power_cond(D, 0.5 + x / (2 * psi)) if x <= psi else 0.0, psi)
        # (A) psi fixed, D random
        mA = mde_search(lambda x: power_uncond(n, (psi + x) / 2, (psi - x) / 2) if x <= psi else 0.0, psi)
        pwC_atC = power_cond(D, 0.5 + mC / (2 * psi)) if mC else None
        pwA_atC = power_uncond(n, (psi + mC) / 2, (psi - mC) / 2) if mC else None
        # (B) p_c fixed at the observed ON-only rate
        mB = mde_search(lambda x: power_uncond(n, pc_rate + x, pc_rate), 0.5)
        simA = simulate(n, (psi + mA) / 2, (psi - mA) / 2) if mA else None
        simB = simulate(n, pc_rate + mB, pc_rate) if mB else None
        # power at observed |Delta| at the observed split
        pb_o, pc_o = max(b, c) / n, min(b, c) / n
        pw_obs = power_uncond(n, pb_o, pc_o)
        pw_obs_sim = simulate(n, pb_o, pc_o)
        out.append(dict(arm=lab, n=n, d_obs=dobs, b=b, c=c, D=D, psi=psi, pc=pc_rate, p_raw=praw, mde_paper=mde_paper,
                        mde_C=100 * mC if mC else None, power_paper_mde_uncond=pwA_atC,
                        mde_A=100 * mA if mA else None, simA=simA, mde_B=100 * mB if mB else None, simB=simB,
                        power_obs=pw_obs, power_obs_sim=pw_obs_sim))
    json.dump(out, open(OUT / "t4_mde.json", "w"), indent=1)

    f = lambda x: "not attainable (> ψ)" if x is None else f"{x:.1f}pp"
    L = ["## Task 4 — MDE at 80% power, exact McNemar (α = 0.05 two-sided)", "",
         "ψ = observed discordance rate (b+c)/n; p_c = observed ON-only (breadth-wins) discordance rate. "
         "(C) = paper convention, discordant count D fixed at the observed value (conditional power). "
         "(A) = ψ fixed, D ~ Binom(n, ψ) random (unconditional). (B) = p_c fixed, p_b = p_c + Δ (discordance grows with Δ). "
         "Power is exact enumeration over (D, b); bracketed values are Monte-Carlo checks (200,000 simulated trials). "
         "'Power at obs.' = unconditional power at the observed split (|Δ|, observed p_b and p_c).", "",
         "| null arm | n | Δ obs | disc OFF/ON | ψ | raw p | paper MDE | MDE (C) | uncond. power at (C) MDE | MDE (A) [sim power] | MDE (B) [sim power] | power at obs. Δ [sim] |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in out:
        L.append(f"| {r['arm']} | {r['n']} | {r['d_obs']:+.1f}pp | {r['b']}/{r['c']} | {100*r['psi']:.1f}% | {fmt_p(r['p_raw'])} | "
                 f"{r['mde_paper']:.1f}pp | {f(r['mde_C'])} | {100*r['power_paper_mde_uncond']:.0f}% | "
                 f"{f(r['mde_A'])}" + (f" [{100*r['simA']:.1f}%]" if r['simA'] else "") + " | "
                 f"{f(r['mde_B'])}" + (f" [{100*r['simB']:.1f}%]" if r['simB'] else "") + " | "
                 f"{100*r['power_obs']:.0f}% [{100*r['power_obs_sim']:.0f}%] |")
    txt = "\n".join(L) + "\n"
    (OUT / "t4_mde.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
