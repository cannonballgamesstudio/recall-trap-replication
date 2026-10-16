# Recall Trap — design-authority FREE analyses (reanalysis2, 2026-10-15)

No model calls, no GPU, no Docker (Task 13 skipped, see below). Paper not edited. Nothing committed.
Scripts and full tables: this directory (`run_all.sh`; per-task `tN_*.md` / `.json`).

**Conventions.** Δ in pp. b/c = first-arm-only / second-arm-only wins. McNemar = exact, two-sided. Wild = WCR wild-cluster bootstrap-t, Webb 6-point weights, B = 9,999, seed 20261014, G = 12 repositories. Its CI is found by test inversion on a 0.05 pp grid (0.01 pp in 10c), and every acceptance region is a single interval. CR2 = Bell–McCaffrey SE with BM degrees of freedom (about 3.3). Flip = exact repository sign-flip. Errored instances are scored unresolved.

**Task 0 — error_instances (nonzero only).**

| report | error_instances |
|---|---|
| gpt discovery ON / OFF | 3 / 5 |
| gpt logged re-run ON / OFF | 0 / 1 (sphinx-8269) |
| gpt T | 2 (sphinx-7985, sympy-20438) |
| gpt BM25 ON | 1 |
| Qwen3-Coder local ON (qwen30b_ON_rg) | 1 (sphinx-8475) |
| qwen3or K=12 ON | 1 |
| coder30b_c12k ON | 2 |
| 87-instance pilot ON | 1 |
| DeepSeek ON | 1 |

All other reports used have 0: Qwen T, both T′, dense, Qwen3.6 K = 4/12/40, agentic, and all 6 Branch A reports.

---

## 1. gpt decomposition against the pre-registered logged re-run (same 473)

| refs | ON / T / OFF | contrast | Δ | b/c | McN p | wild 95% CI; p | CR2 p | flip p | share |
|---|---|---|---|---|---|---|---|---|---|
| **re-run** | 40.6 / 40.6 / 46.7% | G = OFF−ON | +6.13 | 65/36 | 0.0051 | [+3.3, +12.0]; 0.018 | 0.032 | 0.0059 | |
| | | OFF−T (depth) | +6.13 | 66/37 | 0.0055 | [+0.3, +8.9]; 0.040 | 0.028 | 0.051 | 100% |
| | | T−ON (trim) | 0.00 | 41/41 | 1.000 | [−3.3, +7.1]; 1.00 | 1.00 | 1.000 | 0% |
| discovery (Table V, reproduced) | 39.1 / 40.6 / 46.9% | G / depth / trim | +7.82 / +6.34 / +1.48 | 71/34, 63/33, 46/39 | 3.9e−4 / 0.0029 / 0.515 | wild p 0.116 / 0.187 / 0.167 | 0.044 / 0.078 / 0.271 | 0.119 / 0.199 / 0.292 | 81% / 19% |

**60% rule on the re-run: "depth carries the effect"** (depth share 100%, McNemar p = 0.0055). The identity Δdepth + Δtrim = G holds exactly.

## 2. TOST equivalence for T−ON (90% CIs; pass if the CI lies inside ±m)

| contrast | Δ | inst. 90% CI | wild 90% CI | ±3 pp (inst. / wild) | 0.4·G margin | 0.4·G (inst. / wild) | smallest passing margin (inst. / wild) |
|---|---|---|---|---|---|---|---|
| gpt T−ON (Table V refs) | +1.48 | [−1.73, +4.69] | [−0.52, +4.38] | **fail / fail** (TOST p = 0.22) | 3.13 | fail / fail | 4.69 / 4.38 |
| gpt T−ON (re-run refs) | 0.00 | [−3.15, +3.15] | [−3.05, +5.85] | fail / fail (p = 0.059) | 2.45 | fail / fail | 3.15 / 5.85 |
| Qwen3-Coder T−ON | −0.21 | [−1.56, +1.14] | [−0.91, +0.89] | **PASS / PASS** (p = 3.3e−4) | 2.37 | PASS / PASS | 1.56 / 0.91 |
| agentic sonnet-5, fusion OFF−ON | −1.40 | [−4.02, +1.21] | [−3.90, +1.80] | fail / fail | — | — | 4.02 / 3.90 |
| agentic sonnet-5, dense OFF−ON | −1.80 | [−4.01, +0.41] | [−4.05, +0.85] | fail / fail | — | — | 4.01 / 4.05 |
| fusion × dense interaction | +2.63 | [−2.04, +7.31] | [−1.82, +9.58] | fail / fail | — | — | 7.31 / 9.58 |

The expected pattern is confirmed: gpt fails and Qwen passes, at both margins. For "not detected; CI" wording, the 95% CIs are:

| contrast | inst. 95% CI | wild 95% CI |
|---|---|---|
| agentic fusion | [−4.52, +1.72] | [−4.75, +3.05] |
| agentic dense | [−4.44, +0.83] | [−4.65, +2.00] |
| fusion × dense | [−2.94, +8.20] | [−4.07, +12.63] |

## 3. Holm over the confirmatory family (unrounded)

| method | Qwen3.6 K=12 raw → Holm | gpt re-run raw → Holm | both survive? |
|---|---|---|---|
| exact McNemar (pre-registered) | 0.013283 → 0.020127 | 0.010063 → 0.020127 | yes |
| wild (MC SE ≈ 0.0015) | 0.029103 → 0.037404 | 0.018702 → 0.037404 | yes |
| CR2 | 0.048618 → 0.078795 | 0.039398 → 0.078795 | no |
| sign-flip | 0.078125 → 0.078125 | 0.005859 → 0.011719 | gpt only |

## 4. ITT: never-submitted scored as failures (n = 500)

| arm | never-sub ON/OFF | PP Δ (p) | ITT Δ; b/c; McN p; wild p | worst case (ON never-sub = resolved) Δ; b/c; McN p; wild p |
|---|---|---|---|---|
| Qwen3.6 K=4 | 18/17 | +4.94 (1.9e−4) | +4.80; 31/7; 1.2e−4; 0.032 | **+1.20; 30/24; 0.50; 0.57** |
| Qwen3.6 K=12 | 0/1 | +3.61 (0.0133) | +3.60; 33/15; 0.0133; 0.029 | +3.60 (identical) |
| Qwen3.6 K=40 | 32/12 | +10.07 (7.7e−10) | +9.20; 54/8; 1.7e−9; 0.0125 | **+2.80; 53/39; 0.175; 0.57** |
| DeepSeek-v4-pro | 1/0 | +6.21 (4.5e−4) | +6.20; 53/22; 4.5e−4; 0.0076 | +6.00; 53/23; 7.6e−4; 0.0081 |
| dense (gpt) | 3/3 | +5.67 (0.0097) | +5.40; 69/42; 0.0132; 0.165 | +4.80; 69/45; 0.031; 0.204 |

## 5. Leave-django-out and leave-one-repo-out (LOO)

| contrast | full Δ; b/c; p | without django: n; Δ; b/c; McN p | LOO Δ range | largest LOO McN p (repo dropped) | LOO sign change |
|---|---|---|---|---|---|
| Qwen3.6 K=12 (confirmatory) | +3.61; 33/15; 0.0133 | 268; **+2.24; 13/7; 0.263** | +2.24 to +4.00 | 0.263 (django) | no |
| gpt re-run (confirmatory) | +5.40; 65/38; 0.0101 | 269; +7.06; 37/18; 0.0145 | +4.60 to +7.06 | 0.032 (astropy) | no |
| gpt discovery | +7.60; 73/35; 3.3e−4 | 269; +7.43; 40/20; 0.0135 | +6.12 to +9.21 | 0.0135 (django) | no |
| DeepSeek | +6.21; 53/22; 4.5e−4 | 269; +6.69; 27/9; 0.0039 | +5.62 to +6.69 | 0.0039 (django) | no |
| dense | +5.67; 69/41; 0.0097 | 266; +4.51; 35/23; 0.148 | +4.29 to +6.53 | 0.148 (django) | no |
| QC T: OFF−T / T−ON | +6.13 (38/9) / −0.21 (7/8) | 256; +3.91 (12/2, p = 0.013) / 0.00 (1/1) | +3.91 to +6.74 / −0.47 to 0.00 | 0.013 / 1.0 | no / (null) |
| gpt T, Table V refs: OFF−T / T−ON | +6.34 (63/33) / +1.48 (46/39) | 256; +5.08 (34/21, p = 0.105) / +1.95 | +4.98 to +8.14 / +0.86 to +2.05 | 0.105 / 0.74 | no / no |
| gpt T, re-run refs: OFF−T / T−ON | +6.13 (66/37) / 0.00 (41/41) | 256; +4.69 (32/20, p = 0.126) / +3.12 (25/17) | +4.69 to +6.98 / −0.70 to +3.12 | 0.126 / 1.0 | no / (null) |

Per-repository Δ and b/c for every contrast are in `t5_loo.md`.

## 6. Concordant subset

| quantity | value |
|---|---|
| File-level concordance (ON chunk = first OFF chunk of that file) | 2153/2431 = 88.6% (the paper's figure) |
| **Instance-level concordance (every T file concordant)** | **260/473 = 55.0%** |
| Position of the ON chunk among the file's OFF chunks | 1st 2153, 2nd 99, 3rd 24, 4th+ 18, absent 137 |

| model / refs | subset | OFF−ON | OFF−T | T−ON |
|---|---|---|---|---|
| Qwen3-Coder | concordant (260) | +5.77 (22/7, p = 0.008; wild 0.060) | +6.54 (22/5, p = 0.0015; wild 0.059) | −0.77 (4/6, p = 0.75) |
| | discordant (213) | +6.10 (16/3) | +5.63 (16/4) | +0.47 (3/2) |
| gpt, Table V refs | concordant (260) | +6.92 (39/21, p = 0.027) | +6.54 (35/18, p = 0.027) | +0.38 (26/25, p = 1.0) |
| | discordant (213) | +8.92 (32/13) | +6.10 (28/15) | +2.82 (20/14) |
| gpt, re-run refs | concordant (260) | **+3.46 (32/23, p = 0.28)** | +3.85 (32/22, p = 0.22) | −0.38 (22/23) |
| | discordant (213) | +9.39 (33/13, p = 0.0045) | +8.92 (34/15) | +0.47 (19/18) |

## 7. Structural rank fact

Under a single ranking, three things hold by construction:
- (i) files(OFF) ⊆ files(ON).
- (ii) Each OFF file's ON chunk is that file's first OFF chunk, so T ⊆ OFF chunk for chunk, and OFF−T adds exactly OFF's lower-ranked same-file chunks.
- (iii) Every chunk OFF adds over T has rank ≤ K, and every chunk ON adds over T has rank > K.

So OFF's extra chunks outrank ON's extra chunks by construction. A rank-matched K-slot pack with OFF's rank profile is OFF itself. The observed departures, (i) 94.6% and (ii) 88.6% of files / 55.0% of instances, measure the drift between the two service instances.

local_packs.json holds only `pack`, `files` and `n_hits` per side, with no rank or score fields. Chunk headers are `### file:line — symbol [kind]`. The 41 header hits on "score" or "rank" are all symbol or file names, such as `roc_auc_score` and `_ranking.py`.

## 8. E5 (Qwen3-Coder) Low−High interaction with a difficulty control (Low−High = −(paper's E3))

| model | Low−High, OFF−ON | 95% CI | p | OFF−T (secondary) |
|---|---|---|---|---|
| crude (no adjustment) | +4.96 | [−0.5, +10.4] | 0.076 | +4.39 (p 0.13) |
| MH-stratified by difficulty (3 levels) | +4.91 | [−0.5, +10.4] (bootstrap [−0.4, +10.4]) | 0.077 | +4.33 (0.14) |
| MH: difficulty × multi-file × added-lines tercile | +4.55 | [−0.9, +10.0] | 0.100 | +3.61 (0.21) |
| GEE logit off×lowM, + difficulty + arm×difficulty | log-ROR +0.862, ROR 2.37 [1.09, 5.12] | | **0.029** | ROR 1.99 [0.94, 4.23], 0.073 † |
| GEE logit, + added lines and multi-file (each × arm) | ROR 2.41 [1.11, 5.21] | | 0.026 | 0.073 † |
| RD regression with difficulty, CR2 by repository | +4.91 | [−4.2, +14.0] | 0.197 | +4.33 (0.105) |

Difficulty is balanced across strata (Low-M 39/52/9% vs High-M 38/52/9% for <15 min / 15 min–1 h / ≥1 h; median added lines 4 vs 5), so it does not confound E5. Adjustment moves the interaction by ≤ 0.4 pp.

† For OFF−T, difficulty was collapsed to two levels (<15 min vs ≥15 min), because T resolves 0/45 instances in the ≥1 h stratum, which makes the 3-level model quasi-separated.

## 9. Repository-cluster bootstrap

| estimand | n (clusters) | Δ | instance boot 95% CI; P(Δ*>0) | repo-cluster 95% CI; P(Δ*>0) | label (0.80 rule) |
|---|---|---|---|---|---|
| Branch A, A1 gpt (2 seeds) | 105 (77) | +2.38 | [−1.9, +6.7]; 0.843 | [−1.9, +7.1]; 0.827 (80% CI [−0.5, +5.4]) | sign-consistent, unchanged |
| A2 ≥ 2026-04-01 / A6 single-file / A5 Qwen | 49 (40) / 39 (32) / 105 (77) | 0.0 / 0.0 / +0.95 | P 0.40 / 0.45 / 0.61 | [−4.2, +4.1] / [−8.3, +9.4] / [−2.0, +4.3] | uninformative, unchanged |
| PolyBench pooled | 617 (19) | +2.59 | [+0.00, +5.37]; P(≤0) = 0.030 | **[−1.19, +6.62]; P(≤0) = 0.100** (wild p 0.215; flip p 0.254) | G-4 verdict unchanged |
| PolyBench A3B / gpt | 280 (17) / 337 (19) | +2.86 / +2.37 | [+0.36, +5.36] / [−1.48, +6.53] | [−0.36, +6.84] / [−3.86, +8.36] | |

## 10. Numeric fixes

| item | result |
|---|---|
| (a) fusion × dense +2.6 | The +2.63 is an instance-paired DiD on the 494 instances paired in both arms. The 6 instances dense never submitted carry fusion d = (−1, 0, 0, −1, −1, 0), so fusion's Δ on the 494 is +8.30, not +7.60: 8.30 − 5.67 = +2.63. Table II's marginal Δs differ by only +1.93. Inference: wild p = 0.208, CR2 p = 0.322, flip p = 0.275. **Against the re-run: +0.20** (fusion re-run +5.87 on the 494; 95% CI [−5.2, +5.6]; wild p = 0.93). |
| (b) fusion × BM25 against the re-run | **+8.60** (n = 500). Instance 95% CI [+3.2, +14.0], p = 0.0018. Wild [+6.0, +15.5], p = 0.0079. CR2 [+3.6, +13.6], p = 0.011. Flip p = 0.0059. The discovery-draw version, +10.80, has wild p = 0.051 and flip p = 0.063. |
| (c) re-run wild CI, 0.01 pp grid | [+3.19, +11.31] (B = 9,999, paper seed). With B = 99,999 and seeds 20261014/1/2/3: [+3.17 to +3.18, +11.24 to +11.28]. The acceptance region is one interval. **[+3.2, +11.3] is correct.** The asymmetry is genuine: the p-curve falls from 0.32 at +4.0 to 0.05 at +3.2, but decays slowly above the estimate (0.089 at +10.0). |
| (d) Qwen3-Coder K=12 pairs | See the table below. |

| pair | resolved ON / OFF | where it feeds |
|---|---|---|
| **local qwen30b_{ON,OFF}_rg** | 33 / 62 | Table V, Fig. 1, random-chunk control (6.6% / 12.4%), E5, fix locality |
| **OpenRouter qwen3or_k12** | 37 / 58 | Budget-K sweep (7.4% / 11.6%, +4.2, 33/12), E5 proxy-M K=4/12/40 cells, MDE row K=4, **and the anchor table's QC column**: all five cells match (B→C +31.2 26/1, B→B +0.4, C→C −5.7, A→A −1.7, B→A 0.0). The local pair would give B→C +30.0 (24/0), B→B −0.4, C→C +8.6. |
| coder30b_c12k | 35 / 59 | Not cited in v2. |

## 11. Per-stratum point estimates, memorization (OFF−ON, pp)

| model | strata | estimates | all positive? |
|---|---|---|---|
| gpt, pooled over both draws | Low-M, High-M; M = 0/1/2/3; S1; P1 −/+; P2 −/+; P3 −/+; B→C; E2 (Low-M ∩ B→C); High-M ∩ B→C | +6.4, +6.5; +6.4/+5.5/+5.0/+12.5; +10.7; +7.1/+7.7; +5.7/+7.3; +6.2/+6.9; +25.6; +55.6; +21.8 | **yes** (range +5.0 to +55.6) |
| gpt, discovery draw only | | | No: M=0 among P1-eligible and S1 (n = 14) are **0.0**. Everything else is positive. |
| gpt, re-run only | | | yes |
| Qwen3-Coder E5, OFF−ON and OFF−T | | | yes, every non-empty stratum (Low +8.6 / High +3.6 for OFF−ON; M=3 is empty) |
| Qwen3-Coder, T−ON | | | Mixed, as expected for a null (High −0.8, Low +0.5) |
| Qwen3-Coder, K=4 proxy-M | | | One stratum at −0.4 (M=1, P1-eligible) |

## 12. T−ON 95% CIs

| contrast | instance 95% | wild 95% | CR2 95% |
|---|---|---|---|
| gpt (Table V refs) +1.48 (46/39) | [−2.34, +5.30] | [−1.42, +5.48] | [−1.89, +4.85] |
| gpt (re-run refs) 0.00 (41/41) | [−3.76, +3.76] | [−3.35, +7.10] | [−7.66, +7.66] |
| Qwen3-Coder −0.21 (7/8) | [−1.82, +1.40] | [−1.36, +1.14] | [−1.28, +0.85] |

## 13. Environment-parity spot check: SKIPPED

The GPU model server was up: llama-server with Qwen3-Coder-30B on :8091, using 23.8 GB of VRAM and driven by a running `fanout_calibrate.py` job. Docker was idle, but because the server was up, no Docker command was issued and no WSL caches were dropped. Details and the run recipe are in `t13_env_parity.md`.

---

## Surprises, most verdict-relevant first

1. **The Qwen3.6 confirmatory test rests on django.** Without django it is +2.24 pp (13/7, McNemar p = 0.26). Every other leave-one-out fit stays at p ≤ 0.05; dropping django alone flips the conclusion. The gpt re-run is robust (LOO max p = 0.032) and gets stronger without django (+7.06). Dense also loses significance without django (p = 0.148).
2. **The budget claim is not robust to adversarial ITT.** Qwen3.6 K=40 never-submitted is 32 ON vs 12 OFF. Plain ITT keeps the claim (+9.2, p = 1.7e−9). The worst case (ON never-submitted counted as resolved) gives +2.8 (p = 0.18, wild p = 0.57), and K=4 drops to +1.2 (p = 0.50). "Largest at K=40 / does not shrink" therefore depends on how the 32 ON non-submissions are treated. K=12, DeepSeek and dense are robust.
3. **gpt depth term against the pre-registered re-run:** the verdict is unchanged ("depth carries the effect"), but the split is cleaner (100% / 0%, trim 41/41). The depth term is now repository-level significant under wild (p = 0.040) and CR2 (0.028), and borderline under sign-flip (0.051). The paper's "gpt instance-level only" sentence is tied to the discovery-draw references (flip 0.199).
4. **TOST:** gpt T−ON fails ±3 pp equivalence with every reference pair and both CI types. The smallest margin it would pass is 4.4–5.9 pp. "Neither help nor hurt" or "matches" is licensed for Qwen3-Coder only (passes at both ±3 and 0.4·G = 2.37). For gpt, use "not detected; 95% CI [−2.3, +5.3]".
5. **Instance-level concordance is 55.0%, not 88.6%.** The paper's 88.6% is per file. On the concordant 260, point estimates keep the pattern (depth ≈ G, trim ≈ 0) for all three model/reference pairs. However, the gpt re-run OFF−ON there is only +3.46 (p = 0.28) against +9.39 on the discordant 213. Significance in the concordant subset survives at the instance level for Qwen3-Coder and gpt discovery only, and not under clustering.
6. **The anchor table's QC column comes from a different run** (OpenRouter qwen3or_k12) than every other Qwen3-Coder-30B K=12 figure (local qwen30b_rg). The "+25 to +31 pp" in the Discussion uses the OpenRouter +31.2; the local pair gives +30.0.
7. **Fusion × BM25 against the re-run (+8.6) is significant under every method** (wild 0.008, CR2 0.011, flip 0.006). It is stronger than the discovery-draw +10.8 the paper reports (wild 0.051). **Fusion × dense against the re-run is +0.2**, so the +2.6 is a discovery-draw artefact of 6 excluded instances.
8. **"No stratum ... outside +5.7 to +7.3" is false.** The pooled gpt strata span +5.0 (M=2) to +12.5 (M=3), and +10.7 for S1, before counting the B→C strata. They are all positive, but the range sentence needs replacing (e.g., "all positive, +5.0 to +12.5 outside B→C").
9. **The E5 interaction is scale-dependent.** On the risk-difference scale it stays non-significant after the difficulty control (+4.9 pp, p = 0.077; CR2 p = 0.20). On the logit scale (GEE) it is p = 0.029 (ROR 2.37), because Low-M ON resolves 4.1% against 8.6% for High-M. Difficulty is balanced, so it is not the explanation. "Larger in Low-M" still needs the hedge that the RD interaction is not significant.
10. **PolyBench under a repository-cluster bootstrap:** the CI widens to [−1.2, +6.6] with P(Δ ≤ 0) = 0.10. The instance-clustered [0.0, +5.3] and one-sided 0.031 overstate precision. The G-4 verdict is unchanged. Branch A is unchanged (A1 still sign-consistent; P = 0.83).
11. Holm reproduces the paper (0.020 / 0.037 / 0.079 / 0.012 and 0.078). The re-run wild CI [+3.2, +11.3] is correct; its asymmetry is genuine.
