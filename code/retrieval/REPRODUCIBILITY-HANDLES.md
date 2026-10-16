# Reproducibility handles (program record)

> Program record, reproduced as written apart from anonymization (commit identifiers shown as [commit]; they are listed in preregistrations/PROVENANCE.md). Section and appendix numbers inside it are the record's own and do not correspond to the submitted paper; README.md maps the paper's tables and figures to files.

The released artifact contains the single-shot runner (SEARCH/REPLACE applied to a per-arm isolated checkout, then git diff; raw responses persisted as an audit trail where logged), the agentic harness used only for the boundary condition, the retrieval-service retrieval fleet configuration (fusion backend, `lex_mode=ids`, `w_graph=1.0`, embedder Qwen3-Embedding-8B-Q8_0 via llama.cpp, full un-elided identity string, chunker size/overlap/boundary policy, and the exact `retrieval-service` commit), the served packs for every arm, the predictions, raw responses, grading reports, the per-instance inclusion table, and the analysis scripts. Every table row maps to its inputs through a per-instance manifest. Model slugs, providers, and decoding parameters are recorded in the harness configuration and the pre-registration records; per-instance checkouts and Docker images are excluded by design and rebuild from the served packs.

**In this anonymized package:** `README.md` (layout, paper element -> file map, reproduction steps),
`data/arms.json` and `results/core/inclusion_table.csv` (per-instance manifest), and `MANIFEST.sha256`
(checksums of every file). The retrieval-service configuration is in
`code/retrieval/CONFIG.md`; its source revision is `4fab615` (2026-07-14).
