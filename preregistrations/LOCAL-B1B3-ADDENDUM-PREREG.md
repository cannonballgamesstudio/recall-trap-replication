# Pre-registration addendum: local single-daemon replication (B1), token-matched T (B2), practitioner baseline (B3)

Status: PRE-REGISTRATION ADDENDUM to `TRIMMED-BREADTH-PREREG.md`. Written 2026-10-15, before any pack
is built, any generation is run, or any grading is done for these arms. Commit this file and record the
commit hash before the first retrievald query. Do not edit the arms, gates, estimands, predictions, or
interpretation rules after that point. Put deviations in the dated log in §12.

Design authority: owner-approved design of 2026-10-15 (B1–B3, local only, $0).

---

## 1. Purpose and relation to the headline

This addendum **replicates and does not replace** the headline. The headline ON/OFF contrasts and the
Trimmed-Breadth T results stay as reported. B1–B3 answer three follow-up questions on one local model,
at $0:

1. **B1.** Does the decomposition (OFF − ON) = (OFF − T) + (T − ON) hold when all three packs come from
   **one pinned daemon**, so that the TRIMMED-BREADTH §2 structural fact holds by construction rather
   than approximately (TRIMMED-BREADTH D1: 94.6% subset, two daemons)? Three decoding seeds per arm give
   the run-to-run variance that the headline lacks.
2. **B2.** Is the T vs OFF gap a token-count effect? Arm TM holds T's content fixed and pads it to OFF's
   size with non-T material.
3. **B3.** How does a practitioner's obvious alternative (keep T's files, widen each chunk with
   surrounding lines to OFF's per-file size) compare to OFF and T?

## 2. Pinned retrieval stack

- **Worktree:** `code/retrieval`, HEAD `4fab615b4fe5148a8a8b7121c2e058f47a16366d`
  ("fix(rag): per-request dedup override"), clean. The executor verifies that `ragfusion` imports from the
  worktree's `src/` before the first query.
- **One daemon** (port `:8083`), started from the worktree with:
  - `RETRIEVALD_BACKEND=fusion`
  - `RETRIEVALD_REGISTRY_DB=<EVAL_ROOT>\registry.db` (the Verified refs are the 539 `ready` refs under
    `config_hash='p5'`, the headline index; no rebuild)
  - `RETRIEVALD_EMBED_MODEL=openai:Qwen/Qwen3-Embedding-8B`, `RETRIEVALD_DIMS=4096`
  - `OPENAI_BASE_URL=http://127.0.0.1:8082`, `OPENAI_API_KEY=sk-noauth`
  - `RETRIEVALD_DEFAULT_IDENTITY=local` (caller-login fallback; does not enter retrieval)
  - every other setting at the 4fab615 `RetrievaldConfig` default: `dedup_file=True`, `fusion_lex_mode=ids`,
    `fusion_w_graph=1.0`, `fusion_w_prior=0.3`, instruct-prefixed query. `RETRIEVALD_QUERY_DEDUP_FILE` is
    **not** set.
  - Launch: `python -m uvicorn ragfusion.retrievald.server:build_app --factory --host 127.0.0.1 --port 8083`.
- **Embedder:** `<LLAMA_DIR>\llama-server.exe -m <LLAMA_DIR>\Qwen3-Embedding-8B-Q8_0.gguf --embeddings
  --host 127.0.0.1 --port 8082 -ngl 99 -c 8192`. The headline index used the same GGUF; GPU vs CPU
  arithmetic can perturb query embeddings in the last digits (disclosed, as in CONTAMINATION-PREREG A.3).
- **Queries.** All via `POST /v1/query` with `repo`, `branch=<instance_id>`, `text=problem_statement[:6000]`,
  `mode="hybrid"`, `code_only=true`, and an explicit per-request `dedup`. For each instance, four queries
  against the same daemon:

  | query | dedup | limit | use |
  |---|---|---|---|
  | Q-ON12 | true | 12 | ON pack |
  | Q-OFF12 | false | 12 | OFF pack |
  | Q-ON48 | true | 48 | TM padding candidates (ranks 13+); rank/score record |
  | Q-OFF48 | false | 48 | rank/score record |

  Every hit's (file, line, symbol, kind, score, rank) is stored for all four queries in
  `work/p5\b1b3_prov.json`. Packs are rendered with the pinned `format_pack` from
  `scripts/eval/g_plane_prompts.py`. A failed query raises and is retried; an instance whose queries fail
  three times is excluded and listed.
- **Known source of within-file order differences, stated in advance.** With `code_only=true` and
  dedup on, the fusion backend fetches 5 × limit candidates; with dedup off it fetches 3 × limit. The
  candidate depth therefore differs between Q-ON12 (60) and Q-OFF12 (36) even inside one daemon, and so
  can the within-file order. This is why concordance (§4.3) is reported, not gated.

## 3. Arms

All arms use the same renderer, `SYS` prompt, user-turn template, edit format (SEARCH/REPLACE), apply
logic, and grading. Pack file: `work/p5\b1b3_packs.json`, arm keys exactly `ON`,
`OFF`, `T`, `TM`, `P`. Its sha256 is logged in §12 before generation.

- **ON.** The Q-ON12 hits, as served: up to 12 files × 1 chunk.
- **OFF.** The Q-OFF12 hits, as served: the raw top-12 chunks, about 5 files with several chunks each.
- **T (trimmed breadth).** OFF's file set, in OFF rank order (order of each file's first OFF chunk).
  Each file gets exactly one chunk: the ON chunk for that file, byte-identical (asserted on file, start
  line, and snippet text). No filler.
- **TM (token-matched T).** T's chunks in T order, then padding chunks appended in rank order. Candidates
  are the Q-ON48 hits at rank ≥ 13 whose file is not in files(T), one chunk per file (the dedup-ON
  ranking already gives one per file). Greedy closest-match rule on rendered character count, with
  target = `len(format_pack(OFF))`: append the next candidate if it brings `len(format_pack(TM))`
  strictly closer to the target, otherwise stop. Chunks are never truncated. If candidates run out
  first, TM stays short and the instance is logged.
- **P (practitioner baseline).** T's files, in T order, one chunk each. Each ON chunk is widened with
  adjacent source lines from the file at `base_commit` (read with `git show base_commit:path` from the
  swe_bench cache clone) until its snippet length reaches that file's **OFF per-file character count**
  (the sum of `len(snippet)` over the file's OFF chunks). Widening rule: alternate one line below, then
  one line above, starting below; stop before the line that would exceed the target; if one side hits a
  file boundary, continue on the other side. If the ON chunk already meets or exceeds the target, it is
  left unchanged. The rendered header uses the new start line, with the ON chunk's symbol and kind. If
  the ON snippet cannot be located verbatim in the base_commit file, that file keeps its unwidened ON
  chunk and the case is logged.

Decomposition, exact on the same paired instances and draws:

    (OFF − ON) = (OFF − T) + (T − ON) = Δ_depth-at-fixed-files + Δ_file-trim
    (OFF − T)  = (OFF − TM) + (TM − T) = Δ_content-at-fixed-tokens + Δ_tokens-at-fixed-content

## 4. Construction gates (re-run of TRIMMED-BREADTH §5; computed before any generation)

1. **Subset:** fraction of instances with files(OFF) ⊆ files(ON). Expected ≈ 100%. **Threshold ≥ 95%.**
   Violating instances are excluded from T, TM, and P and listed. If fewer than 95% satisfy it, stop
   before generation and log a deviation; the design authority decides.
2. **Chunk identity for T:** every T slot equals the ON chunk for its file. **100% required**; otherwise
   stop.
3. **Concordance (reported, not gated):** over files in files(OFF) ∩ files(ON), the share where the ON
   chunk equals the **top-ranked OFF chunk** of that file. Also reported: the share where the ON chunk
   appears anywhere among that file's OFF chunks. TRIMMED-BREADTH D1 reference (two daemons): 88.6% and
   94.4%.
4. **Size table (reported):** per arm, mean slot count and mean rendered pack characters; TM/OFF and
   P/OFF character ratios (mean, and share of instances within ±10%); number of TM instances that ran out
   of candidates; number of P files left unwidened, and why.
5. **Prefix consistency (reported):** share of instances where Q-ON48's top 12 equals Q-ON12's hits, and
   the number of TM padding files that also appear in files(ON).

**Instance set.** n = 500 (`instances_verified.json`). If gate 1 passes at 100%, all 500 are analysed.
If it passes below 100%, ON and OFF are still generated on all 500, but every contrast involving T, TM,
or P is analysed on the passing set, and OFF − ON is reported on both the passing set (for the exact
decomposition) and all 500.

## 5. Model, serving, and decoding

- **Model:** `<LLAMA_DIR>\Qwen3-Coder-30B-A3B-Instruct-UD-Q5_K_XL.gguf`.
- **Serving (reference):** `<LLAMA_DIR>\llama-server.exe -m <gguf> -c 16384 --parallel 2 --jinja -ngl 99
  --host 127.0.0.1 --port 8090`. The per-slot context is 8192 tokens, so a long prompt can end a reply by
  context before `max_tokens` is reached. This is the same for every arm, and is reported through
  `finish_reason` and `prompt_tokens` per arm (§7.3).
- **Generation:** `scripts/eval/local_dedup_ab.py` in fan-out mode, one call per arm:

      python local_dedup_ab.py --arm <ARM> --packs-file b1b3_packs.json --ids-file <set.txt>
          --n-samples 3 --temperature 0.2 --top-p <TOP_P> --per-sample-seed --nonce
          --max-tokens 6000 --max-attempts 3 --timeout 900 --concurrency 2 --model-tag b1b3q30

  with `LOG_RESPONSE_TEXT=1`. For P: `--n-samples 1`. Output: `preds_local_b1b3q30_<ARM>_s{00,01,02}.jsonl`
  (one valid swebench predictions file per seed) and `raw_local_b1b3q30_<ARM>_fanout.jsonl`.
- **Fan-out mode supports this use (checked 2026-10-15).** Each (instance, j) is one independent
  single-shot call. j indexes the seed, and each sample index gets its own predictions file. Infra
  failures are retried up to 3 times with a fresh nonce, and a rerun resumes missing (instance, j)
  units. Three differences from the headline's legacy single-shot payload apply equally to every arm and
  are disclosed:
  - (a) A one-line nonce, `Request nonce: <16 hex> (opaque request id; ignore it).`, is appended to
    the user turn.
  - (b) `seed` is sent.
  - (c) `top_p` is always sent, because fan-out mode cannot omit it. To match the legacy payload's
    effective sampling, `<TOP_P>` is set to the server's default `top_p`. That value is read from
    `GET /props` (`default_generation_settings`) at launch and logged in §12 before the first call.
  - All other samplers stay at server defaults. Temperature 0.2 and max_tokens 6000 match the headline.
- **Seeds (fixed hash scheme, as implemented in `local_dedup_ab.py`):**
  - Seed: `seed(iid, arm, j) = int.from_bytes(sha256("seed|{iid}|{arm}|{j}")[:4], "big") & 0x7FFFFFFF`.
  - Index and arm: j ∈ {0, 1, 2}, arm ∈ {ON, OFF, T, TM, P} (exact pack-file keys).
  - Nonce: `sha256("nonce|{iid}|{arm}|{j}|{attempt}")[:16]`.
  - Because `arm` enters the hash, draws in different arms are independent draws, not common random
    numbers. "Seed j" is a draw index shared across arms for pairing.
  - With `--parallel 2` continuous batching, a fixed seed is not bitwise-reproducible across runs. Seeds
    are recorded for audit, not exact replay.
- **Runs:** B1 = {ON, OFF, T} × 3 seeds (9 prediction files); B2 = TM × 3 seeds (3 files);
  B3 = P × 1 seed (1 file).
- **B3 condition:** P generation runs only if every B1 and B2 file is fully graded (0 harness errors)
  by 2026-10-18 21:00 EDT. P packs are built in any case (no GPU). If the deadline is missed, B3 is
  logged as not run.

## 6. Grading

- Official harness: `python -m swebench.harness.run_evaluation --dataset_name
  princeton-nlp/SWE-bench_Verified --predictions_path <file> --run_id <label> --max_workers 6
  --cache_level instance` (max_workers within 4–8). B1's 9 files are graded in one Docker session, and
  B2's 3 files in the next.
- **Docker Hub pulls are authenticated.** `docker login` state is verified before every session. This
  fixes the cause of the 429 errors in TRIMMED-BREADTH.
- WSL page caches are dropped before and after every grading batch.
- **Harness errors are infrastructure failures, never model failures.** Each report's `error_instances`
  is checked before any analysis. Errored instances are regraded with the same run_id (the harness skips
  completed instances), and retry passes repeat until errors reach 0. If an instance errors
  deterministically in 3 consecutive passes with the same cause, stop and log a deviation. It is not
  scored.
- Empty patches are submitted and count as unresolved. A (instance, j) with no predictions row after
  retries counts as never-submitted, and its pair is excluded for that seed.

## 7. Analysis

### 7.1 Estimands

Raw resolve difference, on pairwise-attempted instances, for:

**OFF − ON, OFF − T, T − ON, TM − T, OFF − TM** (B1/B2), and **P − OFF, P − T** (B3).

Each is reported **per seed** (j = 0, 1, 2) and **pooled**. Pooled = the resolve-rate difference over
all instance × seed draws on the common set. For P (1 seed), the comparison arm's three draws are
averaged per instance, and the per-seed j = 0 contrast is also reported.

### 7.2 Inference

- **Primary (pooled): instance-paired cluster bootstrap.** Instances are resampled with replacement,
  and all draws of an instance (every arm, every seed) move together. B = 10,000, RNG seed 20261015.
  Percentile 95% CI. "Significant" for the pooled verdict means the 95% CI excludes 0.
- **Per seed:** exact McNemar with b/c reported (TRIMMED-BREADTH §7).
- **Robustness:** wild cluster bootstrap by repository (Webb 6-point weights, G = 12) on per-instance
  seed-averaged differences.
- **Mixed model:** mixed logit `resolved ~ arm + (1 | instance) + (1 + arm | seed)`, fitted per
  contrast pair, reporting the arm effect and the **between-seed variance of Δ** (the random-slope
  variance).
  - With 3 seeds the slope variance is weakly identified. If the fit is singular or does not converge,
    report `(1 | instance) + (1 | seed)`, plus the empirical between-seed variance of the three per-seed
    Δs.
  - Engine: R `lme4::glmer` (Laplace) if installable at analysis start. Otherwise statsmodels
    `BinomialBayesMixedGLM` (variational Bayes; posterior mean and SD).
  - The engine is chosen and logged before any model is fitted. The mixed model is secondary and
    does not enter any verdict.
- **Equivalence (TOST):** ±3pp margin, α = 0.05 each side. Equivalence is declared if the pooled
  instance-bootstrap **90%** CI lies inside (−3pp, +3pp).

### 7.3 Secondary

Both-non-empty conditional; parse → apply → test funnel from the raw logs; empty, `finish_reason=length`
and instant-EOS rates per arm; mean `prompt_tokens` and `completion_tokens` per arm; served rank and score
distributions per arm, from the limit-48 records.

## 8. Verdict rule (unchanged from TRIMMED-BREADTH §4, applied to the seed-pooled estimate)

Let G = pooled OFF − ON on the decomposition set.

- If pooled Δ_depth (OFF − T) ≥ 60% of G and OFF − T is significant (§7.2 pooled), report
  **"depth carries the effect"**.
- If pooled Δ_trim (T − ON) ≥ 60% of G and T − ON is significant, report **"file trimming carries the
  effect"**.
- Otherwise report **"both components contribute; the partition is not resolved at this n"**.

No outcome is described as a refutation. "Refute" is not used.

## 9. Predictions (fixed now; every outcome is reportable)

1. **Depth carries:** the B1 pooled verdict is "depth carries the effect".
2. **Trim is negligible:** T − ON is equivalent to 0 within ±3pp (TOST, §7.2).
3. **TM ≈ T:** TM − T is equivalent to 0 within ±3pp (TOST). This is what the depth account predicts
   at fixed content.
4. **OFF > TM:** pooled OFF − TM > 0 (95% CI lower bound > 0).
5. B3 (if run) has no directional prediction. P − OFF and P − T are reported descriptively with 95% CIs.

Reading of B2: if (3) and (4) both hold, the OFF − T gap is content (extra same-file chunks), not token
count. If TM − T > 0 and OFF − TM ≈ 0, the gap is attributable to pack size, and the paper says so.

## 10. Resources, sequencing, and cost

- **GPU and Docker never overlap.** The order is:
  1. Wait until the running fan-out calibration (`fanout_calib`) has finished and no `llama-server`
     process is running (`nvidia-smi` and the process list).
  2. Start the embedder (:8082) and the daemon (:8083).
  3. Prefetch all four queries per instance.
  4. Stop the embedder.
  5. Build packs and run the gates (CPU).
  6. Start Qwen (:8090) and generate B1, then B2 (then B3 if eligible).
  7. Shut down `llama-server`.
  8. Drop WSL caches.
  9. Grade.
- Long jobs are launched as one-shot Task Scheduler tasks, deleted after use, never as session
  background shells.
- **The fan-out pilot's generation (FANOUT-PILOT-PREREG) is deferred** until the B1–B3 GPU phase ends.
  This executor does not touch the fan-out pilot.
- **Cost: $0.** No paid API calls; local GPU and Docker only.

## 11. Threats

- Single model (Qwen3-Coder-30B-A3B), low base rate (headline reference 33/500 ON and 62/500 OFF).
  Three seeds raise the effective draw count, but not the instance count.
- TM pads with ranks 13+ by design, so its padding is lower-ranked, other-file material. TM − T
  therefore measures adding lower-ranked breadth at OFF's size, not adding arbitrary tokens.
- P's widened lines are adjacent source text, not retriever-selected chunks. This is intended: it is
  the practitioner alternative.
- Per-slot context of 8192 tokens: larger packs (OFF, TM, P) leave less completion room than T. This
  is reported through `finish_reason` and `prompt_tokens`.
- The nonce line and explicit `top_p`/`seed` make prompts and payloads differ from the headline's
  legacy payload. For that reason, B1 arms are compared only with B1 arms, never with the headline Qwen
  arms.

## 12. Deviations and hash log (append-only, dated)

_(empty at registration)_

**2026-10-15 19:15–19:50 EDT: retrieval, gates, packs (executor). Addendum commit f600ac8.**
- **Sequencing.** Started after `fanout_calib` logged `EXIT=0` (19:15) and no `llama-server` was
  running (GPU 1.6 GB baseline). One-shot task `b1b3_retrieval` (deleted after use):
  - started embedder :8082 (`-ngl 99 -c 8192`) and the pinned daemon :8083;
  - verified the pin: `ragfusion` loaded from `code/retrieval`, HEAD 4fab615b, tracked tree
    clean;
  - smoke query (astropy-12907, ON12) reproduced the headline ON file set;
  - prefetched 500 × 4 queries with 0 failures (19:15:58 → 19:35:14);
  - then stopped the embedder and the daemon.
  - Raw provenance: `p5\b1b3_prov.json`.
- **Gate 1 (subset): PASS, 478/500 = 95.6%** (threshold 95%). The 22 violators are excluded from T, TM
  and P. They are:
  - astropy-13453;
  - django-11740, -12125, -12262, -12273, -13212, -13279, -14404, -14580, -14855, -15037, -15525,
    -17029;
  - matplotlib-23314 (the missing file is a gold file: `lib/mpl_toolkits/mplot3d/axes3d.py`);
  - xarray-4966; pylint-6386, -7080; sklearn-25973; sphinx-9711; sympy-15875, -20801, -21379.
  - Full list in `p5\b1b3_gates.json`. 21 of the 22 are also among the 27 two-daemon violators of
    TRIMMED-BREADTH D1; django-15525 is new.
- **Gate 2 (T chunk identity): PASS, 2460/2460 = 100%.**
- **Concordance (reported):** ON chunk = top OFF chunk of its file in 2301/2609 = 88.2%; ON chunk among
  that file's OFF chunks in 2449/2609 = 93.9%. These match the two-daemon values (88.6%, 94.4%).
  One daemon therefore does **not** bring files(OFF) ⊆ files(ON) to ≈100% and does not raise
  concordance. The §2 explanation applies (dedup-ON fetches 5 × limit, dedup-OFF 3 × limit, and the
  fusion ranking depends on candidate depth). TRIMMED-BREADTH D1's attribution to "two daemons" is
  thus at best partial. Reported, not acted on.
- **Prefix consistency (reported): 0/500.** Q-ON48's top 12 never equals Q-ON12. Fusion scores are
  depth-relative (rank 1 scores 60 at limit 12 and 240 at limit 48), so the limit-48 ranking is a
  re-ranking over a deeper candidate pool, not an extension of the limit-12 ranking. As a result,
  1006 of TM's padding chunks (about 2.1 per instance) come from files that are in files(ON12) but
  not in files(T). This is allowed by the §3 rule as written (rank ≥ 13 in Q-ON48, file ∉ files(T)).
  It is **flagged to the design authority** because "ranks 13+" was presumably meant as material
  beyond ON's 12. TM has not been generated. B2 waits for that decision, and B1 (ON/OFF/T) does not
  depend on it.
- **Sizes (means).**

  | arm | slots | rendered chars | n |
  |---|---|---|---|
  | ON | 11.93 | 6002 | 500 |
  | OFF | 12.00 | 6322 | 500 |
  | T | 5.15 | 2799 | 478 |
  | TM | 12.90 | 6323 | 478 |
  | P | 5.15 | 4972 | 478 |

  - TM/OFF chars: mean 1.000, 99.8% within ±10%. 2 instances ran out of candidates
    (requests-5414, -6028).
  - P/OFF chars: mean 0.901, 55.7% within ±10%. P per file: 1308 widened, 1146 unchanged (the ON
    chunk was already ≥ the file's OFF character count), 6 located but not widened, 0 unlocated.
- **Implementation notes (no protocol change).**
  - (a) P locates the ON snippet as a verbatim substring of the base_commit file. Served snippets
    drop the first line's indentation and can end mid-line, so P's chunk text is the full source
    lines covering the match, then widened per §3. When the snippet occurs more than once, the
    occurrence nearest the declared line is used.
  - (b) The first build failed to read source for 326 P files: the sympy, matplotlib and xarray
    caches are non-bare clones, and `git --git-dir` fails on them. Fixed (`git -C`) and rebuilt
    before any generation. ON/OFF/T are unaffected (they do not read source).
- **Packs:** `p5\b1b3_packs.json` sha256 `80382193ed00186ba324af7b0333ed5e7126faecb7dfbc254ad919091248d0e9`
  (first, superseded build kept as `p5\b1b3\b1b3_packs_build1.json`). Instance sets:
  `p5\b1b3_ids_all.txt` (500), `p5\b1b3_ids_T.txt` (478).
- **Serving (19:51).**
  - `llama-server` b9837 with `-c 16384 --parallel 2 --jinja -ngl 99`.
  - `/props`: per-slot n_ctx 8192, total_slots 2.
  - Default sampling: top_p 0.95, top_k 40, min_p 0.05, repeat_penalty 1.0.
  - **`--top-p 0.95`** is used for all arms (§5c).
- **GLMM engine (§7.2), chosen before any fit:** statsmodels 0.15.0 `BinomialBayesMixedGLM.fit_vb`. R is
  not installed, and a system-wide R install was not attempted.

**2026-10-15 (D-TM): TM padding rule corrected before any TM generation; design-authority ruling in
`TM-RULING-2026-10-15.md`. Outcome-blind: nothing graded or read.**
- **Trigger.** The §4.5 prefix-consistency check registered for this purpose failed on 0/500 instances:
  Q-ON48's top 12 never equals Q-ON12. Fusion ranks over a depth-truncated candidate pool (5 × limit
  with dedup), so Q-ON48 is a re-ranking over 240 candidates, not an extension of Q-ON12. The registered
  padding clause "rank ≥ 13 in Q-ON48, file ∉ files(T)" therefore does not realise the §3/§11 construct
  "lower-ranked, other-file material beyond ON's 12": under it, 1006 of 3704 padding chunks (27%, about
  2.1 per instance) come from files(ON12), and 944 of those are byte-identical to the chunk ON served.
  TM as first built was T plus a partial copy of ON plus beyond-ON files, which would mix the `T − ON`
  file-trim component into `TM − T`.
- **Rule as corrected.** TM padding candidates are the Q-ON48 hits whose file is not in files(ON12), in
  Q-ON48 rank order; on the gate-1 set this also excludes every OFF and T file. The `rank ≥ 13` clause is
  dropped: it was a proxy for "beyond ON12" and, with the explicit file exclusion, would only skip the
  non-ON files the deeper ranking rates highest (3.1 of Q-ON48's top 12 per instance on average). The
  greedy closest-match rule, target, one-chunk-per-file, no-truncation, and short-instance logging are
  unchanged. T's content and order are unchanged.
- **Alternative considered and rejected.** Padding from the limit-12 list (ON12's non-T files first)
  puts 3057/3629 padding slots on ON files and makes TM ≈ ON reordered; B2 would replicate B1.
- **Pre-build values from the ruling's analysis (the rebuild must reproduce them):** TM/OFF chars mean
  0.9997, 100% within ±10%; 7.25 padding slots per instance; 35.1 candidates per instance (min 7);
  1 instance ran out of candidates (requests-5414); padding files in files(ON) = 0 by construction;
  40% of padding slots are at Q-ON48 rank ≤ 12.
- **Files.** `p5\b1b3_packs.json` (sha `80382193…d0e9`, the B1 input) is not modified. Rebuilt packs
  are written to `p5\b1b3_packs_b2.json`; ON/OFF/T/P entries asserted byte-identical to the B1 file; its
  sha256 is logged here before the first TM call: `7bc292621dd4fc260e48defde259f0be692820e0508d0151d5afe939107b1249`. B2 uses `--packs-file b1b3_packs_b2.json`.
- **Related, same cause.** The dedup-OFF side is equally depth-unstable: Q-OFF48's top 12 equals
  Q-OFF12 chunk-exactly in 4/500 instances (file set: 111/500). This is the mechanism behind the gate-1
  and concordance results above and behind TRIMMED-BREADTH D1; see the D1 entry below.
- **Secondary analysis added (pre-registered here, before grading; does not enter any verdict).**
  "Nested subset" = gate-1 instances where every T chunk appears among its file's OFF chunks, so that
  OFF ⊇ T holds content-wise exactly: 358/478. All §7.1 contrasts involving T or TM are additionally
  reported on this subset as a sensitivity to the 6.1% of T files whose ON chunk is not among OFF's
  chunks.
- **§7.3 note.** Served `score` values are rank-derived (`n − i` over the fetched pool: 60/240 for
  dedup-ON at limit 12/48, 36/144 for dedup-OFF) and are not comparable across limits or dedup modes.
  §7.3 reports ranks; scores, if shown, are labelled rank-derived.

**2026-10-15 (D1 revisited): single daemon does not resolve TRIMMED-BREADTH D1; cause corrected.**
Subset 478/500 = 95.6% (two daemons: 94.6%), top-concordance 88.2% (88.6%), any-concordance 93.9%
(94.4%), 21 of the 22 violators shared. The cause is deterministic and inside the fusion backend at
4fab615: with `code_only`, dedup-ON fetches 5 × limit candidates and dedup-OFF 3 × limit, and the fused
ranking (weighted RRF over depth-truncated arm lists, plus a graph arm seeded from the fused prefix with
`cap = fetch`) is not prefix-stable in depth. ON is therefore one-per-file over a 60-deep ranking while
OFF is the top 12 of a 36-deep ranking, in one process. D1's attribution to two daemons is withdrawn as
the primary cause; cross-process nondeterminism is at most a residual. No retrieval is re-run and no
arm is changed. Disclosure wording is in `TM-RULING-2026-10-15.md` §7.

**2026-10-16 02:27 EDT: B1 generation complete; B2 started (executor; operational, no protocol change).**
- **Timestamp correction** to the 2026-10-15 retrieval entry: Qwen serving came up at 19:38 (`props_8090.json`
  written 19:38:30) and B1 generation started 19:39 (`gen_ON.log` created 19:39:09), not "19:51". Nothing
  else in that entry changes.
- **B1:** task `b1b3_gen_b1` (deleted after use), `--packs-file b1b3_packs.json`, `--top-p 0.95`, 3 seeds.
  ON 1500/1500, OFF 1500/1500, T 1434/1434 (478 × 3). **0 infra failures** (no retries exhausted).
  Generation-side rates, read before any grading:

  | arm | empty patch | finish=length | instant EOS | mean prompt tokens |
  |---|---|---|---|---|
  | ON | 678/1500 | 40 | 0 | 2176 |
  | OFF | 603/1500 | 43 | 0 | 2252 |
  | T | 674/1434 | 30 | 0 | 1392 |

- **B2:** task `b1b3_gen_b2` started 02:27 on the same server, `--packs-file b1b3_packs_b2.json`
  (sha `7bc29262…1249`, per D-TM), arm TM, 478 × 3.

**2026-10-16 12:50 EDT: B2 generation complete; B1 grading complete except one deterministic harness error;
stopped per §6, no analysis run (executor).**
- **B2 generation:** TM 1434/1434 (478 × 3), 0 infra failures; empty 621, finish=length 44, instant EOS 0,
  mean prompt tokens 2262 (OFF 2252). `llama-server` stopped 04:50; GPU idle before grading.
- **B1 grading:** task `b1b3_grade_b1` (deleted after use), 04:51–12:13, one Docker session, official harness,
  `--max_workers 6 --cache_level instance`. Docker Hub pulls authenticated (stored Hub credential, user
  `[author]`, visible to the WSL docker client); WSL caches dropped before and after. Reports:
  ON s00/s01/s02 completed 274/273/274; OFF 298/298/300; T 246/250/260; empty patches as submitted.
- **Harness errors: 1 instance, sphinx-doc__sphinx-8475, in 4 of 9 arm-seeds** (ON s00, OFF s02, T s00,
  T s01). Cause is identical in every pass: `tests/test_build_linkcheck.py` hits the harness's 1800 s test
  timeout ("Timeout error: 1800 seconds exceeded"), which swebench counts as an error, not an outcome.
  **Three consecutive passes** (two in the batch, a third run 12:15–12:47) gave the same timeout in all
  four. Diagnostic: the **gold patch** for sphinx-8475, run in the same environment
  (`run_id b1b3_gold_sphinx8475`), **resolves in about 2 minutes**, so the environment is sound; the hang
  is induced by these model patches (they add a requests GET fallback in linkcheck). In the other 5
  arm-seeds the instance has an empty patch (ON s02, OFF s00) or completed grading (ON s01, OFF s01, T s02);
  their outcomes were not read.
- **Action:** per §6 ("errors deterministically in 3 consecutive passes with the same cause, stop and log a
  deviation. It is not scored"), §7 analysis is **not run**. The handling of sphinx-8475 is referred to the
  design authority. B2 grading (TM) continues meanwhile in task `b1b3_grade_p3b2`; nothing is analysed.

**2026-10-16 (D-8475): sphinx-doc__sphinx-8475 harness timeout classified as patch-induced and scored as
unresolved; general rule for TM and B3; design-authority ruling in `SPHINX8475-RULING-2026-10-16.md`.
Outcome-blind: only `error_*` report fields, the gold run, and the four errored cells' patches and test
output were read; no `resolved_ids` and nothing of the five normally graded or empty cells.**
- **Cause corrected.** The hang is not network latency. At base commit `3ea1ec84`, linkcheck's worker loop
  calls `check()` without a `try/except` and `write_doc` waits on `rqueue.get()` without a timeout. Each of the
  four patches (ON s00, OFF s02, T s00, T s01) inserts a HEAD/GET block at the top of `check_uri` that raises an
  uncaught exception (`ConnectionError` re-raised on the fixture's refused `localhost:7777` link; `NameError:
  head`; `UnboundLocalError: resp`; `AttributeError: session`), killing the worker; the main thread then blocks
  forever. Every hung run shows `collected 18 items` and no test completes. The gold patch passes 18/18 in
  3.11 s with the same live network (the §12 "about 2 minutes" was container lifecycle). 12/12 passes agree
  across `--max_workers` 6 and 1. No finite `--timeout` terminates a deadlock; option (iii) is rejected.
- **Classification rule (pre-registered now, binds TM and P).** A harness error that survives §6's three passes
  is Class I (infrastructure: pull/build/Docker/DNS/memory, or gold also fails/hangs, or cause not locatable in
  the patch) → never scored, regrade, else stop; or Class P (patch applied, gold resolves in the same
  environment and session, identical failure in 3 passes, mechanism located in the patch) → **scored as
  attempted and unresolved**. Evidence per cell is logged. `--timeout` stays 1800 s for all arms.
- **Sensitivity 1 (the ruling's default: scored).** The four B1 cells are Class P and are scored unresolved. n = 500 / 478, pairing and the exact
  decomposition are unchanged. §6's "harness errors are infrastructure failures, never model failures" is a
  false premise for this instance; its purpose (never record infrastructure noise as model failure) is kept.
  A hanging patch is treated as §6 already treats an empty patch: submitted, attempted, not resolved; the
  harness's own `resolved_instances / total_instances` assigns the same grade.
- **Primary (the literal §6 / common-set reading).** sphinx-8475 removed from every arm and seed.
  **Sensitivity 2 (extreme bound).** The four cells scored as resolved. Both reported beside every §7.1
  contrast and every §8/§9 verdict and prediction. Maximum leverage of the instance: 0.20 pp on any pooled Δ
  (0.21 pp on the 478 set), 1 on any per-seed b/c. A verdict or prediction that differs across the three is
  reported as not robust to this instance; none is upgraded.
- **Analysis script.** `b1b3_analyze.py` aborts unless each report's `error_ids` equals exactly its registered
  Class-P set; `--sphinx8475 {exclude,scored,upper}` (default `exclude`) writes `results.json`,
  `results_scored.json`, `results_upper.json`. Committed before any analysis is run. §7.3 funnel gains "applied → test: harness
  timeout (Class P)".
- **B3 eligibility.** §5's "fully graded (0 harness errors)" is read as 0 unclassified or Class-I errors; a
  Class-P cell is fully graded. Otherwise the four B1 files could never satisfy it.
- **TM status at this entry:** TM s00 0 errors; TM s01/s02 [TM s02 graded with 0 errors / Class-P cells: TM s01,
  sphinx-doc__sphinx-8475: patch applied; identical `Timeout error: 1800 seconds exceeded` after `collected 18 items`
  with no test completing, in 3 consecutive passes (two in-batch at `--max_workers 6`, third at 1); gold run
  `b1b3_gold_sphinx8475` (same environment, same day) resolves; mechanism in the patch: it calls the nonexistent
  `self._request` (`AttributeError`), and evaluating its handler `except requests.exceptions.TooManyRedirects`
  raises a second `AttributeError` (`sphinx.util.requests` has no `exceptions`), uncaught in the worker, so the
  main thread blocks on `rqueue.get()`. CLASS_P extended with (TM, 1)].
- **Alternatives considered and rejected.** (iii) longer timeout: futile and a per-cell harness-setting
  deviation. (i) as primary: post-treatment exclusion of nine cells, five of them cleanly graded, on the
  content of the model's patches; kept as sensitivity A.
- **Primary chosen by the owner (2026-10-16): exclusion; the ruling's default (scoring) is reported as sensitivity 1.**

**2026-10-16 14:35 EDT: §7 run for B1+B2; B3 started (executor; operational).**
- Run after commits eeadc36 (D-8475), ef49968 (analysis script), 1e256fa (GLMM on the primary set). Every
  report's `error_ids` equals its registered Class-P set (ON s00, OFF s02, T s00, T s01, TM s01: sphinx-8475;
  all others empty).
- Outputs (`p5\b1b3\`, sha256 prefix): `results.json` (primary, exclusion) `ece6db5e…`;
  `results_scored.json` `da3ba48a…`; `results_upper.json` `b313693f…`; `results_compare.json` `177b8f22…`;
  `glmm.json` `09a45e45…`. §8 verdict and §9 predictions 1–4 are identical across the three handlings.
- B3 eligible (no unclassified or Class-I errors). Qwen restarted with the same command (`/props` again
  n_ctx 8192, top_p 0.95); `gen_b3.cmd 0.95` (P, 478 × 1, `--packs-file b1b3_packs_b2.json`, P entries
  byte-identical to the B1 packs). Task `b1b3_auto_b3` stops `llama-server` after generation and then grades
  P under the same Class I/P rule.
- Note: the B1-era `props_8090.json` was overwritten by the B3 restart (deleted by the executor before
  relaunch). Its values were logged above (2026-10-15 entry); the B3 copy is `props_8090_b3.json`.


**2026-10-16 (note on D-8475).** The D-8475 "alternatives rejected" bullet records the ruling's default; the owner subsequently chose exclusion (option i) as primary, so that bullet's "(i) as primary … rejected" is superseded by the owner line.

**2026-10-16 16:00 EDT: B3 generated and graded; §7 rerun with P (executor; operational).**
- **Generation:** P 478/478 (1 seed), 14:36–15:27, 0 infra failures; empty 214, finish=length 15, instant
  EOS 0, mean prompt tokens 2074. Task `b1b3_auto_b3` stopped `llama-server` at 15:27 before grading.
- **Grading:** 15:27–15:52, one pass, **0 harness errors** (sphinx-8475 graded normally in P). WSL caches
  dropped before and after; authenticated pulls. No Class-P cell added; CLASS_P unchanged (5 cells).
- **§7 rerun** (all arms) with no code change. B1/B2 estimates are unchanged. Outputs, sha256 prefix:
  `results.json` (primary) `55ddd119…`, `results_scored.json` `a008abb5…`, `results_upper.json` `ad1a62aa…`,
  `results_compare.json` `ec2c12da…` (they supersede the 14:35 files, which lacked P).
- Tasks `b1b3_gen_b3` and `b1b3_auto_b3` deleted. Launch and helper scripts are versioned under
  `scripts/eval/b1b3_ops/` (copies of the files run from `p5\b1b3\`), with `props_8090_b3.json`.

**2026-10-16 (D-8475b, owner): primary handling of sphinx-8475 reverted to the ruling's default, AFTER results were seen.**
- Change: the primary handling of the five Class-P cells (ON s00, OFF s02, T s00, T s01, TM s01) is
  "scored as attempted and unresolved" (`results_scored.json`, `a008abb5…`), the default in
  `SPHINX8475-RULING-2026-10-16.md`. Exclusion (`results.json`, `55ddd119…`) and the upper bound
  (`results_upper.json`, `ad1a62aa…`) are reported as sensitivities. This reverses the owner's earlier
  choice of exclusion (entry above).
- Timing, disclosed: made on 2026-10-16 after the §7 results under all three handlings were known, in
  response to a blind review. The review noted that in the released inclusion table sphinx-8475 is a harness
  error only on the ON side in four other arms, so exclusion removes ON-side failures there.
- Effect: none on any decision. The §8 verdict and §9 predictions 1–4 are identical across the three
  handlings (above). Pooled Δ differs by at most 0.08 pp. All three files stay reported, and the paper
  states the switch.
