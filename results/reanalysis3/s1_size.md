## Analysis 1 — Wild-bootstrap size check under the actual cluster structure (POST HOC)

Null data are generated from each confirmatory contrast's own instances: the observed paired differences d_i, repository labels and cluster sizes are kept and the ON/OFF labels are randomised, so the true mean difference is 0. DGP A (requested) swaps labels within instance (d*_i = s_i·d_i), R = 2,000 replicates. DGP B (added; harsher) swaps labels for whole repositories (d*_g = s_g·d_g), all 4,096 patterns enumerated, which keeps between-repository effect heterogeneity. Each replicate runs the paper's WCR-Webb wild bootstrap-t (B = 999 fresh weights), CR2 with BM df, the exact repository sign-flip, the registered percentile repository bootstrap (999 reps; reject if the 95% CI excludes 0), exact McNemar and an iid z-test. Nominal α = 0.05. MC SE of a rate near 0.05 at R = 2,000 is ≈ 0.005.

| instance structure | n | discordant (django) | CR2 df | DGP | wild (WCR-Webb) | CR2-BM | sign-flip | registered pct bootstrap | McNemar | iid z |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3.6-27B K=12 (n=499) | 499 | 48 (28) | 3.33 | A: within-instance swap, R=2,000 | **0.051** | **0.041** | 0.021 | 0.091 | 0.029 | 0.055 |
| | | | | B: whole-repository swap, all 4,096 | **0.057** | **0.031** | 0.016 | 0.078 | — | — |
| gpt re-run (n=500) | 500 | 103 (48) | 3.33 | A: within-instance swap, R=2,000 | **0.049** | **0.027** | 0.032 | 0.076 | 0.045 | 0.045 |
| | | | | B: whole-repository swap, all 4,096 | **0.058** | **0.062** | 0.043 | 0.105 | — | — |
| gpt discovery draw (n=500) | 500 | 108 (48) | 3.33 | A: within-instance swap, R=2,000 | **0.059** | **0.031** | 0.036 | 0.100 | 0.051 | 0.051 |
| | | | | B: whole-repository swap, all 4,096 | **0.060** | **0.131** | 0.039 | 0.113 | — | — |

### Why the re-run's wild 95% CI [+3.2, +11.3] has a tighter lower bound than the iid CI

Re-run, n = 500: Δ = +5.40. Interval constructions (all 95%):

| construction | SE (pp) | 95% CI |
|---|---|---|
| iid (instance) normal | 2.02 | [+1.45, +9.35] |
| CR1 (repository) SE, normal | 1.45 | [+2.55, +8.25] |
| CR1 SE, t(G−1 = 11) | 1.45 | [+2.20, +8.60] |
| CR2 SE, t(BM df = 3.33) | 1.64 | [+0.47, +10.33] |
| wild WCU (unrestricted), symmetric percentile-t | 1.45 | [+1.80, +9.00] |
| wild WCU, equal-tailed percentile-t | 1.45 | [+1.81, +9.02] |
| **wild WCR (the paper's), test inversion, 0.01pp grid** | 1.45 (observed t uses CR1) | **[+3.19, +11.31]** (1 piece) |

Test inversion: at each candidate b0 the WCR bootstrap imposes Δ = b0 when building the bootstrap samples and keeps b0 in the CI iff p(b0) > 0.05. The observed statistic t(b0) = (Δ̂ − b0)/SE_CR1 uses one fixed CR1 SE; only the bootstrap reference distribution changes with b0:

| b0 (pp) | observed t(b0) | 95% quantile of abs(t*) under b0 | p(b0) | django share of Σ(restricted cluster sum)² | share of abs(t*) in (0.9, 1.1) |
|---|---|---|---|---|---|
| +0.00 | +3.72 | 3.10 | 0.0187 | 0.49 | 0.07 |
| +1.00 | +3.03 | 2.66 | 0.0233 | 0.37 | 0.07 |
| +2.00 | +2.34 | 2.16 | 0.0270 | 0.20 | 0.09 |
| +3.00 | +1.65 | 1.61 | 0.0396 | 0.03 | 0.11 |
| +3.19 | +1.52 | 1.52 | 0.0502 | 0.01 | 0.12 |
| +3.50 | +1.31 | 1.49 | 0.1236 | 0.00 | 0.13 |
| +4.00 | +0.96 | 1.66 | 0.3202 | 0.05 | 0.12 |
| +5.40 | +0.00 | 2.48 | 1.0000 | 0.41 | 0.07 |
| +8.00 | -1.79 | 3.40 | 0.2991 | 0.77 | 0.08 |
| +10.00 | -3.17 | 3.78 | 0.0892 | 0.83 | 0.09 |
| +11.31 | -4.07 | 4.07 | 0.0501 | 0.84 | 0.09 |
| +12.00 | -4.54 | 4.20 | 0.0413 | 0.85 | 0.09 |

Exact repository sign-flip test inverted (0.01pp grid): 95% CI [+3.07, +12.37].

Rejection rate of the test of H0: Δ = b0 when the truth is Δ = b0 and the 12 restricted repository sums are sign-symmetric (all 4,096 patterns S*_g = b0·n_g ± (S_g − b0·n_g); inner WCR B = 999):

| b0 | wild WCR | CR2-BM |
|---|---|---|
| lower (+3.19pp) | 0.051 | 0.000 |
| upper (+11.31pp) | 0.054 | 0.091 |
| zero (+0.00pp) | 0.057 | 0.062 |

Per-repository contributions (re-run):

| repository | n | Σd | mean d (pp) |
|---|---|---|---|
| astropy/astropy | 22 | +5 | +22.7 |
| django/django | 231 | +8 | +3.5 |
| matplotlib/matplotlib | 34 | -1 | -2.9 |
| mwaskom/seaborn | 2 | +0 | +0.0 |
| pallets/flask | 1 | +1 | +100.0 |
| psf/requests | 8 | +2 | +25.0 |
| pydata/xarray | 22 | +2 | +9.1 |
| pylint-dev/pylint | 10 | +1 | +10.0 |
| pytest-dev/pytest | 19 | +1 | +5.3 |
| scikit-learn/scikit-learn | 32 | +1 | +3.1 |
| sphinx-doc/sphinx | 44 | +2 | +4.5 |
| sympy/sympy | 75 | +5 | +6.7 |

Outer-loop seed: 20261016.
