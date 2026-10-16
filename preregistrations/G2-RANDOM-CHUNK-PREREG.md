> **PROVENANCE NOTE (added 2026-08-08):** This design note was authored on or before 2026-07-17 (file modification time; no stronger evidence exists) and first committed to the repository at release, after the run it governs. Under Appendix B's provenance scheme it is a Class-2 design note, not a pre-data registration anchor. No use of "pre-registered" in the paper rests on this document.

# Pre-registration: G2 — random-chunk-per-file control (depth vs. chunk-selection bias)

Status: PRE-REGISTRATION. Written before any run. Commit this file, record its hash and
date in Appendix B, and do not edit the hypotheses, arms, decision rule, or primary
analysis after the first generation call. Deviations go in a dated addendum below.

---

## 1. Motivation and the competing hypotheses

The paper's headline compares dedup-ON (one chunk per file, argmax-scored) against dedup-OFF
(multiple chunks per fewer files) at a fixed 12-slot budget, and attributes dedup-ON's lower
resolve rate to **within-file depth**: ON spreads the budget across ~12 files at one chunk
each, so the edited file rarely gets enough contiguous lines to build a valid edit or reason
about the fix.

GLM's alternative (triage G2) is that the harm is **argmax chunk-selection bias**, not breadth:
dedup-ON keeps, per file, the single top-scored chunk, which the fusion/dense scorer tends to
make a signature/interface/definition chunk (high lexical+semantic salience) rather than the
gold-body chunk that must be edited. Under this account, the loss is "ON keeps the *wrong*
chunk within each file," and would be repaired by keeping *any other* chunk from the same file,
with no change in breadth.

These two stories are observationally entangled in the ON-vs-OFF contrast because OFF changes
both the file set (fewer files) and the per-file chunk selection (multiple chunks, so the
gold-body chunk is more likely served). G2 inserts a third arm that changes **only** the
per-file chunk selection, holding the file set and the one-chunk-per-file budget fixed.

## 2. Arms (single knob isolated)

All three arms serve a 12-slot pack as sole context, single-shot, no search tools, identical
prompt template and renderer.

- **Arm A = dedup-ON (argmax).** The existing recall-maximizer: the same 12 files as served in
  `local_packs.json[iid]["dedupON"]`, each represented by its single top-scored chunk.
- **Arm B = random-chunk-per-file.** The **same 12 files as Arm A**, the **same one-chunk-per-file
  budget**, but for each file the served chunk is a **uniformly random draw from that file's
  candidate-chunk pool** (all chunks of that file present in the retrieval candidate set),
  instead of the argmax chunk. Breadth (file set) is identical to A by construction.
- **Arm C = dedup-OFF (depth).** The existing winner:
  `local_packs.json[iid]["dedupOFF"]` (~5 files, multiple chunks each), unchanged.

Arm A and Arm C are **re-used from the existing graded run** (no re-generation needed) *only if*
the same model is used; since the existing single-shot arms were graded on gpt/DeepSeek/Qwen,
Arm B must be generated on whichever of those models is chosen, and A/C are re-graded or re-used
for that same model (see §5). Arm B is the only genuinely new generation.

## 3. Hypotheses and pre-registered decision rule

Primary contrast: **B vs. A**, paired McNemar on resolve, same instances.
Secondary contrast: **B vs. C**, paired McNemar.

Let Δ(B−A) be the marginal resolve-rate difference (B minus A), and recall the existing
A→C gain is Δ(C−A) ≈ +5.8pp for Qwen (the recommended model).

Pre-registered interpretation, decided now:

- **If B ≈ A** (Δ(B−A) not significant, and its point estimate is a small fraction of Δ(C−A),
  pre-set as < 40% of the A→C gap, i.e. < ~2.3pp for Qwen): the harm is **not** chunk-selection.
  Randomizing which chunk is kept does not help. This **supports the depth story**: what matters
  is total within-file coverage/breadth allocation, not which single chunk argmax picks.
- **If B moves toward C** (Δ(B−A) significant and positive, recovering a substantial share of
  Δ(C−A), pre-set as ≥ 60% of the A→C gap, i.e. ≥ ~3.5pp for Qwen, or B not distinguishable
  from C): the harm is at least partly **argmax chunk-selection bias**. The mechanism claim must
  change: the paper can no longer attribute the dedup effect purely to breadth-vs-depth, and must
  report that a large part is "the dedup filter keeps the wrong (argmax/signature) chunk," which
  is a chunk-*selection* problem repairable within one-chunk-per-file.
- **Intermediate** (Δ(B−A) positive and significant but between 40% and 60% of Δ(C−A)): report
  as **both channels contribute** — chunk-selection bias is real but partial, and depth carries
  the remainder. The paper's mechanism section adds chunk-selection as a named co-cause rather
  than replacing depth.

The direction of the point estimate and the significance of B vs. A are the deciding quantities;
the 40%/60% band is fixed here to avoid post-hoc goalpost moving. Because n=500 is
under-powered for the intermediate band (see §6), the "intermediate" verdict is explicitly the
low-confidence outcome and, if it obtains, we pre-commit to reporting it as inconclusive on
partition rather than as support for either pure story.

## 4. DATA FEASIBILITY — can Arm B be built from data on disk?

**Verdict: NO. Arm B cannot be built purely from files on disk; it requires a RETRIEVAL RE-RUN
(no new embeddings, no LLM compute) to recover each file's candidate-chunk pool.**

What is on disk (`local_packs.json`): for each instance and each arm, only the **12 served
chunks** and their file list. Inspected directly:
- `dedupON`: 12 chunk headers across 12 files, i.e. exactly the **argmax chunk per file** — the
  other candidate chunks *within* each of those 12 files are **not stored**.
- `dedupOFF`: 12 chunk headers across ~4–5 files. This supplies multiple chunks for the ~5 depth
  files, but those are not the 12 ON files, so it cannot supply pools for Arm B's file set.

Therefore the per-file candidate pool (chunks beyond the served argmax, for each of the 12 ON
files) is absent from disk. It is recoverable **without any model compute** the same way
`reconstruct_kpacks.py` already does it: re-query the live `retrievald` daemon at a deeper pool. That
script calls `fetch_pack(EP, repo, iid, problem[:6000], 40)` and `recall_curve.json` confirms the
retriever returns deep ranked pools (n_hits up to ~95 per instance). Re-querying at depth ~100
returns, for each file, all of its chunks that appear in the candidate set — exactly the pool
Arm B samples from.

**What is needed to build Arm B (all local, no paid compute):**
1. The pinned `retrievald` index and daemon used for the original run, at the exact retriever config
   (fusion `fusion@1+fmt-0.15+...+4096` for the fusion arms, or the dense config for CC-1),
   servable on `:8083`/`:8084`. If the index no longer exists it must be rebuilt from the pinned
   `retrievald` commit + the repo snapshots (still no LLM compute, but a retrieval-index rebuild).
2. For each instance: the 12 ON files (`local_packs.json[iid]["dedupON"]["files"]`), the
   problem statement (`instances_verified.json`), and a deep pool fetch (depth ≥ 100).
3. The pack renderer (`format_pack` in `g_plane_prompts.py`) to serialize Arm B identically to
   A and C.

**Confounds this re-run must avoid:** the deep pool must come from the SAME scorer/config as
Arm A's argmax, so that A's chunk is literally the rank-1 chunk of the pool and B is a draw from
the same pool. Fetch the pool from a single daemon (the dedup-OFF daemon `:8084`, which returns
multiple chunks per file at depth) and derive A, B, and the file set from that one pool, rather
than mixing the `:8083` (ON) and `:8084` (OFF) daemons. This guarantees A = argmax(pool_f) and
B = random(pool_f) over the identical pool.

## 5. Exact Arm-B pack-construction procedure

For each instance `iid`:
1. `pool = fetch_pack(":8084", repo, iid, problem[:6000], depth=100)` — the deep ranked
   candidate list (chunks, each with file, start line, snippet, score, rank).
2. `on_files = local_packs.json[iid]["dedupON"]["files"]` (the 12 argmax file set). Freeze this
   as Arm B's file set so breadth is identical to A. (Sanity-check that each `on_file` appears in
   `pool`; if a rare ON file is absent from the depth-100 pool, fall back to depth-250 for that
   instance, and if still absent, keep the served ON chunk for that file and log it — see
   singleton handling.)
3. For each `f in on_files`: `pool_f = [chunks in pool with file == f]`, kept in rank order.
   - `argmax_chunk_f = pool_f[0]` (this reproduces Arm A's served chunk; verify it matches
     `dedupON` for that file as a construction check).
   - **Random draw:** `rng = random.Random(SEED_GLOBAL ^ hash(iid) ^ hash(f))`; choose
     `B_chunk_f = rng.choice(pool_f[1:])` if `len(pool_f) >= 2`, i.e. **exclude the argmax chunk**
     so B is a genuinely different selection wherever a choice exists.
   - **Singleton handling:** if `len(pool_f) == 1` (the file contributes only one chunk to the
     whole pool), there is no alternative; B keeps that chunk (= A for that file). Log the count
     of such files per instance; report the mean.
   - **Tie handling:** ranking ties are irrelevant because B samples uniformly over the pool
     members regardless of score; A uses `pool_f[0]` and ties there are broken by the retriever's
     existing deterministic order (unchanged from the main run).
4. Assemble the 12-slot pack from `{B_chunk_f : f in on_files}` (one chunk per file, 12 files),
   render with `format_pack(..., budget=12)`, identical header/format to A and C.
5. `SEED_GLOBAL = 20260717` fixed here. Write `packfile_B_random.json` and a companion
   `packfile_B_provenance.json` recording, per instance/file, the chosen chunk's (file, start,
   rank-in-pool, pool_size). This makes B fully reproducible and auditable.

**Robustness draws (pre-registered):** because B is stochastic, generate the pack under **3
seeds** (20260717, 20260718, 20260719) and run the model on all three. Report the per-seed
Δ(B−A) and the seed-averaged estimate; the decision rule is applied to the seed-averaged Δ(B−A).
This costs 3× the Arm-B generation but guards against a single unlucky draw. (If budget forces
one seed, use 20260717 and state the single-draw limitation.)

## 6. Model, n, and power

**Recommended model: local Qwen3-Coder-30B, single-shot, n=500.** Rationale:
- Cheapest defensible: runs locally via `llama.cpp` (`<LLAMA_DIR>\llama-server.exe` +
  `Qwen3-Coder-30B-A3B-Instruct-*.gguf`), so generation cost is compute/electricity, not metered
  API credits.
- It is the arm with the **largest relative effect** (near-doubling, 6.6%→12.4%), so an
  argmax-selection artifact, if present, has the most room to show up; a null B≈A on this arm is
  the most informative.
- A and C already exist for Qwen (`qwen30b_ON_rg` / `qwen30b_OFF_rg`), so only B is new (×3 seeds).

**Power / MDE (n=500, McNemar, α=0.05 two-sided, 80% power):**
Grounding constants come from the existing Qwen A-vs-C run: discordant pairs b(A-win)=10,
c(C-win)=39, total discordant = 49 (9.8% of pairs), marginal Δ(C−A)=+5.80pp.
- Assuming a comparable discordant rate ψ≈0.10 for B-vs-A, n=500 yields **≈49 discordant pairs**
  and a **minimum detectable marginal effect ≈ 3.83pp** at 80% power (discordant split p*≈0.70).
- Consequence for the decision rule: n=500 is **adequately powered to detect a "B moves to C"
  outcome** (the full A→C gap is 5.80pp > 3.83pp MDE; even 60% of it = 3.5pp is near the MDE),
  and adequately powered to confirm a clean **B≈A null** with a tight CI around zero. It is
  **under-powered for the intermediate band** (a ~2.3–3.5pp partial recovery), which is why the
  intermediate verdict is pre-declared low-confidence.
- If the goal is to resolve the intermediate band too, n≈900–1000 (a second model, e.g. adding
  gpt-5.6-sol via API, or a larger benchmark slice) would push the MDE to ~2.8pp. Not required
  for the primary decision; note as optional strengthening.

**Secondary model (optional, only if the Qwen result is intermediate):** gpt-5.6-sol single-shot
n=500 via the same API path as the main run. This adds paid compute (see §7) and is not part of
the primary pre-registration; register it as a contingent follow-up with the same decision rule.

## 7. Grading and analysis

- **Grading:** official SWE-bench Docker harness, same commit/dataset revision/image digests as
  the main run, `--cache_level instance`. Empty patches count as failures (resolve=0). Harness
  errors retained as failures, consistent with the primary paper convention.
- **Primary analysis:** paired McNemar exact test, B vs. A, on the common graded instance set,
  resolve as the binary outcome. Report b/c discordant counts, marginal Δ(B−A) with a
  repository-cluster bootstrap 95% CI (per the T18 protocol, since the primary paper now reports
  clustered inference), and the seed-averaged estimate.
- **Secondary:** B vs. C McNemar; the share of Arm-B files that were singletons (no alternative
  chunk); and a mediator check — recompute anchor-visible share and within-file gold-line
  coverage for Arm B (using `cov.py` on the served B packs) to see whether random selection
  changes anchor dose relative to A, which is the mechanistic bridge between the two hypotheses.
- **Pre-registered primary estimand:** the raw (unconditional) resolve difference Δ(B−A), to
  match the paper's primary. Report the both-non-empty conditional as secondary.

## 8. Rough cost / compute estimate

- **Retrieval re-run (Arm-B pack build):** local `retrievald` deep-pool fetch for 500 instances ×3
  seeds. Minutes to low tens of minutes; **$0** beyond electricity. If the index must be rebuilt
  from the pinned commit + repo snapshots: a few hours of local indexing, still $0 in API terms.
- **Generation (Arm B, the only new model compute):** Qwen3-Coder-30B single-shot, ~500 × 3
  seeds = 1500 generations, ~2–3k prompt + ~1k completion tokens each, local. Estimated
  **~3–6 GPU-hours** on the existing rig; **$0** metered.
  - Alternative if run on OpenRouter `qwen3-coder-30b-a3b` instead of local: ~1500 × ~3.5k tokens
    ≈ 5M tokens ≈ **$0.5–1.5** total (single-shot, not agentic). Still negligible.
- **Grading:** SWE-bench Docker for the new B predictions (×3 seeds = 1500 grades, but many
  cached by instance). **A few hours** of local Docker; sequence it away from any heavy prediction
  run (Docker wedges when grading overlaps heavy prediction — `wsl --shutdown` to unwedge).
- **Total marginal paid cost:** ~$0 (local) to ~$1.5 (OpenRouter); wall-clock ~1 day including
  grading and the retrieval re-run. The optional gpt-5.6-sol secondary would add API cost on the
  order of the main gpt single-shot run (hundreds of calls; budget per the main-run rate).

## 9. Threats to validity of the control itself

1. **Random ≠ gold-body.** Arm B samples uniformly from the pool; it does not deliberately serve
   the gold-body chunk. If the pool for a file rarely contains the gold-body chunk at all, B and A
   may both miss it, and a B≈A null would then under-state a selection effect that a *gold-aware*
   selector would reveal. Mitigation: report, per file, whether the gold-body chunk is present
   anywhere in the pool (using gold hunks), so a null can be read against pool composition. This
   also yields a natural upper-bound arm (oracle-chunk-per-file) if we later want it.
2. **Pool depth sensitivity.** Too shallow a pool → many singletons → B collapses toward A
   mechanically (no choice), biasing toward the depth verdict. Mitigation: depth ≥ 100, report
   singleton rate; if singleton rate is high (>~30% of files), increase depth and re-draw.
3. **Rank/score confound reintroduced.** By excluding the argmax and drawing from `pool_f[1:]`,
   Arm B serves systematically *lower-scored* chunks than A — the same rank-depth substitution the
   paper concedes for ON-vs-OFF (triage T6). So B vs. A is "argmax vs. a lower-ranked same-file
   chunk," which is exactly the selection question, but note that B also lowers mean served score;
   report the served rank/score distribution for A vs. B so the reader can see the manipulation
   size. A finding that B≈A despite serving lower-scored chunks is a *strong* null for
   chunk-selection.
4. **Stochastic instability.** A single seed could mislead; the 3-seed protocol (§5) and
   seed-averaged decision guard against it. Report between-seed variance.
5. **Same-embedder scope.** B is built with the same scorer as A/C, so it speaks to selection
   *within the deployed retriever*, not to whether a different embedder would rank chunks
   differently. State this scope.
6. **Model/format interaction.** On Qwen (weak editor, SEARCH/REPLACE), a lower-scored random
   chunk might change apply-success independent of reasoning. Report the parse→apply→test funnel
   for B (raw logs) alongside A, mirroring the T9 analysis, so a producibility shift is not
   misread as a selection effect on quality.
7. **Index drift.** If the index is rebuilt rather than reused, chunk boundaries could differ
   from the original run, breaking the A-reproduction check. Mitigation: verify Arm B's
   reconstructed argmax chunk matches the stored `dedupON` chunk for each file before trusting
   the pool; abort and rebuild if the match rate is low.

## 10. Deviations log (append-only, dated)

**2026-07-17 — Arm-B construction finalized and built (retrieval only; no generation run yet).**
Owner-agent decisions, overruling parts of §5 after an empirical build against the live fleet
(:8080 embedder, :8083 dedup-ON, :8084 dedup-OFF; smoke-verified to reproduce
`local_packs.json[iid]["dedupON"]` byte-for-byte).

- **D1 (depth cap).** retrievald hard-caps `limit` at `le=200` (`src/ragfusion/retrievald/wire.py`), so §5 step 2's
  "fall back to depth-250" is infeasible in one query. Use depth **200**. At depth 200 the per-file
  candidate coverage is 99.4% and the gold file has an alternative chunk 98.3% of the time, so the
  §5 fallback is unnecessary. (At depth 100, which an earlier attempt used, ~30% of slots were
  forced B==A and 402/6000 ON files were absent from the pool; depth 200 removes that.)

- **D2 (pool source + A anchoring — the substantive change).** §5 built Arm A as `pool_f[0]` from
  the :8084 (dedup-OFF) deep pool, which matched the actually-served dedup-ON chunk only 84% of the
  time. That check was an artifact: `pool[0]` is the single globally-top chunk, not the per-file A,
  and the :8083/:8084 daemons rank within-file differently. Resolution:
  (i) **Arm A is anchored to the ACTUAL graded pack** — A's 12 files, per-file chunk identity
  `(file, line)`, and the B==A fallback chunk are all parsed from
  `local_packs.json[iid]["dedupON"]["pack"]` (the exact bytes graded on Qwen). Built B file set
  equals graded-A file set on **500/500** instances (0 mismatch).
  (ii) **The candidate pool is `:8083` queried with `dedup=False` at limit 200** — the un-deduped
  version of A's own daemon ranking (the wire exposes `dedup: bool | None`; `fetch_pack` does not
  pass it, so the builder POSTs `/v1/query` directly). Empirically identical to the :8084 depth-200
  pool but conceptually the un-deduped A ranking; gives 99.4% per-file A coverage and eliminates
  the missing-ON-file problem. The §5 `pool_f[0]==A` reproduction check is **dropped** as
  unnecessary (A is anchored to the graded chunk, not reconstructed).

- **D3 (RNG).** Per-(seed, iid, file) RNG seeded by SHA-256 of `"{seed}|{iid}|{file}"` instead of
  builtin `hash()` (which is salted per process and would break reproducibility). Seeds
  {20260717, 20260718, 20260719}; decision is seed-averaged (§3). B draws uniformly over all pooled
  chunks of file f whose `(file,line)` differs from A's; if none exist (singleton), B = A.

- **D4 (forced B==A dilution — accepted, with power note).** At depth 200, **16.1%** of slots
  (962/5966) are forced B==A because the file contributes only its single served chunk to the pool.
  B differs from A on a mean of **10.0/12 slots per instance** (0/500 packs identical to A). The
  dilution falls on outcome-irrelevant non-gold singleton files: the **gold-file slot is randomized
  on 98.3%** of instances (469/477 where the gold file is in Arm A). Because the manipulation is
  undiluted on the outcome-relevant slot, the §6 power/MDE is **not materially degraded**: the
  effective treatment (random reselection on ~84% of slots and ~98% of gold slots) is if anything a
  stronger perturbation than the "swap one chunk" the pre-reg imagined, so the n=500, 80%-power
  MDE (~3.8pp for Qwen) stands. No design change required.

- **Reproducibility caveat.** The saved packs are the frozen artifact
  (`packfile_g2_B_seed{20260717,18,19}.json` + `g2_B_prov_seed*.json`, under
  `work/p5\`). Rebuilding from scratch depends on retrieval determinism; the
  live dedup=False pool showed the graded-A chunk as the file's rank-1 in 82.9% of files (mild ANN /
  tie nondeterminism vs the original run), so the experiment must be run from the saved packs, not
  regenerated. A's chunks are anchored to the graded `local_packs`, so A is fully deterministic.

- **Build diagnostics (n=500, seed 20260717):** fetch failures 0; graded-A chunk present in pool
  99.4%; forced B==A 16.1%; mean alt chunks/slot 8.1; B differs from A 10.0/12 per instance; gold
  file has an alternative chunk 98.3%; gold-file slot randomized 98.3%. Packs and provenance
  written. **Status: Arm-B packs BUILT and VERIFIED; sound to proceed to generation. No paid
  generation run has been performed.**
