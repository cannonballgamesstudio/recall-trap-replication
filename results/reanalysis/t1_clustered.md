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
