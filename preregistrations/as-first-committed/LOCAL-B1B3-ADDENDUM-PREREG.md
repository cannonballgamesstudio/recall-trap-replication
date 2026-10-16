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
