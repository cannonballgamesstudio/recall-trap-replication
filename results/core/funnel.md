# Parse-apply-test funnel (recomputed from raw responses + official reports)

| arm | side | n (raw rows) | emitted text | applied | resolved | test-pass given applied |
|---|---|---|---|---|---|---|
| P2_deepseek_fusion | ON | 499 | 94.4% | 51.1% | 13.0% | 23.9% (61/255) |
| P2_deepseek_fusion | OFF | 500 | 94.2% | 54.6% | 19.2% | 31.9% (87/273) |
| P2_deepseek_fusion | OFF-ON | | | | | +7.9pp |
| P4_DENSE1_gpt_dense | ON | 497 | 99.6% | 80.7% | 41.4% | 48.4% (194/401) |
| P4_DENSE1_gpt_dense | OFF | 497 | 100.0% | 80.3% | 46.9% | 55.1% (220/399) |
| P4_DENSE1_gpt_dense | OFF-ON | | | | | +6.8pp |
| F1_gpt_logged_replication | ON | 500 | 100.0% | 80.8% | 41.0% | 47.0% (190/404) |
| F1_gpt_logged_replication | OFF | 500 | 99.6% | 79.2% | 46.4% | 53.5% (212/396) |
| F1_gpt_logged_replication | OFF-ON | | | | | +6.5pp |
| P3_qwen36_fusion_K12 | ON | 500 | 70.4% | 44.6% | 9.2% | 20.2% (45/223) |
| P3_qwen36_fusion_K12 | OFF | 499 | 69.9% | 40.7% | 12.8% | 29.6% (60/203) |
| P3_qwen36_fusion_K12 | OFF-ON | | | | | +9.4pp |
| M1_qwen3coder30b_AC | ON | 413 | 100.0% | 44.8% | 5.3% | 10.3% (19/185) |
| M1_qwen3coder30b_AC | OFF | 413 | 100.0% | 44.8% | 10.9% | 20.5% (38/185) |
| M1_qwen3coder30b_AC | OFF-ON | | | | | +10.3pp |
| R1_gpt_bm25 | ON | 500 | 99.6% | 68.6% | 37.2% | 50.1% (172/343) |
| R1_gpt_bm25 | OFF | 500 | 99.2% | 69.8% | 34.0% | 43.8% (153/349) |
| R1_gpt_bm25 | OFF-ON | | | | | -6.3pp |
