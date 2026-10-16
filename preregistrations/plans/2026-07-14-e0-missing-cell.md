# E0 — the missing cell (oracle pack + TOOLS ON)

> Pre-registered 2026-07-14, after the oracle arm graded but BEFORE any
> oracle+tools instance is run. Binds the analysis.

## Why this exists: our oracle arm is confounded, and we were told so in advance

The oracle arm changed **two things at once**: it gave the agent perfect context
AND removed its search tools. From

| arm | resolved (n=92) |
|---|---|
| oracle pack, no tools | 85.9% |
| fusion pack, no tools | 76.1% |
| BM25 pack, no tools | 76.1% |
| explorer, all tools | 75.0% |

we claimed "exploration is a substitute for bad retrieval, not an independent
good." **That claim is not supported by these cells.** Nothing here separates
"perfect context helped" from "removing tools helped." ORACLE-SWE
(arXiv 2604.07789) pre-emptively rejected designs like ours for exactly this
reason — *"this would confound the effect of oracle information with the agent's
built-in capabilities"* — and they are right.

Prior art also now owns most of what we thought was new (found by a hostile hunt
2026-07-14, recorded here so it cannot be quietly forgotten):
- **SWE-Explore (2606.07297):** oracle-localized regions vs agent-explored regions
  into a search-free patcher: 59.7% vs 48.0% (+11.7pp). Our +10.9pp is the same
  finding with a different knob.
- **SWE-bench (Jimenez et al., ICLR'24) Table 6:** trimming an oracle pack to
  ±15 lines around the diff RAISES resolve (Claude 2: 4.8% → 5.9%). Tables 2/3:
  as context grows, BM25 recall rises while resolve falls. That is our
  "precision, not recall" mechanism — published in the benchmark's own paper.
- **Zhao et al. (2411.19463):** retriever choice (BM25 vs miniLM vs OpenAI) is
  "largely flat or erratic" for code tasks — the inert half of our curve.

## The one cell that decides whether a paper exists

**ORACLE PACK + ALL TOOLS.** Identical oracle pack (gold-patch files + line
ranges, 12 slots), identical turn cap (10), full default toolset (Bash, Grep,
Glob, Read, Edit, Write). The system prompt is `PACK_TOOLS_SYSTEM`: `PACK_SYSTEM`
with only the three tool-restriction sentences replaced by permissive ones
(diff disclosed in `g_plane_prompts.py`; no other wording changed).

This isolates the TOOLS variable at fixed, perfect context.

- **Slice:** the same pre-declared first-100 instance_ids used by the oracle arm.
- **Grading:** official Docker harness, `--cache_level instance`.
- **Analysis:** McNemar exact, paired, vs the oracle (no-tools) arm on the common
  graded set.

## Decision rules (binding, applied literally)

1. **oracle+tools significantly BELOW oracle−tools (McNemar p<0.05):** tools
   ACTIVELY HARM an agent that already has good context. This is the paper. It
   contradicts ORACLE-SWE's stated design premise, it is not in any of the six
   hunters' reports, and the confound objection becomes our headline rather than
   our fatal flaw.
2. **No significant difference (p≥0.05, and the CI excludes a ≥5pp benefit from
   tools):** exploration is REDUNDANT given good context, not harmful. Weaker.
   Survivable as a short empirical note; it is ORACLE-SWE's result plus a
   redundancy corollary, and must be framed as such.
3. **oracle+tools significantly ABOVE oracle−tools:** our causal claim is DEAD.
   Only "oracle context helps" survives, and that is published (SWE-Explore,
   ORACLE-SWE, and SWE-bench's own oracle setting). **Kill the paper**; keep the
   apparatus (see below).

**Prediction, recorded before the run (so it cannot be retrofitted):** I expect
rule 2 — no significant difference, with tools costing context but not accuracy.
The smoke instance already shows the shape: same instance, same pack, same patch,
peak context 29.4k with tools vs 9.0k without. If tools are merely redundant we
should see that pattern hold — equal resolve, 3x the context.

I have been wrong twice in two days (I predicted the oracle would falsify at
77-79%; it came in at 85.9%. I proposed Table 6 of the SWE-bench paper as a novel
prediction). This prediction is worth exactly what those were worth.

## What survives regardless of the outcome

The one cell no hunter found in the literature: **a fully-tooled exploring agent
(75.0%) is statistically indistinguishable from a toolless agent handed a plain
BM25 pack (76.1%)** — neither exploration nor retrieval sophistication buys
anything over the crudest possible retriever. That is a negative result, it is
ours, and it needs a **TOST equivalence test at n=500 with a pre-declared margin
(±3pp)** — not a McNemar p-value — before it can be claimed. "p=1.00" at n=92 is
an underpowered null, not an equivalence.

## If the paper dies (rule 3)

Ship the apparatus, not the finding: a toolless pack-injection harness on
SWE-bench Verified with official Docker grading and gold-derived packs is the
only instrument that can SYNTHESIZE arbitrary retrieval quality and measure its
conversion to resolve rate. Nobody can scoop our apparatus; they keep scooping
our findings.
