# Pre-registration: Trimmed-breadth arm (T) and oracle-select bound (O)

Status: PRE-REGISTRATION. Written 2026-10-14, before any pack is built or any generation is run for
these arms. Commit this file and record the commit hash before the first generation call. Do not edit
the arms, estimands, predictions, or interpretation rules after that point. Put deviations in the dated
log in §9.

Design authority: methodology review of 2026-10-13, which followed four blind MSR-style reviews and a
forensic re-check of draft-v5.

---

## 1. Question

The headline contrast (dedup-ON vs dedup-OFF, fixed 12-slot pack, single-shot, no tools) bundles two
changes into one flag:

- **file trimming:** OFF serves fewer files, about 5 instead of 12.
- **within-file depth:** OFF serves several chunks per kept file instead of one.

The paper cannot currently say which of the two carries the effect. Arm T separates them exactly, on
the same instances.

## 2. Structural fact the design relies on (must be verified, §5)

Dedup-ON post-filters the ranking to one chunk per file before the top-12 cut, so the ON pack is the
top-12 files by best chunk. Every file in the OFF pack has at least one chunk in the raw top-12, so it
also ranks in the top-12 by best chunk. Hence **files(OFF) ⊆ files(ON)** by construction, apart from
ties and short packs, and each OFF file's ON chunk is that file's argmax chunk.

## 3. Arms

All arms use the same renderer, prompt template, edit format (SEARCH/REPLACE), and grading.

- **ON** (existing): 12 files × 1 argmax chunk.
- **OFF** (existing): the raw top-12 chunks, about 5 files with several chunks each.
- **T (new) = trimmed breadth.** The OFF pack's file set, in OFF rank order. Each file gets exactly one
  chunk: the chunk dedup-ON served for that file. It must be byte-identical to the ON pack's chunk for
  that file (assert by (file, start line) and text). No filler slots, so T has about 5 slots and about
  600 tokens.
- **O (new, nice-to-have, local only) = oracle-select bound.** ON's 12 files, one chunk each. For the
  gold file, the chunk is the candidate with maximal overlap with the gold-patch lines; all other files
  keep their ON chunk. This is gold-dependent, so it is labelled an *oracle bound*, never a policy.

Decomposition, exact on the same paired instances:

    (OFF − ON) = (OFF − T) + (T − ON) = Δ_depth-at-fixed-files + Δ_file-trim

## 4. Predictions and interpretation rules (fixed now; both outcomes are reportable)

- **Depth account:** Δ_depth (OFF − T) carries most of the OFF − ON gap; T ≤ ON or T ≈ ON. T is the
  smallest pack of the three, so the token confound runs *against* the depth account. T ≤ ON would
  therefore be strong evidence for depth.
- **Trim / less-is-more account:** Δ_trim (T − ON) ≈ OFF − ON, and Δ_depth ≈ 0 (T ≈ OFF).
- **Interpretation rule.** Let G = OFF − ON on the same instances. If the Δ_depth point estimate is
  ≥ 60% of G and OFF − T is significant (McNemar, α = 0.05), report "depth carries the effect". If the
  Δ_trim point estimate is ≥ 60% of G and T − ON is significant, report "file trimming carries the
  effect": the paper then reframes the mechanism as "fewer files, not deeper files", and the
  recommendation becomes "do not pad to k files". Otherwise report "both components contribute; the
  partition is not resolved at this n". No outcome is described as a refutation.
- **O (if run):** if O < OFF (point estimate, with its McNemar p reported), then one-chunk-per-file
  selection, even with oracle choice, does not reach multi-chunk depth. If O ≈ OFF or higher, then
  selection can account for the gap and the depth account weakens. Reported as a bound.

## 5. Construction checks (abort if they fail)

1. Subset property: report the fraction of instances with files(OFF) ⊆ files(ON). Expected about
   100%. Instances that violate it are excluded from T and listed. If fewer than 95% satisfy it, stop
   and log a deviation.
2. Chunk identity: for every T slot, its chunk equals the ON chunk for that file. 100% required.
3. Report T's slot count and token count against ON and OFF.

## 6. Models and settings

- **Primary (paid, requires owner approval of spend before launch): gpt-5.6-sol**, single-shot, n = 500,
  on the headline fusion packs. Same provider slug, temperature 0.2, and max_tokens 6000 as the headline
  arms. Raw responses are logged.
- **Secondary (free, run first as the pipeline smoke test): Qwen3-Coder-30B-A3B, local**, same
  settings as that model's existing reference ON/OFF arms (recorded in their run logs). n = 500. Arm O
  runs on this model only.
- The reference ON and OFF arms for each model are the existing graded runs. No regeneration.

## 7. Analysis

- **Primary estimand:** raw resolve difference on pairwise-attempted instances (never-submitted pairs
  excluded, per §4.6 of the paper). Paired exact McNemar for OFF − T and T − ON, with b/c reported.
- **Uncertainty:** wild cluster bootstrap by repository (Webb 6-point weights, G = 12) and CR2 SEs.
  Instance-paired SE for the decomposition terms.
- **Secondary:** both-non-empty conditional; parse → apply → test funnel from raw logs; empty and
  fin=length rates per arm.
- **Wording:** "refute" is not used anywhere.

## 8. Threats

- T changes pack size (fewer slots and tokens), which biases toward the trim account. This is disclosed
  and runs against the depth account.
- T orders files by OFF rank; ON orders by best-chunk rank. Within T, the order follows the OFF pack
  exactly.
- Single seed. Decoding is stochastic at temperature 0.2. The headline has two draws (+7.6 and +5.4)
  for reference on run-to-run variance.

## 9. Deviations log (append-only, dated)

**2026-10-14 (D1): §5.1 construction check FAILED. Execution stopped before any generation.**
Built Arm T from `work/p5\local_packs.json`. This is the served pack file for
both reference pairs: gpt-5.6-sol `local_gpt56sol_dedup{ON,OFF}` (196/234) and Qwen3-Coder-30B
`qwen30b_{ON,OFF}_rg` (33/62). Both ran through `local_dedup_ab.py` with the default `--packs-file`.
The parser round-trips all 1000 source packs byte-exactly. Slot counts match `n_hits` and file sets
match `files`.

- **Subset property: 473/500 = 94.6%, below the 95% threshold.** 27 instances have at least one
  OFF file outside ON's 12 files (44 such files in total). Repositories: django 14, sympy 4,
  astropy 2, pylint 2, scikit-learn 2, matplotlib 1, xarray 1, sphinx 1. None of the 17 short ON
  packs (n_hits < 12) is a violator. In 1 of the 27, the missing file is a gold file. Violators:
  astropy-13236, astropy-13453, django-10973, -11555, -11740, -12125, -12262, -12273, -13212,
  -13279, -14404, -14580, -14855, -15037, -15104, -17029, matplotlib-23314, xarray-4966,
  pylint-6386, pylint-7080, sklearn-14629, sklearn-25973, sphinx-9711, sympy-15875, -20801, -21379,
  -22456.
- **Chunk identity (§5.2), on the 473 satisfying instances: 2431/2431 = 100%.**
- **Slot and size (§5.3), means:** ON 11.93 slots / 6002 pack chars; OFF 12.00 / 6318;
  T 5.14 / 2787.
- **Related diagnostic (the §2 structural claim):** for T's files, the ON chunk equals the first OFF
  chunk of that file in 2153/2431 = 88.6% of files. It appears anywhere among that file's OFF
  chunks in 2294/2431 = 94.4%. So the claim that each OFF file's ON chunk is that file's argmax
  chunk does not hold exactly. The likely cause is the one G2 recorded in its D2: ON and OFF packs
  were served by two separate daemons (:8083 dedup-ON, :8084 dedup-OFF), and the two rank chunks
  within a file differently.
- **Outcome exposure of the 27 violators in the reference arms:** Qwen ON 0, OFF 1; gpt ON 11,
  OFF 12.
- **Action taken:** stopped, per §5. Pack files were not written and nothing was generated or
  graded, on either model. Arm O was not built. How to proceed is left to the design authority.


**Deviation 1: decision, 2026-10-14, pre-generation. Nothing generated; $0 spent.**
- **Gate outcome.** The §5.1 construction gate failed. files(OFF) ⊆ files(ON) holds on 473/500
  instances (94.6%), two instances below the pre-registered 95% threshold. Chunk identity holds on
  2431/2431 served chunks (100%) across the 473 passing instances. The gate is recorded as failed and is
  not relaxed.
- **Cause.** Diagnosed from served packs only; no Arm-T outcome exists. The dedup-ON and dedup-OFF
  reference packs were served by two daemon instances (:8083 and :8084) that order chunks within a file
  differently. The ON chunk is the first OFF chunk for its file in 88.6% of files, and appears among that
  file's OFF chunks in 94.4%. This is the ranking nondeterminism recorded as G2 deviation D2. The §2
  statement that files(OFF) ⊆ files(ON) "by construction" is therefore approximate. The violation is a
  property of the serving fleet, not of the instances. The paper's problem-setting section will disclose
  this approximation.
- **Violators.** 27 instances: django 14, sympy 4, and 9 across six other repositories. In one, the
  missing file is the gold file. None of the 17 short ON packs is a violator. The list is in
  `TRIMMED-BREADTH-VIOLATORS.txt`, committed with this entry. Reference-arm outcomes on the 27 were
  visible when this decision was made, and are disclosed here: gpt-5.6-sol ON 11 / OFF 12;
  Qwen3-Coder-30B ON 0 / OFF 1. Excluding the 27 changes the gpt reference contrast from 196/234 of 500
  (+7.6pp) to 185/222 of 473 (+7.8pp).
- **Decision.** Proceed under the pre-registered exclusion rule on the 473 passing instances.
  Rationale:
  - Redefining T, either as OFF∩ON file sets or with OFF-served chunks, would break the ON-chunk
    identity that T−ON is identified on.
  - Rebuilding all three arms from one daemon would regenerate the reference arms and sever
    comparability with the published contrasts.
  - This decision does not condition on any Arm-T outcome. It does condition on the reference outcomes
    on the 27 being visible, which is disclosed above.
- **Analysis consequences (binding).**
  - (a) The exact decomposition (OFF−ON) = (OFF−T) + (T−ON) is computed on the 473, with the reference
    ON/OFF contrast restricted to the same instances.
  - (b) The full n=500 reference contrast is reported alongside.
  - (c) Sensitivity arm T′ is built for the 27 violators as files(OFF) ∩ files(ON), with ON chunks. A
    pooled n=500 analysis is reported as secondary, labelled as using a non-identical construction on
    27 instances. The gold-file violator is flagged.
  - (d) Worst-case bounds on the 27 are reported, imputing T = ON outcome and T = OFF outcome.
  - (e) All other pre-registered estimands, contrasts, predictions, and interpretation rules are
    unchanged.
- **Arm O (oracle-select).** Not built. Per-file candidate pools were not persisted, and a live
  re-query reproduces the graded rank-1 chunk in only 82.9% of files (G2). Deferred to the follow-up
  Registered Report. No Arm-O data exist, so this is not an outcome-based decision.
- **Cost gate.** A 10-call usage probe comes before any paid approval. Generation on gpt-5.6-sol
  proceeds only if the projected cost for 500 calls (473 T + 27 T′) is at or below $25 and the owner
  approves. Otherwise the run halts and the projection is reported before any further spend.

**Post-hoc clarification, 2026-10-14 (after both T results).** §4 ("the token confound runs *against* the depth account") and the first bullet of §8 ("biases toward the trim account") state the direction of the pack-size confound backwards. T is the smallest pack, so a pure size account also predicts that T resolves lowest. The confound therefore pushes both decomposition terms toward the depth verdict, not against it. No estimand, contrast, interpretation rule, or verdict in this pre-registration depends on those sentences. The decomposition identifies depth against file trimming at a fixed file set. It does not identify depth against token count; a token-matched T is the remaining control. This clarification is disclosed in the paper.

**2026-10-14 22:10 EDT: gpt-5.6-sol Arm T/T′ execution log (executor; operational, no protocol change).**
- **Usage probe.** 10 calls on T packs, chosen outcome-blind as the lowest sha256(`20261014:Tusage:{iid}`)
  over the 500. Model tag `gpt56sol_Tusage10`; these responses are discarded from analysis. Mean
  $0.0243/call, so the projection for 500 calls is $12.16, under the $25 cap. Owner approval was given
  2026-10-14 ("minimum" set).
- **Generation.** `local_dedup_ab.py` was run through a scratchpad wrapper (`run_T_guarded.py`).
  - It is byte-identical in SYS, user turn, temperature 0.2, max_tokens 6000 and the parse rule.
  - It adds OpenRouter `usage:{include:true}`. This is accounting only, with no effect on decoding.
  - It logs usage, served model and provider.
  - It enforces a cumulative-cost guard at $25. The guard never fired.
  - Settings: `openai/gpt-5.6-sol` via OpenRouter, concurrency 8, `LOG_RESPONSE_TEXT=1`.
  - T: 473/473. T′: 27/27. 0 transport failures. All `finish_reason=stop`. All served by provider
    OpenAI.
  - Spend: T $8.893, T′ $0.563, probe $0.243; **total $9.699**.
  - Pack sha256: T `3db69da9…1d72`, T′ `57d9c2b9…f63e`.
- **Grading.** Same command as the headline gpt grading: `run_evaluation`, SWE-bench_Verified,
  `--max_workers 4 --cache_level instance`. It was started 19:45, after all three Branch-A index workers
  logged COMPLETE.
  - T′ (`trimT_gpt56sol_Tprime`): 0 harness errors.
  - T (`trimT_gpt56sol_T`): **174 of 395 non-empty instances are harness errors.** The cause is a Docker
    Hub `429 Too Many Requests` on pulls of uncached `swebench/sweb.eval.*` images. These are not model
    outcomes. The T report is therefore **not analysable as-is**. Those 174 must be regraded with the
    same run_id; the harness skips completed instances. No T verdict has been computed from this report.

**Grading-validity note, 2026-10-14 ~22:45.** Both T arms were graded with large numbers of harness errors. The errors were Docker Hub "429 Too Many Requests" failures pulling uncached evaluation images, not model outcomes. Qwen3-Coder-30B T had 136 errors among 248 non-empty patches. gpt-5.6-sol T had 174 errors among 395. The reference arms had at most 5. Counting the errored instances as unresolved deflates T, so both T analyses reported earlier are INVALID and are withdrawn: the Qwen3-Coder verdict reported 2026-10-14 01:30, and the gpt verdict computed 21:00. That includes their "depth carries the effect" verdicts. Both arms will be regraded with authenticated image pulls, and §7 will be re-run on reports with no infrastructure errors. Per §7, harness errors are infrastructure failures and are not scored as model failures. The post-hoc confound clarification above is a statement about design logic and does not depend on these results.
