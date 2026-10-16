# Paired contrasts (recomputed from results/inclusion_table.csv)

Delta = dedup-OFF minus dedup-ON, percentage points. p = exact McNemar. CI = repository-cluster bootstrap (5000 reps, seed 20260714, percentile). Convention: never-predicted instances excluded pairwise; where an arm has never-predicted instances a second row counts them as empty failures.

| arm | convention | n | ON | OFF | Delta | disc OFF/ON | p raw | p cond | empty ON/OFF | cluster 95% CI | P(D<=0) | LORO |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1_gpt_fusion | pairwise-exclusion | 500 | 39.2% (196) | 46.8% (234) | +7.60 | 73/35 | 0.00033 | 0.002 | 14.0/13.2% | [+0.6, +13.0] | 0.021 | +6.1..+9.2 |
| P2_deepseek_fusion | pairwise-exclusion | 499 | 13.0% (65) | 19.2% (96) | +6.21 | 53/22 | 0.00045 | 0.49 | 45.9/39.7% | [+3.9, +10.1] | 0.000 | +5.6..+6.7 |
| P2_deepseek_fusion | missing-as-empty | 500 | 13.0% (65) | 19.2% (96) | +6.20 | 53/22 | 0.00045 | 0.49 | 46.0/39.8% | [+3.9, +10.1] | 0.000 | +5.6..+6.7 |
| P3_qwen36_fusion_K12 | pairwise-exclusion | 499 | 9.2% (46) | 12.8% (64) | +3.61 | 33/15 | 0.013 | 0.035 | 58.1/57.9% | [+0.9, +4.9] | 0.007 | +2.2..+4.0 |
| P3_qwen36_fusion_K12 | missing-as-empty | 500 | 9.2% (46) | 12.8% (64) | +3.60 | 33/15 | 0.013 | 0.035 | 58.0/58.0% | [+0.9, +4.9] | 0.007 | +2.2..+4.0 |
| P4_DENSE1_gpt_dense | pairwise-exclusion | 494 | 41.5% (205) | 47.2% (233) | +5.67 | 69/41 | 0.0097 | 0.022 | 13.6/12.3% | [-0.9, +8.6] | 0.043 | +4.3..+6.5 |
| P4_DENSE1_gpt_dense | missing-as-empty | 500 | 41.2% (206) | 46.6% (233) | +5.40 | 69/42 | 0.013 | 0.022 | 14.4/12.8% | [-1.2, +8.2] | 0.053 | +4.0..+6.2 |
| P5_qwen25coder32b | pairwise-exclusion | 98 | 9.2% (9) | 11.2% (11) | +2.04 | 4/2 | 0.69 | 0.5 | 41.8/29.6% | [+0.0, +2.6] | 0.247 | +0.0..+2.6 |
| P5_qwen25coder32b | missing-as-empty | 500 | 1.8% (9) | 2.2% (11) | +0.40 | 4/2 | 0.69 | 0.5 | 88.4/86.2% | [+0.0, +0.7] | 0.359 | +0.0..+0.5 |
| P6a_glm52_incompatible | pairwise-exclusion | 497 | 12.9% (64) | 16.9% (84) | +4.02 | 43/23 | 0.019 | 1 | 79.1/70.4% | [+1.6, +9.6] | 0.003 | +3.0..+5.2 |
| P6a_glm52_incompatible | missing-as-empty | 500 | 12.8% (64) | 17.0% (85) | +4.20 | 44/23 | 0.014 | 1 | 79.2/70.4% | [+1.7, +9.6] | 0.003 | +3.2..+5.2 |
| P6b_kimi_incompatible | pairwise-exclusion | 498 | 5.2% (26) | 8.2% (41) | +3.01 | 32/17 | 0.044 | 1 | 89.8/87.8% | [+0.6, +4.3] | 0.008 | +1.9..+3.3 |
| P6b_kimi_incompatible | missing-as-empty | 500 | 5.2% (26) | 8.2% (41) | +3.00 | 32/17 | 0.044 | 1 | 89.8/87.8% | [+0.6, +4.2] | 0.008 | +1.9..+3.3 |
| R1_gpt_bm25 | pairwise-exclusion | 500 | 37.2% (186) | 34.0% (170) | -3.20 | 40/56 | 0.13 | 0.1 | 25.2/24.6% | [-5.9, +0.0] | 0.981 | -4.0..-2.6 |
| M1_qwen3coder30b_AC | pairwise-exclusion | 500 | 6.6% (33) | 12.4% (62) | +5.80 | 39/10 | 3.8e-05 | 0.015 | 43.6/42.4% | [+2.4, +7.3] | 0.000 | +3.7..+6.2 |
| F1_gpt_logged_replication | pairwise-exclusion | 500 | 41.0% (205) | 46.4% (232) | +5.40 | 65/38 | 0.01 | 0.0031 | 14.8/11.8% | [+3.4, +10.3] | 0.000 | +4.6..+7.1 |
| B1_qwen36_K4 | pairwise-exclusion | 466 | 9.2% (43) | 14.2% (66) | +4.94 | 30/7 | 0.00019 | 0.013 | 56.4/52.8% | [+1.1, +7.0] | 0.003 | +2.3..+5.4 |
| B1_qwen36_K4 | missing-as-empty | 500 | 8.6% (43) | 13.4% (67) | +4.80 | 31/7 | 0.00012 | 0.013 | 58.2/55.2% | [+1.2, +6.6] | 0.003 | +2.6..+5.3 |
| B1_qwen36_K40 | pairwise-exclusion | 457 | 9.4% (43) | 19.5% (89) | +10.07 | 53/7 | 7.7e-10 | 0.0015 | 60.4/49.5% | [+5.1, +12.1] | 0.000 | +7.9..+10.8 |
| B1_qwen36_K40 | missing-as-empty | 500 | 8.8% (44) | 18.0% (90) | +9.20 | 54/8 | 1.7e-09 | 0.0015 | 63.2/50.8% | [+4.6, +11.1] | 0.000 | +7.1..+9.9 |
| B2_A3B_K4 | pairwise-exclusion | 500 | 6.8% (34) | 8.8% (44) | +2.00 | 26/16 | 0.16 | 0.8 | 44.0/47.0% | [-1.1, +4.6] | 0.091 | +1.3..+2.5 |
| B2_A3B_K12 | pairwise-exclusion | 500 | 7.4% (37) | 11.6% (58) | +4.20 | 33/12 | 0.0025 | 0.17 | 41.6/38.8% | [+2.4, +5.3] | 0.000 | +3.7..+4.5 |
| B2_A3B_K40 | pairwise-exclusion | 500 | 6.8% (34) | 13.0% (65) | +6.20 | 42/11 | 2.2e-05 | 0.015 | 41.4/36.4% | [+2.5, +8.1] | 0.000 | +3.7..+6.7 |
| A1_agentic_sonnet5_fusion | pairwise-exclusion | 499 | 65.9% (329) | 64.5% (322) | -1.40 | 28/35 | 0.45 | 0.61 | 12.2/14.6% | [-4.0, +2.2] | 0.871 | -2.3..-1.0 |
| A1_agentic_sonnet5_fusion | missing-as-empty | 500 | 65.8% (329) | 64.4% (322) | -1.40 | 28/35 | 0.45 | 0.61 | 12.4/14.8% | [-4.0, +2.2] | 0.871 | -2.3..-1.0 |
| A2_agentic_sonnet5_dense | pairwise-exclusion | 499 | 67.1% (335) | 65.3% (326) | -1.80 | 18/27 | 0.23 | 0.58 | 10.4/11.4% | [-4.0, +1.0] | 0.947 | -2.2..-1.3 |
| A2_agentic_sonnet5_dense | missing-as-empty | 500 | 67.0% (335) | 65.2% (326) | -1.80 | 18/27 | 0.23 | 0.58 | 10.6/11.4% | [-3.9, +1.0] | 0.947 | -2.1..-1.3 |
| A3_agentic_opus_dense_n100 | pairwise-exclusion | 100 | 78.0% (78) | 76.0% (76) | -2.00 | 2/4 | 0.69 | 0.38 | 7.0/4.0% | [-13.6, +1.3] | 0.756 | -13.6..+1.3 |
| A3_agentic_opus_dense_n100 | missing-as-empty | 500 | 15.6% (78) | 15.2% (76) | -0.40 | 2/4 | 0.69 | 0.38 | 81.4/80.8% | [-3.1, +0.3] | 0.754 | -1.1..+0.2 |
| A4_bm25_n100 | pairwise-exclusion | 100 | 76.0% (76) | 74.0% (74) | -2.00 | 2/4 | 0.69 | 0.25 | 7.0/4.0% | [-2.6, +0.0] | 1.000 | -2.6..+0.0 |
| A4_bm25_n100 | missing-as-empty | 500 | 15.2% (76) | 14.8% (74) | -0.40 | 2/4 | 0.69 | 0.25 | 81.4/80.8% | [-0.7, +0.0] | 1.000 | -0.5..+0.0 |
| A5_retired_agentic_18pp | pairwise-exclusion | 499 | 64.9% (324) | 83.2% (415) | +18.24 | 102/11 | 1.3e-19 | 5.7e-08 | 14.4/1.0% | [+14.9, +25.3] | 0.000 | +17.2..+20.1 |
| A5_retired_agentic_18pp | missing-as-empty | 500 | 64.8% (324) | 83.0% (415) | +18.20 | 102/11 | 1.3e-19 | 5.7e-08 | 14.6/1.2% | [+14.8, +25.1] | 0.000 | +17.2..+20.1 |

## Product decomposition (reference = ON)

| arm | dA | dR | Q_on*dA | A_on*dQ | dA*dQ |
|---|---|---|---|---|---|
| P1_gpt_fusion | +0.8 | +7.6 | +0.4 (5%) | +7.2 (94%) | +0.1 (1%) |
| P2_deepseek_fusion | +6.2 | +6.2 | +1.5 (24%) | +4.2 (68%) | +0.5 (8%) |
| P3_qwen36_fusion_K12 | +0.2 | +3.6 | +0.0 (1%) | +3.5 (98%) | +0.0 (0%) |
| P4_DENSE1_gpt_dense | +1.2 | +5.7 | +0.6 (10%) | +5.0 (88%) | +0.1 (1%) |
| P5_qwen25coder32b | +12.2 | +2.0 | +1.9 (95%) | +0.1 (4%) | +0.0 (1%) |
| P6a_glm52_incompatible | +8.7 | +4.0 | +5.3 (132%) | -0.9 (-23%) | -0.4 (-9%) |
| P6b_kimi_incompatible | +2.0 | +3.0 | +1.0 (34%) | +1.7 (55%) | +0.3 (11%) |
| R1_gpt_bm25 | +0.6 | -3.2 | +0.3 (-9%) | -3.5 (108%) | -0.0 (1%) |
| M1_qwen3coder30b_AC | +1.2 | +5.8 | +0.1 (2%) | +5.5 (96%) | +0.1 (2%) |
| F1_gpt_logged_replication | +3.0 | +5.4 | +1.4 (27%) | +3.8 (71%) | +0.1 (2%) |
| B1_qwen36_K4 | +3.6 | +4.9 | +0.8 (16%) | +3.8 (78%) | +0.3 (7%) |
| B1_qwen36_K40 | +10.9 | +10.1 | +2.6 (26%) | +5.9 (58%) | +1.6 (16%) |
| B2_A3B_K4 | -3.0 | +2.0 | -0.4 (-18%) | +2.5 (125%) | -0.1 (-7%) |
| B2_A3B_K12 | +2.8 | +4.2 | +0.4 (8%) | +3.7 (87%) | +0.2 (4%) |
| B2_A3B_K40 | +5.0 | +6.2 | +0.6 (9%) | +5.2 (84%) | +0.4 (7%) |
| A1_agentic_sonnet5_fusion | -2.4 | -1.4 | -1.8 (129%) | +0.4 (-30%) | -0.0 (1%) |
| A2_agentic_sonnet5_dense | -1.0 | -1.8 | -0.8 (42%) | -1.1 (59%) | +0.0 (-1%) |
| A3_agentic_opus_dense_n100 | +3.0 | -2.0 | +2.5 (-126%) | -4.4 (219%) | -0.1 (7%) |
| A4_bm25_n100 | +3.0 | -2.0 | +2.5 (-123%) | -4.3 (216%) | -0.1 (7%) |
| A5_retired_agentic_18pp | +13.4 | +18.2 | +10.2 (56%) | +7.0 (38%) | +1.1 (6%) |

## Holm-Bonferroni over the five primary raw p-values

- P1_gpt_fusion: raw p = 0.0003258, Holm-adjusted = 0.001629
- P2_deepseek_fusion: raw p = 0.0004496, Holm-adjusted = 0.001799
- P4_DENSE1_gpt_dense: raw p = 0.009722, Holm-adjusted = 0.02917
- P3_qwen36_fusion_K12: raw p = 0.01328, Holm-adjusted = 0.02917
- PolyBench_pooled: raw p = 0.0559, Holm-adjusted = 0.0559

## Budget x dedup difference-in-differences (Qwen3.6-27B, K=40 minus K=4)

- pairwise-exclusion: DiD = +5.13pp, cluster 95% CI [+3.19, +7.90], one-sided P(DiD<=0) = 0.0002
- missing-as-empty: DiD = +4.40pp, cluster 95% CI [+2.72, +6.22], one-sided P(DiD<=0) = 0.0002

## Random-chunk selection control (Qwen3-Coder-30B-A3B)

- seed 20260717: B 15/499 (3.0%); B-A -3.6pp (disc 9/27, p=0.00393); B-C -9.4pp (p=1.8e-10)
- seed 20260718: B 18/499 (3.6%); B-A -3.0pp (disc 10/25, p=0.0167); B-C -8.8pp (p=1e-09)
- seed 20260719: B 12/499 (2.4%); B-A -4.2pp (disc 6/27, p=0.000324); B-C -10.0pp (p=7.6e-11)
- pooled B: 3.0%

## Cross-retriever interaction (gpt-5.6-sol, single-shot)

- fusion - BM25: +10.8pp, cluster 95% CI [+3.2, +16.5]
- dense - BM25: +8.9pp, cluster 95% CI [+0.4, +12.4]
- fusion - dense: +1.9pp, cluster 95% CI [-3.1, +9.5]
