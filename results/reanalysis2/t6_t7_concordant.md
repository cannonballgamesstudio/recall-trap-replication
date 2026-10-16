## Task 6 — Concordant-subset sensitivity

Concordant instance = every T file's ON chunk is byte-identical (file, start line, text) to that file's first-listed (top-ranked) OFF chunk. Computed on the 473 T instances.

| quantity | value |
|---|---|
| file-level concordance (ON chunk = first OFF chunk of that file) | 2153/2431 = 88.6% |
| **instance-level concordance (all T files concordant)** | **260/473 = 55.0%** |
| discordant instances | 213 (mean discordant files among them 1.31) |
| position of the ON chunk among that file's OFF chunks (all T files) | 1: 2153, 2: 99, 3: 24, 4+: 18, absent: 137 |

| model / refs | subset | contrast | n | first/second resolved | Δ | b/c | McNemar p | wild 95% CI | wild p | flip p |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3-Coder-30B | all 473 | OFF−ON | 473 | 61/33 | +5.92 | 38/10 | 6.2e-05 | [+1.7, +8.0] | 0.0132 | 0.0156 |
| Qwen3-Coder-30B | all 473 | OFF−T | 473 | 61/32 | +6.13 | 38/9 | 2.5e-05 | [+0.8, +8.5] | 0.0226 | 0.0312 |
| Qwen3-Coder-30B | all 473 | T−ON | 473 | 32/33 | -0.21 | 7/8 | 1.000 | [-1.4, +1.1] | 0.560 | 1.000 |
| Qwen3-Coder-30B | concordant | OFF−ON | 260 | 34/19 | +5.77 | 22/7 | 0.0081 | [-0.2, +8.6] | 0.0600 | 0.125 |
| Qwen3-Coder-30B | concordant | OFF−T | 260 | 34/17 | +6.54 | 22/5 | 0.0015 | [-0.2, +10.3] | 0.0586 | 0.125 |
| Qwen3-Coder-30B | concordant | T−ON | 260 | 17/19 | -0.77 | 4/6 | 0.754 | [-2.6, +2.0] | 0.516 | 0.750 |
| Qwen3-Coder-30B | discordant | OFF−ON | 213 | 27/14 | +6.10 | 16/3 | 0.0044 | [+1.1, +9.3] | 0.0205 | 0.0625 |
| Qwen3-Coder-30B | discordant | OFF−T | 213 | 27/15 | +5.63 | 16/4 | 0.0118 | [+1.2, +9.2] | 0.0151 | 0.0625 |
| Qwen3-Coder-30B | discordant | T−ON | 213 | 15/14 | +0.47 | 3/2 | 1.000 | [+0.0, +0.9] | 1.000 | 1.000 |
| gpt (discovery-draw refs) | all 473 | OFF−ON | 473 | 222/185 | +7.82 | 71/34 | 3.9e-04 | [-2.6, +15.5] | 0.116 | 0.119 |
| gpt (discovery-draw refs) | all 473 | OFF−T | 473 | 222/192 | +6.34 | 63/33 | 0.0029 | [-4.1, +12.8] | 0.187 | 0.199 |
| gpt (discovery-draw refs) | all 473 | T−ON | 473 | 192/185 | +1.48 | 46/39 | 0.515 | [-1.4, +5.5] | 0.167 | 0.292 |
| gpt (discovery-draw refs) | concordant | OFF−ON | 260 | 122/104 | +6.92 | 39/21 | 0.0273 | [-3.9, +14.1] | 0.181 | 0.250 |
| gpt (discovery-draw refs) | concordant | OFF−T | 260 | 122/105 | +6.54 | 35/18 | 0.0270 | [-4.1, +13.6] | 0.205 | 0.203 |
| gpt (discovery-draw refs) | concordant | T−ON | 260 | 105/104 | +0.38 | 26/25 | 1.000 | [-11.6, +6.9] | 0.865 | 1.000 |
| gpt (discovery-draw refs) | discordant | OFF−ON | 213 | 100/81 | +8.92 | 32/13 | 0.0066 | [-4.2, +21.1] | 0.105 | 0.133 |
| gpt (discovery-draw refs) | discordant | OFF−T | 213 | 100/87 | +6.10 | 28/15 | 0.0660 | [-5.7, +13.7] | 0.194 | 0.273 |
| gpt (discovery-draw refs) | discordant | T−ON | 213 | 87/81 | +2.82 | 20/14 | 0.392 | [-3.9, +14.6] | 0.265 | 0.383 |
| gpt (logged re-run refs) | all 473 | OFF−ON | 473 | 221/192 | +6.13 | 65/36 | 0.0051 | [+3.3, +12.0] | 0.0181 | 0.0059 |
| gpt (logged re-run refs) | all 473 | OFF−T | 473 | 221/192 | +6.13 | 66/37 | 0.0055 | [+0.3, +8.9] | 0.0405 | 0.0508 |
| gpt (logged re-run refs) | all 473 | T−ON | 473 | 192/192 | +0.00 | 41/41 | 1.000 | [-3.3, +7.1] | 1.000 | 1.000 |
| gpt (logged re-run refs) | concordant | OFF−ON | 260 | 115/106 | +3.46 | 32/23 | 0.281 | [-1.9, +13.5] | 0.348 | 0.328 |
| gpt (logged re-run refs) | concordant | OFF−T | 260 | 115/105 | +3.85 | 32/22 | 0.220 | [-4.4, +11.4] | 0.198 | 0.227 |
| gpt (logged re-run refs) | concordant | T−ON | 260 | 105/106 | -0.38 | 22/23 | 1.000 | [-5.7, +8.6] | 0.906 | 1.000 |
| gpt (logged re-run refs) | discordant | OFF−ON | 213 | 106/86 | +9.39 | 33/13 | 0.0045 | [+2.2, +17.6] | 0.0063 | 0.0156 |
| gpt (logged re-run refs) | discordant | OFF−T | 213 | 106/87 | +8.92 | 34/15 | 0.0094 | [+1.1, +12.4] | 0.0294 | 0.0742 |
| gpt (logged re-run refs) | discordant | T−ON | 213 | 87/86 | +0.47 | 19/18 | 1.000 | [-4.8, +12.0] | 0.856 | 1.000 |

## Task 7 — Structural rank fact; local_packs.json field audit

**Structural fact (no data needed).** Let one ranking order all chunks. Dedup-OFF serves ranks 1..K. Dedup-ON serves, for each of the first K distinct files in the ranking, that file's best-ranked chunk. Hence, under a single ranking: (i) every OFF file is among ON's files (files(OFF) ⊆ files(ON)); (ii) for every OFF file, the ON chunk is that file's first OFF chunk, so T ⊆ OFF chunk-for-chunk and OFF−T adds exactly OFF's non-first same-file chunks; (iii) every chunk OFF adds over T has rank ≤ K, while every chunk ON adds over T (one per extra file) has rank > K, since those files have no chunk in the top K. So OFF's extra chunks are higher-ranked than ON's extra chunks by construction: rank is not a confound that a reweighting of these arms can remove, and a 'rank-matched' K-slot pack with OFF's rank profile is OFF itself. Any violation of (i) or (ii) in the data measures the difference between the two service instances' rankings, not a property of the policy.

| check | result |
|---|---|
| fields present in local_packs.json (per side) | dedupOFF.files, dedupOFF.n_hits, dedupOFF.pack, dedupON.files, dedupON.n_hits, dedupON.pack |
| fields whose name matches rank/score/sim/dist | none |
| pack header lines containing score/rank/sim tokens | 41, all inside file paths or symbol names (e.g. sklearn/metrics/_ranking.py, roc_auc_score); none is a score or rank value |
| chunk header format | `### <file>:<line> — <symbol> [<kind>]` (no score, no rank; order in the pack is the only rank signal) |
| (i) files(OFF) ⊆ files(ON) | 473/500 = 94.6% |
| (ii) ON chunk = first OFF chunk, per file / per instance | 88.6% / 55.0% (on the 473) |

