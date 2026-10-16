> **PROVENANCE NOTE (added 2026-08-08):** This design note was authored on or before 2026-07-17 (file modification time; no stronger evidence exists) and first committed to the repository at release, after the run it governs. Under Appendix B's provenance scheme it is a Class-2 design note, not a pre-data registration anchor. No use of "pre-registered" in the paper rests on this document.

# Pre-registration: powered cross-paradigm BM25 test of retriever generality

Status: PRE-REGISTRATION. Written before any powered run. Commit this file, record its hash and
date in Appendix B, and do not edit the hypotheses, arms, decision rule, equivalence margin, or
primary analysis after the first generation call. Deviations go in the dated addendum below.

---

## 0. Honesty statement (read first)

This test is designed to be able to **reject** retriever generality, not only to confirm it. A
prior BM25 dedup ON/OFF arm at **n=100** came in at **about −2pp** (dedup-OFF 74/100 resolved vs
dedup-ON 76/100 on the tractable slice), i.e. near-null and slightly negative — the opposite sign
of the fusion/dense effect. That is exactly why BM25 is currently labeled "untested at power" and
why the paper must not assert "retriever-agnostic" on fusion+dense alone.

We pre-commit, before running, to reporting the powered BM25 outcome **either way**:
- If the powered BM25 effect is positive and equivalent to fusion/dense, retriever generality is
  supported across three paradigms (lexical + dense + fusion).
- **If the powered BM25 effect is null or negative, that is a real and publishable result: it
  BOUNDS the recall-trap effect to dense-family (embedding-based) retrieval, and the paper must
  say so and drop any cross-paradigm generality claim.** We will report this outcome with the
  same prominence as a positive one. The design is not conditioned on confirming agnosticism.

## 1. Motivation

The current generality evidence is fusion + dense (CC-1), which are near-siblings: same
Qwen3-Embedding-8B embedder, same chunker, same 12-slot budget, differing only in whether lexical
and graph signals are mixed into the ranking. The only cross-retriever statistic reported is a
fail-to-reject interaction (permutation p=0.39), which is not evidence of equivalence. A genuinely
different retrieval paradigm is **lexical BM25-only**: no learned embedding, a different notion of
relevance (term overlap), and a different chunk-ranking distribution. If dedup-OFF > dedup-ON
replicates at power under BM25 as well as dense and fusion, retriever generality is earned; if it
does not, the effect is scoped to embedding retrievers.

## 2. Arms

Single-shot, 12-slot pack as sole context, no search tools, identical prompt/renderer/grading to
the headline run. Two new arms:
- **BM25 dedup-ON** — lexical-only ranking, one argmax chunk per file, 12 files.
- **BM25 dedup-OFF** — lexical-only ranking, dedup disabled (multiple chunks per fewer files).

Reference arms (already graded, re-used for the interaction contrasts, same model gpt-5.6-sol):
- Fusion dedup-ON/OFF (headline): Δ +7.6pp, n=500.
- Dense dedup-ON/OFF (CC-1): Δ +5.7pp, n=494.

## 3. FEASIBILITY — can both BM25 arms be built from data on disk?

**Verdict: the lexical-mode infrastructure already exists and was used at n=100; scaling to n=500
requires a RE-RETRIEVAL PASS in keyword mode (retrieval only, no new index, no new infra, no LLM
compute). The n=500 candidate pool / packs are NOT yet on disk (only the n=100 packs are).**

Evidence and mechanism:
- Pure BM25 ranking is produced by the existing retriever via the request parameter
  `mode="keyword"` in `fetch_pack(endpoint, repo, ref, query, limit, mode=...)`
  (`scripts/eval/g_plane_prompts.py`), as opposed to `mode="hybrid"` (fusion). This is documented
  in `swe_bench.py` (the `weakpack` control: "the pack is produced by the lexical/BM25 arm alone
  (mode=keyword)") and `p5_run_gplane.py`.
- The dedup ON/OFF toggle is the same daemon split used for the headline (dedup-ON daemon on
  `:8083`, dedup-OFF on `:8084`); combining that with `mode="keyword"` yields the four BM25 cells.
- Both BM25 dedup arms were **already built and graded at n=100**: `kpack_bm25ON.json` /
  `kpack_bm25OFF.json` (100 packs each), `g_bm25ON.g_bm25ON.json` (76/100 resolved) /
  `g_bm25OFF.g_bm25OFF.json` (74/100 resolved). So the pipeline is proven; only the scale (100→500)
  and the model (the n=100 slice must be extended to the full n=500 headline population) are new.

**What is needed for the powered run (all local for retrieval; LLM compute only for generation):**
1. The pinned `retrievald` daemons at `:8083` (dedup-ON) and `:8084` (dedup-OFF) on the same index/commit
   as the headline. If the index is gone, rebuild from the pinned `retrievald` commit + repo snapshots
   (retrieval-index rebuild, still no LLM compute).
2. Re-run `fetch_pack(mode="keyword", limit=12)` for all 500 instances on each daemon →
   `packfile_bm25_ON.json` / `packfile_bm25_OFF.json`. Minutes to tens of minutes, $0.
3. Render with `format_pack` identical to the headline; generate with gpt-5.6-sol; grade with the
   official harness.

Note on the n=100 slice: the existing BM25 grades (74–76% resolved) sit on the tractable
`oracle_slice`, not the representative n=500 population, so they cannot simply be extended — the
powered run must cover the full headline instance set for the ON/OFF contrast and for the
cross-retriever interaction to be on a common population.

## 4. Model, n, power

**Recommended model: gpt-5.6-sol, single-shot, n=500** — matches the headline model and the
fusion/dense reference arms, so the interaction contrasts are model-controlled. Two arms (ON/OFF)
= 1000 new generations.

**Cheaper variant: local Qwen3-Coder-30B, n=500** (free local compute). Use only if the gpt budget
is unavailable; it changes the model relative to the headline reference arms, so the interaction
would then be Qwen-BM25 vs Qwen-fusion vs Qwen-dense (Qwen dense not yet run), a separate and
weaker comparison. gpt is strongly preferred for a clean cross-retriever interaction.

**Power / MDE (n=500, McNemar, α=0.05 two-sided, 80% power):**
- For the within-BM25 ON-vs-OFF test: assuming a discordant rate ψ≈0.15–0.20 (between the dense
  arm's 0.22 and a lower lexical value), n=500 yields ~75–100 discordant pairs and a
  **minimum detectable marginal effect ≈ 3.0–3.4pp**. So the powered BM25 arm can detect an effect
  of the size seen for dense (+5.7pp) or fusion (+7.6pp) with high power, and can place a tight CI
  around a null (the −2pp prior would land with a CI of roughly ±3pp).
- For the **cross-retriever interaction** (BM25 vs fusion, BM25 vs dense): each arm's risk-
  difference SE ≈ sqrt((b+c)/n²) ≈ 1.6–1.8pp, so the interaction contrast SE ≈ 2.3–2.5pp
  (independent-arm bound; the instance-paired version is tighter). This is the binding constraint
  on the equivalence test (see §5).

## 5. THE ANALYSIS DONE RIGHT

### 5.1 Primary within-BM25 test
Paired McNemar exact on BM25 dedup OFF−ON, gpt-5.6-sol, common graded n. Report b/c discordant
counts and the marginal Δ_BM25 with a **repository-cluster bootstrap 95% CI** (5000 reps,
resample repos with replacement) and **leave-one-repository-out** deltas — the same cluster-robust
protocol now applied to the primary result (per the T18 reanalysis), because instances within a
repo are correlated. Empties count as failures; harness errors retained as failures.

### 5.2 Cross-retriever equivalence (TOST), pre-registered
The generality question is whether the dedup effect is the *same* across paradigms. Test each
pairwise interaction Δ_fusion − Δ_BM25 and Δ_dense − Δ_BM25 (and, as an omnibus, the max pairwise
gap across all three) with a **two-one-sided-tests (TOST) equivalence test**:
- **Equivalence margin δ = 5pp**, fixed now. Justification: the smallest confirmed dedup effect is
  the dense arm's +5.7pp; a between-retriever difference smaller than 5pp means all three
  retrievers show a materially similar effect. (A tighter margin of 4pp is reported as a
  secondary, more stringent check; n=500 is borderline-powered for 4pp given the ~2.4pp interaction
  SE, so 5pp is the pre-registered primary margin and 4pp is exploratory.)
- **TOST procedure:** compute the interaction estimate and its cluster-robust SE (repository
  bootstrap of the paired per-instance interaction contrast). Declare equivalence if the 90% CI of
  the interaction falls entirely within (−δ, +δ). Declare a real difference if the 95% CI excludes
  0 and lies outside (−δ, +δ). Otherwise inconclusive.
- Interaction is computed **instance-paired** where possible (the same 500 instances carry a
  fusion pair, a dense pair, and a BM25 pair), which lowers the SE relative to the independent-arm
  bound in §4; report both the paired and the conservative independent-arm versions.

### 5.3 Estimands
Primary within-arm estimand = raw (unconditional) resolve difference, to match the headline.
Report the both-non-empty conditional as secondary, and the empty-rate symmetry per arm (BM25's
lexical ranking may change producibility, so this is diagnostic).

## 6. Pre-registered decision rule and interpretation

Let Δ_BM25 be the cluster-robust BM25 OFF−ON effect, and consider the TOST outcome against δ=5pp.

- **Outcome A — BM25 positive and equivalent** (Δ_BM25 significantly > 0 under cluster-robust
  inference AND all pairwise interactions TOST-equivalent within 5pp): **retriever generality is
  supported across lexical + dense + fusion.** The paper may state "the effect replicates across
  three retrieval paradigms including a non-embedding lexical retriever; the dedup effect is
  equivalent across them within a 5pp margin (TOST p<0.05)." This is the only outcome that earns
  the word "agnostic," now backed by a positive equivalence test rather than a fail-to-reject.
- **Outcome B — BM25 null or negative** (Δ_BM25 not significantly > 0, CI includes or sits below
  0; and/or the fusion-vs-BM25 interaction 95% CI excludes 0 outside the margin): **the effect is
  BOUNDED to dense-family (embedding) retrieval.** The paper must report that BM25 does not show
  the recall trap at power, drop cross-paradigm generality, and scope the claim to embedding
  retrievers (fusion + dense, same embedder). This is a substantive finding: it localizes the
  mechanism to how embedding retrievers distribute within-file chunks, and is consistent with the
  −2pp n=100 prior. We report it as a headline-level result, not a footnote.
- **Outcome C — inconclusive** (Δ_BM25 direction positive but not significant, interaction neither
  equivalent nor clearly different): report as underpowered; state that BM25 generality remains
  open and give the CI. Pre-commit to not spinning this as support.

Mechanistic corollary to pre-register: if Outcome B obtains, compute the anchor-dose mediator
(within-file gold-line coverage, `cov.py`) on the BM25 packs. If BM25 dedup-OFF does **not** raise
anchor dose the way fusion/dense dedup-OFF does (+0.09 line-cov), that explains a BM25 null and
strengthens the "anchor dose is the operative variable, and BM25 doesn't move it" account —
turning Outcome B from a bound into a mechanism confirmation.

## 7. Grading

Official SWE-bench Docker harness, same commit / dataset revision (SWE-bench_Verified
`c104f840...`) / image digests as the headline, `--cache_level instance`, empties = fail. Sequence
grading away from any heavy prediction run (Docker wedges when grading overlaps heavy prediction;
`wsl --shutdown` to unwedge).

## 8. Rough cost / compute estimate

- **Re-retrieval (BM25 packs, n=500 × 2 arms):** local keyword-mode `fetch_pack`; tens of minutes;
  **$0**. Index rebuild if needed: a few hours local, still $0 metered.
- **Generation:** gpt-5.6-sol single-shot, 1000 calls (500 × 2 arms), ~2.5k input + ~0.8k output
  tokens each ≈ 2.5M input + 0.8M output. At frontier single-shot rates this is on the order of
  **$10–40 total** (confirm the exact gpt-5.6-sol per-token price on the serving endpoint before
  launch; lead with the confirmed $/n to the user per cost-discipline). The local-Qwen variant is
  ~$0 (a few GPU-hours) but changes the model.
- **Grading:** SWE-bench Docker for 1000 predictions, many images cached; a few hours local.
- **Total marginal paid cost:** ~$10–40 (gpt) or ~$0 (local Qwen), wall-clock ~1 day including
  retrieval, generation, and grading.

## 9. Threats to validity

1. **Population mismatch with the n=100 prior.** The −2pp prior is on the tractable `oracle_slice`;
   the powered run is on the full n=500. Do not merge them; the powered run stands alone.
2. **BM25 recall floor.** If BM25 retrieves the gold file far less often than the embedding
   retrievers, both BM25 arms may be depressed and the ON/OFF contrast compressed toward zero for a
   recall reason rather than a dedup reason. Mitigation: report BM25 served-pack file recall@12 per
   arm (`local_packs`-style), so a null can be read against BM25's recall level; if BM25 gold-file
   presence is very low, note the effect could be recall-floored, not truly absent.
3. **Producibility shift.** Lexical ranking changes which lines are served, which can change
   SEARCH-anchor availability and thus apply-success independent of reasoning; report the
   parse→apply→test funnel (T9-style) per BM25 arm.
4. **Equivalence-margin dependence.** The agnosticism verdict depends on δ=5pp; report the full
   interaction CI so a reader can apply their own margin, and report the stricter 4pp result.
5. **Same index, same chunker.** BM25 here shares the chunker and repo snapshots with the embedding
   arms, so "different paradigm" isolates the ranking function, not chunking. State this scope; a
   fully independent BM25 (different chunker/tokenizer) is a further test, out of scope.
6. **Interaction power.** n=500 gives an interaction SE ~2.4pp; a true between-retriever difference
   of 2–4pp may be neither TOST-equivalent nor significantly different (Outcome C). Pre-committed to
   reporting that honestly rather than forcing a verdict; note that pooling all three retrievers in
   a mixed-effects model with retriever as a factor is the higher-power follow-up if C obtains.

## 10. Deviations log (append-only, dated)

**2026-07-17 — BM25 packs built and verified (retrieval only; no generation run yet).**
Construction followed §3 with no design change. Built via `mode="keyword"`, limit 12, on the live
fleet: dedup-ON pack from `:8083`, dedup-OFF pack from `:8084` (daemon defaults), rendered with
`format_pack`. Output `bm25_packs.json` mirrors the `local_packs.json` structure
(`{iid: {dedupON:{pack,files,n_hits}, dedupOFF:{...}}}`) so `local_dedup_ab.py --packs-file
bm25_packs.json` consumes it directly (same harness/model as the fusion + dense gpt-5.6-sol
reference arms).

- **Validation:** the build reproduces the existing n=100 `kpack_bm25ON/OFF.json` file-order
  identically on **100/100** instances for both arms — the keyword-mode construction is faithful.
- **Diagnostics (n=500):** fetch failures 0; dedup-ON mean 11.97 distinct files/pack (2 short packs
  with <12 keyword hits, 0 empty); dedup-OFF mean 6.96 distinct files/pack (0 short, 0 empty) —
  correct dedup behavior (ON breadth ~12 files, OFF depth ~7 files), matching the fusion arms'
  shapes.
- **Recall-floor finding (pre-registered threat #2 realized).** BM25 served-pack gold-file recall@12
  is ON **69.0%** / OFF **61.2%** — well below the fusion retriever's 87.8% / 80.6%. BM25 retrieves
  the gold file far less often, so both BM25 arms sit on a lower recall base and the ON/OFF contrast
  may be recall-compressed. This is exactly threat #2; the powered analysis MUST report these
  per-arm recall numbers so a BM25 null can be read against the recall floor rather than as a clean
  absence of the dedup effect. (Note the dedup direction holds: ON 69% > OFF 61%, so dedup remains
  the file-recall maximizer under BM25, preserving the recall-trap premise.)
- **Status: BM25 packs BUILT and VERIFIED; sound to proceed to gpt-5.6-sol generation. No paid
  generation performed.**
