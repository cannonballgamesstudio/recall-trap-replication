# E1 + E2 — the two arms our own data demanded and we never ran

> Pre-registered 2026-07-14, BEFORE either arm is run. Binds the analysis.

## Where we actually are (no spin)

| arm (n=92 paired, official Docker) | resolved |
|---|---|
| oracle pack, tools ON | 88.0% |
| oracle pack, tools OFF | 85.9% |
| fusion pack, tools OFF | 76.1% |
| BM25 pack, tools OFF | 76.1% |
| explorer (no pack, tools ON) | 75.0% |

Oracle tools-ON vs tools-OFF: +2.2pp, McNemar p=0.625, **only 4 discordant pairs**.
That is not "tools are redundant" — it is "we could not detect anything." The
causal claim we were building ("exploration substitutes for bad retrieval") is
**NOT supported** and is hereby withdrawn.

Prior art (hostile hunts, 2026-07-14) has taken most of the rest:
- **RGFL (2601.18044)** already published our failure taxonomy on this benchmark:
  wrong-file 13%, wrong-element 53%, wrong-line 84%, plus a pure-repair residue.
  Our 4.5%/81.8%/13.6% sits inside their CIs. **Claim 1 is a corroboration, not
  a finding.**
- **arXiv 2607.00725** (1 Jul 2026) already states our framing: *"document recall
  — the standard retrieval metric — is the wrong quantity to optimize in this
  regime"* because *"the reader never consumes the retrieved set; it consumes the
  packed context."* Multi-hop QA, not code.
- **Small-to-big / auto-merging / parent-document retrieval** is a standard,
  shipped technique. "Expand retrieved chunks to their parents" is NOT novel.
- Correction to our own record: **SWE-Explore's patcher is tool-using**, not
  search-free (their App. D holds tool set fixed). We asserted otherwise.

## What is actually unmeasured

Both of the following were inferred from a confounded contrast (oracle pack has
perfect file selection AND depth) instead of measured. Neither has been run.

### E1 — fusion pack + TOOLS ON

Our own taxonomy says **81.8% of pack failures are "right file, wrong lines."**
That is exactly the failure a search tool repairs: open the file and scroll. We
measured tools at *oracle* context, where nothing needs rescuing (hence the
null). We never measured them at a **real** pack, where the mechanism predicts
they should matter. Same fusion pack (12 slots, hybrid), `PACK_TOOLS_SYSTEM`,
full toolset, 10 turns.

### E2 — dedup OFF (depth allocation) at a FIXED 12 slots

`RETRIEVALD_QUERY_DEDUP_FILE=0` on a second daemon (:8084). Identical ranking,
identical budget; the ONLY change is that slots are no longer forced onto
distinct files. Verified on astropy-12907: dedup-ON = 12 files x 1 chunk (two
slots spent on *test* files); dedup-OFF = 4 files, with **3 chunks in the gold
file**.

This is the honest test of the claim we have been asserting: that file-dedup —
adopted because it maximized *recall* — starves a fixed-slot pack of the line
depth the patcher needs. Under a hard budget, expansion is **zero-sum**: depth in
file *i* evicts file *j*. Classical small-to-big never faces that trade; that
framing, not the technique, is what would be ours.

**Prior art warns this may FAIL:** Sepidband et al. (2604.05481) report
line-level expansion "frequently degrades performance due to noise
amplification" (avg -3.1 to -3.5 pts), and RGFL found narrowing to gold elements
sometimes did worse than handing over the whole gold file.

## Protocol (binding)

- Slice: the same pre-declared first-100 instance_ids. Arms paired against the
  existing `pack` (76.1%), `oracle` (85.9%), and `explorer` (75.0%) grades.
- Grading: official Docker harness, `--cache_level instance`.
- Analysis: McNemar exact, paired, on the common graded set.
- Cost: 2 x 100 x ~$0.40 = ~$80; hard stop at $150.

## Decision rules (binding)

1. **E1 (tools on a real pack) significantly ABOVE the toolless pack
   (p<0.05):** tools rescue the dominant failure mode. Combined with the oracle
   null (tools add nothing when the pack is already right), this is an
   **interaction**: *search tools are worth exactly as much as your retriever is
   bad.* That is a mechanism nobody has, it explains the field's absorption
   nulls, and it is the paper.
2. **E1 not significant:** tools do NOT rescue right-file-wrong-offset failures
   either. Then the pack regime is simply inferior and the whole
   retrieval-conversion story collapses to "oracle context helps" (published).
3. **E2 (dedup off) significantly ABOVE dedup on:** recall-optimizing dedup
   demonstrably costs resolve at fixed budget. The metric-regime critique becomes
   a *measured* claim in code, not a borrowed framing.
4. **E2 significantly BELOW dedup on:** the depth hypothesis is dead, prior art
   (noise amplification) was right, and I was wrong to pitch it. Report it.
5. **E2 not significant:** allocation is not the lever; the 9.8pp is file
   *selection*, not shape. The honest conclusion is that our retriever simply
   picks the wrong files, and no repacking fixes that.

**Predictions, recorded before the run.** E1: significant (+5 to +9pp) — the
taxonomy makes this near-mechanical. E2: significant but small (+2 to +4pp).

**My prediction record this week: 0 for 3.** I predicted the oracle would falsify
(it didn't), I pitched Table 6 of the SWE-bench paper as a novel insight (it
wasn't), and I built a causal claim on cells that couldn't support it. These
predictions are worth exactly what those were.
