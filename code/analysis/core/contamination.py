"""Contamination-dosage stratification (paper Sec. 'Contamination-dosage stratification').

Stratifies the per-repository dedup effect (Delta = OFF - ON) by repository popularity
(GitHub stars, a coarse memorization-pressure proxy): Spearman rho between stars and the
per-repository effect, and a median split (high minus low popularity) per arm.

NOTE: the star snapshot used for the paper's numbers was not retained. STARS below are
approximate public GitHub star counts (thousands) and are an input you may replace; the
qualitative result (no popularity dose-response) is what the paper relies on, and exact
rho values depend on the snapshot.

Outputs results/contamination.md and results/contamination_per_repo.csv.
"""
from __future__ import annotations

from scipy.stats import spearmanr

from common import RESULTS, load_inclusion, paired, repo_of, write_csv, binom_two_sided

STARS_K = {  # approximate, thousands of GitHub stars
    "astropy/astropy": 4.6, "django/django": 82, "pallets/flask": 69, "matplotlib/matplotlib": 20.5,
    "pylint-dev/pylint": 5.4, "pytest-dev/pytest": 12.3, "psf/requests": 52.5, "scikit-learn/scikit-learn": 61,
    "mwaskom/seaborn": 12.8, "sphinx-doc/sphinx": 6.7, "sympy/sympy": 13.2, "pydata/xarray": 3.7,
}
ARMS = ["P1_gpt_fusion", "P2_deepseek_fusion", "P3_qwen36_fusion_K12", "P4_DENSE1_gpt_dense"]


def main():
    tab = load_inclusion()
    lines = ["# Contamination-dosage stratification (recomputed; approximate star snapshot)", ""]
    per_repo_rows, rhos, hl = [], [], []
    med = sorted(STARS_K.values())[len(STARS_K) // 2 - 1: len(STARS_K) // 2 + 1]
    cut = sum(med) / 2
    for arm in ARMS:
        on, off = tab[(arm, "ON")], tab[(arm, "OFF")]
        rows = paired(on, off)["rows"]
        eff = {}
        for rp in STARS_K:
            sub = [r for r in rows if repo_of(r[0]) == rp]
            if not sub:
                continue
            d = 100 * (sum(1 for _, a, b in sub if b == "resolved") - sum(1 for _, a, b in sub if a == "resolved")) / len(sub)
            eff[rp] = d
            per_repo_rows.append(dict(arm_id=arm, repo=rp, stars_k=STARS_K[rp], n=len(sub), delta_pp=round(d, 2)))
        rho = spearmanr([STARS_K[r] for r in eff], [eff[r] for r in eff]).correlation
        strata = {}
        for name, keep in (("high", lambda r: STARS_K[repo_of(r[0])] > cut), ("low", lambda r: STARS_K[repo_of(r[0])] <= cut)):
            sub = [r for r in rows if keep(r)]
            b = sum(1 for _, a, x in sub if x == "resolved" and a != "resolved")
            c = sum(1 for _, a, x in sub if a == "resolved" and x != "resolved")
            strata[name] = (100 * (b - c) / len(sub), len(sub), binom_two_sided(b, b + c))
        rhos.append(rho); hl.append(strata['high'][0] - strata['low'][0])
        lines.append(f"- {arm}: Spearman rho(stars, per-repo Delta) = {rho:+.2f}; high-popularity Delta "
                     f"{strata['high'][0]:+.1f}pp (n={strata['high'][1]}, p={strata['high'][2]:.3g}); low-popularity Delta "
                     f"{strata['low'][0]:+.1f}pp (n={strata['low'][1]}, p={strata['low'][2]:.3g}); high-low "
                     f"{strata['high'][0]-strata['low'][0]:+.1f}pp")
    write_csv(RESULTS / "contamination_per_repo.csv", per_repo_rows)
    lines += ["", f"Mean across arms: rho = {sum(rhos)/len(rhos):+.2f}; high-minus-low = {sum(hl)/len(hl):+.1f}pp",
              "", f"Median split at {cut:.1f}k stars. Per-repository deltas in contamination_per_repo.csv."]
    (RESULTS / "contamination.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
