## Analysis 5 — Practitioner baseline P (POST HOC)

### (a) Same-seed contrasts (seed 0 only; P has one seed)

The paper's Table VI P rows compare P's single seed with the 3-seed mean of OFF/T. Here P seed 0 is compared with OFF seed 0 and T seed 0 on the same instances.

| contrast | n | rates A / B | Δ (pp) | b/c | McNemar p | iid 95% CI | wild 95% CI; p | CR2 95% CI; p | flip p | pct-cluster 95% CI |
|---|---|---|---|---|---|---|---|---|---|---|
| P−OFF seed 0, scored primary | 478 | 9.41% / 11.09% | -1.67 | 22/30 | 0.332 | [-4.63, +1.28] | [-3.37, +1.33]; 0.403 | [-5.29, +1.95]; 0.251 | 0.500 | [-3.14, +0.87] |
| P−T seed 0, scored primary | 478 | 9.41% / 6.90% | +2.51 | 23/11 | 0.0576 | [+0.13, +4.89] | [-1.99, +4.96]; 0.168 | [-0.58, +5.60]; 0.0839 | 0.250 | [-1.18, +4.24] |
| P−ON seed 0, scored primary | 478 | 9.41% / 6.69% | +2.72 | 23/10 | 0.0351 | [+0.37, +5.06] | [-0.08, +5.92]; 0.0532 | [-0.46, +5.89]; 0.0738 | 0.0938 | [+0.49, +5.31] |
| OFF−T seed 0, scored primary | 478 | 11.09% / 6.90% | +4.18 | 35/15 | 0.0066 | [+1.31, +7.06] | [-1.07, +6.28]; 0.170 | [-0.70, +9.07]; 0.0739 | 0.250 | [-0.35, +5.98] |
| P−OFF seed 0, exclude | 477 | 9.43% / 11.11% | -1.68 | 22/30 | 0.332 | [-4.64, +1.29] | [-3.33, +1.32]; 0.403 | [-5.30, +1.95]; 0.250 | 0.500 | [-3.15, +0.87] |
| P−T seed 0, exclude | 477 | 9.43% / 6.92% | +2.52 | 23/11 | 0.0576 | [+0.13, +4.90] | [-1.98, +4.97]; 0.168 | [-0.58, +5.61]; 0.0838 | 0.250 | [-1.18, +4.25] |
| P−ON seed 0, exclude | 477 | 9.43% / 6.71% | +2.73 | 23/10 | 0.0351 | [+0.38, +5.08] | [-0.07, +5.98]; 0.0529 | [-0.47, +5.92]; 0.0744 | 0.0938 | [+0.49, +5.33] |
| OFF−T seed 0, exclude | 477 | 11.11% / 6.92% | +4.19 | 35/15 | 0.0066 | [+1.31, +7.08] | [-1.11, +6.29]; 0.170 | [-0.70, +9.08]; 0.0735 | 0.250 | [-0.35, +5.98] |

### (b) Pack sizes from the released packs (characters of the rendered pack; 478 gate-passing instances unless stated)

| arm | served pack file | mean slots | mean chars | median chars |
|---|---|---|---|---|
| ON | b1b3_packs_b2.json (served) | 11.93 | 5,991 | 6,040 |
| OFF | b1b3_packs_b2.json (served) | 12.00 | 6,323 | 6,430 |
| T | b1b3_packs_b2.json (served) | 5.15 | 2,799 | 2,778 |
| TM | b1b3_packs_b2.json (served) | 12.40 | 6,323 | 6,435 |
| P | b1b3_packs_b2.json (served) | 5.15 | 5,706 | 5,794 |
| ON / OFF, all 500 | b1b3_packs_b2.json | 11.93 / 12.00 | 6,002 / 6,322 | |
| TM (pre-ruling, never generated) | b1b3_packs.json | 12.90 | 6,323 | |
| P (superseded first build, never generated; 326 P files unread) | <unreleased>/b1b3/b1b3_packs_build1.json | 5.15 | **4,972** | |

P pack identical in b1b3_packs_b2.json and b1b3_packs.json: True; TM identical: False.

| ratio | ratio of means | mean of per-instance ratios | median of per-instance ratios |
|---|---|---|---|
| P/OFF | 0.902 | 0.901 | 0.903 |
| P/T | 2.038 | 2.372 | 1.987 |
| P/ON | 0.952 | 0.959 | 0.954 |
| TM/OFF | 1.000 | 1.000 | 1.001 |
| T/OFF | 0.443 | 0.447 | 0.445 |

