# Recall Trap: POST-HOC robustness analyses (reanalysis3)

**Every analysis in this folder is post hoc.** They were requested by an internal, pre-submission blind statistical review (items A.1, A.2, B, E) after all results were known. None of them is a registered test. The post-hoc size check in the paper's Statistics paragraph comes from `s1_size`.

Scope and rules:
- CPU only. There are no model calls and nothing uses a GPU or Docker.
- **Data.** This package, with `code/prepare_data.py` run once to build `work/p5`. Every grading report used is hash-identical to the one the analyses were first run on. The exception is `instances_verified.json`, which differs only by masking; its repository labels are identical.
- **Writes.** Only into `results/reanalysis3/`.
- **Running.** `code/analysis/reanalysis3/run_all.sh` reruns everything in about 3 minutes. Each script `sN_*.py` writes `sN_*.md` (full tables) and `sN_*.json` (every number).

**Conventions** (as in the paper and reanalysis2):
- d = A − B per instance. Empty patches and harness errors count as failures over the full n. Never-submitted instances are excluded pairwise.
- **wild:** WCR wild-cluster bootstrap-t, Webb 6-point weights, CR1 studentisation, B = 9,999, seed 20261014. The CI comes from test inversion on a 0.05pp grid, and every acceptance region found is a single interval.
- **CR2:** Bell–McCaffrey SE with BM df (about 3.3 on Verified).
- **flip:** exact repository sign-flip over 2^12 assignments.
- **pct:** the *registered* repository percentile bootstrap. It uses 5,000 reps with Python `random` seed 20260714, implemented exactly as `code/analysis/core/common.py::cluster_bootstrap`. Its two-sided p is 2·min(P(Δ*≤0), P(Δ*≥0)).
- **Replication primary** is now "sphinx-8475 Class-P cells scored unresolved", from `results_scored.json`.

---

## Summary: what changes in the paper

| # | Paper text now (main.tex) | What the post-hoc analyses show | Source |
|---|---|---|---|
| 1 | Abstract, §IV-A and Conclusion: both tests "Holm-corrected under the exact test and a 12-repository wild cluster bootstrap". | True only for the paper's own 2-test family {Qwen3.6, gpt **re-run**}. That family departs from the registration: GPT-LOGGED (a)/(c)/(e) keep the discovery draw as headline and put the re-run outside Holm. **2-test family with the registered gpt headline (discovery):** survives under McNemar (adjusted .0133 / .00065) and the registered pct (.030 / .042). It fails under wild (.058 / .104), CR2 (.090 / .090) and flip (.156 / .156). **Registered 5-test family** {gpt discovery, Qwen3.6, dense, DeepSeek, PolyBench}: McNemar keeps all four Verified arms; under wild and pct only DeepSeek survives; under CR2 and flip none survive. **4-test version** (no PolyBench): McNemar all; wild DeepSeek only; CR2 DeepSeek only; flip none; pct Qwen3.6 + DeepSeek. | s2 |
| 2 | §IV Statistics: the percentile cluster bootstrap "is unreliable at G = 12 and was replaced". | This is now evidenced. Under the actual cluster structure the registered pct bootstrap rejects a true null **7.6–11.3%** of the time at nominal 5%. WCR-Webb wild holds **4.9–6.2%**. CR2-BM is conservative (2.2–4.1%) under instance-level nulls, but rejects **13.1%** under a repository-level null with the discovery-draw structure. Cite MacKinnon & Webb (2017). | s1 |
| 3 | Table II: re-run wild CI [+3.2, +11.3], compared with iid. | The CI is from test inversion and is a single interval, and its lower bound is real. The repository SE (CR1 1.45pp) is smaller than the iid SE (2.02pp), because 10 of 12 repositories have mean Δ ≥ +3.1pp (the exceptions are matplotlib −2.9 and seaborn 0.0). At b0 ≈ +3.2 django's null-imposed cluster sum vanishes (django's own Δ is +3.5pp), so the bootstrap critical value drops to 1.52. An exact sign-flip test inverted gives a similar lower bound, **[+3.07, +12.37]**. The WCR test at the lower endpoint rejects 5.1% under a repository-symmetric null. CR2 gives the wider [+0.47, +10.33]. | s1 |
| 4 | Replication numbers (Fig. 1 caption, Table V row 1, Table VI, §V-C) use n = 477 with the instance excluded. | **New primary (scored, n = 478):** <br>• rates: ON 6.2 / T 6.7 / OFF 12.3 / TM 6.8 / P 9.4% <br>• OFF−ON +6.14 [+3.63, +8.65], wild .013 <br>• depth +5.65 [+3.07, +8.30], wild .038 <br>• trim +0.49 [−0.91, +1.88] <br>• TM−T +0.14 [−1.05, +1.39], wild .75 <br>• OFF−TM +5.51 [+2.93, +8.23], wild .014 <br>• P−T +2.72 [+0.42, +5.09], wild **.15** (paper .13) <br>• P−OFF −2.93 [−5.86, +0.00], wild **.21** (paper .24) <br>• nested subset **358** (paper 357): +6.4 / +0.7 / −0.2 <br>• T empty rate 47.1% (paper 47.0) <br>The verdict and all four predictions are unchanged. | s7 |
| 5 | Table VI caption: "TM 12.9/6,323, P 5.2/4,972". | **TM 12.40 slots** (12.90 is the pre-ruling TM, never generated). **P 5,706 characters** (4,972 is the superseded first build, in which 326 P files were not read; it was never generated). P/OFF = **0.902**, P/T = **2.04**. The "0.79" in the review is 4,972/6,322. README line 130 also says TM 12.90. | s5 |
| 6 | Discussion: the retriever's chunks are "worth more than adjacent lines at equal size". | P is 0.90× OFF, not equal size. Same-seed P−OFF (seed 0) is **−1.67pp, 22/30, McNemar p = .33**, wild .40, iid 95% CI [−4.6, +1.3]. | s5 |
| 7 | "depth accounts for 92%". | 92.0%. Instance-paired bootstrap **[67%, 117%]**; repository-cluster **[52%, 103%]**. Headline rows: Qwen3-Coder 104% [77%, 142%] / cluster [75%, 120%]; gpt discovery 81% [38%, 144%], with the cluster interval **unbounded below** (2.6% of draws have G* ≤ 0); gpt re-run 100% [43%, 218%] / [27%, 158%]. | s4 |
| 8 | Trim "equivalent to nothing within ±3pp" (TOST unclustered). | It survives clustering. Replication T−ON passes ±3 under instance, wild, CR2 and pct 90% CIs, with **m\* 1.60 / 1.34 / 1.20 / 1.28**. TM−T has m\* 1.19 / 1.26 / 1.11 / 1.04. Qwen3-Coder headline T−ON has m\* 1.56 / 0.91 / 1.01 / 0.77. gpt fails everywhere: m\* **3.15–5.85** against the re-run and **4.01–4.69** against discovery. The ±3 margin itself was chosen post hoc. | s3 |
| 9 | gpt trim "0.0". | Against the re-run, the 0.0 is a cancellation: django **−3.69** (16/24) against non-django **+3.12** (25/17). Against discovery it is +0.92 / +1.95. Among both-non-empty pairs gpt T−ON is **+1.63** (30/24, p = .50, n = 368) against the re-run, and **+4.02** (34/19, p = .053, n = 373) against discovery. | s3 |
| 10 | E5: interaction "not significant on the risk-difference scale". | It is significant on the logit scale. GEE ROR **2.32 [1.09, 4.91], p = .028** unadjusted (the reviewer's figure, verified), and 2.37, p = .029 with difficulty. On the RD scale it is +4.96pp, instance p .076 and CR2 p .18. Confound checks: (i) the 61 instances with no gold file in the ON pack have 0 discordant pairs, so the effect lives entirely where ON localised the file, and Low-M is larger there too (+10.1 vs +4.0). (ii) **The Low-M excess is concentrated in P1-not-applicable instances**, where the issue names a gold basename: Low-M +12.6 vs High-M 0.0. Where P1 was actually tested, Low-M is +4.5 against High-M +3.9 (RD interaction +0.6, p .85), and Low-M ON resolves 0.9%. | s6 |
| 11 | Pooled-gpt (Branch B estimator) is not reported for RQ1. | Both draws pooled: **+6.50pp**. Exact instance randomisation p 1.3e−4; wild [+0.8, +12.2], p .035; CR2 p .024; flip p .024; pct [+3.0, +11.0]. Each is individually significant. With Qwen3.6, Holm: McNemar, CR2 and pct keep both; wild keeps neither (.058); flip keeps the pooled gpt test only. | s2 |
| 12 | gpt depth term under the registered T reference (discovery). | +6.34 (63/33). McNemar .0029; wild p **.187**; CR2 .078; flip .199; pct [−1.5, +10.9], P(Δ*≤0) = .050. This reproduces reanalysis2 t1. | s2 |

---

## 1. Wild-bootstrap size check under the actual cluster structure (`s1_size.py`)

**Null data.** Each contrast's own instances are used. The observed d_i, the repository labels (G = 12; django 231 of 500) and the cluster sizes are kept, and the ON/OFF labels are randomised, so the true Δ = 0.
- **DGP A** (requested): labels are swapped within instance, d\*_i = s_i·d_i, with R = 2,000.
- **DGP B** (added, harsher): labels are swapped for whole repositories. All 4,096 patterns are enumerated, which keeps any between-repository heterogeneity.
- **Per replicate:** the paper's WCR-Webb wild with B = 999 fresh weights; CR2-BM (df 3.33); exact flip; the registered pct bootstrap with 999 reps, rejecting when its 95% CI excludes 0; McNemar; and iid z.

Empirical rejection rate at α = 0.05 (MC SE ≈ 0.005):

| instance structure | DGP | **wild** | **CR2-BM** | sign-flip | registered pct | McNemar | iid z |
|---|---|---|---|---|---|---|---|
| Qwen3.6-27B K=12 (n = 499; 48 discordant, 28 in django) | A | **0.051** | **0.041** | 0.021 | 0.091 | 0.029 | 0.055 |
| | B | **0.057** | **0.031** | 0.016 | 0.078 | — | — |
| gpt re-run (n = 500; 103 discordant, 48 in django) | A | **0.049** | **0.027** | 0.032 | 0.076 | 0.045 | 0.045 |
| | B | **0.058** | **0.062** | 0.043 | 0.105 | — | — |
| gpt discovery (n = 500; 108 discordant, 48 in django) | A | **0.059** | **0.031** | 0.036 | 0.100 | 0.051 | 0.051 |
| | B | **0.060** | **0.131** | 0.039 | 0.113 | — | — |

Verified twice more:
- With a second outer seed (`s1_size_seed7_B999.md`), wild is 0.050–0.060 and CR2 0.029–0.131.
- With the paper's own B = 9,999 inner bootstrap (`s1_size_seed11_B9999.md`), wild is **0.051–0.062**, CR2 0.022–0.131, and pct 0.078–0.110.
- Sign-flip rates under B are exact and identical in every run.

**Reading.**
- **WCR-Webb wild** is close to nominal under this structure. It runs about 1pp liberal under repository-level nulls (0.057–0.062).
- **CR2-BM** is conservative under instance-level nulls. It is liberal under repository-level nulls for the discovery-draw structure (0.131).
- **The registered percentile bootstrap** over-rejects in every cell (0.076–0.113). This supports the decision to replace it, although that decision was taken post hoc.

**Why the re-run wild CI [+3.2, +11.3] has a tighter lower bound than iid [+1.45, +9.35]:**

| construction | SE (pp) | 95% CI |
|---|---|---|
| iid normal | 2.02 | [+1.45, +9.35] |
| CR1, normal | 1.45 | [+2.55, +8.25] |
| CR1, t(11) | 1.45 | [+2.20, +8.60] |
| CR2, t(3.33) | 1.64 | [+0.47, +10.33] |
| wild WCU (unrestricted) percentile-t, symmetric | 1.45 | [+1.80, +9.00] |
| **wild WCR, test inversion (paper)** | 1.45 | **[+3.19, +11.31]** (single interval) |
| exact repository sign-flip, inverted | — | [+3.07, +12.37] |

- **The CI is by test inversion.** At each b0 the bootstrap imposes Δ = b0. The observed t(b0) = (Δ̂ − b0)/SE_CR1 uses a fixed CR1 SE, and only the reference distribution moves with b0.
- **Between-repository consistency.** The CR1 SE is 28% smaller than the iid SE. Per-repository mean Δ is +3.1 to +100pp in 10 of 12 repositories (the exceptions are matplotlib −2.9 and seaborn 0.0); django is +3.5pp.
- **The critical value collapses near the lower bound.** At b0 ≈ +3.2 to +3.5pp, the null-imposed django cluster sum S_dj − b0·n_dj ≈ 0: django's share of Σ(restricted sums)² is ≤ 0.01. The bootstrap-t is then driven by the 11 small, mostly positive clusters, and its 95% critical value falls to **1.52**, against 2.48 at b0 = Δ̂ and 3.10 at b0 = 0. Above Δ̂, django dominates again (share 0.77–0.84 at b0 = 8–11pp), the critical value rises to 3.4–4.1, and the upper bound is long. That is the asymmetry.
- **It is not a wild artefact.** The exact randomisation (sign-flip) inversion gives nearly the same lower bound (+3.07).
- **It holds at the endpoint.** At the endpoint b0 = +3.19, the WCR test rejects 5.1% of the time (and at b0 = +11.31, 5.4%) when the truth is b0 and repository deviations are sign-symmetric. All 4,096 patterns were used.
- **CR2 is the conservative alternative.** Its lower bound is +0.47.

## 2. RQ1 under the registered structure (`s2_rq1_registered.py`)

**Registered structure, verified in the documents:**
- `GPT-LOGGED-REPLICATION-PREREG.md`:
  - (a) the headline is the discovery run, +7.6, 196/234;
  - (c) the re-run's resolve Δ is a secondary, direction-only endpoint;
  - (e) the re-run is outside Holm.
- `TRIMMED-BREADTH-PREREG.md` §9 D1 names 196/234 as the gpt T reference.
- **Holm family in force when GPT-LOGGED was committed** (c35850a, 2026-08-08). It is the five raw McNemar p in draft-v5 §4.5 (at ab6f065): {gpt discovery, Qwen3.6-27B, DENSE-1, DeepSeek, PolyBench pooled}. The same draft's §6.1, and draft.md (2026-07-16), say "the four single-shot A/Bs". `QWEN36-PREREG.md` names no Holm family; it registers McNemar exact, empties-as-failure.
- **Registered clustered method:** the percentile repository bootstrap.

| contrast | n | ON/OFF | Δ | b/c | McNemar p | wild 95% CI; p | CR2 95% CI; p | flip p | **registered pct 95% CI; P(Δ*≤0); 2-sided p** |
|---|---|---|---|---|---|---|---|---|---|
| **gpt discovery (registered headline)** | 500 | 196/234 | +7.60 | 73/35 | 3.3e−4 | [−2.5, +15.8]; **.104** | [+0.3, +14.9]; .045 | .105 | **[+0.6, +13.0]; .0208; .042** |
| gpt re-run (registered secondary) | 500 | 205/232 | +5.40 | 65/38 | .0101 | [+3.2, +11.3]; .019 | [+0.5, +10.3]; .039 | .0059 | [+3.4, +10.3]; 0/5000; <4e−4 |
| **gpt both draws pooled (per instance)** | 500 | — | +6.50 | 99/53 instances | exact instance randomisation 1.3e−4 (stacked 138/73 nominal 9e−6) | [+0.8, +12.2]; .035 | [+1.6, +11.4]; .024 | .024 | [+3.0, +11.0]; .0004; .0008 |
| Qwen3.6-27B K=12 | 499 | 46/64 | +3.61 | 33/15 | .0133 | [+0.5, +5.2]; .029 | [+0.0, +7.2]; .049 | .078 | [+0.9, +4.9]; .0074; .015 |
| DeepSeek-v4-pro | 499 | 65/96 | +6.21 | 53/22 | 4.5e−4 | [+3.3, +11.6]; .0076 | [+2.7, +9.8]; .010 | .016 | [+3.9, +10.1]; .0002; .0004 |
| DENSE-1 (gpt, dense) | 494 | 205/233 | +5.67 | 69/41 | .0097 | [−2.2, +10.5]; .133 | [−0.0, +11.3]; .050 | .219 | [−0.9, +8.6]; .043; .087 |
| PolyBench pooled (19 repos) | 617 | — | +2.59 | 39/23 | .0559 | [−1.6, +7.1]; .215 | [−1.9, +7.1]; .227 | .254 | [−1.1, +6.7]; .105; .21 (registered was an instance bootstrap) |

Holm-adjusted p (raw → adjusted; ✔ = survives α = .05):

| family | McNemar | wild | CR2 | flip | registered pct |
|---|---|---|---|---|---|
| **F5 registered** {disc, Q3.6, dense, DS, Poly} | disc .0016 ✔, Q3.6 .029 ✔, dense .029 ✔, DS .0018 ✔, Poly .056 | disc .31, Q3.6 .12, dense .31, **DS .038 ✔**, Poly .31 | all ≥ .051 (DS .0506) | all ≥ .078 | disc .125, Q3.6 .059, dense .17, **DS .002 ✔**, Poly .21 |
| **F4** (§6.1 wording) {disc, Q3.6, dense, DS} | all ✔ (.0013 / .019 / .019 / .0013) | **DS .030 ✔** only | **DS .041 ✔** only | none (DS .063) | **Q3.6 .044 ✔, DS .0016 ✔**; disc .083, dense .087 |
| F2-reg {Q3.6, disc} | ✔ ✔ (.0133 / .00065) | .058 / .104 ✗ | .090 / .090 ✗ | .156 / .156 ✗ | ✔ ✔ (.030 / .042) |
| F2-paper {Q3.6, re-run} | ✔ ✔ .020 | ✔ ✔ .037 | ✗ .079 | re-run only (.012; Q3.6 .078) | ✔ ✔ |
| F2-pooled {Q3.6, gpt pooled} | ✔ ✔ | ✗ .058 / .058 | ✔ ✔ (.049 / .047) | pooled only (.049) | ✔ ✔ |

**Percentile cluster bootstrap verified.**
- Every pct row above reproduces `results/core/paired_contrasts.md`: discovery [+0.6, +13.0] 0.021; Qwen3.6 [+0.9, +4.9] 0.007; DeepSeek [+3.9, +10.1] 0.000; dense [−0.9, +8.6] 0.043; re-run [+3.4, +10.3] 0.000.
- Re-running the package's own `paired_contrasts.py` in the copy regenerates that file **byte-identically**.
- Every wild, CR2 and flip p in rows 1, 2, 4, 5 and 6 equals Table II of the paper.

**Disclosure note.** GPT-LOGGED quotes the discovery run's registered clustered CI as **[+0.8, +13.1]**. The package's registered implementation gives [+0.6, +13.0] (same estimator, different implementation and seed in the arXiv-era code). Its RESULT block (+6.41, 67/35, n = 499, CI [+4.92, +11.28]) is the pre-regrade re-run (review item A.3).

**gpt decomposition (473) by reference.**

| term | discovery reference (registered) | re-run reference |
|---|---|---|
| G | +7.82; McN 3.9e−4; wild **.116**; CR2 .044; flip .119; pct [+0.4, +12.8] | +6.13; McN .0051; wild .018; CR2 .032; flip .006; pct [+3.9, +11.3] |
| depth | +6.34; McN .0029; wild **.187**; CR2 .078; flip .199; pct [−1.5, +10.9] | +6.13; McN .0055; wild .040; CR2 .028; flip .051; pct [+1.7, +8.8] |
| trim | +1.48; McN .52; wild .167; pct [−1.1, +5.1] | 0.00; McN 1.0; pct [−2.6, +5.7] |

## 3. Equivalence under clustered 90% CIs (`s3_equiv.py`)

TOST at α = .05 passes iff the 90% CI lies inside ±m. **m\*** = max(|lo|, |hi|) of the 90% CI.

| contrast | n | Δ | instance 90% | wild 90% | CR2 90% (df) | pct-cluster 90% | ±3 passes? | **m\*** (inst / wild / CR2 / pct) |
|---|---|---|---|---|---|---|---|---|
| replication T−ON, scored | 478 | +0.49 | [−0.63, +1.60] (registered boot) | [−0.21, +1.34] | [−0.22, +1.20] (3.36) | [+0.00, +1.28] | all 4 | **1.60 / 1.34 / 1.20 / 1.28** |
| replication TM−T, scored | 478 | +0.14 | [−0.91, +1.19] | [−1.26, +0.94] | [−0.83, +1.11] | [−1.04, +0.67] | all 4 | **1.19 / 1.26 / 1.11 / 1.04** |
| replication T−ON, exclude mode | 477 | +0.49 | [−0.70, +1.68] | [−0.21, +1.34] | [−0.22, +1.20] (3.35) | [+0.00, +1.28] | all 4 | 1.68 / 1.34 / 1.20 / 1.28 |
| replication TM−T, exclude mode | 477 | +0.14 | [−0.91, +1.19] | [−1.26, +0.94] | [−0.83, +1.11] | [−1.04, +0.68] | all 4 | 1.19 / 1.26 / 1.11 / 1.04 |
| Qwen3-Coder headline T−ON | 473 | −0.21 (7/8) | [−1.56, +1.14] (Wald) | [−0.91, +0.89] | [−1.01, +0.59] | [−0.77, +0.58] | all 4 | **1.56 / 0.91 / 1.01 / 0.77** |
| gpt T−ON vs re-run | 473 | 0.00 (41/41) | [−3.15, +3.15] | [−3.05, +5.85] | [−5.76, +5.76] | [−2.31, +4.92] | none | **3.15 / 5.85 / 5.76 / 4.92** |
| gpt T−ON vs discovery | 473 | +1.48 (46/39) | [−1.73, +4.69] | [−0.52, +4.38] | [−1.05, +4.01] | [−0.46, +4.14] | none | **4.69 / 4.38 / 4.01 / 4.14** |

- The instance bootstrap reproduces `results_scored.json` to the last digit.
- The headline rows reproduce reanalysis2 t2.

**gpt trim diagnostics (473).**

| reference | full Δ | django (217): Δ; b/c; contribution | non-django (256): Δ; b/c; contribution | both non-empty: n; Δ; b/c; McNemar p |
|---|---|---|---|---|
| re-run | 0.00 | **−3.69**; 16/24; −1.69 | **+3.12**; 25/17; +1.69 | 368; **+1.63**; 30/24; .50 |
| discovery | +1.48 | +0.92; 20/18; +0.42 | +1.95; 26/21; +1.06 | 373; **+4.02**; 34/19; .053 |
| (Qwen3-Coder) | −0.21 | −0.46; 6/7 | 0.00; 1/1 | 194; +0.52; 4/3; 1.0 |

## 4. Share CI (`s4_share.py`)

| row | n | G / depth / trim (pp) | **share** | instance-paired 95% | repo-cluster 95% | Fieller (inst / CR1 t11) |
|---|---|---|---|---|---|---|
| replication, scored | 478 | +6.14 / +5.65 / +0.49 | **92.0%** | **[67%, 117%]** | **[52%, 103%]** | [68%, 117%] / [76%, 104%] |
| replication, exclude (the paper's 92%) | 477 | +6.15 / +5.66 / +0.49 | 92.0% | [68%, 116%] | [54%, 103%] | [68%, 117%] / [76%, 104%] |
| Qwen3-Coder headline (paper 104%) | 473 | +5.92 / +6.13 / −0.21 | 103.6% | [77%, 142%] | [75%, 120%] | [78%, 142%] / [86%, 114%] |
| gpt vs discovery (paper 81%) | 473 | +7.82 / +6.34 / +1.48 | 81.1% | [38%, 144%] | [0%, 117%] conditional on G* > 0; **2.6% of draws have G* ≤ 0, so effectively unbounded below** | [38%, 146%] / [30%, 118%] |
| gpt vs re-run (paper 100%) | 473 | +6.13 / +6.13 / 0.00 | 100.0% | [43%, 218%] | [27%, 158%] | [44%, 223%] / [42%, 242%] |

- Both bootstraps resample the joint per-instance outcomes, with B = 10,000.
- P(share\* ≥ 60%), the pre-registered rule's threshold, is 0.993 (instance) and 0.963 (cluster) for the replication; 0.84 for gpt vs discovery.

## 5. Practitioner P (`s5_practitioner.py`)

**Same-seed contrasts** (seed 0; scored, n = 478):

| contrast | rates | Δ | b/c | McNemar | iid 95% | wild 95%; p | CR2 p | flip p |
|---|---|---|---|---|---|---|---|---|
| **P−OFF s0** | 9.41 / 11.09% | **−1.67** | 22/30 | **.33** | [−4.63, +1.28] | [−3.37, +1.33]; .40 | .25 | .50 |
| **P−T s0** | 9.41 / 6.90% | **+2.51** | 23/11 | **.058** | [+0.13, +4.89] | [−1.99, +4.96]; .17 | .084 | .25 |
| P−ON s0 | 9.41 / 6.69% | +2.72 | 23/10 | .035 | [+0.37, +5.06] | .053 | .074 | .094 |
| OFF−T s0 (reference) | 11.09 / 6.90% | +4.18 | 35/15 | .0066 | [+1.31, +7.06] | .17 | .074 | .25 |

The exclude mode (n = 477) differs by ≤ 0.02pp. For comparison, Table VI (P against the 3-seed means) gives P−T +2.80 and P−OFF −2.87.

**Sizes, from the released packs.** The served P and TM packs are those in `b1b3_packs_b2.json`; `gen_b2.cmd` and `gen_b3.cmd` pass `--packs-file b1b3_packs_b2.json`.

| arm (478) | slots | mean chars | median chars |
|---|---|---|---|
| ON | 11.93 | 5,991 (6,002 over 500) | 6,040 |
| OFF | 12.00 | 6,323 (6,322 over 500) | 6,430 |
| T | 5.15 | 2,799 | 2,778 |
| **TM (served)** | **12.40** | 6,323 | 6,435 |
| **P (served)** | 5.15 | **5,706** | 5,794 |
| TM pre-ruling (b1b3_packs.json; never generated) | 12.90 | 6,323 | |
| P first build (`<unreleased>/b1b3/b1b3_packs_build1.json`; superseded, never generated) | 5.15 | **4,972** | |

**Ratios:**
- P/OFF: 0.902 as a ratio of means (0.901 mean of per-instance ratios). P/T: **2.04** (2.37 mean of ratios). P/ON: 0.95.
- **The caption's 4,972 is wrong; the served P is 5,706.** 4,972 comes from the first build, in which 326 P files were not read. The addendum's size table records that build, and the review's "0.79×" is 4,972/6,322.
- **TM is 12.40 slots, not 12.9.** 12.9 is the pre-ruling TM.
- `b1b3_gates.json` records the same 5,705.5 for P, but also lists TM 12.895 (pre-ruling). README line 130 repeats TM 12.90.

## 6. Memorization E5 (`s6_e5.py`)

Data: Qwen3-Coder-30B local arms, n = 500; Low-M 222, High-M 278. The sign is Low − High; the paper's E3 is High − Low.

| scale / model | estimate | 95% CI | p |
|---|---|---|---|
| **logit GEE, unadjusted** | **ROR 2.32** (log 0.840, SE 0.383) | [1.09, 4.91] | **.028** (reviewer's t8 figure, verified) |
| logit GEE, + difficulty and arm×difficulty | ROR 2.37 | [1.09, 5.12] | .029 |
| logit GEE, OFF−T | ROR 1.96 | [0.94, 4.09] | .074 |
| RD, instance SE | +4.96pp | [−0.5, +10.4] | .076 |
| RD, CR2 by repository (df 3.5) | +4.96pp | [−3.8, +13.8] | .18 |
| RD, CR2, + difficulty | +4.91pp | [−4.2, +14.0] | .20 |

**Why the scales disagree.**

| stratum | ON | OFF | OR |
|---|---|---|---|
| Low-M | 4.1% | 12.6% | 3.42 |
| High-M | 8.6% | 12.2% | 1.47 |

The same OFF level on a lower ON base is a much larger ratio.

**Stratified by gold-file presence in the ON pack** (the localisation-failure check):

| stratum | Low-M: n; Δ (b/c) | High-M: n; Δ (b/c) | interaction |
|---|---|---|---|
| gold file in ON pack (439) | 189; **+10.1** (22/3) | 250; +4.0 (17/7) | RD +6.1 (p .059; CR2 .15); logit ROR 2.29 [1.06, 4.95], p .036 |
| gold file not in ON pack (61) | 33; 0.0 (0/0) | 28; 0.0 (0/0) | not estimable: 0 discordant pairs |

- Low-M packs contain the gold file slightly less often (85.1% vs 89.9%).
- The whole OFF−ON effect sits where ON localised the file, and Low-M's larger effect persists there. So "Low-M = localisation failure" does not produce the pattern through pack contents.

**Stratified by P1 availability** (P1-NA = the issue names a gold basename; 133 of the 134 instances with n_avail < 3):

| stratum | Low-M: n; ON; Δ (b/c) | High-M: n; ON; Δ (b/c) | interaction |
|---|---|---|---|
| P1 tested (366) | 111; 0.9%; +4.5 (6/1) | 255; 7.5%; +3.9 (16/6) | RD **+0.6** (p .85); ROR 3.94 [0.44, 35], p .22 |
| P1 not applicable (134) | 111; 7.2%; **+12.6** (16/2) | 23; 21.7%; 0.0 (1/1) | RD +12.6 (p .083; CR2 .39); ROR 3.18, p .022 |

- Half of Low-M (111 of 222) is Low-M partly *because* P1 cannot be run.
- The Low-M excess comes from those instances, where the issue names the file.
- Where P1 was actually tested, the Low-M and High-M effects are equal (+4.5 vs +3.9), and Low-M ON is at the floor (0.9%).
- This supports the reviewer's capability and P1-NA confound reading. The effect is present in Low-M in both halves (+4.5 and +12.6), but "larger in Low-M" is not attributable to memorisation.

## 7. Replication restated under the new primary (`s7_replication.py`)

**File of record:** `results/b1b3-replication/results_scored.json` (sha256 A008ABB5…4A9B). Each row was recomputed independently from the 13 raw arm-seed reports. Δ, the registered 95% CI and the per-seed b/c match the file **exactly in all 8 contrasts**. The wild p from two independent implementations agree within Monte Carlo error.

**n:** 478 on the T set; 500 for OFF−ON over all instances.

**Pooled resolve rates (mean of 3 seeds):**
- T set: ON 6.21%, T 6.69%, TM 6.83%, OFF 12.34%, P 9.41% (one seed).
- All 500: ON 6.13%, OFF 11.93%.

| contrast | n | Δ | 95% CI (registered) | 90% CI | wild p | wild 95% CI | CR2 p | flip p | pct-cluster 95% | per seed (b/c, McNemar p) |
|---|---|---|---|---|---|---|---|---|---|---|
| **OFF−ON (G)** | 478 | **+6.14** | [+3.63, +8.65] | [+4.04, +8.30] | **.0134** | [+1.59, +8.54] | .035 | .016 | [+2.27, +8.01] | +4.4 (32/11, .0019); +6.9 (42/9, 3e−6); +7.1 (43/9, 2e−6) |
| **OFF−T (depth)** | 478 | **+5.65** | [+3.07, +8.30] | [+3.42, +7.88] | **.0378** | [+0.40, +8.05] | .044 | **.055** | [+1.42, +7.50] | +4.2 (35/15); +6.1 (41/12); +6.7 (41/9) |
| **T−ON (trim)** | 478 | **+0.49** | [−0.91, +1.88] | [−0.63, +1.60] | .218 | [−0.36, +1.69] | .21 | .25 | [−0.12, +1.58] | +0.2 (12/11); +0.8 (10/6); +0.4 (10/8) |
| **TM−T** | 478 | **+0.14** | [−1.05, +1.39] | [−0.91, +1.19] | .746 | [−1.66, +1.19] | .77 | .88 | [−1.42, +0.78] | 0.0 (9/9); 0.0 (9/9); +0.4 (7/5) |
| **OFF−TM** | 478 | **+5.51** | [+2.93, +8.23] | [+3.28, +7.74] | **.0138** | [+1.51, +7.81] | .039 | .016 | [+1.91, +7.39] | +4.2 (34/14); +6.1 (42/13); +6.3 (42/12) |
| **P−OFF** (P 1 seed vs OFF mean of 3) | 478 | **−2.93** | [−5.86, +0.00] | [−5.37, −0.49] | .207 | [−4.98, +0.77] | .14 | .25 | [−4.76, +0.12] | s0: −1.7 (22/30, .33) |
| **P−T** (P 1 seed vs T mean of 3) | 478 | **+2.72** | [+0.42, +5.09] | [+0.77, +4.67] | .146 | [−1.73, +5.12] | .066 | .20 | [−0.88, +4.42] | s0: +2.5 (23/11, .058) |
| OFF−ON, all 500 | 500 | +5.80 | [+3.47, +8.27] | [+3.80, +7.87] | .0167 | [+1.35, +8.10] | .038 | .016 | [+2.03, +7.58] | +3.8 (32/13); +6.6 (42/9); +7.0 (44/9) |

**Verdict and other quantities:**
- **Verdict:** "depth carries the effect". Depth share **92.0%**, trim share 8.0%, and depth + trim = G exactly.
- **Predictions 1–4:** all true, unchanged from the exclude mode.
- **Between-seed SD of OFF−ON:** 1.51pp.
- **Nested subset** (every T chunk among its file's OFF chunks): **n = 358**. OFF−T +6.42, T−ON +0.65, TM−T −0.19, OFF−TM +6.61, P−T +2.14. Exclude mode: n = 357, +6.44 / +0.65 / −0.19.
- **Empty-patch rates:**
  - T set: ON 45.5, OFF 39.9, T **47.1**, TM 43.3, P 44.8%.
  - All 500: ON 45.2, OFF 40.2%. The paper mixes these denominators: ON and OFF over 500, T, TM and P over 478.
- **Mixed logit** (VB, same specification, scored mode, 2,868 rows), arm effect in posterior SDs from zero: OFF−ON +13.2, OFF−T +12.0, OFF−TM +11.3, T−ON +0.9, TM−T −0.0. The exclude-mode file `glmm.json` (2,862 rows) gives the same pattern.

**Exclude (paper now) → scored (new primary):**

| contrast | exclude, n = 477 | scored, n = 478 |
|---|---|---|
| OFF−ON | +6.15 [+3.70, +8.74] w .0135 | +6.14 [+3.63, +8.65] w .0134 |
| OFF−T | +5.66 [+3.00, +8.32] w .0379 | +5.65 [+3.07, +8.30] w .0378 |
| T−ON | +0.49 [−0.91, +1.89] | +0.49 [−0.91, +1.88] |
| TM−T | +0.14 [−1.12, +1.40] w .746 | +0.14 [−1.05, +1.39] w .746 |
| OFF−TM | +5.52 [+2.87, +8.25] w .0136 | +5.51 [+2.93, +8.23] w .0138 |
| P−OFF | −2.87 [−5.80, +0.07] w .238 | −2.93 [−5.86, +0.00] w .207 |
| P−T | +2.80 [+0.49, +5.17] w .131 | +2.72 [+0.42, +5.09] w .146 |
| OFF−ON, all instances | (499) +5.81 [+3.41, +8.28] | (500) +5.80 [+3.47, +8.27] |

The upper-bound mode (Class-P cells scored as resolved) is in `s7_replication.md`.

**Clustered caveat (new, post hoc).** The replication's registered CIs are instance-level. Clustered CIs are wider:
- OFF−ON: wild [+1.6, +8.5], CR2 [+0.8, +11.5].
- The depth term is repository-significant under wild (.038) and CR2 (.044), but **not under the exact sign-flip (.055)**.

---

## Discrepancies with the current main.tex, beyond the summary table

1. **Fig. 1 caption**: "n = 477: ON 6.1%, T 6.6%, OFF 12.3%" should read **n = 478: 6.2 / 6.7 / 12.3** under the new primary.
2. **Table V row 1 and §V-C**: "(477)", "6.1 / 6.6 / 12.3" and the CIs should be replaced by the s7 scored values. **Table VI**:
   - The pooled-rates line should read **ON 6.2, T 6.7** (TM 6.8, P 9.4 and OFF 12.3 are unchanged).
   - P−T wild p is **.15** (not .13) and P−OFF wild p is **.21** (not .24). The TM−T CI is [−1.05, +1.39].
   - TM is **12.4** slots and P is **5,706** characters.
3. **§V-C**: "On the 357 instances" should read **358** (values unchanged at 1 dp). "47.0% T" should read **47.1%**.
4. **Table I** says "one-process ON/OFF/T … 477, 3 seeds"; under the new primary this is 478. Its footnote ("one instance is excluded") needs the scored wording.
5. **§IV and Table II**: the numbers are all verified. The structural description (re-run as P confirmatory, 2-test Holm, "pre-registered reference") conflicts with GPT-LOGGED (a)/(c)/(e) and TB §9 (see §2 above).
6. **§V-E E5**: "not significant on the risk-difference scale" is correct as stated, but should be paired with the logit ROR 2.32, p = .028. The "(p = 0.08)" after difficulty adjustment equals the reanalysis2 MH-stratified RD p (.077).
7. No other number in the scope of these analyses disagrees with main.tex. Table II's wild, CR2 and flip values for five rows, the Table V gpt rows and their trim 95% CIs ([−3.8, +3.8], [−2.3, +5.3]), and the re-run wild CI [+3.2, +11.3] were all re-derived and match.
