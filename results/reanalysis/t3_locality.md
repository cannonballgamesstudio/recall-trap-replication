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
