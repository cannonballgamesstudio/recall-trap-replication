# Pre-registration — matched agentic Claude fusion A/B (2026-07-15, BEFORE grading)

**Why:** the original "agentic +18.2pp" arm was an ARTIFACT — its two sub-arms ran on
different models (ON=sonnet-5, OFF=opus-4-8) AND different budgets ($1.5 vs $1.0) AND
different pack-server configs (8083 vs 8084). No clean matched agentic fusion A/B has ever
been run. This registers one, to settle whether the depth>breadth effect survives the
agentic (unrestricted-Read) regime when everything but the pack is held fixed.

**Instrument (clean):** `swe_bench.py predict --g-plane packfile` injects a PRE-BUILT pack
into the agentic policy (PACK_SYSTEM, Read/Edit/Write, --max-turns 10). Both arms use the
EXACT single-shot `local_packs.json` packs (dedupON mean 6002 chars / dedupOFF 6318),
flattened to `packfile_ss_dedup{ON,OFF}.json`. Held fixed across arms: model
(`SWE_CLAUDE_MODEL=claude-sonnet-5`), `--budget 1.5`, `--concurrency 3`, `--max-turns 10`,
tools (Read/Edit/Write), `--ref-mode instance`, and the ids. ONLY the pack differs. This
also doubles as a clean single-shot-vs-agentic REGIME comparison at identical pack content.

**Slice:** the pre-registered 100-id `oracle_slice.txt` (cheap first pass). Run IDs
`g_ssagent_dedupON` / `g_ssagent_dedupOFF`.

**Mandatory controls (the lessons from the artifact):**
1. Per-transcript MODEL CENSUS before grading — assert every transcript in both arms is
   claude-sonnet-5 (read the system/init line; do NOT trust the launcher).
2. Log per-arm empty-patch rate AND turn-cap-hit rate as covariates (71/72 of the old ON
   arm's empties were pure 10-turn truncation — breadth may burn the TURN budget, a real
   effect to measure, not hide).

**Primary analysis:** RAW paired McNemar exact (empties = task failure), consistent with
the single-shot arms. Report conditional (both non-empty) as the mechanism decomposition.

**Pre-committed prediction:** NULL (matched agentic dedup comparisons on dense/BM25 are all
null: sonnet/dense -1.8, opus/dense -2, opus/BM25 -2). i.e. agentic Read attenuates the
single-shot depth advantage to non-significance on fusion too.

**Decision rule:**
- Matched OFF-ON significantly POSITIVE (depth wins agentically on fusion, p<0.05): the
  trend continues → SCALE to n=499 sonnet AND run the opus pair. Reopens the moat question.
- NULL or negative: agentic attenuation CONFIRMED on fusion → the depth effect is a
  single-shot / fixed-budget phenomenon; do not claim an agentic/interactive benefit. Report
  as a clean regime boundary (strengthens the "agentic harnesses defeat fixed-budget context"
  methods finding). Do NOT run opus (no trend to chase).
