## Task 8 — E5 (Qwen3-Coder-30B) Low-M vs High-M with a difficulty control

Primary cell OFF−ON (n=500, one draw); secondary OFF−T (n=473). Interaction reported as **Low−High** (paper's E3 = High−Low, so the paper's −5.0 is +5.0 here).

Covariate balance (is Low-M easier?):

| stratum | n | <15m | 15m–1h | ≥1h | mean added lines | median added | multi-file share | ON resolve | OFF resolve |
|---|---|---|---|---|---|---|---|---|---|
| Low-M | 222 | 39.2% | 52.3% | 8.6% | 9.5 | 4 | 13.1% | 4.1% | 12.6% |
| High-M | 278 | 38.5% | 52.2% | 9.4% | 10.3 | 5 | 15.1% | 8.6% | 12.2% |

(a) Stratified Low−High interaction (MH-style weights n_l·n_h/(n_l+n_h); SE from within-cell variances; bootstrap CI resamples within cells, B=10,000):

| contrast | stratification | cells used | n used | Low−High (pp) | SE | 95% CI (normal) | 95% CI (bootstrap) | two-sided p |
|---|---|---|---|---|---|---|---|---|
| OFF−ON | none (crude; Δlow +8.6 n=222, Δhigh +3.6 n=278) | 1 | 500 | +4.96 | 2.80 | [-0.5, +10.4] | — | 0.0763 |
| OFF−ON | difficulty (3) | 3 | 500 | +4.91 | 2.78 | [-0.5, +10.4] | [-0.4, +10.4] | 0.0773 |
| OFF−ON | difficulty × multi-file (6) | 6 | 500 | +4.85 | 2.80 | [-0.6, +10.3] | [-0.6, +10.2] | 0.0827 |
| OFF−ON | difficulty × multi-file × added-lines tercile (18) | 13 | 497 | +4.55 | 2.76 | [-0.9, +10.0] | [-0.7, +9.9] | 0.1000 |
| OFF−T | none (crude; Δlow +8.6 n=210, Δhigh +4.2 n=263) | 1 | 473 | +4.39 | 2.92 | [-1.3, +10.1] | — | 0.133 |
| OFF−T | difficulty (3) | 3 | 473 | +4.33 | 2.91 | [-1.4, +10.0] | [-1.5, +10.2] | 0.138 |
| OFF−T | difficulty × multi-file (6) | 6 | 473 | +4.20 | 2.94 | [-1.6, +10.0] | [-1.4, +10.1] | 0.153 |
| OFF−T | difficulty × multi-file × added-lines tercile (18) | 13 | 470 | +3.61 | 2.86 | [-2.0, +9.2] | [-1.9, +9.2] | 0.208 |

Per-difficulty cells, OFF−ON:

| difficulty | n low / high | Δlow | Δhigh | Low−High |
|---|---|---|---|---|
| 15m-1h | 116 / 145 | +5.2 | +2.8 | +2.4 |
| <15m | 87 / 107 | +14.9 | +4.7 | +10.3 |
| >=1h | 19 / 26 | +0.0 | +3.8 | -3.8 |

(b) GEE logit, instance-clustered, exchangeable. Coefficient = off×lowM (log ratio of odds ratios, Low vs High); >0 = larger OFF effect in Low-M.

| contrast | model | off×lowM log-ROR | SE | ROR [95% CI] | p |
|---|---|---|---|---|---|
| OFF−ON | unadjusted | +0.840 | 0.383 | 2.32 [1.09, 4.91] | 0.0283 |
| OFF−ON | + difficulty, arm×difficulty (requested) | +0.862 | 0.394 | 2.37 [1.09, 5.12] | 0.0287 |
| OFF−ON | + difficulty, log(1+added), multi-file, each × arm | +0.878 | 0.394 | 2.41 [1.11, 5.21] | 0.0259 |
| OFF−T | unadjusted | +0.672 | 0.376 | 1.96 [0.94, 4.09] | 0.0738 |
| OFF−T | + difficulty, arm×difficulty (requested) [difficulty collapsed to <15m / >=15m: T resolves 0 in >=1h] | +0.689 | 0.384 | 1.99 [0.94, 4.23] | 0.0725 |
| OFF−T | + difficulty, log(1+added), multi-file, each × arm [difficulty collapsed to <15m / >=15m: T resolves 0 in >=1h] | +0.703 | 0.392 | 2.02 [0.94, 4.36] | 0.0733 |

(c) Risk-difference regression of the paired d on lowM + covariates, CR2 (Bell–McCaffrey) by repository (G=12):

| contrast | covariates | lowM coef = Low−High (pp) | CR2 SE | df | 95% CI | p |
|---|---|---|---|---|---|---|
| OFF−ON | none | +4.96 | 2.97 | 3.5 | [-3.8, +13.8] | 0.181 |
| OFF−ON | difficulty | +4.91 | 3.08 | 3.5 | [-4.2, +14.0] | 0.197 |
| OFF−ON | difficulty + log(1+added) + multi | +4.74 | 3.04 | 3.5 | [-4.2, +13.7] | 0.204 |
| OFF−T | none | +4.39 | 1.83 | 3.5 | [-1.0, +9.8] | 0.0837 |
| OFF−T | difficulty | +4.33 | 1.98 | 3.5 | [-1.5, +10.2] | 0.105 |
| OFF−T | difficulty + log(1+added) + multi | +4.00 | 1.95 | 3.5 | [-1.7, +9.7] | 0.119 |

