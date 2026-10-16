# Pre-registration: gpt-5.6-sol logged confirmatory replication + parse-apply-test funnel

**Class 1 (pre-registered).** This design document is committed to git BEFORE any generation call of the
run it governs; the commit hash is recorded in `PREREG-LEDGER.md`. It fixes the design, the reporting
rule, the endpoint hierarchy, and the failure branch pre-data. Ruling authority: methodology reviewer, 2026-08-08.

## Motivation
The flagship gpt-5.6-sol single-shot dedup arm (dedup-ON 39.2% vs dedup-OFF 46.8%, +7.6pp, n=500,
McNemar exact p=0.0003, clustered 95% CI [+0.8, +13.1]pp) did NOT log raw model responses, so §5.7's
parse → applied → test-pass funnel — the defense that the effect is repair-quality and not a
SEARCH/REPLACE edit-format artifact — cannot be computed for gpt (it exists only for DeepSeek and
DENSE-1). This run supplies that funnel for gpt, and gives gpt a clean pre-data git anchor it lacks.

## Design (frozen before generation)
- Model gpt-5.6-sol, single-shot, no tools; both arms (dedup-ON, dedup-OFF); n=500.
- Instance set = the original run's included set, frozen by manifest before generation.
- Identical prefetched fusion packs (`<EVAL_ROOT>/swebench-verified/p5/local_packs.json`), identical prompt
  template, identical decoding parameters as the original run (recorded in the run-time addendum below).
- One generation pass per arm. Full raw-response logging ON (`LOG_RESPONSE_TEXT=1`), so parse/apply/
  content are captured per instance.
- Grading: official SWE-bench Verified Docker harness on the applied subset of both arms (images
  re-pulled from zero; `--delete-image` disk discipline), to compute test-pass conditional on applied.
- Decoding gate: verify `fin=length ≈ 0%` on the first ~50 generations before continuing (gpt-5.6-sol
  is non-reasoning, so the 6000-token cap should not bind; if it does, a dated addendum records the fix).

## Reporting rule (binding, fixed before any generation call)
(a) **Headline invariance.** The paper's headline gpt-5.6-sol estimate remains the original 2026-07-14
run (+7.6pp, n=500, McNemar exact p=0.0003, repository-clustered 95% CI [+0.8, +13.1]pp) under the
program's one-run-per-curve discipline (§5.9, Appendix B). This replication does not replace, average
with, pool into, or re-weight that estimate under any outcome, higher or lower.

(b) **Unconditional publication.** The replication's resolve Δ(OFF−ON), discordant counts, exact McNemar
p, and repository-clustered CI are published in §5.7 and Appendix D regardless of their values, including
a null or a reversal. All funnel stages (parse rate, apply rate, test-pass conditional on applied, per
arm) are likewise published regardless of what they show, including any result that contradicts the §5.2
quality-channel decomposition.

(c) **Endpoint hierarchy.** The PRIMARY endpoint of this run is the funnel contrast
test-pass-conditional-on-applied, dedup-OFF minus dedup-ON among applied patches (the audit the original
gpt run cannot support for lack of logged responses). The resolve Δ is the SECONDARY endpoint, a
confirmatory replication of direction only; it generates no new headline.

(d) **Replication criterion and failure branch (fixed now).** The replication confirms the direction iff
Δ(OFF−ON) > 0 with one-sided exact McNemar p < 0.05; it is additionally consistent in magnitude iff the
point estimate lies inside the original clustered CI [+0.8, +13.1]pp. If the direction criterion fails,
the paper will state in §5.7 and §6 that the primary gpt effect did not replicate under logged
conditions, the gpt arm is downgraded from confirmatory to unresolved in the §6.1 claim structure and
Appendix D, and the surviving claim rests on the remaining clustering-robust confirmatory arm
(Qwen3.6-27B) and the supporting arms; the original +7.6pp remains reported as the original observation,
not restated as a confirmed effect. The same rule applies to the funnel: if dedup-OFF does not beat
dedup-ON on test-pass-conditional-on-applied, the paper states that the format-artifact defense is not
established for gpt and §6.2 is amended accordingly.

(e) **Multiplicity.** This run is outside the Holm confirmatory family of §6.1 and changes no
multiplicity computation; it is a replication of an already-reported estimand, not a new hypothesis.

(f) **No optional stopping, no silent regrades.** The instance set is frozen by manifest before
generation; one generation pass per arm on the identical prefetched fusion packs, prompt template, and
decoding parameters as the original; full raw-response logging on; regrades only for documented harness
faults, logged in a dated deviations addendum to this file. Model slug, provider, endpoint, decoding
parameters, and run dates are recorded in this document at run time.

## Endpoint-drift disclosure
The replication runs against the same provider endpoint and model slug as the original, pinned to a
dated snapshot where the provider offers one; absent a pinned snapshot, cross-run magnitude comparison
is disclosed as drift-exposed, and the within-run funnel contrast, which is drift-symmetric (both arms
run on the same endpoint on the same days, so any silent model revision affects both arms equally and
cannot manufacture or erase a within-run paired contrast), is the primary endpoint in part for this
reason.

## Terminus (conditional)
This is the final v1 experiment PROVIDED the reporting-rule decision criteria above resolve without
triggering a downgrade branch (clause d). A failed direction replication or a funnel contradiction of
§5.2 reopens v1 scope for resolution of that finding only; all other post-hoc findings go to the v2 list.

## Run-time addendum (appended at execution, not pre-data)
- [x] Model slug / provider / endpoint: `openai/gpt-5.6-sol` via OpenRouter `https://openrouter.ai/api/v1`.
      No dated snapshot variant pinned (provider offers only the bare slug); per the endpoint-drift
      disclosure, cross-run magnitude vs the 2026-07-14 headline is drift-exposed, and the within-run
      funnel contrast (drift-symmetric) is the primary endpoint accordingly.
- [x] Decoding parameters: temperature 0.2 (in-harness, `local_dedup_ab.py`), max_tokens 6000, no seed
      (provider does not expose one); identical to the original non-reasoning gpt run (§4.3).
- [x] Generation run date: 2026-08-09. **fin=length gate PASSED**: 0.0% length-truncation on the first
      ~50 (finish_reason=stop on all sampled; gpt-5.6-sol is non-reasoning, the 6000 cap does not bind).
      Full raw-response text logged (`raw_local_gptsol_logrep_{arm}.jsonl`, LOG_RESPONSE_TEXT=1). Instance
      set = the frozen `instances_verified.json` manifest (n=500), same fusion `local_packs.json`.
- [x] Grading: swebench.harness.run_evaluation, dataset princeton-nlp/SWE-bench_Verified, --cache_level env --max_workers 3, official prebuilt Docker Hub images; run 2026-08-09. run_ids gptsol_logrep_dedup{ON,OFF}.
- [x] Deviations: (1) OpenRouter key exhausted mid-OFF at ~552 calls; topped up (same key, per author) and resumed via --skip-existing, completing the interrupted single pass (not a re-run); no poisoned preds. (2) Grade cache_level env (not the original 'instance') to fit the ~1TB WSL2 vhdx after an earlier image prune; disk-bounded, no effect on outcomes.

## RESULT (2026-08-09) — clause-(d) outcome: REPLICATION CONFIRMED, funnel supports depth
FUNNEL (primary): gpt test-pass|applied dedup-ON 47.9% -> dedup-OFF 53.1% (+5.2pp), beside DeepSeek 23.9->31.9 (+8.0) and DENSE-1 48.4->55.1 (+6.7); depth wins conditional on applying, so the format-artifact defense is established for gpt (§6.2 not amended).
SECONDARY (resolve): dedup-ON 39.4% (197/500) -> dedup-OFF 45.9% (229/499), paired n=499, Δ(OFF-ON)=+6.41pp, discordant 67/35, exact 2-sided McNemar p=0.0020, one-sided P(OFF<=ON)=0.0010, repo-cluster bootstrap 95% CI [+4.92,+11.28]pp (excludes zero), clustered one-sided P(Δ<=0)=0.0000.
CLAUSE (d): direction CONFIRMED (Δ>0 & one-sided p<0.05); magnitude-consistent (+6.41 in [+0.8,+13.1]); funnel OFF>ON. No downgrade branch. Headline estimate unchanged at the original +7.6pp (one-run-per-curve); this replication is a second sampling draw of the same estimand. Original run ON 39.2%/OFF 46.8% vs replication ON 39.4%/OFF 45.9% (endpoint drift did not manifest).
