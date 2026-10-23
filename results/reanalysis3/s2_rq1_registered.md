## Analysis 2 — RQ1 under the registered structure (POST HOC re-analysis of registered estimands)

Registered structure verified in the documents: GPT-LOGGED-REPLICATION-PREREG (a) headline = discovery draw (+7.6, 196/234); (c) re-run resolve Δ = secondary, direction-only; (e) re-run outside the Holm family. TRIMMED-BREADTH §9 names 196/234 as the gpt T reference. The Holm family in force when GPT-LOGGED was committed (c35850a, 2026-08-08) is draft-v5 §4.5 (ab6f065): five raw McNemar p {gpt discovery, Qwen3.6-27B K=12, DENSE-1, DeepSeek, PolyBench pooled}; the same draft's §6.1 (and draft.md, 2026-07-16) says “the four single-shot A/Bs”. QWEN36-PREREG itself names no Holm family (it registers McNemar exact, empties-as-failure, on n=500). Registered clustered method = repository-cluster percentile bootstrap (5,000 reps, seed 20260714).

Methods: McNemar exact; wild = WCR Webb B=9,999 (CI by inversion); CR2-BM; exact repository sign-flip; pct = registered percentile cluster bootstrap (95% CI; P(Δ*≤0); two-sided p = 2·min(P(Δ*≤0), P(Δ*≥0))).

| contrast | n | ON/OFF | Δ (pp) | b/c | McNemar p | iid 95% CI | wild 95% CI; p | CR2 95% CI; p (df) | flip p | **registered pct 95% CI; P(Δ*≤0); 2-sided p** |
|---|---|---|---|---|---|---|---|---|---|---|
| gpt discovery draw (registered headline) | 500 | 196/234 | +7.60 | 73/35 | 3.3e-04 | [+3.6, +11.6] | [-2.5, +15.8]; 0.104 | [+0.3, +14.9]; 0.0449 (3.33) | 0.105 | [+0.6, +13.0]; 0.0208; 0.0416 |
| gpt logged re-run (registered secondary) | 500 | 205/232 | +5.40 | 65/38 | 0.0101 | [+1.4, +9.4] | [+3.2, +11.3]; 0.0187 | [+0.5, +10.3]; 0.0394 (3.33) | 0.0059 | [+3.4, +10.3]; 0.0000; 0.0e+00 |
| gpt both draws pooled (per-instance mean) | 500 | —/— | +6.50 | 99/53 | stacked 138/73: 9.0e-06 (nominal); instance randomization 1.3e-04 | [+3.2, +9.8] | [+0.8, +12.2]; 0.0354 | [+1.6, +11.4]; 0.0235 (3.33) | 0.0244 | [+3.0, +11.0]; 0.0004; 8.0e-04 |
| Qwen3.6-27B K=12 | 499 | 46/64 | +3.61 | 33/15 | 0.0133 | [+0.9, +6.3] | [+0.5, +5.2]; 0.0291 | [+0.0, +7.2]; 0.0486 (3.33) | 0.0781 | [+0.9, +4.9]; 0.0074; 0.0148 |
| DeepSeek-v4-pro | 499 | 65/96 | +6.21 | 53/22 | 4.5e-04 | [+2.9, +9.6] | [+3.3, +11.6]; 0.0076 | [+2.7, +9.8]; 0.0101 (3.34) | 0.0156 | [+3.9, +10.1]; 0.0002; 4.0e-04 |
| DENSE-1 dense control (gpt) | 494 | 205/233 | +5.67 | 69/41 | 0.0097 | [+1.5, +9.8] | [-2.2, +10.5]; 0.133 | [-0.0, +11.3]; 0.0502 (3.34) | 0.219 | [-0.9, +8.6]; 0.0434; 0.0868 |
| PolyBench pooled (2 models x 4 languages) | 617 | —/— | +2.59 | 39/23 | 0.0559 | [+0.1, +5.1] | [-1.6, +7.1]; 0.215 | [-1.9, +7.1]; 0.227 (10.24) | 0.254 | [-1.1, +6.7]; 0.1048; 0.210 |

Pooled-gpt per-instance mean d̄ distribution: {'-1': 13, '-0.5': 40, '0': 348, '0.5': 67, '1': 32}. b/c in that row count instances with d̄>0 / d̄<0. In the Holm tables the pooled row's 'McNemar' entry is the exact instance-level randomization p (the stacked McNemar is nominal only). A pct P(Δ*≤0) of 0.0000 means 0 of 5,000 draws (p < 2e-4). PolyBench's registered analysis was an instance bootstrap; its pct row here is the repository-cluster version (19 repositories) for comparability.

### Holm-adjusted p by family and method (raw → adjusted)

**F5 registered (draft-v5 §4.5 at c35850a; paired_contrasts.md): gpt discovery, Qwen3.6, dense, DeepSeek, PolyBench**

| method | gpt discovery draw (registered headline) | Qwen3.6-27B K=12 | DENSE-1 dense control (gpt) | DeepSeek-v4-pro | PolyBench pooled (2 models x 4 languages) | all survive α=0.05? |
|---|---|---|---|---|---|---|
| McNemar | 3.3e-04 → 0.0016 | 0.0133 → 0.0292 | 0.0097 → 0.0292 | 4.5e-04 → 0.0018 | 0.0559 → 0.0559 | only gpt discovery draw, Qwen3.6-27B K=12, DENSE-1 dense control, DeepSeek-v4-pro |
| wild | 0.104 → 0.313 | 0.0291 → 0.116 | 0.133 → 0.313 | 0.0076 → 0.0380 | 0.215 → 0.313 | only DeepSeek-v4-pro |
| CR2 | 0.0449 → 0.180 | 0.0486 → 0.180 | 0.0502 → 0.180 | 0.0101 → 0.0506 | 0.227 → 0.227 | none |
| flip | 0.105 → 0.316 | 0.0781 → 0.312 | 0.219 → 0.438 | 0.0156 → 0.0781 | 0.254 → 0.438 | none |
| pct (registered, 2-sided) | 0.0416 → 0.125 | 0.0148 → 0.0592 | 0.0868 → 0.174 | 4.0e-04 → 0.0020 | 0.210 → 0.210 | only DeepSeek-v4-pro |

**F4 registered (§6.1 'four single-shot A/Bs'): gpt discovery, Qwen3.6, dense, DeepSeek**

| method | gpt discovery draw (registered headline) | Qwen3.6-27B K=12 | DENSE-1 dense control (gpt) | DeepSeek-v4-pro | all survive α=0.05? |
|---|---|---|---|---|---|
| McNemar | 3.3e-04 → 0.0013 | 0.0133 → 0.0194 | 0.0097 → 0.0194 | 4.5e-04 → 0.0013 | all |
| wild | 0.104 → 0.209 | 0.0291 → 0.0873 | 0.133 → 0.209 | 0.0076 → 0.0304 | only DeepSeek-v4-pro |
| CR2 | 0.0449 → 0.135 | 0.0486 → 0.135 | 0.0502 → 0.135 | 0.0101 → 0.0405 | only DeepSeek-v4-pro |
| flip | 0.105 → 0.234 | 0.0781 → 0.234 | 0.219 → 0.234 | 0.0156 → 0.0625 | none |
| pct (registered, 2-sided) | 0.0416 → 0.0832 | 0.0148 → 0.0444 | 0.0868 → 0.0868 | 4.0e-04 → 0.0016 | only Qwen3.6-27B K=12, DeepSeek-v4-pro |

**F2-reg (paper's 2-test family, with the registered gpt headline): Qwen3.6, gpt discovery**

| method | Qwen3.6-27B K=12 | gpt discovery draw (registered headline) | all survive α=0.05? |
|---|---|---|---|
| McNemar | 0.0133 → 0.0133 | 3.3e-04 → 6.5e-04 | all |
| wild | 0.0291 → 0.0582 | 0.104 → 0.104 | none |
| CR2 | 0.0486 → 0.0898 | 0.0449 → 0.0898 | none |
| flip | 0.0781 → 0.156 | 0.105 → 0.156 | none |
| pct (registered, 2-sided) | 0.0148 → 0.0296 | 0.0416 → 0.0416 | all |

**F2-paper (as in the current paper): Qwen3.6, gpt re-run**

| method | Qwen3.6-27B K=12 | gpt logged re-run (registered secondary) | all survive α=0.05? |
|---|---|---|---|
| McNemar | 0.0133 → 0.0201 | 0.0101 → 0.0201 | all |
| wild | 0.0291 → 0.0374 | 0.0187 → 0.0374 | all |
| CR2 | 0.0486 → 0.0788 | 0.0394 → 0.0788 | none |
| flip | 0.0781 → 0.0781 | 0.0059 → 0.0117 | only gpt logged re-run |
| pct (registered, 2-sided) | 0.0148 → 0.0148 | 0.0e+00 → 0.0e+00 | all |

**F2-pooled (Qwen3.6, gpt both draws pooled)**

| method | Qwen3.6-27B K=12 | gpt both draws pooled (per-instance mean) | all survive α=0.05? |
|---|---|---|---|
| McNemar | 0.0133 → 0.0133 | 1.3e-04 → 2.7e-04 | all |
| wild | 0.0291 → 0.0582 | 0.0354 → 0.0582 | none |
| CR2 | 0.0486 → 0.0486 | 0.0235 → 0.0469 | all |
| flip | 0.0781 → 0.0781 | 0.0244 → 0.0488 | only gpt both draws pooled |
| pct (registered, 2-sided) | 0.0148 → 0.0148 | 8.0e-04 → 0.0016 | all |

### gpt T decomposition (473) against each reference pair, all methods

| reference: term | Δ (pp) | b/c | McNemar p | wild 95% CI; p | CR2 p | flip p | registered pct 95% CI; P(Δ*≤0) |
|---|---|---|---|---|---|---|---|
| discovery (registered, TB §9): G = OFF−ON | +7.82 | 71/34 | 3.9e-04 | [-2.6, +15.5]; 0.116 | 0.0444 | 0.119 | [+0.4, +12.8]; 0.0234 |
| discovery (registered, TB §9): depth = OFF−T | +6.34 | 63/33 | 0.0029 | [-4.1, +12.8]; 0.187 | 0.0778 | 0.199 | [-1.5, +10.9]; 0.0504 |
| discovery (registered, TB §9): trim = T−ON | +1.48 | 46/39 | 0.515 | [-1.4, +5.5]; 0.167 | 0.271 | 0.292 | [-1.1, +5.1]; 0.1082 |
| re-run (paper): G = OFF−ON | +6.13 | 65/36 | 0.0051 | [+3.3, +12.0]; 0.0181 | 0.0322 | 0.0059 | [+3.9, +11.3]; 0.0000 |
| re-run (paper): depth = OFF−T | +6.13 | 66/37 | 0.0055 | [+0.3, +8.9]; 0.0405 | 0.0281 | 0.0508 | [+1.7, +8.8]; 0.0040 |
| re-run (paper): trim = T−ON | +0.00 | 41/41 | 1.000 | [-3.3, +7.1]; 1.000 | 1.000 | 1.000 | [-2.6, +5.7]; 0.4770 |

