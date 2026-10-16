## Task 10 — Numeric fixes

(a)/(b) Retriever interactions = instance-paired DiD of OFF−ON on instances paired in both arms (n=494 with dense: dense has 3 never-submitted per side; n=500 with BM25).

| interaction | n | fusion Δ on these n | other Δ on these n | marginal difference (Table II Δs) | DiD Δ | inst. 95% CI; p | wild 95% CI; p | CR2 95% CI; p | flip p |
|---|---|---|---|---|---|---|---|---|---|
| fusion(discovery) × dense | 494 | +8.30 | +5.67 | +1.93 | +2.63 | [-2.9, +8.2]; 0.354 | [-4.1, +12.6]; 0.208 | [-4.2, +9.4]; 0.322 | 0.275 |
| fusion(logged re-run) × dense | 494 | +5.87 | +5.67 | -0.27 | +0.20 | [-5.2, +5.6]; 0.942 | [-3.6, +11.1]; 0.929 | [-7.6, +8.0]; 0.942 | 1.000 |
| fusion(discovery) × BM25 | 500 | +7.60 | -3.20 | +10.80 | +10.80 | [+5.1, +16.5]; 1.8e-04 | [-0.1, +18.7]; 0.0513 | [+3.2, +18.4]; 0.0193 | 0.0625 |
| fusion(logged re-run) × BM25 | 500 | +5.40 | -3.20 | +8.60 | +8.60 | [+3.2, +14.0]; 0.0018 | [+6.0, +15.5]; 0.0079 | [+3.6, +13.6]; 0.0110 | 0.0059 |
| dense × BM25 | 494 | +5.67 | -3.04 | +8.87 | +8.70 | [+2.9, +14.5]; 0.0034 | [-1.3, +13.7]; 0.0741 | [+1.5, +15.9]; 0.0305 | 0.125 |

Explanation of +2.6: the 6 instances excluded by the dense arm's never-submitted (django__django-12209, django__django-15503, django__django-16032, pydata__xarray-3095, sphinx-doc__sphinx-10673, sympy__sympy-21379) carry fusion-discovery d = [-1, 0, 0, -1, -1, 0]; on the remaining 494 the fusion discovery Δ is +8.30pp (not +7.60), so the paired DiD is +8.30 − +5.67 = +2.63pp, while Table II's marginal Δs differ by only 7.60 − 5.67 = +1.93.

(c) gpt logged re-run (n=500, +5.40pp): WCR wild-cluster CI by test inversion on a 0.01pp grid (Webb, CR1 t).

| seed | B | wild p | 95% CI (0.01pp grid) | pieces | 90% CI |
|---|---|---|---|---|---|
| 20261014 | 9,999 | 0.0187 | [+3.19, +11.31] | 1 | [+3.43, +9.79] |
| 20261014 | 99,999 | 0.0176 | [+3.18, +11.26] | 1 | [+3.43, +9.79] |
| 1 | 99,999 | 0.0180 | [+3.17, +11.24] | 1 | [+3.42, +9.77] |
| 2 | 99,999 | 0.0179 | [+3.17, +11.28] | 1 | [+3.42, +9.82] |
| 3 | 99,999 | 0.0176 | [+3.18, +11.26] | 1 | [+3.43, +9.80] |

p(δ0) along the grid (seed 20261014, B=9,999): 2.5pp→0.032, 3.0pp→0.040, 3.1pp→0.043, 3.2pp→0.051, 3.3pp→0.068, 3.5pp→0.124, 4.0pp→0.320, 5.4pp→1.000, 8.0pp→0.299, 10.0pp→0.089, 11.0pp→0.056, 11.3pp→0.050, 11.5pp→0.047, 12.0pp→0.041

Why asymmetric: the bootstrap-t null distribution is re-generated at each δ0 from restricted residuals d−δ0, and with 12 clusters of very unequal size (django n=231, cluster sums of d: astropy +5/22, django +8/231, matplotlib -1/34, seaborn +0/2, flask +1/1, requests +2/8, xarray +2/22, pylint +1/10, pytest +1/19, scikit-learn +1/32, sphinx +2/44, sympy +5/75), the studentized statistic's distribution is not symmetric in δ0: below the estimate the p-curve drops from >0.3 to <0.05 within ~1pp (δ0 between +3.2 and +4.0), above it decays slowly. The asymmetry is genuine, not a bisection artefact: the fine grid, five seeds and B up to 99,999 reproduce [+3.2, +11.3] to within MC error, and the acceptance region is a single interval.

(d) Qwen3-Coder-30B-A3B K=12 ON/OFF candidates, fingerprinted against the paper's printed values.

| pair (report files) | n | ON / OFF resolve | Δ; b/c; p | single-file: n, Δ, b/c | multi-file: n, Δ, b/c | B→C: n, Δ, b/c | error_instances ON/OFF |
|---|---|---|---|---|---|---|---|
| qwen30b_*_rg (local GGUF, regraded): local_qwen3coder30b_dedupON.qwen30b_ON_rg.json / local_qwen3coder30b_dedupOFF.qwen30b_OFF_rg.json | 500 | 6.6% (33) / 12.4% (62) | +5.8; 39/10; 3.8e-05 | 429, +6.3, 37/10 | 71, +2.8, 2/0 | 80, +30.0, 24/0 | 1/0 |
| qwen3or_k12 (OpenRouter, budget sweep): local_qwen3or_k12_dedupON.qwen3or_k12_dedupON.json / local_qwen3or_k12_dedupOFF.qwen3or_k12_dedupOFF.json | 500 | 7.4% (37) / 11.6% (58) | +4.2; 33/12; 0.0025 | 429, +4.2, 30/12 | 71, +4.2, 3/0 | 80, +31.2, 26/1 | 1/0 |
| coder30b_c12k (local, 12k ctx): local_coder30b_c12k_dedupON.coder30b_c12k_dedupON.json / local_coder30b_c12k_dedupOFF.coder30b_c12k_dedupOFF.json | 500 | 7.0% (35) / 11.8% (59) | +4.8; 36/12; 7.2e-04 | 429, +5.1, 34/12 | 71, +2.8, 2/0 | 80, +30.0, 25/1 | 2/0 |
| local_dedup (87-instance pilot): local_qwen3coder30b_dedupON.local_dedupON.json / local_qwen3coder30b_dedupOFF.local_dedupOFF.json | 79 | 13.9% (11) / 21.5% (17) | +7.6; 8/2; 0.109 | 67, +9.0, 8/2 | 12, +0.0, 0/0 | 15, +40.0, 6/0 | 1/0 |

Anchor-transition table (paper Table VII, QC column: B→C +31.2 (26/1), B→B +0.4, C→C −5.7, A→A −1.7, B→A 0.0) recomputed for each full-500 candidate:

| pair | B→C | B→B | C→C | A→A | B→A |
|---|---|---|---|---|---|
| qwen30b_*_rg (local GGUF, regraded) | +30.0 (24/0, n=80) | -0.4 (5/6, n=249) | +8.6 (10/4, n=70) | +0.0 (0/0, n=60) | +0.0 (0/0, n=32) |
| qwen3or_k12 (OpenRouter, budget sweep) | +31.2 (26/1, n=80) | +0.4 (4/3, n=249) | -5.7 (3/7, n=70) | -1.7 (0/1, n=60) | +0.0 (0/0, n=32) |
| coder30b_c12k (local, 12k ctx) | +30.0 (25/1, n=80) | +0.0 (4/4, n=249) | +1.4 (7/6, n=70) | -1.7 (0/1, n=60) | +0.0 (0/0, n=32) |

Mapping to the paper (matched on printed values):

| paper location | printed values | feeding pair |
|---|---|---|
| Table V (Arm T references), Fig. 1 caption | ON 7.0%, OFF 12.9% on the 473; G +5.9, 38/10 | qwen30b_{ON,OFF}_rg (M1 in inclusion table) |
| §V within-file selection (random-chunk control) | 'own ON and OFF runs (6.6%, 12.4%)' | qwen30b_{ON,OFF}_rg (33/500, 62/500) |
| §V-D E5 (Branch B on Qwen3-Coder), Table VIII E5 OFF−ON rows | full +5.8; low +8.6 / high +3.6 | qwen30b_{ON,OFF}_rg (contam_common.T_ARM) |
| Table VIII E5 'K=4/12/40 Δlow (proxy M)' and §V-D proxy-M sentence | +3.2 / +7.7 / +7.2 | qwen3or_k{4,12,40} (contam_common.ARMS['qwen3coder']) |
| §RQ2 Budget K (exploratory Qwen3-Coder sweep) | +2.0 (26/16), +4.2 (33/12), +6.2 (42/11); 'budget sweep's (7.4%, 11.6%)' | qwen3or_k{4,12,40} |
| Table MDE 'Qwen3-Coder-A3B K=4' | 500, +2.0, 26/16 | qwen3or_k4 |
| Fix locality (§RQ2 'six arms'; earlier t3 row 'Qwen3-Coder-30B-A3B' 429, +6.3, 37/10 / 71, +2.8, 2/0) | single +6.3 (37/10), multi +2.8 (2/0) | qwen30b_{ON,OFF}_rg |
| **Anchor table (Table VII) QC column** | **B→C +31.2 (26/1)** | **qwen3or_k12 (OpenRouter budget-sweep pair), NOT the local pair that feeds Table V / E5 (local pair gives B→C +30.0, 24/0)** |
| coder30b_c12k pair (35/59) | — | not cited in v2 main.tex (no printed value matches); earlier Gate-1/cap2 program |

