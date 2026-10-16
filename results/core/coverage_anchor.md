# Served-pack coverage and anchor dose (recomputed)

| packs | side | n | any-gold-file present | mean gold-line coverage | anchor-visible share | mean distinct files |
|---|---|---|---|---|---|---|
| fusion | ON | 500 | 0.878 | 0.090 | 0.210 | 11.93 |
| fusion | OFF | 500 | 0.806 | 0.179 | 0.356 | 5.30 |
| dense | ON | 500 | 0.890 | 0.083 | 0.198 | 11.95 |
| dense | OFF | 500 | 0.802 | 0.187 | 0.386 | 5.34 |
| bm25 | ON | 500 | 0.690 | 0.059 | 0.138 | 11.97 |
| bm25 | OFF | 500 | 0.612 | 0.088 | 0.188 | 6.96 |

## Resolve rate by anchor stratum (oracle diagnostic)

| arm | ON anchor-visible | ON anchor-absent | OFF anchor-visible | OFF anchor-absent | within-visible residual (OFF-ON) |
|---|---|---|---|---|---|
| P1_gpt_fusion | 54.3% (n=105) | 35.2% (n=395) | 61.2% (n=178) | 38.8% (n=322) | +7.0pp |
| P2_deepseek_fusion | 30.5% (n=105) | 8.4% (n=394) | 38.8% (n=178) | 8.4% (n=322) | +8.3pp |
| P3_qwen36_fusion_K12 | 23.8% (n=105) | 5.3% (n=395) | 30.9% (n=178) | 2.8% (n=321) | +7.1pp |
| M1_qwen3coder30b_AC | 16.2% (n=105) | 4.1% (n=395) | 29.8% (n=178) | 2.8% (n=322) | +13.6pp |
| P4_DENSE1_gpt_dense | 50.5% (n=99) | 39.2% (n=398) | 57.5% (n=193) | 40.1% (n=304) | +7.0pp |
| R1_gpt_bm25 | 55.1% (n=69) | 34.3% (n=431) | 55.3% (n=94) | 29.1% (n=406) | +0.2pp |

## Pack-content failure classes, gpt-5.6-sol dedup-ON (Table 'fail')

graded n=497, failures=301

| class | n | resolve | share of failures | prevalence |
|---|---|---|---|---|
| A_gold_absent | 60 | 15.0% | 16.9% | 12.1% |
| B_present_lines_absent | 359 | 37.3% | 74.8% | 72.2% |
| C_lines_covered | 78 | 67.9% | 8.3% | 15.7% |

## Gold-file presence among gpt-5.6-sol discordant pairs (fusion)

- OFF-win, gold file present in ON only: 6
- OFF-win, gold file present in both: 60
- OFF-win, gold file present in neither: 7
- ON-win, gold file present in ON only: 4
- ON-win, gold file present in both: 30
- ON-win, gold file present in neither: 1
