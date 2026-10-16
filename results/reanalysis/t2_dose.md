## Task 2 — Qwen3.6-27B dose-response, K = 4 / 12 / 40 (EXPLORATORY)

All three K ran at 32k completion budget, reasoning on. Never-submitted instances excluded pairwise. Δ = OFF − ON (pp). Empty = empty patch (counted as failure). fin=length = raw finish_reason 'length' (truncated generation), rate over the paired n.

| K | never-sub ON/OFF | n | ON | OFF | Δ (pp) | b/c (OFF/ON) | McNemar p | empty ON/OFF (%) | empty-asym p | fin=length ON/OFF (%) |
|---|---|---|---|---|---|---|---|---|---|---|
| K=4 | 18/17 | 466 | 43 (9.2%) | 66 (14.2%) | +4.94 | 30/7 | 1.9e-04 | 56.4/52.8 | 0.181 | 23.2/21.0 |
| K=12 | 0/1 | 499 | 46 (9.2%) | 64 (12.8%) | +3.61 | 33/15 | 0.0133 | 58.1/57.9 | 1.000 | 28.5/27.9 |
| K=40 | 32/12 | 457 | 43 (9.4%) | 89 (19.5%) | +10.07 | 53/7 | 7.7e-10 | 60.4/49.5 | 1.3e-04 | 32.2/29.5 |

Product decomposition (A = attempt = 1 − empty, Q = resolved | attempted; ΔR = Q_on·ΔA + A_on·ΔQ + ΔA·ΔQ).

| K | A ON/OFF | Q ON/OFF | ΔA (pp) | ΔQ (pp) | ΔR | producibility Q_on·ΔA | quality A_on·ΔQ | interaction ΔA·ΔQ |
|---|---|---|---|---|---|---|---|---|
| K=4 | 0.436/0.472 | 0.212/0.300 | +3.65 | +8.82 | +4.94 | +0.77 (16%) | +3.84 (78%) | +0.32 (7%) |
| K=12 | 0.419/0.421 | 0.220/0.305 | +0.20 | +8.47 | +3.61 | +0.04 (1%) | +3.55 (98%) | +0.02 (0%) |
| K=40 | 0.396/0.505 | 0.238/0.385 | +10.94 | +14.77 | +10.07 | +2.60 (26%) | +5.85 (58%) | +1.62 (16%) |

Secondaries.

| K | both-non-truncated: n, Δ, b/c, p | both-non-empty: n, Δ, b/c, p |
|---|---|---|
| K=4 | n=293, +6.48, 25/6, p=8.8e-04 | n=140, +7.86, 14/3, p=0.0127 |
| K=12 | n=269, +6.32, 28/11, p=0.0095 | n=121, +9.09, 17/6, p=0.0347 |
| K=40 | n=231, +14.72, 39/5, p=1.4e-07 | n=123, +13.01, 20/4, p=0.0015 |

Growth tests (instance-paired on instances paired at both K; wild = WCR Webb B=9,999; CR2 with BM df).

| contrast | n overlap | ΔΔ (pp) | instance SE | inst. 95% CI | inst. p | wild 95% CI | wild p | CR2 95% CI (df) | CR2 p | sign-flip p | marginal ΔΔ (own sets) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ΔΔ(40−4) | 425 | +5.18 | 1.87 | [+1.5, +8.8] | 0.0056 | [+1.2, +8.2] | 0.0124 | [+2.6, +7.8] (3.3) | 0.0070 | 0.0625 | +5.13 |
| ΔΔ(40−12) | 456 | +6.36 | 1.74 | [+2.9, +9.8] | 2.7e-04 | [+2.3, +7.7] | 0.0080 | [+2.9, +9.8] (3.2) | 0.0093 | 0.0156 | +6.46 |
| ΔΔ(12−4) | 465 | -1.51 | 1.65 | [-4.7, +1.7] | 0.362 | [-2.7, +1.2] | 0.296 | [-4.3, +1.3] (3.4) | 0.197 | 0.500 | -1.33 |

Ordinal trend (K coded 0/1/2), clustered by instance:

| model | trend coefficient | SE | p |
|---|---|---|---|
| GEE logit, y ~ C(K) + off + off×K, exchangeable | log-OR per K step +0.190 (OR 1.21 [1.03, 1.43]) | 0.084 | 0.0235 |
| same, independence working corr. | +0.185 (OR 1.20) | 0.080 | 0.0210 |
| GEE identity, d ~ K (risk-difference trend) | +2.52 pp per K step | 0.90 | 0.0050 |
| conditional (discordant pairs, n=145): logit P(OFF wins) ~ K | +0.305 | 0.228 | 0.182 |
