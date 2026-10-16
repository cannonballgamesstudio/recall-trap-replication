# Replication package: "The Recall Trap: When Higher File Recall Lowers Issue Resolution"

Anonymized for double-anonymous review (MSR 2027). This package lets a reviewer

1. recompute every reported statistic from the released per-instance data, with no model calls, no GPU and no Docker (about 10 minutes in total);
2. inspect the exact served context packs, model outputs and official grading reports behind every row;
3. audit the pre-registrations, their original commits and their deviation logs;
4. re-run generation and grading end to end.

Author names, organization, hostnames, local paths and archival identifiers have been removed. Internal names were renamed consistently: the retrieval package is `ragfusion`, its query daemon is `retrievald` (environment variables `RETRIEVALD_*`, response header `X-Retrievald-Backend-Version`), the internal agent daemon is `harnessd`, and other internal environment variables use the prefix `HARNESS_`. Local roots are written as placeholders: `<EVAL_ROOT>` (checkouts, indexes, registry), `<HF_HOME>` (Hugging Face cache), `<LLAMA_DIR>` (llama.cpp binaries and GGUF files), `<repo>` (the authors' development repository), `<scratch>` (a temporary directory) and `<home>`. Third-party content is left as it was served or produced. The exception is a small number of spans that matched the anonymity filter by coincidence, which are masked and listed in `data/MASKING.md`.

## Layout

```
README.md                  this file
LICENSE, LICENSE-DATA.md   code: MIT; data and results: CC BY 4.0
MANIFEST.sha256            sha256 of every file in the package
preregistrations/          every design document the paper relies on, as submitted (HEAD)
  PROVENANCE.md            original commit + date (UTC) of each document, and its full commit log
  LOCAL-B1B3-ADDENDUM-PREREG.md, TM-RULING-2026-10-15.md, SPHINX8475-RULING-2026-10-16.md
                           single-retriever three-seed replication: addendum (with its section-12 execution log)
                           and the two deviation rulings
  as-first-committed/      the first committed version, when it differs from HEAD
  TURNCAP-SWEEP-PROTOCOL.md  protocol of the read-budget sweep (written before the runs, never committed; exploratory)
  plans/                   design-committed allocation plan (gpt discovery draw, DeepSeek) + wider-program plans
  hypothesis-registry.md   the program's hypothesis registry with dispositions ("Program history")
code/
  prepare_data.py          one-time setup: gunzip data/**/*.gz, build the flat view work/p5/
  retrieval/               retrieval service (`retrievald`) + fusion backend at the pinned revision (package `ragfusion`); CONFIG.md
  eval/                    single-shot harness (local_dedup_ab.py), agentic harness (swe_bench.py, g_plane_*),
                           read-budget loop harness (local_agentic_ab.py, at the revision that ran the sweep),
                           pack building (prefetch_*.py, fusion_*.py), Arm T construction (build_T.py, run_T_guarded.py),
                           memorization probes (contam_*.py), post-cutoff slice (contam_post_*.py, gold_gate_eval.py,
                           agg_reports.py), SWE-PolyBench tooling (polybench_*.py, build_gold_batches.py), grading commands
    b1b3/                  single-retriever replication: prefetch, pack build + gates, TM rebuild, analysis, GLMM;
                           ops/ = the launch, serving and grading scripts as run
  analysis/
    core/                  inclusion table, paired contrasts, coverage/anchor, funnel, PolyBench verdict (run_all.sh)
    reanalysis/            small-sample clustered inference (wild/CR2/sign-flip), budget sweep, fix locality, MDE (run_all.sh)
    reanalysis2/           T decomposition vs. the logged re-run, TOST, Holm, ITT, LOO, concordance, E5, Branch-A bootstrap (run_all.sh)
    trimmed_breadth/       Arm T analyses on the headline arms + reconstruction of the withdrawn first-pass grading
    turncap/               read-budget sweep recompute (turncap_recompute.py)
    misc/                  Qwen3.6 truncation, anchor classes, Low-M MDE, pack sizes, figure script
    original/              the authors' original analysis and figure scripts (paths anonymized)
data/
  arms.json                every SWE-bench Verified arm: model, retriever, harness, K, packs, predictions, raw, report, paper_ref
  swe-verified/            inputs/, packs/, predictions/, raw_responses/, grading/{summary,per_instance}/, auxiliary/
  b1b3-replication/        single-retriever replication: raw retrieval provenance, packs, gates, build logs, instance sets,
                           predictions and grading reports for ON/OFF/T/TM (3 seeds) and P (1 seed), gold run
  trimmed-breadth/         Arm T and T' packs, predictions, raw responses, grading (both passes), build report
  memorization-branchB/    probe outputs (P1, P2, P3) for both models, P2 grading, M tables, joins
  post-cutoff-branchA/     SWE-rebench post-cutoff instances, packs, predictions, raw responses, gold gate, grading, join
  polybench/               SWE-PolyBench packs, instances, predictions, raw responses, gold-smoke lists, grader results
  turncap-sweep/           read-budget sweep (caps 2/3/5/10/30 x ON/OFF): predictions, per-instance loop metrics,
                           grading reports, and the cap-30 OFF resume logs (stub-row evidence)
  MASKING.md               coincidental filter matches masked inside third-party text
results/
  core/  reanalysis/  reanalysis2/  trimmed-breadth/  b1b3-replication/  memorization-branchB/  post-cutoff-branchA/
  turncap-sweep/  misc/  figures/
```

File-name glossary: `dedupON` = the production default (at most one chunk per file), `dedupOFF` = raw ranking. `gpt56sol`/`gptsol` = gpt-5.6-sol. `logrep` = the pre-registered logged gpt re-run. `dsv4` = DeepSeek-v4-pro. `qwen36` = Qwen3.6-27B. `qwen3coder30b`/`qwen30b` (local GGUF) and `qwen3or` (OpenRouter) = Qwen3-Coder-30B-A3B. `qwen25coder32b`/`local2` = Qwen2.5-Coder-32B. `gptsol_dense`/`cc1` = the dense-retriever control. `bm25` = the BM25 arm. `g2Brand` = random chunk per file. `qs2_k4`/`qs2_k40` = Qwen3.6-27B budget arms. `ssagent500`, `g_dense500`, `g_*` = agentic arms. `trimT_*_T` = Arm T on the headline arms, `*_Tprime` = T' on the 27 subset-gate violators. `b1b3` = the single-retriever replication (`b1b3q30` = Qwen3-Coder-30B-A3B Q5_K_XL GGUF; `_s00`..`_s02` = decoding seed; arms `ON`, `OFF`, `T`, `TM` = token-matched T, `P` = practitioner baseline, called W (widened chunks) in the paper; `b1b3_packs_b2.json` = the packs file with the rebuilt TM). `agentic_qwen3coder30b_or_t{c}` = the read-budget sweep at turn cap c (Qwen3-Coder-30B-A3B through OpenRouter). `contamP*` = memorization probes. `*_post*` = post-cutoff slice. `_rg` = regrade (the consistent grading pair used for analysis). The `paper_ref` field of each arm in `data/arms.json` gives the tables, figures and sections of the paper that use it.

## Quick start (recompute the paper's numbers)

Requirements: Python 3.10+ with `numpy`, `scipy`, `pandas`, `statsmodels`, `matplotlib`. `tiktoken` is optional (token counts in `pack_sizes.py`). Run everything from the package root.

```sh
python code/prepare_data.py              # gunzip + build work/p5 (once)
sh code/analysis/core/run_all.sh         # results/core/        (~1 min)
sh code/analysis/reanalysis/run_all.sh   # results/reanalysis/  (~1 min)
sh code/analysis/reanalysis2/run_all.sh  # results/reanalysis2/ (~7 min)
python code/analysis/trimmed_breadth/analyze_T.py         # Qwen3-Coder-30B Arm T (headline arms)
python code/analysis/trimmed_breadth/analyze_T_gpt.py     # gpt-5.6-sol Arm T
python code/analysis/trimmed_breadth/reconstruct_first_pass.py
for m in exclude scored upper; do python code/eval/b1b3/b1b3_analyze.py --sphinx8475 $m; done   # results/b1b3-replication/ (~1 min)
python code/eval/b1b3/b1b3_analyze.py --compare            # the three sphinx-8475 handlings side by side (primary = scored)
python code/eval/b1b3/b1b3_glmm.py                         # secondary mixed logit -> results/b1b3-replication/glmm.json
python code/analysis/turncap/turncap_recompute.py         # results/turncap-sweep/ (read-budget sweep, ~1 min)
for s in qwen36_truncation anchor_strata mde_lowM pack_sizes; do python code/analysis/misc/$s.py; done
python code/analysis/misc/make_v2_figs.py                 # results/figures/*.pdf
```

We re-ran all of these from a clean copy of this package before release. Every `.md` table in `results/core/`, `results/reanalysis/` and `results/reanalysis2/` was reproduced byte-for-byte. The only differences were in the last floating-point digit of a few `results/reanalysis/*.json` values, which is BLAS/numpy-version noise. The two Arm T analyses and the first-pass reconstruction reproduce the numbers printed in the paper. The four files `results/b1b3-replication/results*.json` are reproduced byte-for-byte; their sha256 prefixes (`55ddd119`, `a008abb5`, `ad1a62aa`, `ec2c12da`) are the ones recorded in section 12 of `LOCAL-B1B3-ADDENDUM-PREREG.md`. `glmm.json` (variational Bayes fit, no verdict depends on it) reproduces to within a relative difference of 3e-5 (all values; JSON outputs elsewhere differ only at floating-point noise, below 1e-5 relative). `results/turncap-sweep/turncap_recompute.md` and `.json` are reproduced byte-for-byte from the released (compressed, masked) data in `data/turncap-sweep/`.

Conventions (as in the paper): Δ = dedup-OFF minus dedup-ON. Empty patches and harness errors count as failures over the full n. Instances never predicted in one arm are excluded pairwise. The primary test is exact McNemar on the raw paired difference. Clustered inference is over the G = 12 repositories: a wild cluster bootstrap-t with Webb weights (B = 9,999, seed 20261014, CI by test inversion), CR2 with Bell–McCaffrey df, and an exact repository sign-flip. The single-retriever replication pools three seeds per instance and reports an instance-paired bootstrap 95% CI (B = 10,000, seed 20261015) with a wild cluster bootstrap p (Webb weights, B = 9,999), as pre-registered in its addendum (section 7).

## Paper element → data → code → result

Table and figure numbers are those of the submitted paper: Table I (study design), II (K = 12 results), III (Qwen3.6-27B budget sweep), IV (SWE-PolyBench), V (read-budget sweep), VI (trimmed-breadth decomposition), VII (token-matched and widened-chunk controls), VIII (anchor transitions), IX (MDE); Fig. 1 (three packs), Fig. 2 (forest plot). The memorization checks have no table; they are reported in the text of Sec. V-D. Labels inside some result files and analysis scripts (`results/reanalysis2/`, `code/analysis/reanalysis2/`) follow the numbering of an earlier draft and were left as generated so that the outputs stay reproducible byte-for-byte: there, "Table V" is the paper's Table VI (trimmed-breadth decomposition), "Table VII" is Table VIII (anchor transitions), and "Table VIII" (memorization) is Sec. V-D. The `paper_ref` fields in `data/arms.json` use the paper's numbering. Data paths are relative to `data/`, code paths to `code/`, pre-registrations to `preregistrations/`.

| paper element | data | pre-registration | code | result file |
|---|---|---|---|---|
| Fig. 1 (three packs; resolve rates in the caption) | `b1b3-replication/` (Qwen3-Coder-30B rates, n = 478); `trimmed-breadth/` + `swe-verified/*gpt56sol_dedup*` (gpt-5.6-sol, n = 473, against its registered reference pair, the discovery draw) | `LOCAL-B1B3-ADDENDUM-PREREG.md`, `TRIMMED-BREADTH-PREREG.md` | `analysis/misc/make_v2_figs.py`; `eval/b1b3/b1b3_analyze.py`; `analysis/trimmed_breadth/analyze_T_gpt.py` | `results/figures/packs_v2.pdf`; rates in `results/b1b3-replication/results_scored.json` (primary; pooled `rate_A`/`rate_B`) and `results/trimmed-breadth/T_gpt56sol_analysis.txt` (gpt-5.6-sol) |
| Table I (study design) | `arms.json`; the per-experiment folders below | `PROVENANCE.md` (class of each arm) | — | — |
| Table II, Qwen3.6-27B K=12 (P) | `swe-verified/{predictions,raw_responses}/*qwen36_k12*`, `grading/summary/local_qwen36_k12_dedup*.json`; packs `local_packs.json` | `QWEN36-PREREG.md` (+Amendment 1); 16k discarded run kept as `*_16k_discarded.jsonl` | core, reanalysis, reanalysis2 | `results/reanalysis/t1_clustered.md` (wild/CR2/flip), `results/reanalysis2/t3_t4_holm_itt.md` (Holm, unrounded), `results/core/paired_contrasts.md` |
| Table II, gpt-5.6-sol logged re-run (P) | `*gptsol_logrep*` (full response text logged) | `GPT-LOGGED-REPLICATION-PREREG.md` | same | same; funnel `results/core/logrep_funnel_result_FINAL_GRADES_rerun.txt` |
| Table II, gpt-5.6-sol discovery draw (D) | `*gpt56sol_dedup*` (responses not logged) | `plans/2026-07-14-e1-e2-allocation.md` | same | same |
| Table II, DeepSeek-v4-pro (D) | `*dsv4*` (`_rg` reports) | `plans/2026-07-14-e1-e2-allocation.md` | same | same; producibility in `results/core/paired_contrasts.md` |
| Table II, dense-retriever control (PP) | `*gptsol_dense*`, packs `dense_packs.json` | `CLEAN-CONTROL-DESIGN.md`, `PREREG-LEDGER.md` | same | same |
| Table II, BM25 (E) | `*gpt56sol_bm25*`, packs `bm25_packs.json` | `BM25-AGNOSTIC-PREREG.md` (Class 2), `as-first-committed/CONTEXT-VAULT-section8.md` | same | `results/reanalysis/t1_clustered.md` (interactions), `results/core/coverage_anchor.md` (gold-line coverage) |
| Table II, Qwen2.5-Coder-32B (E) | `*qwen25coder32b*` | — | core | `results/core/paired_contrasts.md`; MDE `results/reanalysis/t4_mde.md` |
| Fig. 2 (forest) | as Table II | — | `analysis/misc/make_v2_figs.py` (values from t1) | `results/figures/forest_v2.pdf` |
| Sec. I gold-file presence 0.878 / 0.806 | packs + `swe-verified/inputs/gold_patches.json` | — | core (`coverage_anchor.py`) | `results/core/coverage_anchor.md` |
| Sec. IV single-retriever replication: construction, gates (subset 95.6% = 478, T chunk identity 100%), TM and P (= W) rules, sizes | `b1b3-replication/b1b3_prov.json` (raw ranked hits of the four queries per instance), `b1b3_gates.json`, `b1b3_build_log.json` (per-instance TM/P construction), `b1b3_packs.json`, `b1b3_ids_{all,T}.txt` | `LOCAL-B1B3-ADDENDUM-PREREG.md` (sections 2–5, 12) | `eval/b1b3/b1b3_prefetch.py`, `b1b3_build.py` | `b1b3-replication/b1b3_gates.json` |
| Sec. IV TM padding deviation (D-TM) | `b1b3-replication/b1b3_packs_b2.json` (TM rebuilt; ON/OFF/T/P byte-identical to `b1b3_packs.json`), `tm_c_build.json` | `TM-RULING-2026-10-15.md`; addendum section 12 (D-TM) | `eval/b1b3/b1b3_build_tm_c.py` | `b1b3-replication/tm_c_build.json` (`check`: TM/OFF ratio, candidates, ran-out instance) |
| Sec. IV sphinx-8475 harness timeout (Class P; primary: the five cells scored unresolved, n = 478; sensitivities: excluded, n = 477, and scored resolved) | `b1b3-replication/local_b1b3q30_*.json` (`error_ids`), gold run `gold.b1b3_gold_sphinx8475.json` | `SPHINX8475-RULING-2026-10-16.md`; addendum section 12 (D-8475, and D-8475b, which made the ruling's default "scored unresolved" the primary after the results were known; disclosed) | `eval/b1b3/b1b3_analyze.py` (`CLASS_P`, `--sphinx8475`; its help text still labels `exclude` as primary, as run before D-8475b), `eval/b1b3/ops/gold_sphinx8475.sh` | `results/b1b3-replication/results_scored.json` (primary), `results.json` (excluded), `results_upper.json` (scored resolved), `results_compare.json` |
| Sec. IV grading of the headline T arms (withdrawn first pass) | `trimmed-breadth/grading/logs/eval_trimT_*` (first pass + regrade logs), `grading/per_instance/*.tar.gz` | `TRIMMED-BREADTH-PREREG.md` (grading-validity note) | `analysis/trimmed_breadth/reconstruct_first_pass.py` | `results/trimmed-breadth/WITHDRAWN_first-pass_*` (reconstructed reports + the withdrawn Qwen analysis) |
| Sec. V-A Holm, leave-one-repository-out (incl. Qwen3.6-27B without django: +2.2, p = 0.26) | as Table II | — | reanalysis2 (`t3_t4_holm_itt.py`, `t5_loo.py`) | `results/reanalysis2/t3_t4_holm_itt.md`, `results/reanalysis2/t5_loo.md` |
| Sec. V-A Qwen3.6-27B empty (58%) and truncation (28%) rates (Manski bounds in the result files) | `swe-verified/raw_responses/raw_local_qwen36_*` | — | `analysis/misc/qwen36_truncation.py` | `results/misc/qwen36_truncation.txt`, `results/reanalysis2/t10_numeric.md` |
| Sec. V-A "where the gain runs" (A/Q decomposition, test pass given applied) | raw responses of logged arms | — | core (`paired_contrasts.py`, `funnel.py`) | `results/core/paired_contrasts.md`, `results/core/funnel.md` |
| Table III + K trend (Qwen3.6 K=4/12/40; ΔΔ, GEE, ITT and adversarial bound) | `*qwen36_k4*`, `*qwen36_k40*` (`qs2_*` reports), packs `packs_k4.json`, `packs_k40.json` | — (exploratory) | reanalysis (`t2_dose.py`), reanalysis2 | `results/reanalysis/t2_dose.md`, `results/reanalysis2/t3_t4_holm_itt.md` (never-submitted ITT) |
| Sec. V-B Qwen3-Coder-30B K sweep (API) | `*qwen3or_k{4,12,40}*` | — | core | `results/core/paired_contrasts.md` |
| Sec. V-B retriever interactions | packs + reports of the Table II arms | — | reanalysis | `results/reanalysis/t1_clustered.md` |
| Table IV (SWE-PolyBench) | `polybench/` | `GENERALITY-BENCH-PREREG.md` (exclusions frozen before any A/B outcome) | `analysis/core/polybench_verdict.py`, `polybench_clustered_sens.py` | `results/core/GENERALITY-FINAL-VERDICT.txt` (+ `.rerun.txt`), `results/reanalysis2/t9_cluster_boot.md` |
| Sec. V-B fix locality | `swe-verified/inputs/gold_patches.json` + reports | — | reanalysis (`t3_locality.py`) | `results/reanalysis/t3_locality.md` |
| **Table V** (same-model read-budget sweep, exploratory: Qwen3-Coder-30B-A3B in a ReAct loop at turn caps 2/3/5/10/30, n = 500; row 1 = the single-shot pair); Sec. V-B "Read budget"; Sec. IV deviation (ix) (stub rows) | `turncap-sweep/` (`preds_agentic_qwen3coder30b_or_t{c}_dedup{ON,OFF}.jsonl.gz`, per-instance loop metrics `raw_agentic_*.jsonl.gz` (turns, reads, peak_ctx, total_tok), reports `agentic_*.or_t{c}_dedup*.json`, cap-30 OFF resume logs `cap30_off_resume{,2,3}.log`); row 1 from `swe-verified/grading/summary/local_qwen3coder30b_dedup{ON,OFF}.qwen30b_*_rg.json` | `TURNCAP-SWEEP-PROTOCOL.md` (written before the runs, never committed; exploratory) | `eval/local_agentic_ab.py` (harness); `analysis/turncap/turncap_recompute.py` | `results/turncap-sweep/turncap_recompute.md` (Δ, disc, McNemar p, instance CI, wild and sign-flip p, empty rates, conditional Δ, mean turns and peak context, `turns==0` stub rows, harness errors), `.json` |
| Sec. V-B / Sec. VI-A different-model agentic arms (sonnet-5, opus-4-8) | `*ssagent500*`, `*g_dense500*`, `*g_denseON/OFF*`, `*g_bm25ON/OFF*` (+ `*.metrics.jsonl`) | `AGENTIC-BENCH-PREREG-2026-07-15.md` | core | `results/core/paired_contrasts.md`, `results/reanalysis2/t2_tost.md` |
| Sec. V-C pack sizes on the 473 headline instances (5.1 slots / 2,787 chars; token counts) | packs | — | `analysis/misc/pack_sizes.py` | `results/misc/pack_sizes.txt` |
| Sec. II / V-C structural facts (94.6% subset, 88.6% top chunk) | packs | `TRIMMED-BREADTH-PREREG.md` §9 | reanalysis2 (`t6_t7_concordant.py`) | `results/reanalysis2/t6_t7_concordant.md` |
| **Table VI row 1** (single-retriever replication, QC, 3 seeds, n = 478: OFF−ON, OFF−T, T−ON, verdict) | `b1b3-replication/` (`preds_local_b1b3q30_{ON,OFF,T}_s0{0,1,2}.jsonl.gz`, reports `local_b1b3q30_*.json`, packs `b1b3_packs.json.gz`, ids `b1b3_ids_T.txt`) | `LOCAL-B1B3-ADDENDUM-PREREG.md` (sections 7–9; D-8475), `SPHINX8475-RULING-2026-10-16.md` | `eval/b1b3/b1b3_analyze.py` | `results/b1b3-replication/results_scored.json` (`contrasts.OFF-ON`, `OFF-T`, `T-ON`, `verdict`) |
| Table VI rows 2–4 (T on the headline arms), verdict rule, T' sensitivity | `trimmed-breadth/` (+ ON/OFF reference arms in `swe-verified/`) | `TRIMMED-BREADTH-PREREG.md`, `TRIMMED-BREADTH-VIOLATORS.txt` (Deviation 1) | `eval/build_T.py`, `eval/run_T_guarded.py`, `analysis/trimmed_breadth/analyze_T*.py` | `results/trimmed-breadth/T_analysis.txt`, `T_gpt56sol_analysis.txt`; flip/wild p in `results/reanalysis2/t1_decomp.md` |
| **Table VII** (TM−T, OFF−TM, W−T, W−OFF; W = arm `P` in the files; pooled rates; per-seed Δ; sizes) | `b1b3-replication/` (`*_TM_s0{0,1,2}*`, `*_P_s00*`, packs `b1b3_packs_b2.json.gz`) | `LOCAL-B1B3-ADDENDUM-PREREG.md` (TM, P; predictions 3–4), `TM-RULING-2026-10-15.md` | `eval/b1b3/b1b3_analyze.py` | `results/b1b3-replication/results_scored.json` (`contrasts.TM-T`, `OFF-TM`, `P-T`, `P-OFF`); slots/characters per arm from `data/b1b3-replication/b1b3_packs_b2.json.gz` on the 478 ids of `b1b3_ids_T.txt` (see below) |
| Sec. V-C replication: per-seed Δ and between-seed SD, funnel (empty rates), robustness to sphinx-8475, mixed logit, nested subset (358) | `b1b3-replication/` | addendum sections 7.2, 7.3, D-TM (nested subset), D-8475, D-8475b | `eval/b1b3/b1b3_analyze.py`, `b1b3_glmm.py` | `results/b1b3-replication/results_scored.json` (`per_seed`, `funnel`, `nested_subset`), `results_compare.json` (all three handlings), `glmm.json` (fitted on the n = 477 exclusion set, as committed before it was run) |
| Sec. V-C headline-arm concordance (260 / 213 instances) | packs | `TRIMMED-BREADTH-PREREG.md` §9 | reanalysis2 (`t6_t7_concordant.py`) | `results/reanalysis2/t6_t7_concordant.md` |
| Sec. V-C random chunk per file | packs `packfile_g2_B_*`, `*g2Brand*` | `G2-RANDOM-CHUNK-PREREG.md` (Class 2) | core | `results/core/paired_contrasts.md` |
| Table VIII (anchor transitions) | packs + gold patches | — | `analysis/misc/anchor_strata.py` | `results/misc/anchor_strata.txt`, `results/core/coverage_per_instance.csv` (per-instance coverage labels) |
| Sec. V-D free checks (verbatim reproduction, PolyBench B→C share) | predictions, gold patches, PolyBench packs | — | reanalysis2 (`t10_numeric.py`, `t9_cluster_boot.py`) | `results/reanalysis2/t10_numeric.md`, `t9_cluster_boot.md` |
| Sec. V-D Branch B (gpt-5.6-sol; E1–E4, S1, single-probe strata) | `memorization-branchB/` (`raw_P{1,2,3}_gpt56sol.jsonl`, `preds_P2_*`, `contamP2_*` report, `M_table_gpt56sol.json`) | `CONTAMINATION-PREREG.md`, `CONTAMINATION-P1-FILTER.txt` | `eval/contam_prep.py`, `contam_probe.py`, `contam_score.py` (m-table, join), `contam_common.py` | `results/memorization-branchB/join_gpt_gpt56sol.json`, `results/reanalysis2/t11_strata.md`; MDE `results/misc/mde_lowM.txt` |
| Sec. V-D E5 (Qwen3-Coder-30B; depth/trim by stratum, proxy-M K sweep) | `*_qwen3coder30b_local*`, `M_table_qwen3coder30b_local.json` | same | same | `results/memorization-branchB/join_qwen3coder_qwen3coder30b_local.json`, `results/reanalysis2/t8_e5_difficulty.md`, `t11_strata.md` |
| Sec. V-D Branch A (A1–A6) | `post-cutoff-branchA/` | `CONTAMINATION-PREREG.md` (Branch A, §E log) | `eval/contam_post_*.py`, `gold_gate_eval.py`, `agg_reports.py`, `branchA_usage_probe.py` | `results/post-cutoff-branchA/join_post.json`, `results/reanalysis2/t9_cluster_boot.md` |
| Table IX (MDE) | reports | — | reanalysis (`t4_mde.py`), `misc/mde_lowM.py` (T−ON rows) | `results/reanalysis/t4_mde.md`, `results/misc/mde_lowM.txt` |
| Sec. IV harness errors (counted as failures; deviation iii regrading) | all reports | — | reanalysis2 (`t0_audit.py`) | `results/reanalysis2/t0_audit.md` |
| Sec. VI-A hypothesis registry, program history | — | `hypothesis-registry.md`, `PREREG-LEDGER.md`, `preregistration-records.md`, `reasoning-model-incompatibility-log.md` (GLM-5.2, Kimi) | — | — |

The per-instance inclusion table promised in the paper is `results/core/inclusion_table.csv`. It has one row per (arm, side, instance), with a mutually exclusive status (resolved, unresolved, empty, harness_error, never_predicted) and the exact input files. Per-arm counts are in `results/core/inclusion_summary.csv`. For the single-retriever replication the per-arm-seed funnel (submitted, empty, graded, Class-P harness timeout, resolved) is in `results/b1b3-replication/results_scored.json` (`funnel`), and the per-instance outcomes are the `resolved_ids`, `unresolved_ids`, `empty_patch_ids` and `error_ids` of each `data/b1b3-replication/local_b1b3q30_*.json` report. The served-pack dataset is in `data/*/packs/`, `data/post-cutoff-branchA/post_packs.json` and `data/b1b3-replication/b1b3_packs*.json.gz`. Gold-line coverage and anchor labels per instance are in `results/core/coverage_per_instance.csv`, and are recomputed by `analysis/misc/anchor_strata.py`.

Pack sizes of the replication as printed in Table VII (mean slots / rendered characters over the 478 instances of `b1b3_ids_T.txt`, computed from `b1b3_packs_b2.json.gz`, the packs that were served): ON 11.93 / 5,991, OFF 12.00 / 6,323, T 5.15 / 2,799, TM 12.40 / 6,323 and P (= W) 5.15 / 5,706 (TM/OFF character ratio 1.000, P/OFF 0.90). `b1b3_gates.json` (`sizes`) records the first build: ON and OFF over all 500 instances (11.93 / 6,002 and 12.00 / 6,322) and the first, superseded TM (12.90 / 6,323); the rebuilt TM pads T with 7.25 chunks per instance on average (`tm_c_build.json`).

## Pre-registrations and their original commits

The paper does not print commit identifiers, because of double-anonymous review. The original commits of the design documents are listed below; `preregistrations/PROVENANCE.md` has the full per-document commit logs. Identifiers refer to the authors' private repository and can be verified on de-anonymization. Times are UTC, converted from the commit timestamps.

| document | governs | original commit | first data |
|---|---|---|---|
| `TRIMMED-BREADTH-PREREG.md` | Arm T on the headline arms (RQ3) | `14ed196`, 2026-10-14 04:06 (Deviation 1 + violators list: `c201ff2`, 04:16) | T generation started after `c201ff2` |
| `CONTAMINATION-PREREG.md` (+ `CONTAMINATION-P1-FILTER.txt`) | Branch B, E5, Branch A | `e9eede2`, 2026-10-14 13:33 | probes after `e9eede2`; joins after the M-table commits `e2890d4` (gpt) and `657be52` (Qwen3-Coder) |
| `LOCAL-B1B3-ADDENDUM-PREREG.md` | single-retriever replication: ON/OFF/T, TM, P | `f600ac8`, 2026-10-15 20:00 (gates + pack hash `33aa630`, 23:40; D-TM `ee7cb20`, 23:48; D-8475 `eeadc36`, 2026-10-16 18:35; D-8475b `9cd8199`, 2026-10-17 02:31, after the results, disclosed) | packs built after `f600ac8` (the prefetch script refuses to run before it); TM generated after `89d1aee`/`ee7cb20`; analysis run after `eeadc36` |
| `TM-RULING-2026-10-15.md` | TM padding rule (option c) | `89d1aee`, 2026-10-15 23:47 | before any TM generation |
| `SPHINX8475-RULING-2026-10-16.md` | Class-P harness timeout (sphinx-8475) | `82981da`, 2026-10-16 16:57 | before any replication outcome was read |
| `QWEN36-PREREG.md` (+ Amendment 1) | Qwen3.6-27B confirmatory arm | `adc864d`, 2026-07-17 21:24 | after commit |
| `GPT-LOGGED-REPLICATION-PREREG.md` | gpt logged re-run (confirmatory) | `c35850a`, 2026-08-09 03:47 | after commit |
| `GENERALITY-BENCH-PREREG.md` | SWE-PolyBench | `492c432`, 2026-08-06 17:36 (exclusions frozen `b9e36b0` and `e3e1ef0`) | after `b9e36b0` / `e3e1ef0` |
| `AGENTIC-BENCH-PREREG-2026-07-15.md` | agentic arms | `211261a`, 2026-07-16 05:14 | after commit |
| `plans/2026-07-14-e1-e2-allocation.md` | gpt discovery draw, DeepSeek (design-committed) | `1eaab36`, 2026-07-14 16:56 | same day; ordering rests on run logs |
| `CLEAN-CONTROL-DESIGN.md` | dense control design audit | `470a1c7`, 2026-07-16 01:07 | — |
| `G2-RANDOM-CHUNK-PREREG.md`, `BM25-AGNOSTIC-PREREG.md`, `PREREG-LEDGER.md` | random-chunk control, BM25 TOST (Class 2: no pre-data commit) | `e188957`, 2026-08-08 20:24 | before commit (hence Class 2) |
| `TURNCAP-SWEEP-PROTOCOL.md` | read-budget sweep (Table V; exploratory) | never committed (written 2026-07-16 before the runs; named `TURNCAP-SWEEP-PREREG.md` in the authors' repository) | 2026-07-16 to 07-17; the harness revision that ran it is `3baddcc` (2026-07-16 22:02) |

Times written inside the pre-registration documents themselves are as the authors wrote them (local time, marked EDT where stated).

## Hashes of record

These are the sha256 values committed in the pre-registration logs before the corresponding joins or analyses, recomputed on the released files.

| file | committed sha256 (prefix) | released file |
|---|---|---|
| `data/memorization-branchB/M_table_gpt56sol.json` | `b849fdf1` | identical |
| `data/memorization-branchB/M_table_qwen3coder30b_local.json` | `49dfe773` | identical |
| `data/post-cutoff-branchA/manip_checks.json` (= `manip_checks_gold105.json`) | `a4f1ee9a` | identical |
| `data/post-cutoff-branchA/manip_checks_all108.json` | `0150a551` | identical |
| `data/post-cutoff-branchA/gold_pass_ids_post.txt` | `b22ac55c` | identical |
| `data/post-cutoff-branchA/join_post.json` | `9dee3565` | identical (also in results/) |
| `data/trimmed-breadth/packs/packfile_T_*.json` | `3db69da9` | identical |
| `data/trimmed-breadth/packs/packfile_Tprime_*.json` | `57d9c2b9` | identical |
| `data/post-cutoff-branchA/post_packs.json` | `84a6b050` | 6 coincidental filter matches masked; original hash in `data/MASKING.md` |
| `data/b1b3-replication/b1b3_packs.json` | `80382193` | 9 coincidental filter matches masked (an e-mail domain in third-party code); original hash in `data/MASKING.md` |
| `data/b1b3-replication/b1b3_packs_b2.json` | `7bc29262` | same 9 spans masked; original hash in `data/MASKING.md` |
| `results/b1b3-replication/results.json`, `results_scored.json`, `results_upper.json`, `results_compare.json` | `55ddd119`, `a008abb5`, `ad1a62aa`, `ec2c12da` | identical, and reproduced byte-for-byte from the released data |
| retrieval code | revision `4fab615` (2026-07-14 22:47 UTC) | `code/retrieval/` |

## Re-running generation and grading

Docker images, repository checkouts and indexes are not included. They are large and rebuild from the inputs. The served packs are included, so generation can be re-run without rebuilding any index.

1. **Environment.** Python 3.12. The official SWE-bench harness (`pip install swebench`, run on Linux/WSL2 with Docker) grades every Verified arm: `--dataset_name princeton-nlp/SWE-bench_Verified --cache_level instance` with `--max_workers 4` (API arms) or `6`–`8` (local arms) and `--timeout 1800`. The exact commands are in `data/trimmed-breadth/grading/commands/`, `data/memorization-branchB/local_run/grade_p2.sh`, `code/eval/grading/` and `code/eval/b1b3/ops/`. Pull images authenticated: anonymous registry pulls hit the rate limit that invalidated the first Arm T grading. Branch A uses the same harness with `--dataset_name nebius/SWE-rebench-leaderboard --split test --namespace swerebench` (`code/eval/grading/grade_one_post.sh`, gold gate `run_gold_post.sh`). SWE-PolyBench uses its unmodified `run_evaluation.py`.
2. **Models.** API models go through OpenRouter (`OPENROUTER_API_KEY`): gpt-5.6-sol and Qwen3-Coder-30B-A3B (budget sweep) at temperature 0.2 and `max_tokens=6000`; DeepSeek-v4-pro at 16k tokens with a 2k reasoning cap. Local models are served by llama.cpp `llama-server` on an OpenAI-compatible endpoint: Qwen3.6-27B (reasoning on, 32k), Qwen3-Coder-30B-A3B GGUF (6000 tokens; also the E5 probe stack and the single-retriever replication, Q5_K_XL, `code/eval/b1b3/ops/serve_qwen.cmd`, server properties in `props_8090_b3.json`) and Qwen2.5-Coder-32B. The embedder for the retrieval index is Qwen3-Embedding-8B Q8_0 GGUF, served by llama.cpp in embedding mode. `code/retrieval/CONFIG.md` gives the full embedder identity, fusion weights and chunker policy.
3. **Single-shot generation** (per arm and side). Example for the logged gpt re-run:
   ```sh
   LOG_RESPONSE_TEXT=1 python code/eval/local_dedup_ab.py --arm dedupON --ids all \
       --root work/p5 --instances-file instances_verified.json --packs-file local_packs.json \
       --endpoint https://openrouter.ai/api/v1 --api-model openai/gpt-5.6-sol \
       --api-key-env OPENROUTER_API_KEY --model-tag gptsol_logrep --concurrency 6 --max-tokens 6000
   ```
   Repeat with `--arm dedupOFF`. Arm T uses `--packs-file packfile_T_gpt56sol.json` (key `T`), driven by `code/eval/run_T_guarded.py`. The other arms' pack files and decoding settings are in `data/arms.json` and the pre-registrations. `local_dedup_ab.py` applies the model's SEARCH/REPLACE blocks to a pristine checkout at `base_commit` under `--root` and captures `git diff` as the prediction.
4. **Arm T construction (headline arms).** `python code/eval/build_T.py` builds T and T' from `local_packs.json` and the violators list, with the byte-identity and round-trip checks of the pre-registration's §5 (`data/trimmed-breadth/build/T_build_report.json`).
5. **Single-retriever replication.** `code/eval/b1b3/ops/run_retrieval.cmd` starts the embedder and one `retrievald` process from the pinned revision and runs `b1b3_prefetch.py`, which stores the four ranked queries per instance (dedup on/off at limits 12 and 48) in `b1b3_prov.json`. `b1b3_build.py` builds ON/OFF/T/TM/P from that file and runs the gates (`b1b3_gates.json`); `b1b3_build_tm_c.py` rebuilds TM under the ruling (`b1b3_packs_b2.json`). Generation: `gen_b1.cmd` (ON, OFF, T), `gen_b2.cmd` (TM) and `gen_b3.cmd` (P), each `local_dedup_ab.py --n-samples 3 --per-sample-seed --temperature 0.2 --max-tokens 6000` (P: `--n-samples 1`). Grading: `grade_b1b3.sh` (retry passes until no harness errors; persistent errors are classified, never scored). `b1b3_waitup.py` and `b1b3_prefetch.py` keep their execution guards (pinned worktree at `4fab615`, addendum committed), which refer to the authors' repository; remove them to re-run elsewhere.
6. **Memorization probes.** `contam_prep.py p1-filter` and `contam_prep.py p3-inputs` build the probe inputs. `contam_probe.py run --probe {P1,P2,P3} --tier N` runs the probes (`--tag qwen3coder30b_local --endpoint ...` for the local model). P2 predictions are graded with the Verified harness. `contam_score.py m-table --tag ... --p2-report ...` writes the M table, which is hashed and committed before `contam_score.py join --family {gpt,qwen3coder} --tag ...`.
7. **Post-cutoff slice.** `contam_post_manifest.py` (instances created on or after 2026-02-16), then `contam_post_clone.py`, `contam_post_index.py` and `contam_post_prefetch.py` (packs from the pinned retrieval revision), then `contam_post_analyze.py checks` (outcome-blind manipulation checks), generation with `local_dedup_ab.py`, the gold gate (`gold_gate_eval.py`), grading (`agg_reports.py` rebuilds a run report from per-instance reports), and finally `contam_post_analyze.py join`.
8. **Agentic arms.** `code/eval/swe_bench.py` in pack-file mode (see `p5_run_gplane.py`, `run_dense500.py`), with Read/Edit/Write and no search tools, at most 10 turns.
9. **Read-budget sweep.** `code/eval/local_agentic_ab.py` (the revision that ran the sweep) is a ReAct loop over the same fixed 12-slot packs (`local_packs.json`): the model may emit `READ: path[:a-b]` lines, then SEARCH/REPLACE blocks; `--max-turns` is the cap and the only setting besides `--arm` that varies. Decoding is fixed in the harness (temperature 0.2, `max_tokens=2000` per turn), and it reads instances, packs and checkouts under `work/p5`. Per cell (the protocol's canonical command): `python code/eval/local_agentic_ab.py --arm dedupOFF --max-turns 3 --ids all --endpoint https://openrouter.ai/api/v1 --api-model qwen/qwen3-coder-30b-a3b-instruct --api-key-env OPENROUTER_API_KEY --model-tag qwen3coder30b_or --concurrency 3`, for caps 2, 3, 5, 10, 30 and both arms; grade with the Verified harness as above. Some OFF cells first wrote `turns=0` stub rows when a request failed (credit exhaustion or a transient 429); resume skipped them, and a first grading scored them as failures. They were regenerated and regraded (`cap30_off_resume2.log` shows 49 such rows, `cap30_off_resume3.log` the clean rerun), and every released `raw_agentic_*` file has 0 `turns==0` rows. The cap-30 OFF files hold 504 rows for 500 instances (4 duplicates; the last row wins in the metrics and the grading report lists each instance once). `raw_agentic_qwen3coder30b_or_t30_dedupOFF.jsonl.tmp` is a stray temporary file kept for provenance.

The scripts keep the defaults of the authors' directory layout as placeholders (`<EVAL_ROOT>`, `<HF_HOME>`, `<LLAMA_DIR>`). Pass `--root` and the file names explicitly, as above.

## Not included, and why

* Docker images, repository clones and checkouts, retrieval indexes and embedding caches: large, and rebuildable from the inputs.
* Per-instance harness logs other than `report.json` (test output, run logs), and full agentic transcripts. The agentic arms ship `*.metrics.jsonl` (turns and tool counts) and their predictions.
* The raw model responses of the single-retriever replication (logged, about 34 MB). Its predictions, grading reports and served packs are included.
* The SWE-rebench leaderboard parquet (third-party dataset). `instances_post.json` holds every field used.
* Raw responses for runs that predate response logging: the gpt discovery draw, Qwen2.5-Coder-32B, GLM-5.2 and Kimi. The logged gpt re-run supplies the gpt funnel.
* Studies of the same program that the paper does not report (a best-of-N fan-out pilot and a gate-isolation study). Their design documents and data are available on request. The read-budget (turn-cap) sweep, which the paper reports, is included.
* Unarchived one-off snippets: the BM25 pack builder (the BM25 packs are released as served).

## Licence

Code: MIT (`LICENSE`). Data and results produced by the authors: CC BY 4.0 (`LICENSE-DATA.md`). Third-party benchmark material keeps its original licence.
