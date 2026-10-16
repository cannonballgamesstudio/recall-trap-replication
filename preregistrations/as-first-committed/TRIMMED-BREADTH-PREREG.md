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

(none yet)
