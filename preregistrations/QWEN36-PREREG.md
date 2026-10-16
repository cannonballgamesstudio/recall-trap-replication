# Pre-registration — Qwen3.6-27B confirmatory replication arm

**Timestamp: 2026-07-17, written BEFORE any Qwen3.6-27B output was generated.**

## What we pre-register
Before generating any `qwen/qwen3.6-27b` output, we pre-register a **confirmatory replication** of the
paper's primary result: **dedup-OFF > dedup-ON at K=12**, paired McNemar exact test, empties-as-failure
(primary), on the identical served packs (`local_packs.json`, n=500), identical harness
(`scripts/eval/local_dedup_ab.py`) and identical official SWE-bench Verified Docker grading. This is a
**direct replication** of the gpt-5.6-sol primary result (ON 39.2% / OFF 46.8%, +7.6pp, McNemar p=0.0003),
not a new hypothesis. Direction, test, and grading are fixed in advance.

## Why this model (the honest justification)
1. **Open-weights reproducibility (lead reason).** Qwen3.6-27B is Apache-2.0. A *powered* arm of the paper
   on open weights can be independently re-run by any reviewer — which the closed gpt-5.6-sol headline can
   never be. This is the primary motivation.
2. **Fills the strong-open point in a capability spectrum.** Existing arms: weak open MoE (Qwen3-Coder-30B-
   A3B, ~7% single-shot resolve, directional) and frontier closed (gpt-5.6-sol, ~47%, +7.6pp). Qwen3.6-27B
   (dense, near-frontier on agentic SWE-bench) fills the missing strong-open middle. The generality claim is
   "does the trap hold across a ~7x resolve-capability range," reported as a fixed-K=12 capability-spectrum
   TABLE — **never fused into a single per-K curve** (one-model-per-curve confound rule).

**Not because a prior arm failed:** the effect was already positive on two models (gpt powered; A3B
directional) before this arm. This is not hunting a first success.

## Decoding (held CONSTANT across ALL arms and K — a confound, not a knob)
- `max_tokens = 16000` (Qwen3.6 allows 131k; 16k gives headroom to avoid the truncation-driven empty
  patches that contaminated the A3B arm — A3B hit its 6000 cap with `fin=length`). Verify `fin=length ≈ 0%`
  on the first ~50 generations; if any truncation, raise uniformly and regenerate affected arms.
- `temperature = 0.2` (matches the paper's existing single-shot protocol).
- **Reasoning: ON** (Qwen3.6-27B is a reasoning model, ON by default on OpenRouter — verified 2026-07-17;
  a trivial probe emitted 4,339 chars of reasoning). Held ON across all arms to match gpt-5.6-sol's
  reasoning nature for a fair capability comparison. Setting identical across every arm.

## Regime
**Single-shot only** (one context pack, no tools, no iteration). We do NOT add an agentic arm: §5.5 already
establishes the effect dissolves under unrestricted Read, and single-shot is the studied fixed-budget
deployment regime (§6.3). We explicitly do **not** claim single-shot resolve reflects Qwen3.6's agentic
ceiling (its 77.2 SWE-bench Verified is an agentic-stack number).

## Reporting commitment
We report **all** generated arms, including nulls (as we already report the A3B K=4 null, +2.0pp p=0.164).
The model post-dates the analysts' training-knowledge cutoff, limiting behavior-conditioned selection.

## Scope (staged, gated on replication)
1. **Stage 1:** K=12 ON/OFF, n=500 — powered replication. Gate: report regardless of outcome.
2. **Stage 2 (only if Stage 1 replicates):** K=4 (token-neutral rescue point) + K=40 (DeepDiscovery
   large-budget crossover). Full 5-K (add K=8/20) only if the resolve×context Pareto figure is promoted to
   a named contribution.

---

## Amendment 1 — 2026-07-17, pre-regeneration (written and committed BEFORE any 32k generation)

**Trigger.** The ON-arm's first 71/500 generations at `max_tokens=16000` showed `fin=length` in 18/71
(25.4%), exceeding the pre-registered decoding gate ("Verify fin=length ≈ 0% on the first ~50 generations;
if any truncation, raise uniformly and regenerate affected arms"). The run was halted at 71.

**Blind diagnostic (finish-reason and reasoning-length only; blind to the ON/OFF resolution contrast — no
resolution-rate-by-arm was computed on the pre-amendment data).** The truncation is **bimodal**, not
budget-starvation. Successful generations (`fin=stop`, patch>0, n=31) finish reasoning at p50=2,754 /
p95=9,217 / max=10,546 chars (~2.6k tokens) — 16k was already ~7x their headroom. Truncated generations
(n=18) are a **disjoint runaway-reasoning population**, `reasoning_len` median 77,457 / max 91,043 chars,
with content=0 in 17/18 (the 18th is a distinct content-runaway: content=64,945 / reasoning=3,605). No
generation occupies the 10.5k–77k-char gap. **The truncated-reasoning lengths are right-censored at the 16k
completion wall; their true lengths are unobserved** — "non-terminating" cannot be asserted from 16k data.

**Change.** `max_tokens` 16000 → 32000, applied uniformly to both arms and all K. Reasoning remains ON;
temperature 0.2 unchanged; no separate reasoning-token cap is introduced. Rationale: (a) satisfies the fired
gate; (b) **de-censors** the truncated tail — generations that self-terminate in the 16k–32k band are
rescued real successes lost only to the wall, while those still generating at 32k are *confirmed*
non-terminators; (c) 32k is >12x the empirical success reasoning-ceiling (10.5k chars), so it is the
**terminal** cap — no would-be success has ever approached it, and budget beyond 32k can only feed confirmed
runaways. The value was set from these decoding/length diagnostics, blind to the ON/OFF resolution contrast.
Cost disclosure: the ~25% runaway tail now runs its output budget toward 32k rather than stopping at the 16k
wall, so tail output roughly doubles; expect the full 500×2 run at ~$25 (vs ~$15 at 16k).

**Data handling.** All 71 pre-amendment (16k) generations are discarded and excluded from analysis
(archived as `*_16k_discarded.jsonl` for provenance). Both arms are regenerated from scratch at 32000.

**Residual truncation.** `fin=length` at 32000 is pre-declared a **capability failure** (runaway reasoning
>12x the success ceiling), counted as failure under the empties-as-failure primary. The earlier
"escalate to 48k if >2%" contingency is **withdrawn**; 32k is terminal — beyond it only confirmed
non-terminators are fed, with zero rescue possible.

**Pre-specified robustness (elevated from backup to primary defense).** Alongside the unchanged primary
(empties-as-failure McNemar): (i) per-arm `fin=length` rate, **split** into reasoning-runaway/content=0 vs
content-runaway; (ii) per-arm **runaway-regime-entry rate** = fraction of gens with `reasoning_len` > 15,000
chars (safely above the 10.5k success ceiling, well below the 77k runaway floor), whether or not truncated —
this catches an arm entering the pathological regime even below the wall; (iii) discordant-pair breakdown by
finish reason (the load-bearing cell: OFF-runaway-empty vs ON-clean-success); (iv) complete-case McNemar
dropping any pair truncated in either arm; (v) Manski-style bounds (truncated-empties as failure vs success).
All (i)–(ii) are computable post-hoc from the logged `raw_*.jsonl` (`finish_reason`, `content_len`,
`reasoning_len`) — no harness change.

**Scope.** Decoding-budget only; identical across arms; sized blind to the outcome contrast; cannot
manufacture the effect direction. Reasoning ON→OFF was considered and **rejected** to preserve comparability
with the gpt-5.6-sol primary claim (a reasoning-tier result) and because a mid-reasoning forced cutoff would
degrade the OFF arm asymmetrically.
