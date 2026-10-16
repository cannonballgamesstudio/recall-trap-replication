> **Note (added for this package).** This protocol was written before the runs but was never committed to version control; the paper treats the sweep as exploratory. It is reproduced below unchanged apart from anonymization; in the authors' repository the file is named `TURNCAP-SWEEP-PREREG.md`.

# Pre-registration — single-model read-budget (turn-cap) sweep (2026-07-16, BEFORE any OpenRouter run)

**Status:** frozen pre-registration. Commit this file before setting `OPENROUTER_API_KEY`.
Executed exactly as written; deviations get a dated amendment appended below, never a silent edit.

---

## 0. Bottom line (read this first)

We convert the paper's three-confounded-point "absorption" curve — single-shot (cap≈1),
one cheap loop, and a *different-model* sonnet free loop — into a **measured decay curve on
ONE fixed model** (qwen/qwen3-coder-30b-a3b-instruct on OpenRouter), the same weak model as
our single-shot Qwen arm. Hypothesis: the composition effect Δ = resolve(dedupOFF) −
resolve(dedupON), in pp, is a **monotone-decreasing function of the model's read budget**,
going from the large single-shot + (≈+5.8pp) to ≈0 at a free loop.

**Cheapest run order that resolves axis-vs-cliff:** run **cap 3 then cap 2 at n=500 first
(≈$3.3 total)**. Those two points, joined to the existing cap=1 single-shot anchor (+5.8pp),
already discriminate the three hypotheses: a clean monotone step-down (5.8 → ~3–4 → ~1–2)
says AXIS and we spend the rest of the budget confirming it reaches 0 (caps 10, 30); a
collapse to Δ≈0 already at cap 2–3 says CLIFF and we stop after one confirmatory high-cap
point; a flat-and-significant Δ out to cap 3 says NOT-absorption and we investigate the
model mismatch instead of buying more caps. Full local weak-model sweep is **≈$14**; the
frontier confirmation arm (**gated**, launched only on a clean monotone local curve) adds
**≈$50–90**. Worst case to a decision is the $3.3 low-cap pair.

---

## 1. Cost estimate (lead)

**Pricing assumption (VERIFY against OpenRouter dashboard on first 10 instances, then lock):**
qwen/qwen3-coder-30b-a3b-instruct blended **$0.15 / 1M tokens** (input-dominated MoE; providers
quote ≈$0.07–0.10/M in, $0.26–0.40/M out — recompute the table below if the measured blended
rate differs by >30%). The harness logs `total_tok` per instance in `raw_*.jsonl`, so the real
cost is reconciled after cap 3 runs and the table is re-scaled before committing to caps 10/30.

Per-instance token model (input accumulates across turns because chat is stateless; peak_ctx
measured ≈4.5k at cap 3 → most instances stop well before the cap, so these are loop-mean, not
worst-case, totals):

| cap | mean total_tok/inst (est.) | $/inst @ $0.15/M | n/arm | arms | **$/cap** |
|----:|---------------------------:|-----------------:|------:|-----:|----------:|
| 2   | 9k   | $0.00135 | 500 | 2 | **$1.35** |
| 3   | 13k  | $0.00195 | 500 | 2 | **$1.95** |
| 5   | 22k  | $0.00330 | 300 | 2 | **$1.98** |
| 10  | 42k  | $0.00630 | 300 | 2 | **$3.78** |
| 30  | 65k  | $0.00975 | 250 | 2 | **$4.88** |

**Local weak-model sweep total ≈ $13.9** (call it **$12–20** with token-estimate variance).
Grading is local Docker (no API cost). cap=1 already exists (single-shot Qwen, n=500) — free.

Frontier confirmation arm (Section 5), **gated**: assume a frontier model at blended ≈$3/M
(≈20× qwen). Endpoints {cap 3, cap 30} at n=150, 2 arms: cap 3 ≈$11.7, cap 30 ≈$45 → **≈$57**;
adding cap 10 (n=150) ≈$31 → **≈$88**. Recommend the 2-endpoint version (~$57).

**Program total: ≈$14 (local) + ≈$57 (frontier, gated) ≈ $71**, but the go/no-go means a CLIFF
or NOT-absorption result stops after ≈$3–8 local and skips the frontier entirely.

---

## 2. Instrument (held fixed)

`scripts/eval/local_agentic_ab.py` — ReAct loop; system prompt offers `READ: path[:a-b]` then
`SEARCH/REPLACE` edits; injects the SAME fixed 12-slot fusion packs from `local_packs.json`
(dedupON mean ≈6002 chars / dedupOFF ≈6318); `--max-turns` sets the cap; `--arm dedupON|dedupOFF`
selects the pack; grades via the official SWE-bench-Verified Docker harness. Logs per instance
in `raw_agentic_<tag>_t<cap>_<arm>.jsonl`: `turns`, `reads`, `finished`, `applied`, `patch_len`,
**`peak_ctx`**, **`total_tok`**.

**OpenRouter adaptation required before run (small, one-time):** `chat_once` currently sends only
`Content-Type`. Add the `--api-key-env`/`--api-model` path so it sends
`Authorization: Bearer $OPENROUTER_API_KEY` and posts to `https://openrouter.ai/api/v1/chat/completions`
with `model=qwen/qwen3-coder-30b-a3b-instruct`. No other loop logic changes — the pack injection,
READ-over-EDIT priority, empty-patch handling, resume dedup, and `force_rmtree` checkout reaping
are held exactly as in the local runs so the OpenRouter cap=N result is comparable to the local
cap=1 single-shot anchor. Set `--model-tag qwen3coder30b_or` to keep OpenRouter preds distinct
from the local files.

Canonical per-cell command (repeat per arm × cap):

```
python scripts/eval/local_agentic_ab.py \
  --arm dedupOFF --max-turns 3 --ids all \
  --endpoint https://openrouter.ai/api/v1 \
  --api-model qwen/qwen3-coder-30b-a3b-instruct \
  --api-key-env OPENROUTER_API_KEY \
  --model-tag qwen3coder30b_or --concurrency 3
```

Held fixed across ALL cells: packs file (`local_packs.json`), model, temperature (0.2),
max_tokens (2000), the 500-id slice (`--ids all`), tools, and the grading harness. **ONLY `--arm`
and `--max-turns` vary.** cap=1 is NOT re-run — it is the existing single-shot Qwen arm (n=500).

---

## 3. Design: caps, n, and per-cap MDE

**Caps to run:** {2, 3, 5, 10, 30}. cap=1 exists as single-shot (the zero-read floor). cap=30 is
the **same-model free endpoint** (see §6 — we do NOT borrow the sonnet null for the trend fit).

**Power model (validated):** exact-McNemar MDE at 80% power, α=0.05, holding the discordant rate
`p_disc`: **MDE₈₀ ≈ 2.8 · √(p_disc / n)**. This reproduces the paper's agentic-fusion sonnet null
(p_disc = 63/499 = 0.126, n=499 → 2.8·√(0.126/499) = 4.45pp ≈ the reported 4.5pp). Single-shot
Qwen had p_disc = 49/500 = 0.098 (disc 39/10) with Δ=+5.8pp. We assume p_disc rises modestly with
cap (loop variance adds discordance), 0.10 at low caps → 0.13 near the free end.

| cap | n/arm | assumed p_disc | **MDE₈₀** | rationale |
|----:|------:|---------------:|----------:|-----------|
| (1) | 500 (have) | 0.098 | 4.0pp | single-shot anchor, Δ+5.8pp observed |
| 2   | 500 | 0.10 | **4.0pp** | decision-critical: is the effect still large one read above zero? |
| 3   | 500 | 0.11 | **4.2pp** | decision-critical + reconciles the partial local cap-3 run |
| 5   | 300 | 0.12 | **5.6pp** | curve shape only; run last / on demand |
| 10  | 300 | 0.13 | **5.8pp** | matches the sonnet free-loop cap; mid-high anchor |
| 30  | 250 | 0.13 | **6.4pp** | same-model free endpoint; trend + sonnet corroborate the null |

**Triage, not uniform n=500.** Low caps (2, 3) get full n=500 because that is where the effect is
expected to still be detectable (≈4–6pp) and where the axis-vs-cliff decision is made — MDE ≈4pp
cleanly separates a real +5.8pp from ~0. High caps expect Δ≈0; their per-cap nulls are looser
(MDE ≈6pp) but the inference there is carried by (a) the pooled **trend test** (§4) and (b) the
external sonnet null (MDE 4.5pp). **Option** if budget allows: raise caps 10 and 30 to n=500
(+≈$5) to tighten both endpoint nulls to ≈4.3pp — recommended only if cap-30 lands in [0, 3pp]
and a tighter bound would strengthen the §5.5 claim.

---

## 4. Analysis (pre-committed)

**Primary per-cap:** RAW paired **McNemar exact** on per-instance resolve outcomes,
**empties = task failure** (consistent with every arm in the paper). Report Δ(pp), discordant
(OFF-wins / ON-wins), raw p, and the conditional (both-non-empty) McNemar as the mechanism
decomposition — never as the headline.

**Primary trend test (the new inference):** the axis claim is a *monotone decay*, tested by
pooling all instance-arm outcomes across caps into a mixed-effects logistic regression:

```
resolve ~ dedup * x  +  (1 | instance)          # x = cap OR measured mean peak_ctx (fit both)
```

The **dedup × x interaction coefficient** is the composition-effect slope. Pre-committed
one-sided test: **interaction < 0** (effect shrinks as budget grows). Report the interaction
coefficient, its 95% CI, and p. Fit x = cap (turns proxy) AND x = log(cap) AND x = measured
per-cap mean `peak_ctx` (the real axis, §6); pre-commit to reporting all three, headline the
peak_ctx fit. As a nonparametric backstop, also report the ordered sequence Δ₁…Δ₃₀ with 95% CIs
and note whether it is monotone non-increasing within CI overlap.

**Decision rules (explicit):**

| pattern of Δ across caps | interaction test | verdict | action |
|---|---|---|---|
| monotone ↓ from +5.8pp, Δ₃₀ CI includes 0 | slope<0, p<0.05 | **AXIS CONFIRMED** | promote to a §5.5 result: absorption capacity is the moderator; single-shot / fixed-budget is the boundary |
| Δ≈0 (CI incl. 0) already by cap 2–3, flat above | slope n.s. or step | **CLIFF** | effect is a single-shot / zero-read phenomenon; report as a sharp regime edge, not a smooth axis |
| Δ flat AND significant (CIs exclude 0) to cap 30 | slope n.s., Δ₃₀≠0 | **NOT absorption** | pack composition binds regardless of reads → contradicts the sonnet null → investigate model mismatch (§6), do NOT claim absorption |

---

## 5. Frontier confirmation arm (gated)

**Purpose:** show the decay is not a weak-model artifact. **Go/no-go gate — launch ONLY if the
local qwen curve is cleanly monotone (AXIS verdict above).** If local is CLIFF or NOT-absorption,
do not spend frontier money; the local result already answers the question.

**Design:** the frontier OpenRouter model used in the paper's headline (gpt-5.6-sol tier), endpoints
**{cap 3, cap 30}, n=150/arm**, same instrument and packs. n=150 gives MDE₈₀ ≈ 2.8·√(0.12/150) ≈
7.9pp — deliberately a *direction* check on the two endpoints (does a strong model show the SAME
big-at-cap-3 → null-at-cap-30 shape the weak model showed), not a powered per-cap test. Add cap 10
(n=150) only if the two endpoints are ambiguous. **Cost line: ≈$57 (2 endpoints) / ≈$88 (3 caps).**
Gate on it explicitly in the run log.

---

## 6. Confounds & hygiene

- **Turns vs context (the real x-axis).** Turns are a proxy; **context is the axis**. `peak_ctx`
  and `total_tok` are logged per instance. Report per-cap-per-arm mean/median `peak_ctx` and mean
  turns-used, and place every Δ on the measured-`peak_ctx` axis, not just the nominal cap. The
  headline trend fit uses peak_ctx (§4).
- **Empties.** A weak model in a tight loop emits many empty patches (and the harness's READ-over-
  EDIT priority can consume a turn on a hallucinated read). **Pre-committed: empties = failure**,
  raw McNemar primary. Report **attempt-rate (non-empty patch %) and turn-cap-hit rate per cap per
  arm** as covariates — breadth (dedupOFF) may burn turns differently from depth, which is a real
  effect to measure, not to hide (this is exactly what corrupted the original agentic arm).
- **Harness behavior held constant.** READ-over-EDIT priority, the compact-READ context storage,
  the 2-reads-per-turn cap, and `force_rmtree` reaping affect absolute rates but are identical
  across arms and caps, so they do not confound the A/B or the trend.
- **Model mismatch to the sonnet free loop.** The existing free-loop null is *sonnet*, a different
  model. It is used ONLY as an external corroboration point plotted separately — **it is NOT a
  point in the trend regression.** The same-model free endpoint is **qwen cap=30**; that is what
  the axis claim rests on.
- **Resume / reap safety.** The harness appends to `preds_*.jsonl`, dedups completed ids on
  restart, and `force_rmtree`s each checkout. Safe to kill and resume any cell. Grading: **sequence
  Docker grading AFTER heavy prediction finishes** (per lab ops: overlapping wedges Docker;
  `wsl --shutdown` to unwedge). Launch sweeps via Task Scheduler for sweep-proof runs.
- **Pre-register before running.** This file is committed before `OPENROUTER_API_KEY` is set; the
  commit hash is the pre-registration timestamp.

---

## 7. Run order, early-stop, and budget

Ranked to reach a verdict fastest and cheapest:

1. **cap 3, both arms, n=500** (≈$1.95). Reconciles the partial local cap-3 run; cheapest
   informative low point. **Reconcile measured `total_tok` against §1 and re-scale the cost table.**
2. **cap 2, both arms, n=500** (≈$1.35). Completes the low-cap pair. → **First decision on {1,2,3}.**
3. **cap 10, both arms, n=300** (≈$3.78). Mid-high anchor at the sonnet cap.
4. **cap 30, both arms, n=250** (≈$4.88). Same-model free endpoint; closes the curve.
5. **cap 5, both arms, n=300** (≈$1.98). Fill the shape ONLY if the trend fit needs the midpoint.

**Early-stop rules:**
- After {1,2,3}: if cap 2 AND cap 3 both show Δ within [−2, +2]pp (CI includes 0) → **CLIFF**;
  skip caps 5/10; run cap 30 at n=150 (≈$3) as a single confirmatory free endpoint, then stop.
  Total ≈ **$6–7**.
- After {1,2,3}: if Δ steps down monotonically (e.g. ≈5.8 → 3–4 → 1–2, low-cap CIs excluding 0)
  → **AXIS looking likely**; proceed to caps 10 and 30 to confirm Δ→0; skip cap 5 unless the
  peak_ctx trend fit is non-monotone and needs the point. Total ≈ **$12–14**, then open the
  frontier gate.
- After {1,2,3}: if Δ stays ≈+5–6pp and significant at cap 3 → **NOT-absorption**; stop buying
  caps, do not open the frontier gate, and open a model-mismatch / harness investigation instead.

**Budget envelope:** local sweep ≈$14 (worst case full 5 caps), ≈$6–7 on an early CLIFF stop;
frontier confirmation ≈$57 (gated on AXIS). Program ≈$14–71 depending on which hypothesis the
data selects, with the axis-vs-cliff fork resolved for ≈$3.3 at caps 2+3.

---

## 8. Amendments

_(none — append dated entries here if execution deviates from the above)_
