## Task 1 — Small-sample repository-clustered inference (G=12 repositories)

Δ = dedup-OFF − dedup-ON (pp), instance-paired, never-submitted excluded pairwise. Wild = wild cluster restricted bootstrap-t, Webb 6-point weights, B=9,999, CR1 studentization, CI by test inversion. CR2 = Bell–McCaffrey bias-reduced SE with BM Satterthwaite df. Sign-flip = exact repository-level randomization over all 2^12 = 4,096 sign assignments of repository totals (two-sided). Interactions = instance-paired difference-in-differences on the overlapping instances.

| contrast | n | Δ (pp) | disc OFF/ON | McNemar p | wild 95% CI | wild p | CR2 SE (df) | CR2 95% CI | CR2 p | sign-flip p |
|---|---|---|---|---|---|---|---|---|---|---|
| gpt-5.6-sol fusion (P1) | 500 | +7.60 | 73/35 | 3.3e-04 | [-2.5, +15.8] | 0.104 | 2.42 (3.3) | [+0.3, +14.9] | 0.0449 | 0.105 |
| gpt logged re-run (F1) | 500 | +5.40 | 65/38 | 0.0101 | [+3.2, +11.3] | 0.0187 | 1.64 (3.3) | [+0.5, +10.3] | 0.0394 | 0.0059 |
| Qwen3.6-27B K=12 (P3) | 499 | +3.61 | 33/15 | 0.0133 | [+0.5, +5.2] | 0.0291 | 1.18 (3.3) | [+0.0, +7.2] | 0.0486 | 0.0781 |
| DeepSeek-v4 (P2) | 499 | +6.21 | 53/22 | 4.5e-04 | [+3.2, +11.6] | 0.0076 | 1.18 (3.3) | [+2.7, +9.8] | 0.0101 | 0.0156 |
| DENSE-1 (P4) | 494 | +5.67 | 69/41 | 0.0097 | [-2.2, +10.5] | 0.133 | 1.89 (3.3) | [-0.0, +11.3] | 0.0502 | 0.219 |
| gpt BM25 (R1) | 500 | -3.20 | 40/56 | 0.125 | [-7.1, +0.2] | 0.0615 | 1.08 (3.3) | [-6.5, +0.1] | 0.0521 | 0.129 |
| interaction fusion − BM25 | 500 | +10.80 | — | — | [-0.1, +18.7] | 0.0513 | 2.54 (3.3) | [+3.2, +18.4] | 0.0193 | 0.0625 |
| interaction dense − BM25 | 494 | +8.70 | — | — | [-1.4, +13.7] | 0.0741 | 2.41 (3.3) | [+1.5, +15.9] | 0.0305 | 0.125 |
| interaction fusion − dense | 494 | +2.63 | — | — | [-4.1, +12.7] | 0.208 | 2.27 (3.3) | [-4.2, +9.4] | 0.322 | 0.275 |

Supplement: instance-level (unclustered) paired SE, one-sided sign-flip, studentized sign-flip.

| contrast | instance SE (pp) | sign-flip one-sided p | studentized sign-flip p |
|---|---|---|---|
| gpt-5.6-sol fusion (P1) | 2.05 | 0.0527 | 0.119 |
| gpt logged re-run (F1) | 2.02 | 0.0029 | 0.0117 |
| Qwen3.6-27B K=12 (P3) | 1.38 | 0.0391 | 0.0312 |
| DeepSeek-v4 (P2) | 1.71 | 0.0078 | 0.0156 |
| DENSE-1 (P4) | 2.11 | 0.109 | 0.172 |
| gpt BM25 (R1) | 1.96 | 0.967 | 0.0742 |
| interaction fusion − BM25 | 2.89 | 0.0312 | 0.0703 |
| interaction dense − BM25 | 2.97 | 0.0625 | 0.0938 |
| interaction fusion − dense | 2.84 | 0.138 | 0.217 |
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
## Task 3 — Fix locality (per arm; no cross-arm meta-analysis)

Gold patches with ≥1 pre-image file: 500; single-file 429 (85.8%), multi-file 71. Never-submitted excluded pairwise. Interaction = GEE logistic y ~ off + multi + off×multi, clustered by instance (exchangeable); ratio of odds ratios multi/single. RD-scale = Δ_multi − Δ_single with independent-strata SE (strata are disjoint instances).

| arm | single-file: n, Δ (pp), b/c, p | multi-file: n, Δ (pp), b/c, p | RD-scale Δ_multi−Δ_single (SE), p | GEE off×multi: ROR [95% CI], p |
|---|---|---|---|---|
| gpt-5.6-sol fusion | 429, +8.6, 67/30, 2.2e-04 | 71, +1.4, 6/5, 1.000 | -7.2 (5.2), 0.167 | 0.79 [0.37, 1.67], 0.539 |
| DENSE-1 | 426, +6.6, 66/38, 0.0078 | 68, +0.0, 3/3, 1.000 | -6.6 (4.3), 0.130 | 0.77 [0.42, 1.39], 0.384 |
| DeepSeek-v4 | 428, +6.8, 49/20, 6.4e-04 | 71, +2.8, 4/2, 0.688 | -4.0 (4.0), 0.317 | 1.08 [0.28, 4.09], 0.913 |
| Qwen3-Coder-30B-A3B | 429, +6.3, 37/10, 9.8e-05 | 71, +2.8, 2/0, 0.500 | -3.5 (2.5), 0.169 | 1.56 [0.30, 8.20], 0.599 |
| Qwen3.6-27B K=12 | 428, +4.2, 32/14, 0.0114 | 71, +0.0, 1/1, 1.000 | -4.2 (2.5), 0.0990 | 0.68 [0.16, 2.90], 0.598 |
| gpt logged re-run | 429, +6.3, 59/32, 0.0061 | 71, +0.0, 6/6, 1.000 | -6.3 (5.4), 0.243 | 0.78 [0.37, 1.65], 0.510 |

Supplement — pooled over the paper's four locality arms (gpt fusion, DENSE-1, DeepSeek, A3B), arm-specific main effects, common off×multi, clustered by instance (500 instances, 3986 obs): log-ROR -0.148 (SE 0.226), ROR 0.86, p = 0.513.
## Task 4 — MDE at 80% power, exact McNemar (α = 0.05 two-sided)

ψ = observed discordance rate (b+c)/n; p_c = observed ON-only (breadth-wins) discordance rate. (C) = paper convention, discordant count D fixed at the observed value (conditional power). (A) = ψ fixed, D ~ Binom(n, ψ) random (unconditional). (B) = p_c fixed, p_b = p_c + Δ (discordance grows with Δ). Power is exact enumeration over (D, b); bracketed values are Monte-Carlo checks (200,000 simulated trials). 'Power at obs.' = unconditional power at the observed split (|Δ|, observed p_b and p_c).

| null arm | n | Δ obs | disc OFF/ON | ψ | raw p | paper MDE | MDE (C) | uncond. power at (C) MDE | MDE (A) [sim power] | MDE (B) [sim power] | power at obs. Δ [sim] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| agentic fusion (sonnet-5) | 499 | -1.4pp | 28/35 | 12.6% | 0.450 | 4.5pp | 4.5pp | 79% | 4.6pp [80.4%] | 5.8pp [80.5%] | 12% [12%] |
| agentic dense (sonnet-5) | 499 | -1.8pp | 18/27 | 9.0% | 0.230 | 3.8pp | 3.9pp | 80% | 3.9pp [80.7%] | 5.2pp [80.6%] | 22% [22%] |
| Qwen2.5-Coder-32B | 98 | +2.0pp | 4/2 | 6.1% | 0.690 | 5.7pp | 5.7pp | 47% | not attainable (> ψ) | 11.2pp [80.2%] | 5% [5%] |
| agentic BM25 (opus-4-8) | 100 | -2.0pp | 2/4 | 6.0% | 0.690 | 5.6pp | 5.6pp | 47% | not attainable (> ψ) | 13.2pp [80.1%] | 5% [5%] |
| agentic dense (opus-4-8) | 100 | -2.0pp | 2/4 | 6.0% | 0.690 | 5.6pp | 5.6pp | 47% | not attainable (> ψ) | 13.2pp [80.1%] | 5% [5%] |
| A3B K=4 (text, §5.9) | 500 | +2.0pp | 26/16 | 8.4% | 0.164 | 3.6pp | 3.6pp | 77% | 3.8pp [80.2%] | 4.2pp [80.1%] | 29% [29%] |
| SWE-PolyBench pooled (text, §5.10) | 617 | +2.6pp | 39/23 | 10.0% | 0.0560 | 3.6pp | 3.8pp | 82% | 3.7pp [80.5%] | 4.0pp [80.7%] | 49% [49%] |
## Task 5 — Holm over the 2-test confirmatory family

| test | Δ (pp) | n | raw McNemar p | Holm-adj. | wild p | Holm-adj. | CR2 p | Holm-adj. | sign-flip p | Holm-adj. |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3.6-27B K=12 | +3.61 | 499 | 0.0133 | 0.0201 | 0.0291 | 0.0374 | 0.0486 | 0.0788 | 0.0781 | 0.0781 |
| gpt logged re-run | +5.40 | 500 | 0.0101 | 0.0201 | 0.0187 | 0.0374 | 0.0394 | 0.0788 | 0.0059 | 0.0117 |

## Task 6 — Qwen3.6-27B K=12 truncation robustness (pairwise n=499)

| quantity | value |
|---|---|
| raw (primary) | n=499, Δ +3.61pp, 33/15, p=0.0133 |
| fin=length rate, arm level (own submitted denominator) | ON 142/500 = 28.4% ; OFF 139/499 = 27.9% |
| fin=length rate, paired n=499 | ON 142 = 28.5% ; OFF 139 = 27.9% |
| both-non-truncated (neither arm fin=length) | n=269, Δ +6.32pp, 28/11, p=0.0095 |
| both-non-empty (conditional estimand) | n=121, Δ +9.09pp, 17/6, p=0.0347 |
| PRIMARY imputation set: every unresolved fin=length response | ON 142 ; OFF 139 |
| symmetric imputation: truncated = failure in both arms | +3.61pp |
| symmetric imputation: truncated = success in both arms | +3.01pp |
| TRUE worst-case (Manski) bounds: ON-trunc→success & OFF-trunc→fail / reverse | [-24.85, +31.46]pp |
| sensitivity set: truncated AND empty only | ON 140 ; OFF 139 |
| sensitivity: symmetric success / worst-case | +3.41pp / [-24.45, +31.46]pp |
| worst-case, n=500 missing-as-empty denominators | [-24.40, +31.40]pp |
| OFF discordant wins where ON truncated | 5 of 33 |
| ON discordant wins where OFF truncated | 4 of 15 |
