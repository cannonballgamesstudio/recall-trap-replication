## Analysis 7 — Single-retriever replication restated under the new primary (Class-P cells scored unresolved)

File of record: `results/b1b3-replication/results_scored.json` (sha256 A008ABB5…4A9B, identical in the package and in the original run directory). Every number below was recomputed independently from the 13 raw reports; the 'match' column is the exact comparison (Δ, registered 95% CI, per-seed b/c). Δ and CIs in pp; CIs are the registered instance bootstrap (percentile, B = 10,000) unless labelled. Wild p: file = b1b3_analyze.py (Python RNG); mine = numpy implementation, independent weights (MC SE ≈ 0.0015 at p ≈ 0.02).

| contrast | n | rate A / B | Δ | 95% CI (registered) | 90% CI | wild p (file / mine) | wild 95% CI (mine) | CR2 p; 95% CI | flip p | pct-cluster 95% CI | per-seed Δ (b/c, McNemar p) | match |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OFF-ON | 478 | 12.34% / 6.21% | +6.14 | [+3.63, +8.65] | [+4.04, +8.30] | 0.0134 / 0.0141 | [+1.59, +8.54] | 0.0352; [+0.75, +11.52] | 0.0156 | [+2.27, +8.01] | +4.4 (32/11, 0.0019); +6.9 (42/9, 3.4e-06); +7.1 (43/9, 2.0e-06) | yes |
| OFF-T | 478 | 12.34% / 6.69% | +5.65 | [+3.07, +8.30] | [+3.42, +7.88] | 0.0378 / 0.0382 | [+0.40, +8.05] | 0.0442; [+0.26, +11.04] | 0.0547 | [+1.42, +7.50] | +4.2 (35/15, 0.0066); +6.1 (41/12, 8.2e-05); +6.7 (41/9, 5.6e-06) | yes |
| T-ON | 478 | 6.69% / 6.21% | +0.49 | [-0.91, +1.88] | [-0.63, +1.60] | 0.218 / 0.218 | [-0.36, +1.69] | 0.210; [-0.46, +1.43] | 0.250 | [-0.12, +1.58] | +0.2 (12/11, 1.000); +0.8 (10/6, 0.454); +0.4 (10/8, 0.815) | yes |
| TM-T | 478 | 6.83% / 6.69% | +0.14 | [-1.05, +1.39] | [-0.91, +1.19] | 0.746 / 0.744 | [-1.66, +1.19] | 0.765; [-1.15, +1.43] | 0.875 | [-1.42, +0.78] | +0.0 (9/9, 1.000); +0.0 (9/9, 1.000); +0.4 (7/5, 0.774) | yes |
| OFF-TM | 478 | 12.34% / 6.83% | +5.51 | [+2.93, +8.23] | [+3.28, +7.74] | 0.0138 / 0.0134 | [+1.51, +7.81] | 0.0386; [+0.51, +10.51] | 0.0156 | [+1.91, +7.39] | +4.2 (34/14, 0.0055); +6.1 (42/13, 1.1e-04); +6.3 (42/12, 5.2e-05) | yes |
| P-OFF | 478 | 9.41% / 12.34% | -2.93 | [-5.86, +0.00] | [-5.37, -0.49] | 0.207 / 0.206 | [-4.98, +0.77] | 0.139; [-7.48, +1.62] | 0.250 | [-4.76, +0.12] | -1.7 (22/30, 0.332) | yes |
| P-T | 478 | 9.41% / 6.69% | +2.72 | [+0.42, +5.09] | [+0.77, +4.67] | 0.146 / 0.139 | [-1.73, +5.12] | 0.0656; [-0.31, +5.75] | 0.195 | [-0.88, +4.42] | +2.5 (23/11, 0.0576) | yes |
| OFF-ON_all500 | 500 | 11.93% / 6.13% | +5.80 | [+3.47, +8.27] | [+3.80, +7.87] | 0.0167 / 0.0164 | [+1.35, +8.10] | 0.0376; [+0.59, +11.01] | 0.0156 | [+2.03, +7.58] | +3.8 (32/13, 0.0066); +6.6 (42/9, 3.4e-06); +7.0 (44/9, 1.2e-06) | yes |

Verdict (file): depth carries the effect; G +6.14, depth +5.65, trim +0.49, depth share 92.0%. Mine: depth share 92.0%; identity depth + trim = G holds exactly: True. Predictions (file): {'verdict_s8': 'depth carries the effect', 'pred1_depth_carries': True, 'pred2_trim_TOST3': True, 'pred3_TM_eq_T_TOST3': True, 'pred4_OFF_gt_TM': True}.

Between-seed SD of OFF−ON: 1.51pp (file variance 2.290 pp²).

Pooled resolve rates (mean over seeds) and empty-patch rates:

| arm | T set (478): resolve / empty | all 500: resolve / empty |
|---|---|---|
| ON | 6.21% / 45.5% | 6.13% / 45.2% |
| OFF | 12.34% / 39.9% | 11.93% / 40.2% |
| T | 6.69% / 47.1% | — |
| TM | 6.83% / 43.3% | — |
| P | 9.41% / 44.8% | — |

Nested subset (every T chunk among its file's OFF chunks; file of record): n = 358: OFF-T +6.42; T-ON +0.65; TM-T -0.19; OFF-TM +6.61; P-T +2.14. Exclude mode: n = 357: OFF-T +6.44; T-ON +0.65; TM-T -0.19; OFF-TM +6.63; P-T +2.24.

Old primary (exclude, results.json; the source of the paper's current numbers) vs new primary (scored) vs upper bound:

| contrast | exclude (n) Δ [95% CI]; wild p | **scored (n) Δ [95% CI]; wild p** | upper (n) Δ [95% CI] |
|---|---|---|---|
| OFF-ON | (477) +6.15 [+3.70, +8.74]; 0.0135 | **(478) +6.14 [+3.63, +8.65]; 0.0134** | (478) +6.14 [+3.63, +8.65] |
| OFF-T | (477) +5.66 [+3.00, +8.32]; 0.0379 | **(478) +5.65 [+3.07, +8.30]; 0.0378** | (478) +5.58 [+2.93, +8.23] |
| T-ON | (477) +0.49 [-0.91, +1.89]; 0.2175 | **(478) +0.49 [-0.91, +1.88]; 0.2180** | (478) +0.56 [-0.84, +1.95] |
| TM-T | (477) +0.14 [-1.12, +1.40]; 0.7456 | **(478) +0.14 [-1.05, +1.39]; 0.7456** | (478) +0.07 [-1.19, +1.32] |
| OFF-TM | (477) +5.52 [+2.87, +8.25]; 0.0136 | **(478) +5.51 [+2.93, +8.23]; 0.0138** | (478) +5.51 [+2.93, +8.23] |
| P-OFF | (477) -2.87 [-5.80, +0.07]; 0.2379 | **(478) -2.93 [-5.86, +0.00]; 0.2074** | (478) -3.00 [-5.93, -0.07] |
| P-T | (477) +2.80 [+0.49, +5.17]; 0.1310 | **(478) +2.72 [+0.42, +5.09]; 0.1457** | (478) +2.58 [+0.21, +4.95] |
| OFF-ON_all500 | (499) +5.81 [+3.41, +8.28]; 0.0166 | **(500) +5.80 [+3.47, +8.27]; 0.0167** | (500) +5.80 [+3.47, +8.27] |

Secondary mixed logit (VB; same specification as b1b3_glmm.py) refit in scored mode — arm effect posterior mean / SD (log-odds) and mean/SD:

| contrast | rows | mean | SD | mean/SD |
|---|---|---|---|---|
| OFF-ON | 2868 | +1.712 | 0.130 | +13.2 |
| OFF-T | 2868 | +1.589 | 0.132 | +12.0 |
| T-ON | 2868 | +0.164 | 0.187 | +0.9 |
| TM-T | 2868 | -0.008 | 0.198 | -0.0 |
| OFF-TM | 2868 | +1.452 | 0.128 | +11.3 |

