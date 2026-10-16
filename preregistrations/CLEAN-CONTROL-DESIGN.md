# Clean-Control Design — pre-registration (adversarial design audit, 2026-07-15)

> Scope: the dedup-OFF (depth) > dedup-ON (breadth) claim at a fixed 12-slot pack
> budget on SWE-bench Verified. Every cell below was verified against the actual
> harness code, prediction files, and grading reports — not the vault's prose.
> Sources: `scripts/eval/swe_bench.py` (run_predict, lines 407–588),
> `scripts/eval/local_dedup_ab.py`, `scripts/eval/prefetch_500.py`,
> `scripts/eval/prefetch_dense_500.py`, `scripts/eval/run_dense500.py`,
> `scripts/eval/g_plane_prompts.py`, `src/ragfusion/fusion/fuse.py::dedup_by_file`,
> `src/ragfusion/retrievald/config.py` (RETRIEVALD_QUERY_DEDUP_FILE), and the
> `preds_*/raw_*/​*.report.json` artifacts under `work/p5/`.

---

## 1. Per-arm confound table (from code, not from memory)

Dedup definition (all arms identical, verified): ON = `dedup_by_file()` keeps the
first-ranked chunk per file, over-fetch backfills to 12 distinct files (breadth,
measured 11.9 files/pack). OFF = raw ranking, multiple chunks per file (depth,
measured 5.3 files/pack). ON served by retrievald :8083 (`dedup_file=True` default),
OFF by :8084 (`RETRIEVALD_QUERY_DEDUP_FILE=0`). Slot budget: `fetch_pack(..., limit=12)`
+ `format_pack(hits, 12)` in every arm — 12 slots everywhere, confirmed.

| arm | generator model | pack construction | regime | slot budget | patch protocol | result |
|---|---|---|---|---|---|---|
| Claude agentic (`g_pack` vs `g_packdepth`) | claude-sonnet-5 (`p5_run_gplane.py --model` default) | FUSION `mode=hybrid` (lex+dense+graph+trigram+prior), live fetch | **AGENTIC**: `PACK_SYSTEM`, `--tools Read,Edit,Write`, `--max-turns 10`; **Read is UNRESTRICTED** (whole repo; only the `trust` arm has the pack-scope hook) | 12 | `git diff` of agent edits | ON 64.9% / OFF 83.2%, **+18.2pp**, n=499, p<1e-4 (n_d=113) |
| gpt-5.6-sol (headline tier gate) | openai/gpt-5.6-sol via OpenRouter | FUSION `mode=hybrid`, prefetched `local_packs.json` (`prefetch_500.py`) | **SINGLE-SHOT**: one chat completion, no tools, aider SEARCH/REPLACE `SYS`, temp 0.2, max_tokens 6000 | 12 | parse blocks → apply → `git diff` | ON 196 / OFF 234, **+7.6pp**, n=500, p=0.0003 (n_d=108: 73 OFF-only / 35 ON-only) |
| dense-500 | claude-sonnet-5 (`run_dense500.py MODEL`) | **DENSE-only** `mode=semantic` (plain cosine), prefetched `kpack_dense500_{ON,OFF}.json` | **AGENTIC**: `--g-plane packfile` = identical policy to `g_pack` (PACK_SYSTEM, Read/Edit/Write, 10 turns, Read unrestricted) | 12 | `git diff` | ON 335 / OFF 326, **−1.8pp**, p≈0.23 (n_d=45: 27 ON-only / 18 OFF-only; ON submitted 499/500) |
| DeepSeek-V4 (in flight) | deepseek/deepseek-v4-pro via OpenRouter | FUSION, same `local_packs.json` bytes as gpt | SINGLE-SHOT, max_tokens 16000, reason-cap 2000 | 12 | blocks → apply → diff | pending; **empty-rate asymmetry ON 45.9% / OFF 39.8%** |
| Qwen3-Coder-30B (in flight) | local llama-server :8090 | FUSION, same `local_packs.json` | SINGLE-SHOT, max_tokens 6000 | 12 | blocks → apply → diff | pending; empties 43.6% / 42.4% (symmetric) |

**The crux.** dense-500 differs from the gpt-5.6-sol headline in **three variables
simultaneously**: (1) generator model (claude-sonnet-5 vs gpt-5.6-sol), (2) pack
construction (dense-only vs fusion), (3) regime AND patch protocol (10-turn
Read/Edit/Write agent + git diff vs single-shot no-tools SEARCH/REPLACE). Its null
is therefore uninterpretable **against the single-shot headline**. It differs from
the Claude AGENTIC result in exactly ONE variable (pack construction) — see §4 for
what that does and does not license.

**Audit findings beyond the suspected confound (must be disclosed):**

- **F1 — "fixed budget" is only enforced in single-shot arms.** In `pack`/`packfile`
  arms, Read is registered and unscoped: the agent can open ANY repo file. The
  12-slot budget is advisory (prompt-discouraged), not structural. A breadth pack
  hands the agent 12 file pointers it can convert to depth by Reading — a mechanism
  that *predicts* attenuation of the dedup effect in agentic arms and is consistent
  with dense-500's low discordance (9.0% vs gpt's 21.6%) and high both-resolve
  agreement (308/500). The single-shot arms are the only true test of the thesis.
- **F2 — pack-size claim in the vault is wrong at pack level.** Measured mean pack
  chars: fusion ON 6002 / OFF 6318 (+5.3% OFF); dense ON 5492 / OFF 5825 (+6.1% OFF).
  Depth packs are slightly LARGER, not smaller — CONTEXT-VAULT §6's "token confound
  inverted in our favor (depth used FEWER tokens)" must be corrected or re-scoped to
  peak agent context. Direction of concern: OFF's advantage could partially be a
  +5–6% content-budget advantage. Handle as covariate (§3.C1).
- **F3 — DeepSeek empty-rate asymmetry (45.9% vs 39.8%) is in the effect's
  direction.** With empties counted as failures, ~6pp of any DeepSeek delta could be
  protocol artifact (reasoning-token wall), not context quality. gpt is clean
  (14.0% / 13.2%); the headline is not materially threatened, but DeepSeek cannot be
  reported unconditionally (§3.C2).
- **F4 — the manipulation check passes everywhere** (fusion 11.9 vs 5.3 files/pack;
  dense 11.9 vs 5.3; 12 slots in all four packfiles), so no arm is a null-by-broken-knob.

---

## 2. The #1 clean control (pre-registered)

### CC-1: gpt-5.6-sol, single-shot, DENSE-only packs, dedup ON vs OFF, n=500

*The corrected version of what dense-500 was supposed to be.*

- **Held fixed:** generator model (openai/gpt-5.6-sol), regime (single-shot
  OpenRouter, no tools, aider SEARCH/REPLACE, temp 0.2, max_tokens 6000), slot
  budget (12), dedup semantics, grading (official Docker, empties=failures),
  instance set (all 500 Verified), even the exact pack BYTES — reuse
  `kpack_dense500_{ON,OFF}.json` unchanged, so this cell shares packs with the
  agentic dense-500 run and shares model+regime with the gpt headline.
- **Varied (the ONE factor):** pack construction — dense-only vs the headline's
  fusion. Read directly against the gpt fusion cells already graded.
- **Hypotheses and predictions, stated before the run:**
  - **H1 (depth>breadth is a general fixed-budget property of semantic retrieval):**
    Δ_dense(gpt, single-shot) > 0, McNemar exact two-sided p<0.05; expected
    magnitude +4 to +8pp. Then the dense-500 null is attributed to the agentic
    regime's soft budget (F1) and/or model, and the paper's general claim stands
    with the agentic cells demoted to a robustness footnote.
  - **H0 (effect is fusion-pack-specific):** Δ ≈ 0 with the 95% CI excluding +5.7pp.
    Then the claim NARROWS to multi-signal fusion retrieval; the mechanism section
    must drop generic "depth surfaces gold lines → resolves" causation (already
    wounded by the coverage-decoupling finding: dense-OFF raises gold-line coverage
    +0.086 ≈ fusion's +0.105 with no resolve gain) and pursue the composition story —
    fusion-ON's breadth slots are cross-signal DIVERSE files (true distractors),
    dense-ON's breadth slots are semantic near-neighbors (benign).
- **n and power.** n=500 (the full benchmark; n is capped — no more instances exist,
  and multi-seed pooling is out of scope). Power arithmetic from the observed gpt
  discordance model: to detect +7.6pp at 80% power (two-sided α=0.05) with the gpt
  arm's conditional split c/(b+c)=0.676, McNemar needs ≈61 discordant pairs, i.e.
  n≈285 at the observed 21.6% discordance → at n=500 (expected n_d≈108) power ≈96%.
  If dense discordance is lower (agentic dense showed 9.0%; assume it transfers
  worst-case), n_d≈45 still gives MDE@80% ≈ +3.7pp. Blended planning MDE@80%:
  **≈ +5.7pp at n_d≈108; ≈ +3.7pp at n_d≈45** — adequate against a +7.6pp target
  either way. A half-size effect (+3.8pp) has only ~50% power at n_d≈108: therefore
  the decision rule below uses an explicit CI bound instead of treating p>0.05 as
  "no effect."
- **Decision rule (binding):**
  1. p<0.05 and Δ>0 → H1; report dense as replicating; retriever-generality claim
     restored (within semantic retrievers; BM25 remains a disclosed null).
  2. p≥0.05 and 95% CI for Δ excludes +5.7pp → H0; narrow the claim to fusion packs;
     rewrite mechanism per above.
  3. p≥0.05 and CI includes +5.7pp → underpowered/ambiguous; report as such,
     claim stays scoped to fusion packs (conservative default).
  4. p<0.05 and Δ<0 → reversal; strong fusion-specificity; report prominently.
- **Mandatory covariate reporting:** per-arm empty rate and SEARCH/REPLACE
  apply-rate; McNemar sensitivity restricted to pairs non-empty in BOTH arms;
  per-arm mean pack chars (F2).
- **Engineering note:** `local_dedup_ab.py` expects
  `packs[iid][arm] = {"pack","files"}`; `kpack_dense500_*.json` stores bare pack
  strings. Write a ~20-line adapter that derives `files` by parsing the
  `### <path>:<line>` headers (regex `^### (.+?):\d`) — do NOT refetch, so the pack
  bytes stay identical to the agentic dense-500 run. Cost ≈ 1,000 OpenRouter calls.

---

## 3. Runner-up controls, ranked

- **R1 — Claude-sonnet-5, single-shot, FUSION packs, n=500 (already planned,
  currently paused — RESUME).** Holds pack+regime fixed at the headline spec,
  varies model. Buys two things at once: (a) the regimen-consistent cross-model
  table (Claude / gpt / DeepSeek / Qwen all single-shot fusion) that §10.B of the
  vault already demands; (b) paired with the existing Claude AGENTIC +18.2pp, it
  isolates the REGIME factor within (Claude, fusion) — the only clean regime
  contrast available, since the `claude` CLI cannot drive gpt agentically.
- **R2 — finish DeepSeek-V4 and Qwen3 n=500 (in flight).** These are the model
  controls (pack+regime held). Pre-commit: DeepSeek is reportable unconditionally
  only if its per-arm empty rates converge to within 3pp; otherwise report the
  both-nonempty conditional McNemar as primary for that model and the
  unconditional as sensitivity, plus a `finish_reason` audit from
  `raw_local_dsv4_*.jsonl`. Qwen already symmetric — no special handling.
- **R3 — Claude-sonnet-5, single-shot, DENSE packs, n=500.** Completes the 2×2
  (model × pack) within single-shot. Run ONLY if CC-1 and R1 disagree in sign or
  significance — otherwise it adds a multiplicity hit for no inferential gain.
- **R4 — covariate analyses (no new runs; required in Methods regardless):**
  - C1 pack-size: report Δ within pack-chars-matched strata (or logistic model with
    pack_chars covariate) to bound the +5–6% OFF size advantage (F2).
  - C2 editable-surface/anchor-leakage: in the SEARCH/REPLACE protocol, depth packs
    provide more verbatim gold-file text to anchor edits — the effect could be
    "more copyable lines," not "better understanding." Bound it with: per-arm
    apply-rate, resolve conditional on ≥1 applied edit, and resolve conditional on
    gold-file-in-pack. If OFF's advantage survives conditioning, the artifact
    reading is bounded out; a dedicated protocol control (full-function rewrite) is
    NOT justified unless conditioning is ambiguous.
  - C3 contamination: the paired design nets out instance-level memorization except
    for the interaction "depth shows more gold-file text → better trigger for a
    memorized fix." No cheap clean control exists on Verified; handle as (i) a
    named limitation, (ii) repo-stratified deltas (memorization should be
    repo-uneven), (iii) the swebench-ml held-out second benchmark as the real
    robustness answer (nice-to-have tier, unchanged).

---

## 4. What the dense-500 null does and does NOT license

**Licenses:**
- Within (claude-sonnet-5, agentic `packfile` regime, 12-slot soft budget): the
  dedup toggle on DENSE-only packs produces no detectable effect (−1.8pp,
  n_d=45, MDE@80% ≈ 3.7pp — a genuinely powered null *in that cell*, not the
  information-free 6-discordant n=100 version).
- Combined with the same-model same-regime fusion result (+18.2pp): **in the
  agentic regime, the dedup effect requires the fusion pack composition.** That
  contrast is single-variable and is the one legitimate use of dense-500.

**Does NOT license:**
- Any statement about the single-shot headline (gpt +7.6pp): model, regime, and
  protocol all differ. "Dense null → effect isn't about retrieval breadth" is
  unavailable until CC-1 runs.
- "The effect is model-specific" or "regime-specific" — those factors were never
  isolated.
- Even the agentic-scoped inference carries F1: with unrestricted Read, the agentic
  cells do not test the paper's fixed-budget thesis at all; they test a soft-budget
  variant where the agent can buy back depth. The agentic numbers should be
  re-labeled "soft-budget agentic robustness," and the fixed-budget claim should
  rest exclusively on single-shot cells.

**Multiplicity note:** CC-1 + R1 + R2 add four confirmatory tests to the program
ledger (7 prior hypotheses). Report all McNemar p-values exactly and state the
family; the headline gate (p=0.0003) survives any reasonable correction, the new
cells must be interpreted with that context.
