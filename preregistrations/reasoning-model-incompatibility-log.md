# Reasoning-model incompatibility log (program record)

GLM-5.2 (`z-ai/glm-5.2`) and Kimi-k2.7-code (`moonshotai/kimi-k2.7-code`), both via OpenRouter, are
documented as **incompatible** with the single-shot, no-tools regime: under a bounded completion
budget the provider either ignores the requested reasoning cap or does not allow reasoning to be
disabled, so most completions end before any SEARCH/REPLACE block is emitted. They are counted as
**neither replications nor non-replications** and are excluded from the confirmatory family.

## Evidence in this package

| model | arm | submitted | empty patches | empty rate | resolved | files |
|---|---|---|---|---|---|---|
| GLM-5.2 | dedup-ON | 499 | 395 | 79.2% | 64 | `data/swe-verified/predictions/preds_local_glm52_dedupON.jsonl`, `grading/summary/local_glm52_dedupON.local_glm52_dedupON.json` |
| GLM-5.2 | dedup-OFF | 498 | 350 | 70.3% | 85 | `..._glm52_dedupOFF...` |
| Kimi-k2.7-code | dedup-ON | 499 | 448 | 89.8% | 26 | `..._kimi_dedupON...` |
| Kimi-k2.7-code | dedup-OFF | 499 | 438 | 87.8% | 41 | `..._kimi_dedupOFF...` |

Per-instance statuses are in `results/inclusion_table.csv` (arms `P6a_glm52_incompatible`,
`P6b_kimi_incompatible`); `results/paired_contrasts.md` reports their contrasts for completeness only.
At these empty rates the resolve contrast measures patch *producibility* under a truncated budget,
not the packing policy, which is why they are not interpreted.

**Limitation (disclosed):** these two runs predate raw-response persistence (added to the harness
after the reasoning-field defect was found, Section 4 of the paper); the raw provider responses
for GLM-5.2 and Kimi were therefore not retained in this package. The evidence released is the
prediction files (empty `model_patch`) and the official grading reports. The analogous defect and
its fix are visible in the DeepSeek-v4 raw logs (`raw_local_dsv4_*.jsonl`: `finish_reason`,
`reasoning_len`, `content_len` per instance).
