# GENERALITY-BENCH-PREREG — "The Recall Trap" beyond Python / SWE-Verified

**Status:** PRE-REGISTERED (binding). Written before any generality run.
**Date:** 2026-07-16 (revised). **Author:** [author] [author].
**Paper:** *The Recall Trap* (the paper draft). **Do not edit the draft from this doc.**

Binding rules below are numbered **G-1 … G-6**. Outcomes get appended to this file (append-only);
the decision rules are fixed in advance so a null cannot be re-spun into a win.

> **REVISION NOTE (supersedes the 2026-07-16 morning draft).** The prior plan used the in-house
> **swebench-ml** set and *grafted* an execution grader onto it by joining to Multi-SWE-bench.
> That is now **rejected by hard constraint**: the generality arm must run on an **existing,
> off-the-shelf, execution-graded code-repair benchmark that ships its own working grader**
> (test_patch / FAIL_TO_PASS + PASS_TO_PASS, Docker or equivalent). **We construct and graft NO
> grader.** swebench-ml is retrieval-only (`gold_files`, no `test_patch`, no tests) → it is **out** of
> the generality arm (it remains valid only as a retrieval-MRR side-check, never as a resolution
> benchmark). This revision rebuilds the plan on **SWE-PolyBench** (primary) and **Multi-SWE-bench**
> (optional second), each of which ships its own grader.

---

## 0. What we are replicating (direction, not mechanism)

The core result to generalize is the **single-shot file-dedup A/B**, exactly as run on SWE-bench
Verified:

- FIXED 12-slot pre-injected code pack (fusion index over the repo at `base_commit`), **no tools**,
  the benchmark's **own execution grading**, one flag toggled: **one-chunk-per-file dedup (recall@k
  maximizer) ON vs OFF** (file breadth vs within-file depth). Model emits a patch from the pack alone;
  apply; grade pass/fail.
- On SWE-Verified this *raises* resolution **+5.7 to +7.6pp** across four arms (gpt-5.6-sol +7.6pp,
  DeepSeek-V4 +6.2pp, Qwen3-Coder-30B +5.8pp, dense control +5.7pp), retriever-agnostic
  (fusion×dense interaction p=0.39), mediated by anchor dose.

**GOAL:** show the inversion replicates *in DIRECTION* on **non-Python / non-SWE-Verified code** — not
to re-measure the mechanism. We buy external validity on the axis the draft concedes as untested
(§6.2 "Generality envelope"): **language / ecosystem**. Everything else (pack format, no-tools,
grading philosophy, SEARCH/REPLACE apply) is held identical to the headline. The benchmark supplies
its **own** oracle; we supply only the fusion index + packs (the same infra we already run for
SWE-bench Verified).

---

## 1. Benchmark selection — off-the-shelf graders only (verified live 2026-07-16)

Requirement restated as a filter every candidate must pass: **ships its own execution grader**
(test_patch + FAIL_TO_PASS/PASS_TO_PASS, Docker or equivalent), **gives repo + base_commit** for a
clean checkout (so we can build the fusion index), and **provides gold changed-file lists** for the
retrieval eval. Multilingual strongly preferred; contamination-freshness secondary.

### 1.1 Full candidate audit (all verified live)

| Candidate | Exists / source (live-verified) | Ships own grader? | Languages | n | base_commit + gold files? | Verdict |
|---|---|---|---|---|---|---|
| **SWE-PolyBench** (Amazon) | arXiv **2504.08703**; GitHub `amazon-science/SWE-PolyBench`; HF `AmazonScience/SWE-PolyBench` (+`_500`,`_Verified`) | **YES** — per-instance **pre-built Docker images on GHCR** (`ghcr.io/timesler/swe-polybench.eval.x86_64.<instance_id>:v1.1`); F2P/P2P; `run_evaluation.py` w/ `--evaluate-gold` | **Java, JavaScript, TypeScript, Python** | 2,110 (PB500=500 bal.; PBv=382–394) | **YES** — `base_commit`,`patch`,`test_patch`,`F2P`,`P2P`,`modified_nodes`; **ships file-level + node-level retrieval metrics** | **PRIMARY** |
| **Multi-SWE-bench** (ByteDance) | arXiv **2504.02605**; GitHub `multi-swe-bench/multi-swe-bench`; HF `ByteDance-Seed/Multi-SWE-bench` | **YES** — `python -m multi_swe_bench.harness.run_evaluation --config …`; Docker per instance; `f2p_tests`/`p2p_tests` | **Java, TS, JS, Go, Rust, C, C++** (no Python) | 1,632 (mini=400, 8 langs) | `fix_patch`/`test_patch` present; **base commit via `base` dict `sha`, not a clean top-level `base_commit`** (extraction step) | **OPTIONAL 2nd** (language breadth) |
| **SWE-bench-Live** (Microsoft) | arXiv **2505.23419**; GitHub `microsoft/SWE-bench-Live`; HF `SWE-bench-Live/SWE-bench-Live` | **YES** — per-instance Docker (RepoLaunch), `FAIL/PASS_TO_PASS`, `python -m evaluation.evaluation` | **Python only** | ≥1,565 / 223 repos; verified 500 (+50/mo) | YES | **Backstop** (contamination-robust, but single-language → doesn't buy the language axis) |
| SWE-bench Multimodal | arXiv 2410.03859; JS, 617 inst, 17 repos | Yes, but 83.5% of tasks **require image input** | JavaScript | 617 | partial | **Reject** — multimodal changes the modality; code-only slice is small/ill-defined for a text pack |
| SWE-gym | arXiv 2412.21139 | training env, not a frozen held-out eval | Python | — | — | **Reject** — training substrate, single-language, overlaps SWE-Verified repos |
| GitBug-Java | Java reproducible-bug set | Yes (per-bug test exec) | **Java only** | ~199 | yes | **Reject for generality** — single-language; no multilingual gain over PolyBench-Java |
| BugsInPy | Python real bugs + tests | Yes | **Python only** | ~500 | yes | **Reject** — single-language, redundant with SWE-Verified |
| Defects4J | Java bug DB w/ test suites | Yes | **Java only** | 835 | yes (checkout tool) | **Reject** — single-language, old (heavy contamination), not issue/PR-shaped |
| RepoBench / CrossCodeEval | code-**completion** / retrieval benchmarks | **NO execution/patch grader** | multi | — | n/a | **Reject** — no test oracle at all; measures completion, not repair |

### 1.2 Primary — **SWE-PolyBench** (decisive single recommendation)

**Why it is the pick, concretely:**
1. **It ships its own grader — zero construction.** Per-instance Docker images are **pre-built and
   published on GHCR** (`ghcr.io/timesler/swe-polybench.eval.x86_64.<instance_id>:v1.1`) — we *pull*,
   we do not build. Grading is `python3 src/poly_bench_evaluation/run_evaluation.py --dataset-path …
   --predictions-path predictions.jsonl --result-path ./eval_logs`, using shipped **F2P/P2P**. A
   **`--evaluate-gold`** mode runs the gold patch with **no predictions file** — this is our free
   "gold-applies" smoke test.
2. **It natively ships the retrieval eval we need.** SWE-PolyBench introduces **file-level** retrieval
   metrics (recall/precision vs the ground-truth changed-file set) **and** node-level (CST) metrics
   (`--node-metrics`). Our fixed-pack dedup A/B is *exactly* a file-localization instrument — the gold
   changed-file list is a first-class field, no derivation needed.
3. **Instances give a clean checkout.** Fields (HF card, verified): `instance_id`, `repo`,
   **`base_commit`**, `patch` (gold, test-code stripped), `test_patch`, `F2P`, `P2P`,
   `problem_statement`, `language`, `Dockerfile`, `test_command`, `task_category`
   (Bug Fix / Refactoring / Feature), `modified_nodes`. Everything the pack-builder needs.
4. **Four languages incl. Python** — Java / JavaScript / TypeScript / Python. Python **ties back to
   SWE-Verified** (a same-endpoint internal control), while Java/JS/TS deliver the generality claim.
5. **License = MIT** (dataset and code) — the cleanest of all candidates for a published artifact.
6. **A ready-made balanced subset.** **PB500** = 500 instances, **125 per language** (task-category
   40/40/20). We do not have to sub-sample by hand.

> **G-1 (binding).** The generality benchmark is **SWE-PolyBench** (Amazon; arXiv 2504.08703; MIT).
> We grade **only** with its shipped GHCR Docker images + `run_evaluation.py` (F2P/P2P). No grader is
> written, borrowed, or grafted. The pre-registered instance set is **PB500** (500 instances,
> 125 each Java/JS/TS/Python). Retrieval/gold-file eval uses SWE-PolyBench's **own** file-level metric.

### 1.3 Optional second — **Multi-SWE-bench** (buys Go / Rust / C / C++)

If reviewers press for breadth beyond the JVM/JS/Python quartet, add **Multi-SWE-bench** (its own
Docker harness — again no grader construction) for **Go, Rust, C, C++**. Use the **mini** subset
(400 instances, 8 languages) or a per-language cap. **License:** CC0 on the annotations, with upstream
project licenses governing the code. **Caveat that makes it *second*, not primary:** instances expose
the base state via the `base` dict's `sha` (plus PR `number`), **not** a top-level `base_commit`
field — a small deterministic extraction step, and heavier polyglot Docker (cargo/go/cmake/gradle
build at eval time vs PolyBench's pre-pulled images). It also lacks Python (no SWE-Verified tie).

> **G-1b (binding, conditional).** Multi-SWE-bench is run **only** if the primary (PolyBench) lands
> and a broader-language point is wanted. It is graded **solely** by its own
> `multi_swe_bench.harness.run_evaluation`. If Docker build flakiness on this Windows+WSL box (see R1)
> exceeds a 15% instance-loss rate, it is dropped to a **retrieval-only** side-note, not forced.

### 1.4 Contamination backstop — SWE-bench-Live (noted, not primary)

SWE-PolyBench PRs are historical (popular repos, mostly ≤2024/early-2025) → **contamination-plausible**
for 2026 models. That is a *fit caveat*, not a disqualifier (§5). If a reviewer attacks contamination
specifically, **SWE-bench-Live** (Microsoft, Python-only, fresh monthly, its own Docker grader) is the
off-the-shelf answer — but it does **not** buy the language axis, so it is out of scope for *this*
pre-reg and lives in a separate contamination pre-reg if needed.

---

## 2. Models, arms, n, and MDE

**Arms:** single-shot dedup **ON vs OFF only** (the headline instrument). No agentic loop, no k-sweep.
Same regime as `local_dedup_ab.py`: 12 slots, no tools, SEARCH/REPLACE → apply → `git diff` →
**SWE-PolyBench's** grader; empty/failed-apply = task failure (counted, not dropped).

**Models (2, justified):**
1. **Qwen3-Coder-30B-A3B-Instruct** (`qwen/qwen3-coder-30b-a3b-instruct` on OpenRouter,
   ≈ $0.07/M prompt + $0.27/M completion). The weak local-class model that **already replicated on
   SWE-Verified (+5.8pp)**. Near-$0 → run on the FULL PB500. Primary direction signal.
2. **gpt-5.6-sol** (frontier, OpenRouter; ≈ $1.25/M prompt + $10/M completion — labelled estimate).
   The tier-gate model that **passed on SWE-Verified (+7.6pp, McNemar p=0.0003)**. One strong
   non-Claude point so the claim isn't weak-model-only.

We deliberately **omit** DeepSeek-V4 (producibility-channel confound) and Claude (agentic-regimen
tangle) — two models that already replicated is enough for a *direction* test.

**MDE.** Pre-agreed approximation **MDE₈₀ ≈ 2.8·√(p_disc / n)**, discordant-pair fraction
**p_disc ≈ 0.10** (the SWE-Verified rate). The design is **paired** (dedup ON vs OFF on the *same*
instance) so McNemar is more powerful than this unpaired proxy — the numbers below are conservative.

| n (instances) | MDE₈₀ | Interpretation for a ~6–7.6pp effect |
|---|---|---|
| 125 (one PolyBench language) | **7.9pp** | per-language = **direction / sign only** |
| 199 (PolyBench-Python, full) | 6.3pp | borderline |
| 382 (PBv) | 4.5pp | powered |
| **500 (PB500, all langs pooled)** | **4.0pp** | **powered** — primary headline |
| 500 pooled ×2 models = 1000 | 2.8pp | powered (cross-model pool) |

**Pre-registered sizing:**

| Benchmark | Instance set | n | MDE₈₀ (pooled langs) | Powering verdict |
|---|---|---|---|---|
| **SWE-PolyBench (primary)** | **PB500** (125×4) | **500** | **4.0pp** | **Powered** confirmatory (McNemar), per-language = direction |
| Multi-SWE-bench (optional 2nd) | mini | 400 (≈50/lang×8) | 4.4pp pooled | powered pooled; per-language direction-only |

> **G-2 (binding).** The **powered confirmatory** point is **PB500 pooled across its 4 languages**
> (MDE₈₀ 4.0pp < the 5.7–7.6pp effect). **Per-language** cells (n=125, MDE 7.9pp) are **direction /
> sign** tests, reported descriptively — never spun as per-language significance. n is fixed in
> advance; we do **not** grow n after peeking at the sign.

---

## 3. Retrieval / pack build — our only setup cost (identical infra to SWE-Verified)

The single-shot harness consumes a **packs JSON keyed by `instance_id`** with per-arm `{pack, files}`,
built by a prefetch step that queries a **retrievald** fusion index at the repo's `base_commit`, once with
file-dedup ON and once OFF. This is the **same** pack-build we run for SWE-bench Verified — the only
setup we accept.

**Steps (SWE-PolyBench):**
1. **Fetch** `AmazonScience/SWE-PolyBench_500` from HF (500 rows; `repo`, `base_commit`, `patch`,
   `test_patch`, `F2P`, `P2P`, gold changed-file list, `language`).
2. **Clone** each unique `(repo, base_commit)` into `swe-polybench/repos/`. Checkout at `base_commit`
   (all instances give one — no non-git, no missing-commit blockers expected).
3. **Build the fusion index per instance snapshot** with the shipped default identity
   (`fusion@…lex_mode=ids, w_graph=1.0`) — Qwen3-Embedding-8B on the 4090. Dedup within an index by
   caching per unique `base_commit` (many instances of a repo share commits) to avoid rebuilds. **This
   is the dominant compute** (see R2 for the large-TS-repo blocker).
4. **Launch retrievald twice:** `:8083` dedup-ON (default), `:8084` `RETRIEVALD_QUERY_DEDUP_FILE=0` (dedup-OFF) —
   the headline fleet pattern.
5. **Prefetch both arms** → `polybench_packs.json` keyed by `instance_id` with
   `{dedupON:{pack,files}, dedupOFF:{pack,files}}` (adapt `prefetch_packs.py`; query =
   `problem_statement`, k=12).
6. **Grade with SWE-PolyBench's shipped harness** — pull GHCR images, run
   `run_evaluation.py --predictions-path predictions.jsonl`. **No grader integration to write.**

**Reusable vs new:**

| Component | SWE-PolyBench |
|---|---|
| Repo clones | **new** (21 repos; clone at each `base_commit`) |
| Fusion index | **new** (main compute; per unique base_commit) |
| Pack prefetch (ON/OFF) | new (cheap; `prefetch_packs.py` exists) |
| **Grading harness** | **shipped by the benchmark** — pull GHCR images + `run_evaluation.py` (drop-in) |
| Gold changed-file lists (retrieval eval) | **shipped by the benchmark** (file-level metric) |
| `local_dedup_ab.py` | thin `--bench polybench` path-parameterization (chat/apply/resolve already generic) |

**Setup costs & blockers (called out honestly):**
- **R1 — Docker at grade time.** Images are **pre-built on GHCR** (pull, don't build) — much lighter
  than Multi-SWE-bench. Still: Docker wedges when grading overlaps heavy prediction on this Windows+WSL
  box ([[eval-swebench-grading-ops]]) → **sequence predict→grade; `wsl --shutdown` to unwedge**. Disk
  for ~500 instance images is non-trivial; prune per-instance after grading.
- **R2 — large TypeScript repos (the real index blocker).** SWE-PolyBench TS repos average **~8,946
  files** (vs Python ~1,928). Building a fusion index over the biggest TS snapshots is the dominant
  wall-time and a potential OOM/timeout. **Mitigation (pre-registered):** cap index build at a
  per-repo file budget with a documented include/exclude (drop `node_modules`, `dist`, vendored/binary
  — standard for our indexer); if any single instance still can't be indexed within budget, it is
  **excluded before any model run** and logged (never silently dropped, never post-hoc).
- **R3 — per-language chunk shape.** The 12-slot pack shape depends on per-language chunker/AST
  coverage; report per-language pack file/chunk counts so a shrunk Δ is attributable (Backfire B-1).
- **R4 — apply-format producibility.** Qwen3-30B may emit worse SEARCH/REPLACE on TS/Java; decompose Δ
  into attempt-rate vs correct|attempted per language (Backfire B-4).
- **R5 — harness generalization.** `local_dedup_ab.py` hardcodes SWE-Verified paths; needs a thin
  `--bench` pass. PolyBench's grader is *invoked*, not embedded.

---

## 4. Primary analysis + decision rules

**Primary endpoint (per model):** resolution rate under **SWE-PolyBench's** execution grading,
**paired McNemar exact, raw, empties=fail** — identical to the headline. Conditional (both-arms-
non-empty) reported alongside as the mechanism-decomposition channel, never as primary.

**Reporting unit:** per-model 2×2 discordant table (OFF-only-solve b, ON-only-solve c), exact McNemar
p, Δpp; the **pooled-across-models** McNemar (the direction test); and a **per-language sign summary**
(Δ direction in Java / JS / TS / Python) — descriptive, underpowered per cell, showing whether any
language reverses. We also report the **file-level retrieval recall** per arm (PolyBench's own metric)
to confirm the instrument did what it should (ON = broader file coverage, OFF = deeper within-file).

> **G-3 (binding) — direction-replication bar.** Generality is **SUPPORTED** if **PB500 pooled** shows
> a **significant positive** Δ (pooled McNemar p<0.05, Δ>0). It is **CORROBORATED (weaker)** if PB500
> pooled is directionally positive (Δ>0) with **≥3 of 4 languages** positive-signed across **both
> models**, even if the pooled p is marginal. Pre-registered success sentence: *"the recall-trap
> inversion replicates in direction on an off-the-shelf, execution-graded multilingual repair
> benchmark (SWE-PolyBench; Java/JS/TS/Python); sign positive in N/4 languages."* We claim **direction
> generality**, not magnitude transfer.

> **G-4 (binding) — what WEAKENS the paper, reported honestly.**
> - **Powered null on PB500** (MDE 4.0pp, p>0.05, |Δ|<~2pp): reported as **the effect does not
>   generalize beyond Python/SWE-Verified at fixed budget** → scope narrowed in abstract + §6.2. Goes
>   in the dead-hypothesis ledger, not buried.
> - **A clean language reversal** (a language with Δ<0, sign-stable across both models): reported as a
>   **boundary condition** tied to fix-locality / chunking (§6.2, Backfire B-1/B-2). Demotes the claim
>   from "cross-ecosystem" to "demonstrated on {languages that held}."
> - **Python-holds-but-JS/TS-reverses:** the most informative outcome — the effect is JVM/Python-shaped
>   or tied to single-file fix locality; report the §6.2 single-file stratum separately.
> - **Multi-SWE-bench (if run) disagrees with PolyBench:** report both, do not average; PolyBench
>   (powered, its own grader, MIT, base_commit-clean) carries confirmatory weight.

---

## 5. Cost + run order

**Inference cost (OpenRouter; local 4090 FREE for embedding only).** Per single-shot call ≈ 3.4K
prompt (system 0.4K + pack 1.5K + issue 1.5K) + ~1K completion. Two arms × 500 × 2 models = 2,000
generations.

| Line item | calls | Qwen3-30B @ ~$0.0005/call | gpt-5.6-sol @ ~$0.019/call |
|---|---|---|---|
| PB500 × 2 arms (per model) | 1,000 | $0.50 | $19.00 |
| Re-run / resume slack (×1.3) | — | +$0.15 | +$5.70 |
| **Inference subtotal** | — | **~$0.65** | **~$24.7** |
| **PB500 total (both models)** | — | — | **≈ $25** |
| Multi-SWE-bench mini (optional) | +800 | +$0.40 | +$15 | (only if G-1b triggers) |

**Embedding / index build:** 4090, **$0 API** (but the real cost — R2 TS repos). **Grading:** pull
GHCR images + local Docker CPU/GPU, **$0 marginal**, wall-clock + disk is the true cost.

**Bottom line on money:** PB500 across both models ≈ **$25 OpenRouter**. The binding cost is
**engineering + fusion-index wall-time on large TS repos + Docker disk**, not API credits — lead any
go/no-go with the *engineering* estimate, not the trivial $.

> **G-5 (binding) — run order & early-stop.**
> 1. **Gold-applies smoke test FIRST:** run PolyBench `--evaluate-gold` on the PB500 slice; **≥95% of
>    gold patches must flip their F2P** on a clean base checkout before any model run. This validates
>    our checkout + the shipped grader end-to-end (no predictions needed).
> 2. **Build fusion indexes** (smallest→largest; Python/Java before big TS). Log any instance that
>    can't be indexed within the R2 budget and exclude it **before** modelling.
> 3. **Qwen3-30B before gpt** (near-$0; establishes direction cheaply on the full PB500).
> 4. **Early-stop / go-no-go:** if Qwen3-30B on PB500 returns **Δ ≤ 0 with ≥2 languages reversing**,
>    PAUSE before frontier $ — investigate chunking (B-1) / fix-locality (B-2) first. If Qwen3-30B is
>    directionally positive, proceed to gpt-5.6-sol on the same PB500. **No optional stopping on the
>    significance test:** n is fixed by G-2; early-stop governs *whether to spend the next dollar*.
> 5. Multi-SWE-bench (G-1b) only after PolyBench lands and only if breadth is contested.

---

## 6. Backfire flags (where this can come back null/reversed, and what it means)

- **B-1 — polyglot chunking differs.** The 12-slot pack's shape depends on per-language chunker/AST
  coverage. If a language chunks coarser (whole-function vs sub-function), dedup-OFF "depth" may
  already be present at ON, shrinking the gap. A null here = "chunking-granularity-dependent," not
  "false" — mitigate by reporting per-language pack file/chunk counts (ON≈12-shallow vs OFF≈~5-deep).
- **B-2 — multi-file-fix fraction varies by language (ties to §6.2).** SWE-PolyBench overall is
  **~1,085 single-file vs ~625 multi-file (2–5+)**, and performance degrades past 3-file edits. §6.2
  says the effect **concentrates on single-file fixes** (+7.1pp) and **attenuates (not reverses) on
  multi-file** (+1.8pp, n.s.). TS/JS front-end fixes may skew more multi-file → a smaller *pooled* Δ
  that is a **composition** effect, not a mechanism failure. **Mitigation (pre-registered):** stratify
  PB500 by gold-file count exactly as §6.2; report the **single-file stratum Δ** separately — the
  honest generality claim lives in the single-file stratum, the pooled Δ reflects each language's
  fix-locality mix. (SWE-PolyBench's `modified_nodes` + gold file list make this stratification native.)
- **B-3 — contamination (fit caveat, not a backfire per se).** PolyBench repos are popular and
  historical → plausibly in 2026 pretraining. dedup-OFF exposes more verbatim gold lines, a possible
  memorization cue. This does not invalidate a positive result but bounds the claim; the honest hedge
  is "demonstrated on contamination-plausible historical repos," and SWE-bench-Live is the named
  backstop if the point is pressed (§1.4).
- **B-4 — weak-editor producibility on unfamiliar languages.** Qwen3-30B may emit worse SEARCH/REPLACE
  for TS/Java, inflating empties asymmetrically → a producibility (not comprehension) channel. Decompose
  Δ into attempt-rate vs correct|attempted per language; don't let an apply-format artifact masquerade
  as the effect.
- **B-5 — large-TS index truncation biases a language cell.** If R2 forces aggressive exclusion on TS,
  the surviving TS instances are a biased sub-sample. Report the TS inclusion rate and treat the TS
  cell as direction-only if inclusion <80%.

---

## 7. Bottom line

The generality arm runs on **SWE-PolyBench** (Amazon; arXiv 2504.08703; **MIT**), an **existing,
off-the-shelf, execution-graded, multilingual repair benchmark that ships its own grader** — per-
instance **pre-built GHCR Docker images**, F2P/P2P, `run_evaluation.py`, plus **native file-level and
node-level retrieval metrics** and clean `base_commit`/`patch`/`test_patch`/gold-file fields. **We
construct and graft no grader** (this is why swebench-ml is out of the generality arm — it is
retrieval-only). The pre-registered set is **PB500** (500 instances, 125 each **Java / JS / TS /
Python**), **powered** at MDE₈₀ ≈ **4.0pp** pooled — comfortably below the 5.7–7.6pp SWE-Verified
effect — with per-language sign as the direction read and Python as an internal SWE-Verified tie. Two
models already known to replicate (Qwen3-Coder-30B, gpt-5.6-sol); **≈ $25 OpenRouter**; the true cost
is fusion-index wall-time on large TS repos (R2) and Docker disk, not API credits. **Multi-SWE-bench**
(Go/Rust/C/C++, its own Docker harness — again no grafting) is the optional breadth second if
reviewers press beyond the quartet. **SWE-bench-Live** is the named contamination backstop but is
Python-only and out of scope for the language axis. If PB500 replicates positive, the paper earns
"the recall-trap inversion generalizes in direction to an off-the-shelf multilingual execution
benchmark"; if it is a powered null or a clean language reversal, we have found the effect's language
boundary and say so (G-4).

---

## Appendix — external-benchmark verification log (2026-07-16, live)

- **SWE-PolyBench** — arXiv **2504.08703** (Amazon Science); GitHub `amazon-science/SWE-PolyBench`
  (**MIT**); HF `AmazonScience/SWE-PolyBench` (2,110), `_500` (500, 125/lang), `_Verified` (README
  says **382**; HF card says **394** — minor doc discrepancy, verify exact count at fetch time).
  Langs **Java 165 / JS 1,017 / TS 729 / Python 199** (full). Grader: **pre-built per-instance Docker
  on GHCR** `ghcr.io/timesler/swe-polybench.eval.x86_64.<instance_id>:v1.1`; F2P/P2P;
  `python3 src/poly_bench_evaluation/run_evaluation.py --dataset-path … --predictions-path … --result-path …`;
  `--evaluate-gold` runs gold w/o predictions; `--node-metrics` for CST retrieval. Fields:
  `instance_id, repo, base_commit, patch, test_patch, F2P, P2P, problem_statement, language,
  Dockerfile, test_command, task_category, modified_nodes`. Ships **file-level + node-level retrieval
  metrics**. Repo scale: TS avg **~8,946 files**, Python avg **~1,928**; **~1,085 single-file vs ~625
  multi-file** fixes. **CHOSEN AS PRIMARY.**
- **Multi-SWE-bench** — arXiv **2504.02605** (ByteDance Seed); GitHub `multi-swe-bench/multi-swe-bench`;
  HF `ByteDance-Seed/Multi-SWE-bench` (**CC0** annotations; upstream project licenses on code). 7 langs
  Java/TS/JS/Go/Rust/C/C++ (**no Python**); **1,632** instances; **mini = 400** (8 langs). Harness
  `python -m multi_swe_bench.harness.run_evaluation --config …`; Docker built at eval time. Fields
  `org/repo/number/base(dict)/fix_patch/test_patch/f2p_tests/p2p_tests` — **base commit via `base.sha`,
  not a top-level `base_commit`** (extraction step). **OPTIONAL SECOND (language breadth).**
- **SWE-bench-Live** — arXiv **2505.23419** (Microsoft); HF `SWE-bench-Live/SWE-bench-Live`. **Python
  only**; per-instance Docker (RepoLaunch), F2P/P2P; fresh monthly (+50 verified/mo). **Contamination
  backstop only — does not buy the language axis.**
- **Rejected:** SWE-bench Multimodal (2410.03859 — 83.5% require image input, off-modality); SWE-gym
  (2412.21139 — training env, Python); GitBug-Java / BugsInPy / Defects4J (single-language: Java/Py/Java
  respectively); RepoBench / CrossCodeEval (**no execution/patch grader** — completion benchmarks).

---

## Run log (append-only)

**2026-08-06 — G-5 gold-smoke scope, decided before G-5 execution.** The gold-applies
validation (G-5 step 1) is scoped to the **303 instances with a non-empty patch in EITHER
arm** (the union of the weak-model A3B generation: dedupON non-empty = 241, dedupOFF
non-empty = 254, union = 303; per-language Java 91 / JavaScript 88 / Python 89 /
TypeScript 35). **Rationale:** under the empties-as-failure primary endpoint (G-2), an
instance empty in both arms is scored unresolved without the grader ever executing it, so
gold-validating the ~197 all-empty images cannot change or validate any reported table
cell. Gold-smoke on the union therefore gives *census* coverage of exactly the instances
that enter the graded paired A/B, caches the images the A/B grade reuses (no double-pull),
and fits the disk budget. G-5 is harness validation, not inference, so this is a disclosure
of scope, not a substantive deviation to the analysis. The ≥95% gold-flip gate and the
per-language escalation rule are unchanged.

---

## Run log (append-only) — 2026-08-07: G-5 gold-smoke gate outcome + frozen exclusion list

**Gate initially FAILED**, then resolved per the binding gate-failure ruling (host-config repair only, never grader/G-1).
Gold-applies smoke on the 303 non-empty-either-arm union: run 1 flipped 267/303 = **88.1%** (< 95% gate).
Per-cluster diagnosis from container logs → **host-config repair** (num-threads 4→3 to relieve concurrent-JVM memory
pressure; container network confirmed working; no `.wslconfig`, no grader source edit) + **one uniform retry**, then a
**frozen-config full re-smoke** of all 303. Result: **280 gold-valid survivors / 23 excluded (92.4% union validity)**.
The uniform retry recovered flaky failures (svelte 9→2, rocketmq 4→1, prettier/serverless/dubbo→0), confirming those
were transient, not defects.

**Primary analysis set (G-2):** N = 500 − 23 = **477** (MDE₈₀ ≈ 4.05pp, below the 5.7–7.6pp reference effect →
pooled confirmatory status retained). The 197 both-arms-empty instances remain in the denominator as failures
(grader-independent, per the 2026-08-06 scoping note). Exclusion is instance-level, arm-invariant, computable without
model outputs; paired design ⇒ removes whole pairs ⇒ cannot bias the within-pair contrast; exact McNemar is invariant
to it. Per-language survivor validity: Java 89/91 (97.8%), JavaScript 86/88 (97.7%), Python 80/89 (89.9%) — all ≥80%;
**TypeScript 25/35 (71.4%) < the pre-registered 80% inclusion floor (B-5) → reported DESCRIPTIVE-ONLY, no directional
claim** (compounding the already-fired B-4 producibility caveat). G-3 direction test therefore reads over the 3 ratable
languages (Java/JS/Python), TS indeterminate.

**Excluded instances (23), by cause-class:**

- **huggingface/transformers** (9): external-dependency-drift (cdn-lfs.huggingface.co decommissioned; model weights unfetchable; G-1 forbids mounting a host cache)
    - huggingface__transformers-14779
    - huggingface__transformers-19073
    - huggingface__transformers-25358
    - huggingface__transformers-26386
    - huggingface__transformers-29175
    - huggingface__transformers-29589
    - huggingface__transformers-29838
    - huggingface__transformers-6744
    - huggingface__transformers-7272
- **tailwindlabs/tailwindcss** (8): shipped-grader parser defect (jest tests pass + container exit 0, but the shipped TypescriptJestTW F2P matcher does not credit them; G-1 forbids editing the grader)
    - tailwindlabs__tailwindcss-211
    - tailwindlabs__tailwindcss-416
    - tailwindlabs__tailwindcss-417
    - tailwindlabs__tailwindcss-463
    - tailwindlabs__tailwindcss-553
    - tailwindlabs__tailwindcss-773
    - tailwindlabs__tailwindcss-774
    - tailwindlabs__tailwindcss-849
- **coder/code-server** (2): oracle/environment defect: gold patch fails its own shipped FAIL_TO_PASS set, persisting across the frozen-config re-smoke and one uniform retry (ungradeable; re-deriving F2P would be grader construction)
    - coder__code-server-6225
    - coder__code-server-6423
- **sveltejs/svelte** (2): oracle/environment defect: gold patch fails its own shipped FAIL_TO_PASS set, persisting across the frozen-config re-smoke and one uniform retry (ungradeable; re-deriving F2P would be grader construction)
    - sveltejs__svelte-6429
    - sveltejs__svelte-6514
- **apache/rocketmq** (1): oracle/environment defect: gold patch fails its own shipped FAIL_TO_PASS set, persisting across the frozen-config re-smoke and one uniform retry (ungradeable; re-deriving F2P would be grader construction)
    - apache__rocketmq-4122
- **trinodb/trino** (1): oracle/environment defect: gold patch fails its own shipped FAIL_TO_PASS set, persisting across the frozen-config re-smoke and one uniform retry (ungradeable; re-deriving F2P would be grader construction)
    - trinodb__trino-657
**Harness deviations disclosed (no grading code modified — G-1 intact):** (1) num-threads 4→3 (host concurrency);
(2) container run sequencing + per-batch leftover-container sweep + disk-floor guard (host ops); (3) constants.py maven
mirror `dlcdn`→`archive.apache.org` — image-BUILD fallback path only, bypassed by the pre-built GHCR images used for
all graded instances, cannot affect scoring. No parser/scoring/timeout/F2P code touched.

**Standing invariant:** the 303-union was defined by A3B generation; when gpt-5.6-sol is run, any instance with a
non-empty gpt patch outside this validated survivor set gets an incremental gold smoke under the same frozen config
before its A/B grade, same exclusion rules. No instance is graded whose gold has not passed the smoke under the
operative config.

**2026-08-07 — INCREMENTAL gold-smoke (gpt-5.6-sol frontier arm).** gpt attempted 401 instances (union), of which 275
were already gold-valid survivors, 23 already-excluded, and 103 NEW (gpt-reached, A3B-empty). Incremental gold-smoke on
the 103 under the frozen config (nt3 + one uniform retry): **62 new gold-valid survivors, 41 new exclusions.** Extended
survivor set = 280 + 62 = **342**; total exclusions = 23 + 41 = **64**; primary N remains 500 − 64 = **436**. New survivors:
Java 25 / JavaScript 25 / TypeScript 12 (no new Python — the new Python ids were all transformers, excluded on the dead CDN).
New exclusions by repo and cause-class:

- **huggingface/transformers** (19): external-dependency-drift (dead cdn-lfs model CDN; consistent with the original 9)
    - huggingface__transformers-13573
    - huggingface__transformers-13865
    - huggingface__transformers-13989
    - huggingface__transformers-19219
    - huggingface__transformers-19590
    - huggingface__transformers-23126
    - huggingface__transformers-26164
    - huggingface__transformers-27561
    - huggingface__transformers-28398
    - huggingface__transformers-28940
    - huggingface__transformers-29300
    - huggingface__transformers-29680
    - huggingface__transformers-30556
    - huggingface__transformers-30602
    - huggingface__transformers-30772
    - huggingface__transformers-30934
    - huggingface__transformers-31448
    - huggingface__transformers-3198
    - huggingface__transformers-3716
- **keras-team/keras** (6): image-build/grade failure (no result under frozen config)
    - keras-team__keras-18871
    - keras-team__keras-18977
    - keras-team__keras-19201
    - keras-team__keras-19924
    - keras-team__keras-20002
    - keras-team__keras-3983
- **tailwindlabs/tailwindcss** (6): shipped-grader parser defect (consistent with the original 8)
    - tailwindlabs__tailwindcss-109
    - tailwindlabs__tailwindcss-165
    - tailwindlabs__tailwindcss-216
    - tailwindlabs__tailwindcss-236
    - tailwindlabs__tailwindcss-445
    - tailwindlabs__tailwindcss-537
- **langchain-ai/langchain** (3): image-build/grade failure (no result under frozen config)
    - langchain-ai__langchain-19331
    - langchain-ai__langchain-20064
    - langchain-ai__langchain-4009
- **mui/material-ui** (3): image-build-failure (no pre-built GHCR image; grader build fails after retries)
    - mui__material-ui-34138
    - mui__material-ui-38788
    - mui__material-ui-40180
- **coder/code-server** (2): gold patch fails shipped F2P / no result under frozen config (persisted re-smoke+retry)
    - coder__code-server-5633
    - coder__code-server-6115
- **trinodb/trino** (1): gold patch fails shipped F2P / no result under frozen config (persisted re-smoke+retry)
    - trinodb__trino-2764
- **yt-dlp/yt-dlp** (1): gold patch fails shipped F2P / no result under frozen config (persisted re-smoke+retry)
    - yt-dlp__yt-dlp-5933
The gpt A/B is graded on the gpt-non-empty ∩ 342-survivor set; empties-as-failure; TS validity re-checked against the 80% floor.
