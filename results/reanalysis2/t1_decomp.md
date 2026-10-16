## Task 1 — gpt decomposition against the pre-registered logged re-run (same 473 instances)

Same 473 instances as Table V (ON, OFF and T all submitted; 27 subset-gate violators removed). T is the same T draw in both gpt rows; only the ON/OFF reference arms change. Δ in pp; b/c = first-arm-only / second-arm-only wins; McNemar exact two-sided; wild = WCR Webb B=9,999 (G=12); CR2 = Bell–McCaffrey; flip = exact repository sign-flip (4,096 assignments).

| reference arms | contrast | n | first/second resolved | Δ | b/c | McNemar p | wild 95% CI | wild p | CR2 p | flip p | share of G |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-5.6-sol, logged re-run refs | G = OFF−ON | 473 | 221/192 | +6.13 | 65/36 | 0.0051 | [+3.3, +12.0] | 0.0181 | 0.0322 | 0.0059 | 100% |
| gpt-5.6-sol, logged re-run refs | OFF−T (depth) | 473 | 221/192 | +6.13 | 66/37 | 0.0055 | [+0.3, +8.9] | 0.0405 | 0.0281 | 0.0508 | 100% |
| gpt-5.6-sol, logged re-run refs | T−ON (trim) | 473 | 192/192 | +0.00 | 41/41 | 1.000 | [-3.3, +7.1] | 1.000 | 1.000 | 1.000 | 0% |
| gpt-5.6-sol, discovery-draw refs (paper Table V) | G = OFF−ON | 473 | 222/185 | +7.82 | 71/34 | 3.9e-04 | [-2.6, +15.5] | 0.116 | 0.0444 | 0.119 | 100% |
| gpt-5.6-sol, discovery-draw refs (paper Table V) | OFF−T (depth) | 473 | 222/192 | +6.34 | 63/33 | 0.0029 | [-4.1, +12.8] | 0.187 | 0.0778 | 0.199 | 81% |
| gpt-5.6-sol, discovery-draw refs (paper Table V) | T−ON (trim) | 473 | 192/185 | +1.48 | 46/39 | 0.515 | [-1.4, +5.5] | 0.167 | 0.271 | 0.292 | 19% |
| Qwen3-Coder-30B (paper Table V) | G = OFF−ON | 473 | 61/33 | +5.92 | 38/10 | 6.2e-05 | [+1.7, +8.0] | 0.0132 | 0.0278 | 0.0156 | 100% |
| Qwen3-Coder-30B (paper Table V) | OFF−T (depth) | 473 | 61/32 | +6.13 | 38/9 | 2.5e-05 | [+0.8, +8.5] | 0.0226 | 0.0368 | 0.0312 | 104% |
| Qwen3-Coder-30B (paper Table V) | T−ON (trim) | 473 | 32/33 | -0.21 | 7/8 | 1.000 | [-1.4, +1.1] | 0.560 | 0.590 | 1.000 | -4% |

| reference arms | ON / T / OFF resolve on the 473 | depth share | trim share | identity check | 60%-rule verdict |
|---|---|---|---|---|---|
| gpt-5.6-sol, logged re-run refs | 40.6% / 40.6% / 46.7% | 100.0% | 0.0% | +0.000 | depth carries the effect |
| gpt-5.6-sol, discovery-draw refs (paper Table V) | 39.1% / 40.6% / 46.9% | 81.1% | 18.9% | +0.000 | depth carries the effect |
| Qwen3-Coder-30B (paper Table V) | 7.0% / 6.8% / 12.9% | 103.6% | -3.6% | +0.000 | depth carries the effect |

## Task 12 — T−ON 95% CIs (and 90% for reference)

| model / refs | n | T−ON Δ | b/c | instance-paired 95% CI | wild-cluster 95% CI | CR2 95% CI | instance 90% CI | wild 90% CI |
|---|---|---|---|---|---|---|---|---|
| gpt-5.6-sol, discovery-draw refs (paper Table V) | 473 | +1.48 | 46/39 | [-2.34, +5.30] | [-1.42, +5.48] | [-1.89, +4.85] | [-1.73, +4.69] | [-0.52, +4.38] |
| gpt-5.6-sol, logged re-run refs | 473 | +0.00 | 41/41 | [-3.76, +3.76] | [-3.35, +7.10] | [-7.66, +7.66] | [-3.15, +3.15] | [-3.05, +5.85] |
| Qwen3-Coder-30B (paper Table V) | 473 | -0.21 | 7/8 | [-1.82, +1.40] | [-1.36, +1.14] | [-1.28, +0.85] | [-1.56, +1.14] | [-0.91, +0.89] |

