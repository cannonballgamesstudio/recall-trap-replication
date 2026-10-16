# Pre-registration provenance (commit identifiers of record)

Commit identifiers are from the authors' private development repository; they are listed so that the
ordering of design commits and data can be audited on de-anonymization. Each file in this directory is the
version at the time of submission (HEAD). When the first committed version differs, it is in
`as-first-committed/`. Later commits are the dated deviation/execution log that each document keeps in its
own final section. All times in this file are UTC (converted from the commit timestamps).

| document | governs | original commit | date (UTC) | later commits |
|---|---|---|---|---|
| `TRIMMED-BREADTH-PREREG.md` | Arm T / T' on the headline arms (Table VI rows 2-4) | `14ed196` | 2026-10-14 04:06 | `c201ff2` 2026-10-14 04:16; `f24c0ff` 2026-10-15 01:16; `56fa1b9` 2026-10-15 02:00 |
| `TRIMMED-BREADTH-VIOLATORS.txt` | the 27 subset-gate violators (Deviation 1) | `c201ff2` | 2026-10-14 04:16 | none |
| `CONTAMINATION-PREREG.md` | memorization checks: Branch B (gpt primary, E5 secondary) and Branch A (Sec. V-D) | `e9eede2` | 2026-10-14 13:33 | `e760340` 2026-10-15 00:52; `fc6e86e` 2026-10-15 01:57; `35f4194` 2026-10-15 01:58; `bfcf2bd` 2026-10-15 02:22; `e2890d4` 2026-10-15 12:03; `912d529` 2026-10-15 12:14; `50cbd0f` 2026-10-15 14:11; `657be52` 2026-10-15 16:56 |
| `CONTAMINATION-P1-FILTER.txt` | P1 applicability filter (issue names a gold-file basename) | `e9eede2` | 2026-10-14 13:33 | none |
| `QWEN36-PREREG.md` | Qwen3.6-27B K=12 confirmatory arm (+ Amendment 1, 16k->32k) | `adc864d` | 2026-07-17 21:24 | none |
| `GPT-LOGGED-REPLICATION-PREREG.md` | gpt-5.6-sol logged re-run (confirmatory) + funnel | `c35850a` | 2026-08-09 03:47 | `a6b9697` 2026-08-09 04:09; `1d30219` 2026-08-09 22:52 |
| `GENERALITY-BENCH-PREREG.md` | multilingual SWE-PolyBench test (Table IV) | `492c432` | 2026-08-06 17:36 | `7d0016d` 2026-08-06 18:43; `b9e36b0` 2026-08-07 07:58; `e3e1ef0` 2026-08-08 01:04 |
| `AGENTIC-BENCH-PREREG-2026-07-15.md` | agentic-harness arms | `211261a` | 2026-07-16 05:14 | none |
| `G2-RANDOM-CHUNK-PREREG.md` | random-chunk-per-file control (Class 2 design note: no pre-data commit) | `e188957` | 2026-08-08 20:24 | none |
| `BM25-AGNOSTIC-PREREG.md` | BM25 arm TOST design (Class 2 design note: no pre-data commit) | `e188957` | 2026-08-08 20:24 | none |
| `TURNCAP-SWEEP-PROTOCOL.md` | read-budget sweep (Table V; exploratory) | never committed | written 2026-07-16 before the runs (file date) | none; named `TURNCAP-SWEEP-PREREG.md` in the authors' repository |
| `CLEAN-CONTROL-DESIGN.md` | dedup design audit | `470a1c7` | 2026-07-16 01:07 | none |
| `PREREG-LEDGER.md` | ledger of design documents and provenance classes (as of its last commit) | `e188957` | 2026-08-08 20:24 | `7d8a65b` 2026-08-08 20:49; `c35850a` 2026-08-09 03:47; `4df8d5e` 2026-08-09 03:47 |
| `plans/2026-07-14-e1-e2-allocation.md` | gpt discovery draw + DeepSeek allocation (design-committed, D) | `1eaab36` | 2026-07-14 16:56 | none |
| `plans/2026-07-14-oracle-ceiling.md` | wider program (hypothesis registry) | `eae0aeb` | 2026-07-14 13:38 | none |
| `plans/2026-07-14-e0-missing-cell.md` | wider program (hypothesis registry) | `dbc1289` | 2026-07-14 15:42 | none |
| `plans/2026-07-14-c1-delivery-mode-control.md` | wider program (hypothesis registry) | `8b26d65` | 2026-07-14 19:29 | none |
| `plans/2026-07-13-g-plane-design.md` | wider program (hypothesis registry) | `023bc57` | 2026-07-13 23:06 | `b3b693d` 2026-07-13 23:34 |
| `LOCAL-B1B3-ADDENDUM-PREREG.md` | single-retriever three-seed replication: ON/OFF/T, TM, P (= W) (Table VI row 1, Table VII, Fig. 1 rates) | `f600ac8` | 2026-10-15 20:00 | `33aa630` 2026-10-15 23:40; `ee7cb20` 2026-10-15 23:48; `66e31b2` 2026-10-16 16:48; `eeadc36` 2026-10-16 18:35; `43632a2` 2026-10-16 18:39; `6d2b870` 2026-10-16 19:54; `9cd8199` 2026-10-17 02:31 |
| `TM-RULING-2026-10-15.md` | TM padding-rule deviation, replaced before any TM generation (Sec. IV) | `89d1aee` | 2026-10-15 23:47 | none |
| `SPHINX8475-RULING-2026-10-16.md` | sphinx-8475 Class-P harness timeout: scored unresolved (the ruling's default; primary since D-8475b, n=478), with exclusion (n=477) and the upper bound as sensitivities (Sec. IV) | `82981da` | 2026-10-16 16:57 | none |

## Full commit log per document (subject lines; times UTC)

### TRIMMED-BREADTH-PREREG.md
- `14ed196` 2026-10-14 04:06: prereg: trimmed-breadth arm T + oracle-select bound O (decompose dedup effect into depth vs file-trim)
- `c201ff2` 2026-10-14 04:16: prereg(T): Deviation 1 -- subset gate failed at 94.6%; proceed on 473 + T' sensitivity on 27; arm O deferred
- `f24c0ff` 2026-10-15 01:16: prereg(T): post-hoc clarification -- pack-size confound direction was mis-stated in sections 4 and 8; no rule or verdict depends on it
- `56fa1b9` 2026-10-15 02:00: prereg(T): grading-validity note -- both T analyses withdrawn (Docker Hub 429 harness errors: Qwen 136/248, gpt 174/395); regrade pending

### TRIMMED-BREADTH-VIOLATORS.txt
- `c201ff2` 2026-10-14 04:16: prereg(T): Deviation 1 -- subset gate failed at 94.6%; proceed on 473 + T' sensitivity on 27; arm O deferred

### CONTAMINATION-PREREG.md
- `e9eede2` 2026-10-14 13:33: prereg: contamination check (Branch B memorization-stratified test, primary; Branch A post-cutoff sign-consistency, descriptive)
- `e760340` 2026-10-15 00:52: prereg(fanout): record commit hash in status line
- `fc6e86e` 2026-10-15 01:57: prereg(contam): §E log -- prefetch done, ungated manipulation checks (B->C 8.3%), local probe launch, interruption by host memory reaper
- `35f4194` 2026-10-15 01:58: prereg(contam): §E design-authority ruling on Branch A (binding population = gold survivors; run paid arms; retrieval-shifted reporting)
- `bfcf2bd` 2026-10-15 02:22: prereg(contam): §E execution-log entry -- Tier 1 probes generated ($15.50), P2 grading killed by host memory reaper at 173/262
- `e2890d4` 2026-10-15 12:03: prereg(contam): M-table sha256 for gpt-5.6-sol committed before join (low-M share 0.094; power shortfall disclosed pre-join)
- `912d529` 2026-10-15 12:14: prereg(contam): §E erratum -- withdrawn Arm-T reference values in §B.6; E5 uses regraded T
- `50cbd0f` 2026-10-15 14:11: prereg(contam): §E gold gate (105/108 survivors) + survivor manipulation checks sha a4f1ee9a (B->C 8.57%, retrieval-shifted) committed before join
- `657be52` 2026-10-15 16:56: prereg(contam): §E Branch A results (2 seeds, 0 harness errors; A1 sign-consistent, retrieval-shifted) + local Qwen3-Coder M-table sha 49dfe773 committed before qwen3coder join

### CONTAMINATION-P1-FILTER.txt
- `e9eede2` 2026-10-14 13:33: prereg: contamination check (Branch B memorization-stratified test, primary; Branch A post-cutoff sign-consistency, descriptive)

### QWEN36-PREREG.md
- `adc864d` 2026-07-17 21:24: docs(prereg): AMEND Qwen3.6 decoding — 16k→32k before any regen (gate fired, disclosed)

### GPT-LOGGED-REPLICATION-PREREG.md
- `c35850a` 2026-08-09 03:47: prereg(gpt-logged-replication): pre-data anchor for the logged gpt re-run + funnel
- `a6b9697` 2026-08-09 04:09: prereg(gpt-logged-rep): run-time addendum — gen launched 2026-08-09, fin=length gate PASSED (0%)
- `1d30219` 2026-08-09 22:52: prereg(gpt-logged-rep): RESULT — clause-d REPLICATION CONFIRMED, funnel supports depth

### GENERALITY-BENCH-PREREG.md
- `492c432` 2026-08-06 17:36: docs(prereg): register GENERALITY-BENCH (PolyBench) plan before execution grading
- `7d0016d` 2026-08-06 18:43: docs(prereg): log G-5 gold-smoke scope (303 non-empty-either-arm union) before execution
- `b9e36b0` 2026-08-07 07:58: docs(prereg): freeze G-5 exclusion list (23) + survivor set (280/303) before PolyBench A/B
- `e3e1ef0` 2026-08-08 01:04: docs(prereg): incremental gpt gold-smoke — 62 new survivors, 41 new exclusions (N=436) before gpt A/B

### AGENTIC-BENCH-PREREG-2026-07-15.md
- `211261a` 2026-07-16 05:14: paper(recall-trap): major DRAFT surgery to settled narrative

### G2-RANDOM-CHUNK-PREREG.md
- `e188957` 2026-08-08 20:24: docs(paper): v5.1 pre-registration provenance relabel (methodology reviewer binding ruling)

### BM25-AGNOSTIC-PREREG.md
- `e188957` 2026-08-08 20:24: docs(paper): v5.1 pre-registration provenance relabel (methodology reviewer binding ruling)

### CLEAN-CONTROL-DESIGN.md
- `470a1c7` 2026-07-16 01:07: docs(paper): DeepSeek verdict corrected to SUPPORTS (producibility channel); raw = primary

### PREREG-LEDGER.md
- `e188957` 2026-08-08 20:24: docs(paper): v5.1 pre-registration provenance relabel (methodology reviewer binding ruling)
- `7d8a65b` 2026-08-08 20:49: docs(paper): v5.1b Ruling-6 remainder — wider-program hashes + prereg lint
- `c35850a` 2026-08-09 03:47: prereg(gpt-logged-replication): pre-data anchor for the logged gpt re-run + funnel
- `4df8d5e` 2026-08-09 03:47: docs(ledger): fill GPT-LOGGED-REPLICATION-PREREG commit hash c35850a

### plans/2026-07-14-e1-e2-allocation.md
- `1eaab36` 2026-07-14 16:56: feat(gplane): E1 (pack+tools) + E2 (dedup-off depth pack), pre-registered

### plans/2026-07-14-oracle-ceiling.md
- `eae0aeb` 2026-07-14 13:38: docs(plan): pre-register the oracle-ceiling arm BEFORE any instance runs

### plans/2026-07-14-e0-missing-cell.md
- `dbc1289` 2026-07-14 15:42: feat(gplane): E0 — the missing cell (oracle pack + TOOLS ON), pre-registered

### plans/2026-07-14-c1-delivery-mode-control.md
- `8b26d65` 2026-07-14 19:29: feat(gplane): C1 — the delivery-mode control (push vs pull, prompt held fixed)

### plans/2026-07-13-g-plane-design.md
- `023bc57` 2026-07-13 23:06: docs(plan): G-plane design — trust-the-retriever agent policies, pre-registered before any run
- `b3b693d` 2026-07-13 23:34: docs(plan): AMEND G2 before any run — Edit requires prior Read, so Edit-only was an invalid instrument; G2 becomes pack-scoped Read via PreToolUse hook (disclosed)

### LOCAL-B1B3-ADDENDUM-PREREG.md
- `f600ac8` 2026-10-15 20:00: prereg: local B1-B3 addendum (single-instance ON/OFF/T x3 seeds, token-matched T, practitioner baseline) -- committed before any pack build
- `33aa630` 2026-10-15 23:40: prereg(B1-B3): §12 gate results (subset 95.6% PASS, T identity 100%), pack sha 80382193, serving/top_p and GLMM engine logged; build/analysis scripts -- committed before any B1 output is graded or read
- `ee7cb20` 2026-10-15 23:48: prereg(b1b3): §12 D-TM (TM padding rule (c), b2 packs sha 7bc29262) + D1 revisited -- committed before any TM call
- `66e31b2` 2026-10-16 16:48: prereg(b1b3): §12 sphinx-8475 persistent harness timeout logged (unscored, analysis halted pending ruling), serving-time correction; nested-subset secondary in analyze script -- committed before any B1/B2 outcome is read
- `eeadc36` 2026-10-16 18:35: prereg(b1b3): §12 D-8475 (sphinx-8475 Class P; owner primary = exclusion, scoring = sens 1, upper = sens 2; TM s01 Class P, TM s02 0 errors) -- committed before any §7 analysis
- `43632a2` 2026-10-16 18:39: prereg(b1b3): §12 -- §7 run for B1+B2 (result sha prefixes recorded), B3 launched, props-file disclosure
- `6d2b870` 2026-10-16 19:54: prereg(b1b3): §12 D-8475 supersession note + B3 graded (0 errors) and §7 rerun with P; version b1b3 ops/launch scripts and props_8090_b3.json
- `9cd8199` 2026-10-17 02:31: prereg(b1b3): §12 D-8475b -- owner reverts sphinx-8475 primary to scored-unresolved (post-results, disclosed; verdicts identical across handlings)

### TM-RULING-2026-10-15.md
- `89d1aee` 2026-10-15 23:47: prereg(B1-B3): methodology reviewer TM ruling (c) -- pad from Q-ON48 hits outside files(ON12); D1 cause revised (fusion depth non-prefix-stability); committed before TM is built or any B1 output graded

### SPHINX8475-RULING-2026-10-16.md
- `82981da` 2026-10-16 16:57: prereg(b1b3): methodology reviewer ruling on sphinx-8475 -- patch-induced deadlock (Class P) scored unresolved, sensitivities exclude/upper; Class I/P rule binds TM and B3 -- committed before any outcome read

Notes:

- The Branch B join was mechanically blocked until each M table's sha256 was committed: gpt-5.6-sol `e2890d4` (M table sha256 b849fdf1...), Qwen3-Coder-30B `657be52` (49dfe773...). Branch A outcome-blind checks: `50cbd0f` (manip_checks.json sha256 a4f1ee9a...). See README, "Hashes of record".
- The retrieval code used for every pack is the revision `4fab615` (2026-07-14 22:47 UTC), shipped in code/retrieval/. The single-retriever replication served all of its packs from one process started from that revision.
- Times written inside the documents themselves are as the authors wrote them (local time, EDT, where marked).
