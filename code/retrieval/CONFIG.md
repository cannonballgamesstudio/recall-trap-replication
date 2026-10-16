# Retrieval-service configuration (what served every pack)

All SWE-bench Verified packs were produced by the retrieval service in `code/retrieval/ragfusion/` (a FastAPI
daemon, `code/retrieval/ragfusion/retrievald/`, wrapping the fusion backend `code/retrieval/ragfusion/fusion/`). The
code in this package is a verbatim snapshot of the repository revision dated **2026-07-14 22:47
UTC**, the revision that introduced the per-request dedup override and immediately precedes
the pack prefetch (packs written 2026-07-15 to 2026-07-17). Only the package name was rewritten for
anonymization (internal package name -> `ragfusion`); logic is unchanged. The revision identifier is `4fab615` (see the top-level README). Earlier commit identifiers are withheld for
review and will be added on de-anonymization.

The served packs (`data/swe-verified/packs/`) are the frozen experimental input. Re-serving them
from a rebuilt index is not required to reproduce any result, and a rebuilt index may differ
slightly (third-party parser/library drift), which is why the packs are released.

## Two daemons, one code path

| arm | port used | env | effect |
|---|---|---|---|
| dedup-ON (production default) | 8083 | `RETRIEVALD_QUERY_DEDUP_FILE` unset (default on) | post-filter ranking to at most one chunk per file **before** the top-K cut (`fuse.dedup_by_file`, over-fetch 5xK) |
| dedup-OFF | 8084 | `RETRIEVALD_QUERY_DEDUP_FILE=0` | raw fused ranking, top-K |

Both daemons load the same index directory and the same weights; the only difference is the flag.

## Fusion backend (`RETRIEVALD_BACKEND=fusion`) served defaults

| parameter | value | source |
|---|---|---|
| fusion | weighted reciprocal-rank fusion, k = 60 | `fusion/fuse.py::weighted_rrf_scored` |
| `w_dense` | 1.0 | `retrievald/config.py` |
| `w_lex`, `lex_mode` | 1.0, `ids` (identifier-token BM25 over a code-only pool; docs demoted) | config + `fusion/lex.py` |
| `w_graph`, seeds, hops | 1.0, 20, 1 (deterministic call/containment adjacency expansion) | config + `fusion/graph.py` |
| `w_trigram` | 0.0 (off) | config |
| `w_prior` | 0.3 (git-history recency/frequency boost on final ranking) | config + `fusion/priors.py` |
| reranker | off | config |
| query | `problem_statement[:6000]`, mode `hybrid` (DENSE-1 packs: mode `semantic`, i.e. plain cosine with lex/graph/trigram/priors stripped) | `code/eval/prefetch_*.py` |
| query instruction (embedded query prefix) | `Given a code-search intent, retrieve the most relevant source code.` | `srclight_backend.py::DEFAULT_QUERY_INSTRUCT` |
| slot budget K | 12 (primary); 4/8/20/40 for the budget sweep | `--limit` / `--k` |

## Embedder identity (full, un-elided)

* Model: **Qwen3-Embedding-8B**, GGUF quantization **Q8_0** (`Qwen3-Embedding-8B-Q8_0.gguf`), served by
  **llama.cpp `llama-server`** in embedding mode on an OpenAI-compatible endpoint
  (`OPENAI_BASE_URL=http://127.0.0.1:8080`, no `/v1` suffix; key is a dummy string).
* Client identity string: `openai:Qwen/Qwen3-Embedding-8B`, dims **4096**.
* Index identity string recorded in every index (`fusion/identity.py::fusion_identity`):
  `fusion@1+fmt-0.15+openai:Qwen/Qwen3-Embedding-8B+4096`
  (fusion format 1; srclight index format `fmt-0.15`, i.e. srclight 0.15.x).

## Chunker policy (size, overlap, boundary)

* **Boundary:** one chunk per tree-sitter *symbol* (function, method, class, ...), as extracted by the
  open-source `srclight` indexer (0.15.x); files are walked in sorted order, symbols in file order.
  Enclosing class/struct/interface/namespace/module names are attached as `parent`.
* **Overlap:** none (symbol-aligned; nested symbols are separate chunks that may share lines with
  their parent).
* **Embedded text per chunk** (`fusion/ingest.py::_embed_text`): header `relpath [language] parent`,
  then signature, doc comment, then the first **1200 characters** of the symbol body.
* **Served snippet per chunk** (what the model sees in the pack; `fusion/ingest.py::_snippet`): the first
  **15 lines** of the symbol body, capped at **600 characters**.
* **Lexical fields:** name + qualified name; signature; doc comment + body.
* Header-imports enrichment flag: off (default; not exposed).

## Pack rendering

`code/eval/g_plane_prompts.py::format_pack` renders hits in the service's own order (never re-sorted,
no extra truncation) as `## Retrieved context (top-K, ...)` followed by one
`### path:line - symbol [kind]` header and fenced snippet per hit. The identical renderer is used for
both arms.

## Building an index from scratch (optional)

`code/eval/fusion_build_swe.py` builds srclight + fusion indexes per repository at each
instance's checkout (`--augment` adds graph adjacency, trigrams, and git-history priors), with the
embedding endpoint above. `code/eval/prefetch_500.py` (K=12), `prefetch_ksweep.py --k K`,
and `prefetch_dense_500.py` (DENSE-1) query the two daemons and write the pack files.
The BM25 pack builder was an unarchived analysis script; `bm25_packs.json` is released as served.
