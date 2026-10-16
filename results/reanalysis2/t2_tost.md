## Task 2 — TOST equivalence (α = 0.05 per side ⇔ 90% CI inside ±m)

Primary margin m = ±3pp; sensitivity margin m = 0.4·G, with G = OFF−ON on the same 473 for that model and reference pair. m* = smallest symmetric margin the 90% CI would pass. Instance = Wald paired SE; wild = WCR Webb B=9,999 inverted at α=0.10 on a 0.05pp grid (G=12).

| model / refs | contrast | n | Δ | b/c | inst. 90% CI | wild 90% CI | TOST p (inst., ±3) | ±3pp: inst. / wild | 0.4·G | 0.4·G: inst. / wild | m* inst. / wild |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-5.6-sol (discovery-draw refs, Table V) | T−ON (trim) | 473 | +1.48 | 46/39 | [-1.73, +4.69] | [-0.52, +4.38] | 0.218 | fail / fail | 3.13 | fail / fail | 4.69 / 4.38 |
| gpt-5.6-sol (logged re-run refs) | T−ON (trim) | 473 | +0.00 | 41/41 | [-3.15, +3.15] | [-3.05, +5.85] | 0.0587 | fail / fail | 2.45 | fail / fail | 3.15 / 5.85 |
| Qwen3-Coder-30B (Table V) | T−ON (trim) | 473 | -0.21 | 7/8 | [-1.56, +1.14] | [-0.91, +0.89] | 3.3e-04 | PASS (equivalent) / PASS (equivalent) | 2.37 | PASS (equivalent) / PASS (equivalent) | 1.56 / 0.91 |
| agentic sonnet-5, fusion | OFF−ON | 499 | -1.40 | 28/35 | [-4.02, +1.21] | [-3.90, +1.80] | 0.158 | fail / fail | — | — | 4.02 / 3.90 |
| agentic sonnet-5, dense | OFF−ON | 499 | -1.80 | 18/27 | [-4.01, +0.41] | [-4.05, +0.85] | 0.187 | fail / fail | — | — | 4.01 / 4.05 |

95% CIs for the same rows ("not detected; CI" wording):

| model / refs | contrast | Δ | McNemar p | inst. 95% CI | wild 95% CI | wild p | CR2 95% CI | flip p |
|---|---|---|---|---|---|---|---|---|
| gpt-5.6-sol (discovery-draw refs, Table V) | T−ON (trim) | +1.48 | 0.515 | [-2.34, +5.30] | [-1.42, +5.48] | 0.167 | [-1.89, +4.85] | 0.292 |
| gpt-5.6-sol (logged re-run refs) | T−ON (trim) | +0.00 | 1.000 | [-3.76, +3.76] | [-3.35, +7.10] | 1.000 | [-7.66, +7.66] | 1.000 |
| Qwen3-Coder-30B (Table V) | T−ON (trim) | -0.21 | 1.000 | [-1.82, +1.40] | [-1.36, +1.14] | 0.560 | [-1.28, +0.85] | 1.000 |
| agentic sonnet-5, fusion | OFF−ON | -1.40 | 0.450 | [-4.52, +1.72] | [-4.75, +3.05] | 0.299 | [-4.93, +2.13] | 0.414 |
| agentic sonnet-5, dense | OFF−ON | -1.80 | 0.233 | [-4.44, +0.83] | [-4.65, +2.00] | 0.160 | [-4.53, +0.92] | 0.234 |

Fusion × dense interaction (instance-paired DiD of OFF−ON on instances paired in both arms):

| interaction | n | Δ | inst. 95% CI | inst. p | inst. 90% CI | wild 95% CI | wild 90% CI | wild p | CR2 95% CI | CR2 p | flip p | ±3pp TOST (inst./wild) | m* inst./wild |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fusion(discovery draw) − dense | 494 | +2.63 | [-2.94, +8.20] | 0.354 | [-2.04, +7.31] | [-4.07, +12.63] | [-1.82, +9.58] | 0.208 | [-4.18, +9.45] | 0.322 | 0.275 | fail / fail | 7.31 / 9.58 |
| fusion(logged re-run) − dense | 494 | +0.20 | [-5.23, +5.63] | 0.942 | [-4.36, +4.76] | [-3.60, +11.05] | [-2.85, +8.50] | 0.929 | [-7.55, +7.96] | 0.942 | 1.000 | fail / fail | 4.76 / 8.50 |

