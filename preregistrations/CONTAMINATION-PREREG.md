# Pre-registration: Contamination check (Branch B memorization-stratified test; Branch A post-cutoff arm)

Status: PRE-REGISTRATION (draft for owner review). Written 2026-10-14. At the time of writing, no
probe call, no pack prefetch, no generation, and no grading has been run for either branch. Commit
this file and record the commit hash before the first model call of either branch. Do not edit the
probes, the scoring rule, the estimands, or the decision rules after that point. Put deviations in
the dated log in §E.

Design authority: methodology review of 2026-10-13/14 (the AI4SE reviewer's contamination objection:
memorized fixes plus extra same-file anchor text could produce the effect; gpt is flat on PolyBench
Python, −1.3pp, but +7.6pp on Verified). Branch A as reconciled on 2026-10-14.

Relation between the branches (binding):
- **Branch B is primary.** It stratifies the *existing* graded Verified arms by a per-instance
  memorization score M measured on the same model.
- **Branch A is descriptive.** It is a sign-consistency check on post-cutoff data. It has no N floor.
- **A is never pooled with B.** No estimand combines instances, draws, or p-values across branches.
- **The paper's contamination section is carried by B's E1/E2.** A is reported alongside, as its own
  table, with its own label (§A.8).

---

# Branch B (primary): memorization-stratified test on the existing Verified arms

## B.1 Question

Does the dedup-OFF > dedup-ON effect (fixed 12-slot pack, single-shot, SEARCH/REPLACE) survive on
instances where the model shows no measurable memorization of the issue's repository, files, or fix?
If the effect were produced by memorized fixes being unlocked by extra same-file anchor text, it should
shrink toward zero among unmemorized (Low-M) instances, and be larger among memorized ones.

## B.2 Probes (exact)

Common settings for every probe:
- Issue-only. No retrieved code is shown, except the 8 pre-image lines that P3 is defined on.
- Same model as the arm being stratified (§B.6 E5 for the local models).
- Temperature 0. One sample per (probe, instance). No retries except on transport errors (HTTP
  failure or timeout). A transport retry re-issues the identical request.
- Completion budget: gpt-5.6-sol `max_tokens = 6000` (the headline budget). Qwen3.6-27B 32000, with
  reasoning ON (that arm's Amendment-1 budget). Qwen3-Coder-30B uses the budget recorded for its arms;
  this is `local_dedup_ab.py`'s default of 6000 unless the run record shows otherwise. Confirm it from the
  record before launch.
- The issue text is `problem_statement[:6000]`, the same truncation the headline harness uses.
- Raw responses are logged in full: `content`, `reasoning`, `finish_reason`, `usage` (including
  OpenRouter `cost`), and the served `model`/`provider`. They go to
  `data/memorization-branchB/raw_{P1,P2,P3}_{tag}.jsonl`.
- gpt-5.6-sol is called through OpenRouter (`openai/gpt-5.6-sol`, `https://openrouter.ai/api/v1`), the
  same slug and provider as both headline draws. If the provider ignores `temperature` for this
  reasoning model, the run is still one sample per item, and this is disclosed.

The canonical source of every string below is `scripts/eval/contam_common.py`. The text here is copied
from it verbatim. `{…}` marks a substituted field.

**Probe system prompt (P1 and P3):**

```
You are an expert software engineer who knows the source code of popular open-source Python repositories.
```

### P1: file-path identification

Input: the repo name plus `problem_statement`. No code. User turn:

```
Repository: {repo}

## Issue
{issue}

Without seeing any code, list the files in this repository that would most likely need to be edited to resolve the issue. Output at most 3 repository-relative file paths, one per line, most likely first. Output only the paths, with no other text.
```

Parsing (`parse_p1`) reads `content` only. Backticks and quotes are removed. The first path-like
token (`[\w.\-/\\]+\.\w+`) on each line is taken, so bullets and numbering are ignored. Paths are
normalized (`\` → `/`, leading `./` stripped). Duplicates are dropped. The first 3 are kept.

Hit (`score_p1`): `p1_hit = 1` iff some predicted path equals a gold file path, or ends with `/` +
gold path. The suffix clause tolerates a leading repo-name or checkout-directory prefix. Gold files are
the `a/` paths of the gold patch's `diff --git` headers. Basename matches are reported separately as
`p1_base_hit`. They are not part of M.

**P1 is NA on 133 instances**: those whose issue already contains a gold-file basename. Rule, written
down: P1 is NA for instance *i* iff any gold-file basename (the last `/`-separated component, extension
included) occurs as a case-sensitive plain substring of the **full** `problem_statement`. Code:
`contam_common.p1_filtered`. The list is in `docs/paper/CONTAMINATION-P1-FILTER.txt` (sha256 of the id
list `54d482893df8ec079994447d6e96cffd16dd2b466e3ad0f5491609295ddc66a2`). It matches the design
authority's side table (`issue_names_gold.json`, field `base`) exactly: 133 True, 0 disagreements.
None of the 133 match only beyond the 6000-character truncation. P1 is therefore called on
367 instances.

### P2: no-context patch

The system prompt is the headline harness system prompt `local_dedup_ab.SYS`, **byte-for-byte**. The
pack is removed from the user turn, and the sentence the design specifies is added in its place. User turn:

```
Repository: {repo}

You are given no code; write the fix from your knowledge of this repository.

## Issue
{issue}

Emit the SEARCH/REPLACE edits.
```

(Headline user turn for comparison: `{pack}\n\n## Issue\n{issue}\n\nEmit the SEARCH/REPLACE edits.`)

Application follows the headline harness:
- base_commit checkout via `swe_bench.cache_clone` / `prepare_checkout`.
- Parse `content`, falling back to `content + reasoning` when `content` has no block (the headline rule).
- `local_dedup_ab.apply_edits(co, text, known)` with `known = git ls-files` of the checkout. The headline
  passes the pack's files as `known`; with no pack, the full tracked-file list lets the same
  longest-suffix path resolver work, and it carries no gold information.
- `git diff` gives the prediction, which is written to `preds_P2_{tag}.jsonl` and Docker-graded with the
  same SWE-bench harness and images as the headline.
- Scores: `P2_apply = 1` iff ≥ 1 block applied. `P2_resolve` = resolved by the grader.

### P3: pre-image continuation

Input: the gold file path plus the 8 lines before the first gold hunk. Exact construction
(`first_change_line`, `p3_split`):
- Take the first gold file **with a pre-image**, in patch order.
- In its first hunk, L = the pre-image line number of the first changed line: a `-` line, or the
  insertion point of a `+` line.
- prefix = pre-image lines [L−8, L−1], clipped at 1.
- target = pre-image lines [L, L+7].
- Lines are read with `git show {base_commit}:{path}` from the full, non-partial clones
  `<EVAL_ROOT>/swebench/<slug>__idx`. This is read-only and does not fetch.
- P3 is NA if the prefix is empty or the target has fewer than 5 tokens. This applies to 1 instance.

The frozen inputs (prefix and target per instance) are in
`data/memorization-branchB/p3_inputs.json`: 499 eligible, 1 NA, sha256
`d59d4fd380fb42d0afaab3e48f6013ad025fef9a702c641f8674c48a7b0bcb2e`. User turn:

```
Repository: {repo}
File: {path}

Below are {n} consecutive lines from this file. Output the next 8 lines of the file exactly as they appear in the file. Output only those 8 lines, with no explanation and no code fences.

{prefix}
```

(`{n}` = number of prefix lines, 8 unless clipped at the top of the file. `{prefix}` = the lines joined
with `\n`.)

Score (`score_p3`):
- Strip a leading code fence and anything from a later fence onward.
- Keep as many generated lines as the target has (≤ 8).
- Tokenize both texts with `\w+|[^\w\s]`.
- `p3_overlap` = clipped 5-gram recall of the target:
  Σ_g min(count_target(g), count_gen(g)) / (number of target 5-grams).
- `P3 = 1` iff `p3_overlap ≥ 0.5`. The continuous value is kept for analysis.

### Logprob scoring (secondary, local models only)

Logprob scoring is infeasible for gpt. For the local models only, a secondary continuous memorization
measure is the mean per-token log-likelihood of the P3 target given the P3 prompt, under teacher
forcing on the local llama.cpp server. If the serving stack cannot return prompt-token log-probs, the
secondary is reported as **not computed** (logged in §E). No substitute measure is used. It never
enters M.

### PolyBench Python extension (P1, P3)

P1 and P3 are also run on gpt-5.6-sol for the 125 SWE-PolyBench Python instances (served packs at <EVAL_ROOT>/polybench/polybench_packs.json; gold from the HF test.csv), producing M_poly with the same rules (P1 filter recomputed for PolyBench). Pre-registered prediction under the memorization account: the P1 hit rate and High-M share are markedly lower on PolyBench Python than on Verified. Under the comprehension account there is no prediction about M; the B→C contrast on PolyBench should be positive. M_poly is reported as a probe-validity contrast and never pooled with Verified estimands.

Fund it under the §B.11 tiers below. P2 is not run on PolyBench.

## B.3 Scoring code path

All of the following are new files, and none makes any call when imported. This was verified by
importing every `contam_*.py` with sockets, `urlopen` and `subprocess` patched to raise: 0 calls and 0
files written.

| step | script | reads | writes |
|---|---|---|---|
| frozen inputs | `scripts/eval/contam_prep.py p1-filter`, `p3-inputs` | gold patches, Verified instances, full clones (read-only) | `CONTAMINATION-P1-FILTER.txt`, `contam/p3_inputs.json` |
| probes | `scripts/eval/contam_probe.py usage-probe` / `run --probe P1|P2|P3` | prompts from `contam_common.py` | `contam/raw_P*_{tag}.jsonl`, `contam/preds_P2_{tag}.jsonl`, `contam/usage_probe_tier{N}.json` |
| P2 grading | the headline SWE-bench Docker harness, unchanged | `preds_P2_{tag}.jsonl` | report JSON |
| M table | `scripts/eval/contam_score.py m-table --tag {tag} --p2-report …` | raw probe logs + P2 report **only** (never an arm outcome) | `contam/M_table_{tag}.json` + printed SHA-256 + probe-validity report |
| join | `scripts/eval/contam_score.py join --family gpt|qwen36|qwen3coder --tag {tag}` | M table, graded arm reports, served packs | `contam/join_{family}_{tag}.json` |
| free secondaries | `scripts/eval/contam_secondary.py` | graded reports, packs, gold | `contam/secondary.json` |

Shared helpers are in `scripts/eval/contam_common.py`: prompts, parsers, scorers, the A/B/C anchor
classifier (identical to the design authority's `strat_abc.py`), and the arm-to-report map.

`join` **refuses to run** unless the M table's SHA-256 occurs in a committed revision of this file
(`git log --all -S<sha> -- docs/paper/CONTAMINATION-PREREG.md`). This enforces the blinding rule
mechanically. A `--unblinded-test` flag exists for plumbing tests. Its output is labelled not
reportable and is never cited.

## B.4 Memorization score M

`M = [P1 hit] + [P2_apply] + [P3 ≥ 0.5]`, range 0–3, summed over the probes that are available for the
instance:
- **NA probes contribute nothing.** P1 is NA on the 133 filtered instances, and P3 is NA on 1.
- `n_avail` records how many probes M is computed over.
- **Low-M** = M = 0, i.e. every available probe is negative. **High-M** = M ≥ 1.
- The ordinal M is kept, and each probe is also reported alone (positive vs negative stratum, and their
  interaction), per §B.6.
- **Sensitivity S1:** E1 restricted to the 367 P1-eligible instances, where all three probes are
  available.

M is computed per model:
- gpt-5.6-sol M stratifies the two gpt draws.
- Qwen3.6-27B M (OpenRouter, `qwen/qwen3.6-27b`) stratifies its K = 4/12/40 arms.
- Qwen3-Coder-30B OpenRouter M stratifies its K = 4/12/40 arms. Local-GGUF M stratifies the local
  reference pair and Arm T (§B.12, ruling 5).

## B.5 Probe-validity report (reported first; not a gate)

The following are reported before any join:
- the P1 hit rate on the eligible instances, against the published 60–76% band for file-path
  identification on Verified, as given by the design authority (the "SWE-Bench Illusion" line of work,
  arXiv 2506.12286; the citation is checked before the paper uses it);
- the P1 basename-hit rate;
- the P2_apply and P2_resolve rates;
- the P3 positive rate and the distribution of the continuous overlap;
- the M distribution and the Low-M share;
- the P1 hit rate and High-M share on PolyBench Python beside Verified's (E4 extension).

A P1 hit rate **below 30% is disclosed as weak probe validity**. It does not stop the analysis.

## B.6 Estimands

Common rules:
- Paired contrast d = 1[OFF resolved] − 1[ON resolved].
- Pairwise-attempted instances only: never-submitted pairs are excluded, per §4.6 of the paper.
- Instance-clustered bootstrap: resample instances with replacement, and all draws of an instance move
  together. B = 10,000, seed 20261014.
- One-sided p (H1: θ > 0) = (1 + #{θ*−θ̂ ≥ θ̂}) / (B + 1). This is the null-centred bootstrap.
- Code: `contam_score.analyse`.

- **E1 (co-primary): Δ_low**
  - Definition: OFF − ON within Low-M, gpt-5.6-sol.
  - Draws: the headline draw (`local_gpt56sol_dedup{ON,OFF}`) and the logged re-run draw
    (`gptsol_logrep_dedup{ON,OFF}`) are pooled.
  - Inference: instance-clustered bootstrap. Sensitivity: Webb wild-cluster bootstrap-t by repository
    (6-point weights, G = 12, null imposed, CR1 variance, B = 9,999).
  - Test: one-sided H1 Δ_low > 0.
- **E2 (co-primary): Δ_low within B→C.**
  - B→C means the OFF pack supplies the gold pre-image lines and the ON pack does not. Formally, the ON
    pack's anchor class is B (gold file present, some gold lines uncovered) and the OFF pack's class is C
    (every gold file has a chunk overlapping its gold lines).
  - Classes are computed on the served K = 12 packs (`local_packs.json`) by `contam_common.anchor_class`.
    This reproduces the side table `class_abc_500.json` on 500/500 instances. B→C has n = 80.
  - Same draws, bootstrap and one-sided test as E1.
- **E3: interaction Δ_high − Δ_low**
  - Computed on the full sample and within B→C.
  - Instance-clustered bootstrap. Reported one-sided for the decision rule (H1: Δ_high > Δ_low), with a
    95% CI.
- **E4: trend of Δ across M = 0, 1, 2, 3.**
  - OLS slope of the per-instance mean d (averaged over draws) on M.
  - Primary: on the P1-eligible instances, which have the full 0–3 range. Secondary: on all instances,
    with NA counted as 0.
  - Bootstrap 95% CI and two-sided p. Per-level Δ reported.
- **E5: cross-model**
  - Arms:
    - Qwen3.6-27B K = 4/12/40;
    - Qwen3-Coder-30B K = 4/12/40;
    - Arm T, reported as OFF−T and T−ON against the local Qwen3-Coder-30B reference pair.
  - Each arm uses M measured on the stack that served it (§B.12, ruling 5). The primary E5 cell is the
    local T triple (local reference ON, local reference OFF, Arm T) with local-GGUF M.
  - For each arm, report Δ_low, Δ_high, the interaction, S1 and E4.
  - B→C is not computed for the K = 4/40 arms, because their packs differ from the K = 12 packs the
    classes are defined on.
  - E5 is reported, not decided.

Reference values at registration (already public, outcome-visible). Δ is OFF − ON on pairwise-attempted
instances:

| arm | n | Δ |
|---|---|---|
| gpt headline | 500 | +7.6pp |
| gpt logged re-run | 500 | +5.4pp |
| Qwen3.6 K=4 | 466 | +4.94pp |
| Qwen3.6 K=12 | 499 | +3.61pp |
| Qwen3.6 K=40 | 457 | +10.07pp |
| Qwen3-Coder K=4 | 500 | +2.0pp |
| Qwen3-Coder K=12 | 500 | +4.2pp |
| Qwen3-Coder K=40 | 500 | +6.2pp |
| Qwen3-Coder T: OFF−T | 473 | +9.94pp |
| Qwen3-Coder T: T−ON | 473 | −4.02pp |

- **Δ_ref** (the pooled gpt full-sample Δ on the same instances) is ≈ +6.5pp on all 500. It is
  recomputed on the instances with a defined M at join time.

## B.7 Decision rules (fixed now)

Δ_ref = pooled gpt full-sample Δ on the same instances (§B.6).

- **"Effect survives in unmemorized instances"** iff all three hold:
  - E1 one-sided p < 0.05;
  - point(Δ_low) ≥ 0.5·Δ_ref;
  - E2 one-sided p < 0.05.
- **"Measured memorization explains the effect"** iff both hold:
  - point(Δ_low) ≤ 0.25·Δ_ref;
  - E3 one-sided p < 0.05, on the full sample or within B→C.
- **Otherwise: inconclusive.**

The Webb wild-cluster p is reported beside E1 as a sensitivity. It does not enter the rule.

**Wording rule.** The strongest permitted wording is "not explained by measured memorization". The
words "refute" and "contamination-free" are not used anywhere. Under "survives", the paper says the
effect is present among instances with no measured memorization. It does not say memorization is
absent.

## B.8 Power (stated assumptions)

Assumptions:
- Low-M share ≈ 35%;
- discordance (P(d ≠ 0)) 0.20 on the full sample and 0.30 within B→C;
- two draws per instance with intra-instance correlation ≈ 0.4, so the effective number of pairs is
  2n/(1+ρ);
- one-sided α = 0.05.

| estimand | n | power |
|---|---|---|
| E1 | n_low ≈ 175 | MDE80 ≈ 7.3pp; ≈ 65% at 6pp |
| E2 | n ≈ 28 (35% of 80) | ≈ 88% at 25pp |
| E3 | full sample | ≈ 30% |

The design authority's values are taken as binding. A normal-approximation check
(SE = √(p_d / n_eff)) gives:
- E1: MDE80 ≈ 7.0pp and ≈ 68% power at 6pp.
- E2: ≈ 89% power at 25pp.

Both agree within rounding. E3 is underpowered by construction. Its role in the decision rule is only to
license the "explains" label when Δ_low has already collapsed.

## B.9 Blinding and order of operations

Each step must be complete before the next begins.

1. This file, `CONTAMINATION-P1-FILTER.txt`, and all `scripts/eval/contam_*.py` are committed **before
   any call**. The prompts are frozen in that commit.
2. Run the 10-call usage probe (§B.11). Then wait for owner approval of the projection.
3. Run P1, P2 and P3 on gpt-5.6-sol; the OpenRouter open-model probes per approved tiers; the local-GGUF probes for the locally served arms (free).
4. Docker-grade P2.
5. `contam_score.py m-table` for each model. Report the probe-validity report.
6. **Commit the SHA-256 of each M table**, appended to §E, before any join. `join` enforces this.
7. `join`. Report all estimands and the decision label.

## B.10 Free secondary analyses (reported regardless)

These were computed at registration from already-graded, already-seen data by
`contam_secondary.py`. They are reproduced here and are not outcome-blind.

1. **Anchor-transition table.** Δ within the B→C transition, n = 80:

   | arm | Δ | b/c | McNemar p |
   |---|---|---|---|
   | gpt headline | +26.2pp | 23/2 | 1.9e-5 |
   | gpt logged re-run | +25.0pp | 23/3 | 8.8e-5 |
   | Qwen3.6-27B K=12 | +26.2pp | 22/1 | 5.7e-6 |
   | Qwen3-Coder-30B K=12 | +31.2pp | 26/1 | 4.2e-7 |

   This is the +25 to +31pp band across the four K = 12 arms. The full transition × arm table, with the
   B→B, A→A, B→A, C→C rows, goes in the paper.

2. **Verbatim-gold table.**
   - Population: OFF-only wins (pairwise attempted) whose gold patch has ≥ 3 non-empty `+` lines,
     pooled over the two gpt draws.
   - Rule: "reproduces gold" means the model patch's ordered list of non-empty, stripped `+` lines equals
     the gold patch's.
   - Result: **3/89** (headline 2/45, re-run 1/44). Instances: django-13568 (headline), django-14765
     (both draws).

3. **PolyBench Python B→C prevalence**, computed from the served SWE-PolyBench_500 packs
   (`<EVAL_ROOT>/polybench/polybench_packs.json`) with the same classifier and the HF `test.csv` gold
   patches: **24/125 = 19.2%**, vs Verified 80/500 = 16.0%. This is reported as context for the flat
   gpt PolyBench-Python result.

4. Δ within PolyBench-Python B→C (24 instances, of which 18 are in the graded survivor sets; computed on those 18) for gpt-5.6-sol and Qwen3-Coder-30B, with b/c and McNemar p, computed by contam_secondary.py from the graded PolyBench reports.

## B.11 Cost gate (tiers)

The single $50 gate is replaced with tiers. Each tier has its own usage probe and owner approval. If the total projection must be cut, cut in this priority order:
- Tier 1: gpt Verified probes P1/P2/P3, ≤ $50, mandatory.
- Tier 2: Qwen3.6-27B OpenRouter probes, ≤ $15.
- Tier 3: gpt PolyBench P1+P3, ≤ $15 (if cut, P1 only).
- Tier 4: Qwen3-Coder-30B OpenRouter probes, ≤ $10 (if cut, local-GGUF proxy M per ruling 5).

Running guard per tier. Total ceiling $90, owner's call. The design is valid at Tier 1 alone.

Mechanics (`contam_probe.py --tier N`), applied per tier:
- **Usage probe first.** `usage-probe --tier N` makes exactly 10 calls: P1 × 3, P2 × 4, P3 × 3 for the
  Verified tiers (1, 2, 4); P1 × 5, P3 × 5 for Tier 3. Instances are picked by lowest
  sha256(`20261014:{probe}:{iid}`), which is outcome-blind.
- **Projection.** Mean cost per call, per probe, × calls per probe (Verified: P1 367, P2 500, P3 499;
  PolyBench: the PolyBench P1-eligible and P3-eligible counts).
- **Approval.** `run --tier N` refuses a paid run unless that tier's projection is ≤ its cap and
  `--approved-usd ≥ projection` is passed after the owner approves.
- **Running guard.** A cumulative guard halts at the tier's cap, summed over all of that tier's probe logs
  including its usage probe.
- **Usage-probe responses** are logged and are not used in any analysis. The main run re-issues those
  items.
- Locally served (free) probes run without a tier.

## B.12 Threats

- **The probes measure *elicitable* memorization only.** Low-M is "no measured memorization", not "no
  memorization". This is why the wording rule (§B.7) applies.
- **Probe settings differ from the arms.** The probes run at temperature 0. The arms ran at temperature
  0.2. Probe prompts differ from the task prompt by design.
- **The P1 filter makes M's range depend on the instance.** The 133 filtered instances have M over 2
  probes. S1 and the P1-eligible E4 address this.
- M is measured on the stack that served the arm. OpenRouter-served arms (Qwen3.6-27B K=4/12/40 via qwen/qwen3.6-27b; Qwen3-Coder-30B K=4/12/40 via its OpenRouter slug) get OpenRouter-measured M at the same slug. Locally served arms (the Qwen3-Coder-30B reference pair and Arm T) get M measured on the local UD-Q5_K_XL GGUF. If the budget tier for the OpenRouter open-model probes is not approved, the local-GGUF M is used for the OpenRouter arms and labelled 'proxy M' in every table.
- **B→C is defined on served packs** and is a post-treatment property of the pair. It is used as a
  stratum, never as a mediator.

---

# Branch A (descriptive): post-cutoff sign-consistency arm

## A.1 Purpose

This is a descriptive check: does the sign of OFF − ON on tasks created after the model's training
cutoff match the Verified sign? It is not confirmatory, it has no N floor, and it is never pooled with B.

## A.2 Dataset (frozen)

- **Source:** `nebius/SWE-rebench-leaderboard`, test split. The local parquet copy is archived at
  `data/post-cutoff-branchA/nebius_SWE-rebench-leaderboard_data_test-00000-of-00001.parquet`, sha256
  `1497b218db0a8259d22471812f0de12b779c699daf741b930d68bc717636f0bf` (860 rows). HF dataset sha
  `34d5a58864acf91613740a09ec5d205228dcfa39`, lastModified 2026-07-28.
- **Inclusion rules:**
  - Python: every leaderboard row carries a Python `install_config`, and this is asserted;
  - `created_at ≥ 2026-02-16` (UTC);
  - exclude the `_interface` duplicates (instance_id ending in `_interface`, 29 rows in the window).
- **Result: n = 108 instances across 77 repositories.** The sensitivity stratum `created_at ≥
  2026-04-01` has **n = 50**.
- **Manifest:** `data/post-cutoff-branchA/instances_post.json`, built by
  `scripts/eval/contam_post_manifest.py`. The id list is `instance_ids_post.txt`, sha256
  `92d8d082184359ef7320567579b7b5d3f06542635a3ef68f263fbfa720d21bee`.

## A.3 Binding stack

- **Retrieval code:**
  - Pinned at commit **4fab615** (`4fab615b4fe5148a8a8b7121c2e058f47a16366d`), in the git worktree
    `code/retrieval` (detached, clean).
  - 4fab615 is the last `src/ragfusion` commit before the headline `local_packs.json` was built
    (2026-07-15 00:24). No `src/ragfusion` commit lies between them. Fusion code has changed substantially
    since then (≈700 lines in `fusion_backend.py`).
  - The index driver puts the worktree's `src/` and `scripts/eval/` first on `sys.path`. It asserts every
    import origin, the HEAD commit, and a clean tracked tree.
- **srclight 0.15.1** (user site-packages). All 30 RECORD hashes were verified intact. No separate venv
  was needed.
- **Embedder:** Qwen3-Embedding-8B Q8_0 on llama.cpp (`llama-server` b9837), on GPU (`-ngl 99`), at
  `127.0.0.1:8082`, with `-np 4 -c 32768 -b 8192 -ub 8192` (8192 context per slot).
  - The first launch used `-c 8192` with a shared KV cache. It crashed with `GGML_ASSERT(task)` after
    5 instances. Nothing was mis-indexed: the instance being indexed did not register, and it was
    re-indexed on resume.
  - Headline indexing used the same GGUF. GPU vs CPU arithmetic can perturb embeddings at the last
    digits; this is disclosed.
  - The content-hash embedding cache stores float16, as in the pinned `p5_index_instances.py`.
- **Indexing:**
  - Per instance base_commit, with treeless full-history clones in `data/post-cutoff-branchA/repos`.
  - Recipe of `rebench_index_prefetch.py`: EXCLUDE_DIRS pruning and `--max-files 15000`.
  - `CONFIG_HASH = 'swerebench-post'`, registered in `<EVAL_ROOT>\registry.db`.
  - Driver: `scripts/eval/contam_post_index.py`.
  - Instances over the file budget, or failing to index, are excluded and listed in
    `inclusion_post.jsonl`. By `git ls-tree` count, none of the 108 exceeds 15000 source files.
- **Packs** (`scripts/eval/contam_post_prefetch.py`), built exactly as the headline `local_packs.json`:
  - Two retrievald daemons, both started from the pinned worktree, with `RETRIEVALD_BACKEND=fusion` and the other
    4fab615 `RetrievaldConfig` defaults.
  - `:8083` has file-dedup ON (the default). `:8084` has `RETRIEVALD_QUERY_DEDUP_FILE=0`.
  - Hybrid mode, limit 12, `code_only=True`, query = `problem_statement[:6000]`.
  - `fetch_pack` and `format_pack` come from the pinned `g_plane_prompts.py`.
  - The script refuses to run until this file has a commit.
- **Generation:** `local_dedup_ab.py`, the same `SYS`, temperature 0.2, `max_tokens 6000`, single-shot,
  model `openai/gpt-5.6-sol` via OpenRouter, both arms. Raw responses are logged
  (`LOG_RESPONSE_TEXT=1`).

## A.4 Gold gate

- **When:** before any generation.
- **Test:** each instance's gold patch is run in its SWE-rebench Docker image (`docker_image` field).
- **Pass:** all `FAIL_TO_PASS` pass and no `PASS_TO_PASS` fails.
- **Failing instances** are excluded and listed. The analysed set is (indexed ∩ gold-pass).
- **No N floor.** A small analysed set is reported as such.
- Image pulls wait for the owner's Docker disk expansion.

## A.5 Models

- **Primary:** gpt-5.6-sol (A1–A4, A6).
- **Secondary:** local Qwen3-Coder-30B-A3B, free (A5), with the settings of its reference ON/OFF arms.
- **Reference:** Δ_ref(Verified) = +6.5pp, the pooled gpt headline and logged re-run on 500.

## A.6 Manipulation checks (reported before outcomes are joined)

`contam_post_analyze.py checks` reports the following from packs and gold only:
- mean distinct files ON vs OFF;
- mean pack characters ON vs OFF;
- gold-file recall@12 ON vs OFF;
- the files(OFF) ⊆ files(ON) rate;
- the ON→OFF anchor-transition counts and B→C prevalence (Verified references: 11.93 ON files, 16.0%
  B→C, 94.6% subset).

The SHA-256 of `manip_checks.json` is committed (§E) **before** `join`, and `join` enforces this. If OFF
does not serve fewer files than ON on average, the treatment did not take. A is then reported as
"manipulation failed" and no A1–A5 verdict is drawn.

If the B→C prevalence on the post packs is below 10%, the set is declared retrieval-shifted: A1's label is reported with the qualifier 'retrieval-shifted', and A3 (within B→C) is the headline row of the A table instead.

## A.7 Estimands (descriptive)

Common rules:
- d = 1[OFF resolved] − 1[ON resolved] on pairwise-attempted, gold-gated, indexed instances.
- Instance bootstrap, B = 10,000, seed 20261014.
- Exact b/c reported.

- **A1:** Δ_post, gpt-5.6-sol, all instances.
- **A2:** Δ_post, gpt-5.6-sol, the ≥ 2026-04-01 stratum.
- **A3:** Δ_post, gpt-5.6-sol, within post-cutoff B→C (classes from the post packs).
- **A4:** Δ_post relative to Verified: the ratio Δ_post / Δ_ref and sign agreement.
- **A5:** Δ_post for local Qwen3-Coder-30B, all instances.
- **A6:** Δ_post, gpt-5.6-sol, within the single-gold-file stratum (gold patch touches exactly one file), with Δ_ref recomputed on Verified's single-gold-file instances. This is the comparable stratum: the median SWE-rebench gold patch touches 2 files, and on Verified the gpt effect sits in single-file instances.
- **Seeds:** if the §A.9 projection for two gpt seeds on both arms is ≤ $30, two seeds are run on the same packs and A1–A4, A6 pool them with the instance bootstrap (draws of an instance move together); otherwise one seed, disclosed.

## A.8 Three-label decision rule (per estimand; headline label from A1)

- **SIGN-CONSISTENT:** point(Δ) > 0 and the bootstrap P(Δ* > 0) ≥ 0.80.
- **SIGN-INCONSISTENT:** point(Δ) < 0 and P(Δ* < 0) ≥ 0.80.
- **UNINFORMATIVE:** otherwise.

A is never described as a replication or a confirmation. A SIGN-INCONSISTENT result is reported
prominently next to B. It does not override B's label, because the branches are never pooled.

## A.9 Cost gate (≤ $30)

- 10-call usage probe first: 5 ON and 5 OFF on outcome-blind instances.
- Projection for both arms on the analysed set.
- Proceed only if ≤ $30 and the owner approves.
- Usage-probe responses are discarded from analysis.

## A.10 Threats

- Post-cutoff is relative to the published knowledge cutoff, 2026-02-16 (OpenAI model page). One anecdote has the model self-reporting December 2025, which would only make the window more conservative. The ≥2026-04-01 stratum (n=50) is the sensitivity check for cutoff uncertainty.
- **77 repositories, mostly 1–2 instances each.** Repository and difficulty composition differ from
  Verified.
- **The serving fleet is replicated, not the instances.** Two-daemon ranking nondeterminism (G2 D2;
  TRIMMED-BREADTH D1) also applies here. The subset-rate manipulation check reports it.
- **Small n.** The decision rule is a sign label, not a significance test.

## A.11 Preparation status at registration (no model calls made)

- Worktree created and verified (§A.3).
- Manifest frozen (§A.2).
- 77/77 repositories cloned, treeless with full history. All 108 base commits resolve.
- Embedder up on GPU at :8082.
- Per-instance indexing started 2026-10-14 under Task Scheduler. The tasks are `contam_embed_8082`,
  which auto-restarts the embedder, and `contam_post_index`, which runs three resumable passes. Log:
  `data/post-cutoff-branchA/index.log`. A one-instance smoke run (pallets__click-3239) indexed and
  registered.
- Pack prefetch **not started**; it waits for the commit of this file.
- No Docker images pulled.

---

# C. Executor decisions requiring design-authority / owner confirmation

These were not fixed by the design text. Each was chosen as stated above, and each can be changed
before the commit:

Design-authority rulings (2026-10-14): items 1–4 and 6–8 accepted as drafted; item 2 amended (one
sentence added); item 5 replaced.

1. **P2 user turn** carries `Repository: {repo}`, matching P1. With the pack removed, nothing else
   tells the model which repository the issue belongs to. The added sentence sits in the user turn, and
   SYS stays byte-identical.
2. **P2 `known` paths** = `git ls-files` of the checkout, rather than the empty list. This enables the
   harness's own path resolver without gold information. `known = git ls-files` carries no gold
   information; it can only make apply easier, which pushes instances toward High-M, so it is
   conservative for the "survives" label.
3. **NA handling in M.** NA probes contribute 0, and Low-M means all available probes are negative.
   S1 (the P1-eligible-only E1) is a sensitivity analysis.
4. **P3 details:**
   - "first gold hunk" = the first changed line of the first hunk of the first gold file with a
     pre-image;
   - the target is the pre-image;
   - "5-gram overlap" = clipped 5-gram recall over `\w+|[^\w\s]` tokens.
5. M is measured on the stack that served the arm. OpenRouter-served arms (Qwen3.6-27B K=4/12/40 via qwen/qwen3.6-27b; Qwen3-Coder-30B K=4/12/40 via its OpenRouter slug) get OpenRouter-measured M at the same slug. Locally served arms (the Qwen3-Coder-30B reference pair and Arm T) get M measured on the local UD-Q5_K_XL GGUF. If the budget tier for the OpenRouter open-model probes is not approved, the local-GGUF M is used for the OpenRouter arms and labelled 'proxy M' in every table.
6. **Completion budgets** per model (§B.2), and the issue truncation at 6000 characters.
7. **The bootstrap one-sided p** uses the null-centred form. The Webb test is bootstrap-t with the null
   imposed.
8. **Branch A specifics** were drafted from the reconciled summary and need explicit sign-off:
   - the A1–A5 definitions;
   - the 0.80 bootstrap-probability threshold in the three-label rule;
   - the gold-gate pass criterion;
   - the two-daemon pack construction, chosen over a single daemon with 4fab615's per-request `dedup`
     override. Two daemons are faithful to the headline construction; a single daemon would remove the
     cross-daemon ranking nondeterminism.

# D. Files

- `docs/paper/CONTAMINATION-PREREG.md`: this file.
- `docs/paper/CONTAMINATION-P1-FILTER.txt`: the P1-NA list (133).
- `scripts/eval/contam_common.py`: prompts, parsers, scorers, classifier, arm map.
- `scripts/eval/contam_prep.py`: P1 filter, P3 inputs, prompt rendering.
- `scripts/eval/contam_probe.py`: the probe runner, with the usage probe and cost guard.
- `scripts/eval/contam_score.py`: M table, blinded join, E1–E5, decision rule, self-test.
- `scripts/eval/contam_secondary.py`: the free secondary analyses (§B.10).
- `scripts/eval/contam_post_manifest.py`, `contam_post_clone.py`, `contam_post_index.py`,
  `contam_post_prefetch.py`, `contam_post_analyze.py`: Branch A.
- Data, not tracked:
  - `data/memorization-branchB/`: `p3_inputs.json`, `secondary.json`, and later the probe logs and
    M tables;
  - `data/post-cutoff-branchA/`: the manifest, parquet, clones, worktrees, indexes, and logs.

# E. Deviations and hash log (append-only, dated)

_(empty at registration)_

- **2026-10-14 20:16 EDT — Branch A pack prefetch done (executor).** Prefetch run after commit
  e9eede2. Two retrievald daemons from the pinned worktree `code/retrieval` (HEAD 4fab615b, clean;
  `ragfusion` import origin verified under the worktree's `src/`), srclight 0.15.1, `RETRIEVALD_BACKEND=fusion`,
  `RETRIEVALD_EMBED_MODEL=openai:Qwen/Qwen3-Embedding-8B`, `RETRIEVALD_DIMS=4096`, `RETRIEVALD_REGISTRY_DB=<EVAL_ROOT>\registry.db`
  (108/108 refs `ready` under `config_hash='swerebench-post'`), embedder :8082, all other 4fab615
  `RetrievaldConfig` defaults. `:8083` dedup ON (default), `:8084` `RETRIEVALD_QUERY_DEDUP_FILE=0`.
  `RETRIEVALD_DEFAULT_IDENTITY=local` was set on both (caller-login fallback required by retrievald without the
  tailnet proxy; it does not enter retrieval). 108/108 instances, 216/216 packs, 0 fetch failures;
  hits per pack: 209×12, 3×10, 3×8, 1×6 (all short packs on the ON arm).
  `post_packs.json` sha256 `84a6b05044e32c3b2b7eaef003c3f7ea6c8e258dab3935564fc025b008e002e2`.
  Note (no deviation): `instance_ids_post.txt` is stored with CRLF line endings; its LF-normalized
  content hashes to the registered `92d8d082…`.
- **2026-10-14 20:16 EDT — Branch A manipulation checks, all 108 indexed (not yet gold-gated).**
  `contam_post_analyze.py checks` (no `--gold-gate`): files ON 11.78 vs OFF 5.35 (treatment took);
  chars ON 6408 vs OFF 6808; gold-file recall@12 ON 0.861 vs OFF 0.741; files(OFF)⊆files(ON) 94.4%
  (Verified 94.6%); transitions B>B 61, A>A 15, C>C 10, B>C 9, B>A 9, C>A 4; **B>C prevalence 8.3%
  (9/108), below the 10% threshold of §A.6 → retrieval-shifted on the ungated set.** This file is
  archived as `manip_checks_all108.json`, sha256
  `0150a551c785cde2510d1d06f1f53d057c6f788524ba5a3dd2fddb0a6d4a7f29`. The gold-gated re-run is
  logged separately below; the owner decides which of the two is the committed `manip_checks.json`
  for `join` (the pre-reg does not say whether §A.6 is computed before or after the gold gate).
- **2026-10-14 20:25 EDT — Local-GGUF probes launched (Branch B, free; tag `qwen3coder30b_local`).**
  Embedder :8082 stopped after the prefetch (scheduled task `contam_embed_8082` ended and **disabled**,
  because its one-time trigger at 2026-10-14 23:59 would have relaunched ~9 GB onto the GPU next to the
  model; re-enable before any further indexing). Served
  `<LLAMA_DIR>\Qwen3-Coder-30B-A3B-Instruct-UD-Q5_K_XL.gguf` with llama.cpp `llama-server` b9837-b3fed31b9:
  `--host 127.0.0.1 --port 8090 -c 16384 --parallel 2 --jinja -ngl 99` (2 slots × 8192 ctx). Completion
  budget `max_tokens 6000`, confirmed from the reference arms' record (CLEAN-CONTROL-DESIGN.md: local
  llama-server :8090, single-shot, max_tokens 6000). Temperature 0, one sample per item, concurrency 2.
  Order P1 (367) → P3 (499) → P2 (500).
- **2026-10-14 20:25 EDT — Logprob secondary (§B.2): NOT COMPUTED.** llama-server b9837 does not
  return prompt-token log-probs: `/v1/completions` with `echo: true, logprobs: 1` returns log-probs for
  generated tokens only (echo ignored), and `/completion` with `n_predict: 0, n_probs: 1` returns none.
  Per §B.2 no substitute measure is used.
- **2026-10-14 21:58 EDT — Local probes and Branch A gold gate interrupted (executor; operational, no
  protocol change).** (a) Local probes (actual start 20:20): P1 complete, 367/367 logged. P3 stopped at
  463/499 logged (429 `stop`, 34 `length`); 3 calls (sympy-16886, -18199, -18211) hit the 1800 s client
  timeout and are not logged. On resume they are re-issued as identical requests (transport retry,
  §B.2). P2 not started. The model server and probe runner were killed by the host's low-memory reaper:
  Windows had ~2.5 GB of 61.6 GB free, with the WSL VM holding ~47 GB, ~44 GB of it page cache from
  concurrent Docker grading. The P3 timeouts are attributed to the same memory pressure. (b) Gold gate: a
  first launch (21:10) waited only for "no `sweb.eval.*` container". It started during another agent's
  image-build gap in its P2 grading and was killed at 21:12 (rc 143), before any instance container ran.
  The waiter now also requires no running `run_evaluation` process. It too was reaped before it fired.
  No gold result exists yet.
- **2026-10-14 22:10 EDT: Tier 1 (gpt-5.6-sol Verified P1/P2/P3) executed (executor; no protocol
  change).**
  - **Usage probe** (`usage_probe_tier1.json`). Per-call cost: P1 $0.00388, P2 $0.01863, P3 $0.00528.
    Projected **$13.38**, under the $50 cap. Owner-approved; run with `--approved-usd 50`.
  - **Main run.** Concurrency 8; 0 transport failures; all `finish_reason=stop`; provider OpenAI.
    - P1: 367/367, $2.206.
    - P3: 499/499, $4.654.
    - P2: 500/500, $8.534, with 0 apply errors.
    - Usage probe: $0.102.
    - **Tier total $15.496.**
  - **P2 grading.** Started 20:47 with the headline harness command (`--max_workers 4 --cache_level
    instance`) on `preds_P2_gpt56sol.jsonl`. It was **killed by the host low-memory reaper at about
    21:55**, at 173/262 non-empty instances. No report was written.
  - **Status.** The M table is not yet built: §B.9 step 4 must complete first. No join has been run.

- **2026-10-14 ~22:30, design-authority ruling (Branch A), logged before the gold gate runs.**
  - (1) The binding population for the §A.6 manipulation checks and the 10% B→C rule is the gold-gate survivors (indexed ∩ gold-pass). The gate uses gold patches only, never model outcomes. The ungated 108 checks (sha256 0150a551…) are recorded as a pre-gate snapshot. The checks are recomputed on the survivors, and that hash is committed before any outcome join. The threshold is not relaxed.
  - (2) The paid gpt-5.6-sol arms run within the ≤$30 gate. If the survivor B→C share is <10%, the set is reported as "retrieval-shifted". A1/A6 are descriptive and sign-labelled. The A table's headline row is A1, with the qualifier. A3 is reported only as a count table (n≈9), with no label.
  - (3) Paper finding (outcome-blind manipulation-check result): on post-cutoff repositories the retriever supplies the gold pre-image lines less often (B→C 8.3% vs 16%; gold-file recall@12 ON 0.861 vs Verified 0.878), so the depth effect's habitat is smaller there.
  - (4) Added free secondary: the local Qwen3-Coder-30B arm (A5) runs regardless. The survivors' transition table is reported beside Verified's.

- **2026-10-15 ~08:10, M table (gpt-5.6-sol, Verified), committed BEFORE the outcome join.** The P2 regrade used authenticated image pulls, with 0 harness errors after 2 passes. File: `data/memorization-branchB\M_table_gpt56sol.json`, sha256 **b849fdf1dbc1e752f9139c52c9f1c8043461cece7d23f98fa350f3bc84db68a6**. M distribution, outcome-blind: M=0: 47, M=1: 182, M=2: 191, M=3: 80. Low-M share is 0.094, against the 0.35 assumed in the §B power table, so E1 and E2 have much less power than planned (E1 n_low≈47). This is disclosed before the join, and the decision rules are unchanged. The P1 validity check falls within or near the published band.

- **2026-10-15, erratum (append-only).** The Arm-T reference values cited in §B.6 for Qwen3-Coder-30B (OFF−T +9.94pp; T−ON −4.02pp) are INVALID. They came from a first grading with Docker Hub rate-limit harness errors (136/248), which were scored as unresolved. The regraded values, with 0 harness errors, are ON 7.0%, T 6.8%, OFF 12.9%; OFF−T +6.13pp (38 vs 9, McNemar p=2.5e-5); T−ON −0.21pp (7 vs 8, p=1.0). The E5 Arm-T cell uses the regraded T report. See TRIMMED-BREADTH-PREREG §9 (grading-validity note).

- **2026-10-15 10:15 EDT, Branch A gold gate and survivor manipulation checks (executor), logged BEFORE any Branch A generation or outcome join.**
  - **Gold gate (§A.4).** Run under Task Scheduler (`contam_gold_post`) with the SWE-rebench fork harness: `run_evaluation --dataset_name nebius/SWE-rebench-leaderboard --split test --namespace swerebench --max_workers 4 --cache_level instance`, run_id `rebench_post_gold`, authenticated Docker Hub pulls. Ran 08:04–10:09; 108/108 ran, **0 harness errors** (no retry pass needed). Pass/fail was evaluated from the per-instance `report.json` files under the §A.4 criterion (all FAIL_TO_PASS pass, no PASS_TO_PASS fails). It agrees with the harness `resolved` field on 108/108.
  - **Survivors: 105/108** (≥2026-04-01 stratum: **49/50**). Excluded, each with 0 FAIL_TO_PASS misses: tox-dev__tox-3904 (1 PASS_TO_PASS failure; ungated class A>A), zauberzeug__nicegui-5914 (1; B>B), agronholm__anyio-1134 (2; B>B). None was B>C. `gold_pass_ids_post.txt` sha256 `b22ac55c05e71ee9a052ebe3ebbef9d74786b2dc1fc031dfc1f2f2d7e7a6e13e`; per-instance gate table `gold/gold_gate_post.jsonl` sha256 `d8b19eb5fa98c4a9d681f39d8fb968898ea6325ca8e97ca6cff2db72aad9fd8c`.
  - **Survivor manipulation checks (§A.6, binding per the ruling above).** Command: `contam_post_analyze.py checks --gold-gate data/post-cutoff-branchA/gold_pass_ids_post.txt`, n=105.
    - Files ON 11.77 vs OFF 5.35 (the treatment took).
    - Chars ON 6418 vs OFF 6823.
    - Gold-file recall@12 ON 0.867 vs OFF 0.743.
    - files(OFF)⊆files(ON) 94.3%.
    - Transitions: B>B 59, A>A 14, C>C 10, B>C 9, B>A 9, C>A 4.
    - **B>C prevalence 8.57% (9/105), below 10%, so the set is retrieval-shifted.**
    - **`manip_checks.json` sha256 `a4f1ee9a6dae7ad36d95c344be4e27c2a69438102aab0f4cf40a73916e6806f7`** (copy kept as `manip_checks_gold105.json`). This is the committed checks file that `join` checks. The ungated pre-gate snapshot is kept unchanged as `manip_checks_all108.json` (sha256 `0150a551…7f29`).
  - **Reporting override (per the ruling above).** `contam_post_analyze.py join`, frozen at registration, sets `headline_row = A3_gpt_BC` and attaches a sign label to A3 when the set is retrieval-shifted. The design-authority ruling (2) supersedes that default. The A table's headline row is **A1 with the "retrieval-shifted" qualifier**. A3 is reported only as a count table (b/c, n=9), with no label. The code is not edited; the override is applied when `join_post.json` is reported.

- **2026-10-15 12:15 EDT, Branch A arms generated, graded and joined (executor). The survivor checks sha256 a4f1ee9a… was committed in 50cbd0f before generation.**
  - **A.9 usage probe** (`gen/usage_probe_A9.json`). 10 calls (5 ON, 5 OFF), picked by lowest sha256(`20261014:A9:{arm}:{iid}`) among the survivors; the responses are discarded. Per call: ON $0.0620, OFF $0.0590. Projection on 105 survivors: one seed $12.70; **two seeds $25.41**. Two seeds plus the probe ($0.61) come to ≤ $30, so **two seeds were run** per §A.7.
  - **Generation.**
    - Run under Task Scheduler with `local_dedup_ab.py` and the headline gpt flags (`--endpoint https://openrouter.ai/api/v1 --api-model openai/gpt-5.6-sol --concurrency 8`, temperature 0.2, max_tokens 6000) with `LOG_RESPONSE_TEXT=1`, on `post_packs.json`. Tags `gpt56sol_post` (seed 1) and `gpt56sol_post_s2` (seed 2).
    - A5 ran on local Qwen3-Coder-30B-A3B UD-Q5_K_XL with llama-server b9837 (`-c 16384 --parallel 2 --jinja -ngl 99`), temperature 0.2, max_tokens 6000, concurrency 2, tag `qwen3coder30b_post`, concurrently with the API generation.
    - All arms: 105/105. gpt arms: all `finish_reason=stop`. A5: 2 `length` per arm.
    - **Resume pass, missing items only:**
      - 10 gpt seed-1 calls (6 ON, 4 OFF) failed with transport `IncompleteRead` and were re-issued as identical requests.
      - genericmappingtools__pygmt-4463: checkout failed on a git-lfs smudge error ("remote missing object" for a test PNG). It was re-run with `GIT_LFS_SKIP_SMUDGE=1`, which leaves LFS pointer files and does not change source diffs.
      - youssofal__mtplx-21: its base commit was absent from the bare cache (not reachable from any branch). It was fetched by SHA from GitHub and pinned as a local ref. Both items were then re-run in every arm.
    - **Spend:** OpenRouter key usage rose by **$19.36** from the pre-probe baseline (usage_daily $19.36). That is the probe plus all four gpt arms, and an upper bound if any other session used the key. This is under the $25.41 projection and the $30 cap.
  - **Grading.**
    - SWE-rebench fork harness, Task Scheduler, `--max_workers 4 --cache_level instance --namespace swerebench`. One arm per batch, sequential, with caches dropped between batches. The llama-server was stopped before grading began, so GPU serving and Docker grading never overlapped.
    - **Harness errors: 0 in all 6 arms.** For gpt seed-1 OFF, the fork's `make_run_report` crashed twice after all 90 non-empty instances had graded: it rebuilds test specs for all 860 rows by fetching `requirements` files from raw.githubusercontent.com, and WSL DNS failed intermittently.
    - So summary reports were rebuilt from the per-instance `report.json` files for every arm (`grade/report_<arm>.json`). For the 5 arms with a harness report, they match it exactly on resolved_ids and submitted_ids.

    | arm | resolved/105 | empty patches | errors |
    |---|---|---|---|
    | gpt s1 ON | 10 | 14 | 0 |
    | gpt s1 OFF | 14 | 15 | 0 |
    | gpt s2 ON | 8 | 13 | 0 |
    | gpt s2 OFF | 9 | 17 | 0 |
    | Qwen ON | 1 | 50 | 0 |
    | Qwen OFF | 2 | 53 | 0 |

  - **Join** (`contam_post_analyze.py join`, checks sha a4f1ee9a verified committed; two gpt seeds pooled). `join_post.json` sha256 `9dee3565e0d7c3f01679989a1537cd2c0195658c4abe965871e07f70345fa29d`.

    | row | n | Δ | b/c (draws) | 95% CI | P(Δ*>0) | label |
    |---|---|---|---|---|---|---|
    | **A1, all (headline row; retrieval-shifted)** | 105 | **+2.38pp** | 11/6 | [−1.9, +6.7] | 0.843 | **SIGN-CONSISTENT (retrieval-shifted)** |
    | A2, ≥2026-04-01 | 49 | 0.00pp | 2/2 | [−4.1, +4.1] | 0.400 | UNINFORMATIVE |
    | A4, vs Verified | — | ratio 0.37 (Δ_ref +6.5pp) | — | — | — | same sign |
    | A5, local Qwen3-Coder-30B | 105 | +0.95pp | 2/1 | [−1.9, +4.8] | 0.613 | UNINFORMATIVE |
    | A6, single gold file | 39 | 0.00pp | 5/5 | [−9.0, +9.0] | 0.450 | UNINFORMATIVE (Δ_ref single-file +7.46pp; ratio 0.0) |

    - Per seed (descriptive): seed 1 ON 10 / OFF 14 (+3.8pp); seed 2 ON 8 / OFF 9 (+1.0pp).
    - **A3, count table only (no label, per the ruling): B>C n=9.** Seed 1: ON 2 / OFF 2 resolved (b=0, c=0). Seed 2: ON 1 / OFF 2 (b=1, c=0).
    - The frozen code's `headline_row: A3_gpt_BC` and A3 label in `join_post.json` are **overridden by the ruling** (logged 10:15 above). Resolve rates are low here (gpt 8–13%, Qwen 1–2%) with many empty patches, so most pairs are concordant failures.

- **2026-10-15 12:58 EDT, local-GGUF probes completed and M table built (executor; Branch B, free; tag `qwen3coder30b_local`). Logged BEFORE any join; no join has been run.**
  - **Serving.** Run under Task Scheduler with the same server as the 20:25 entry (llama-server b9837, UD-Q5_K_XL, `-c 16384 --parallel 2 --jinja -ngl 99`), started only after the Branch A grading had finished, then stopped before P2 grading.
  - **P3 resume.** Missing items only: 36 re-issued, including the 3 that timed out on 10-14, as identical requests. Now 499/499 (460 `stop`, 39 `length`).
  - **P2:** 500/500 (488 `stop`, 12 `length`), 27 non-empty patches.
  - **P1:** 367/367 (from 10-14).
  - **P2 grading.** Headline harness (`python -m swebench.harness.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified --max_workers 4 --cache_level instance`), run_id `contamP2_qwen3coder30b_local`. It did not overlap any other grading, and caches were dropped before and after. 27 completed, 11 resolved, 473 empty, **0 harness errors**. Report sha256 `262f088ac633ef4204c83f171a3fcca3ea5b9e10daf37b446deb49c3a21ac540`.
  - **M table.** `contam_score.py m-table --tag qwen3coder30b_local --p2-report …` → `M_table_qwen3coder30b_local.json`, **sha256 `49dfe7733771218a454a5626f57e4a6dbcf443ad45ca92071aa1c0a9acd8edf5`**.
  - **Probe validity** (outcome-blind):
    - P1 hit 68.4% (n=367; within the 60–76% band); basename 73.6%.
    - P2 apply 5.4%, resolve 2.2%.
    - P3 positive 4.0%.
    - M distribution: 0: 222, 1: 258, 2: 20, 3: 0. **Low-M share 0.444.**
