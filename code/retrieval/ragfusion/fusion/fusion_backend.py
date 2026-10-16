# src/ragfusion/fusion/fusion_backend.py
from __future__ import annotations

from pathlib import Path

from ragfusion.backend import Capabilities, IndexResult
from ragfusion.fusion.identity import fusion_identity


class FusionBackend:
    """Multi-signal RetrievalBackend (spec: docs/specs/2026-07-10-fusion-backend-design.md).

    Composes srclight as an unmodified library: srclight indexes (keyword/graph
    only), fusion ingests and owns the whole query pipeline. Graph ops delegate
    to an internal SrclightBackend (Task 9).
    """

    def __init__(self, embed_model: str | None = None, dims: int | None = None,
                 reranker=None, query_instruct: str | None = None,
                 dedup_file: bool = True, w_lex: float = 1.0, w_dense: float = 1.0,
                 lex_mode: str = "ids",
                 # library default stays 0.0 (conservative); the SERVED default is 1.0
                 # via RetrievaldConfig (confirmed on swebench-ml -- see config.py citation).
                 w_graph: float = 0.0, seeds: int = 20, graph_hops: int = 1,
                 w_trigram: float = 0.0, w_prior: float = 0.0,
                 header_imports: bool = False,
                 provider_factory=None):
        self.embed_model = embed_model
        self.dims = dims
        self.reranker = reranker
        self.query_instruct = query_instruct
        self.dedup_file = dedup_file
        self.w_lex = w_lex
        self.w_dense = w_dense
        if lex_mode not in ("ids", "full", "off"):
            raise ValueError(f"lex_mode must be ids|full|off, got {lex_mode!r}")
        self.lex_mode = lex_mode
        self.w_graph = w_graph
        self.seeds = seeds
        self.graph_hops = graph_hops
        self.w_trigram = w_trigram
        self.w_prior = w_prior
        # Experiment flag (Task 3, header-imports A/B) -- NOT env-exposed;
        # env comes only if the A/B wins (see .superpowers/sdd/task-3-brief.md).
        self.header_imports = header_imports
        if provider_factory is None:
            def provider_factory(model):
                from srclight.embeddings import get_provider
                return get_provider(model)
        self._provider_factory = provider_factory
        self._provider = None

    def _get_provider(self):
        if self._provider is None:
            self._provider = self._provider_factory(self.embed_model)
        return self._provider

    def _version(self) -> str:
        return fusion_identity(self.embed_model, self.dims)

    def capabilities(self) -> Capabilities:
        import srclight
        modes = ["keyword"]
        if self.embed_model:
            modes += ["semantic", "hybrid"]
        return Capabilities(
            backend_id="fusion",
            backend_version=self._version(),
            backend_running_version=srclight.__version__,
            modes=tuple(modes),
            supports_callgraph=True,
            supports_dims=(self.dims,) if self.dims else (),
            supports_ops=("deps", "file", "tests", "map", "hierarchy"),
        )

    def index(self, worktree_path: str, index_dir: str) -> IndexResult:
        from srclight.db import Database
        from srclight.indexer import Indexer, IndexConfig

        from ragfusion.fusion import store
        from ragfusion.fusion.dense import build_dense
        from ragfusion.fusion.ingest import ingest_srclight
        from ragfusion.fusion.lex import LexIndex

        idx = Path(index_dir)
        idx.mkdir(parents=True, exist_ok=True)

        # Drop any cached handles for this index_dir BEFORE rebuilding: a cached
        # LexIndex/DenseIndex mmaps fusion_bm25/fusion_emb.npy, and on Windows a
        # rewrite of a file with an open mapped section raises OSError (EINVAL) —
        # so a reindex() on the same backend instance that just queried this idx
        # would otherwise fail. Evicting drops the last reference, closing the
        # mmap immediately (CPython refcounting).
        cache = getattr(self, "_handle_cache", None)
        if cache:
            for key in [k for k in cache if k[0] == str(idx)]:
                del cache[key]

        # 1) srclight indexes WITHOUT embeddings — fusion owns dense vectors,
        #    so the GPU isn't paid twice for the same corpus.
        db = Database(idx / "index.db")
        try:
            db.open()
            db.initialize()
            root = Path(worktree_path)
            Indexer(db, IndexConfig(root=root, embed_model=None)).index(root)
            db_stats = db.stats()
        finally:
            db.close()

        # 2) ingest -> fusion.db (chunks + headers)
        ingest_srclight(idx, header_imports=self.header_imports)

        # 3) lexical arm
        conn = store.open_db(idx / "fusion.db")
        try:
            LexIndex.build(conn, idx / "fusion_bm25")
            texts = store.embed_texts(conn)
        finally:
            conn.close()

        # 3b) graph arm: adjacency table (contains/calls/inherits/...) for the
        # graph-expand arm (Task 4). Additive + idempotent — safe to re-run as
        # a standalone augment on an already-built fusion.db.
        from ragfusion.fusion.graph import build_adjacency
        build_adjacency(idx)

        # 3c) trigram arm: identifier-trigram postings for the anchor arm
        # (Task 2, containment-scored). Additive/idempotent, same as adjacency.
        from ragfusion.fusion.trigram import build_trigrams
        build_trigrams(idx)

        # 3d) git-history priors: per-file recency+frequency score for the
        # final-ranking boost (Task 3, query-independent — see query()).
        # Index-time only: wall-clock use here is allowed (build-time artifact).
        from ragfusion.fusion.priors import build_priors
        build_priors(idx, worktree_path)

        # 4) dense arm (only when an embed model is configured)
        if self.embed_model:
            build_dense(texts, self._get_provider(), idx / "fusion_emb.npy")

        return IndexResult(
            backend_version=self._version(),
            files_indexed=db_stats["files"],
            symbols=db_stats["symbols"],
            edges=db_stats["edges"],
            index_dir=str(idx),
        )

    _DOC_OVERFETCH = 3
    _RERANK_OVERFETCH = 5
    _DEDUP_OVERFETCH = 5

    def _handles(self, idx: Path):
        """Cache (LexIndex, DenseIndex|None) per index_dir, keyed by mtimes.

        FIFO-2 eviction: avoids re-loading bm25s/npy on every query() call (measured
        600-950ms per query for the dense float32 copy alone, on top of the
        lexical index load) while staying correct across reindex — the mtime
        key busts the cache the moment fusion.db or fusion_emb.npy changes.
        Acceptable for the eval loop's 1-2 index working set; degrades to an
        extra reload if >2 indices are queried sequentially on the same backend.

        CAVEAT (cross-process): cached mmaps hold sidecar files open, so an
        in-place reindex from ANOTHER process can still hit Windows file locking
        (OSError EINVAL). Same-process eviction via the index() method (lines 85-88)
        covers only this instance. build_dense/LexIndex.build now write into a
        temp path and swap it into place (store.finalize_db does the same for
        fusion.db) — this removes truncate-in-place as a failure mode and
        narrows the cross-process window to the swap itself, but a reader with
        an already-open mmap on the old file can still hit Windows file locking
        during that swap; the durable cross-process fix remains the registry's
        clone+pointer swap, not this cache.
        """
        from ragfusion.fusion.dense import DenseIndex
        from ragfusion.fusion.lex import LexIndex

        emb = idx / "fusion_emb.npy"
        key = (str(idx), (idx / "fusion.db").stat().st_mtime_ns,
               emb.stat().st_mtime_ns if emb.exists() else 0)
        cache = getattr(self, "_handle_cache", None)
        if cache is None:
            cache = self._handle_cache = {}
        if key not in cache:
            if len(cache) >= 2:
                cache.pop(next(iter(cache)))
            dense = DenseIndex.load(emb) if (emb.exists() and self.embed_model) else None
            cache[key] = (LexIndex.load(idx / "fusion_bm25"), dense)
        return cache[key]

    def query(self, index_dir, repo, ref, text, mode="hybrid", limit=20, dims=None,
              code_only=False, rerank=False, dedup=None):
        # dedup=None -> use the backend default (self.dedup_file). A per-request
        # override exists because file-dedup MAXIMIZES recall but COSTS resolve rate
        # when the hits are consumed as a fixed-slot context pack: measured -18.2pp
        # (n=499, p<1e-4) dedup-on vs dedup-off. So the interactive `rag query` keeps
        # dedup on (terse, one-line-per-file scanning), while the pre-injection hook
        # requests dedup=False for a depth-packed context block.
        from ragfusion.backend import Hit
        from ragfusion.fusion import store
        from ragfusion.fusion.dense import embed_query
        from ragfusion.fusion.fuse import dedup_by_file, demote_docs
        from ragfusion.reranker import rerank_hits

        supported = self.capabilities().modes
        if mode not in supported:
            raise ValueError(f"unsupported mode {mode!r}; this backend supports {supported}")
        idx = Path(index_dir)
        lex_h, dense_h = self._handles(idx)

        fetch = limit
        if code_only:
            fetch = max(fetch, limit * self._DOC_OVERFETCH)
        active_rerank = rerank and self.reranker is not None and mode != "keyword"
        if active_rerank:
            fetch = max(fetch, limit * self._RERANK_OVERFETCH)
        if self.dedup_file if dedup is None else dedup:
            fetch = max(fetch, limit * self._DEDUP_OVERFETCH)

        arms: dict[str, list[int]] = {}
        if mode == "keyword":
            arms["lex"] = [r for r, _ in lex_h.search(text, k=fetch)]
        elif mode == "hybrid" and self.lex_mode != "off":
            from ragfusion.fusion.lex import id_tokens
            lex_text = id_tokens(text) if self.lex_mode == "ids" else text
            if lex_text:
                if self.lex_mode == "ids":
                    # code-only pool: identifier-rich docs (changelogs) otherwise
                    # flood the arm — measured, docs/eval/fusion-p1-benchmark.md
                    rows_l = [r for r, _ in lex_h.search(lex_text, k=fetch * 2)]
                    arms["lex"] = self._code_rows(idx, rows_l)[:fetch]
                else:
                    arms["lex"] = [r for r, _ in lex_h.search(lex_text, k=fetch)]
        if mode in ("semantic", "hybrid"):
            if dense_h is None:
                raise RuntimeError(
                    "semantic/hybrid requested but this index has no dense sidecar "
                    "(fusion_emb.npy missing) — likely built by a keyword-only backend; re-index.")
            qvec = embed_query(self._get_provider(), text, self.query_instruct)
            arms["dense"] = [r for r, _ in dense_h.search(qvec, k=fetch)]
        if mode == "hybrid" and self.w_trigram > 0:
            from ragfusion.fusion.lex import id_tokens
            from ragfusion.fusion import trigram as tri_mod
            ids_q = id_tokens(text)
            if ids_q:
                conn_t = store.open_db(idx / "fusion.db")
                try:
                    arms["trigram"] = [r for r, _ in tri_mod.search(conn_t, ids_q,
                                                                    cap=fetch)]
                except Exception as e:
                    import logging
                    logging.getLogger("ragfusion.fusion").warning(
                        "trigram arm dropped: %s: %s", type(e).__name__, e)
                finally:
                    conn_t.close()

        from ragfusion.fusion.fuse import weighted_rrf_scored
        first = weighted_rrf_scored(
            arms, {"lex": self.w_lex, "dense": self.w_dense, "trigram": self.w_trigram})
        if self.w_graph > 0 and mode != "keyword":
            import logging
            from ragfusion.fusion import graph as graph_mod
            conn_g = store.open_db(idx / "fusion.db")
            try:
                g = graph_mod.expand(conn_g, first[: max(0, self.seeds)],
                                     hops=self.graph_hops, cap=fetch)
                arms["graph"] = [r for r, _ in g]
            except Exception as e:
                logging.getLogger("ragfusion.fusion").warning(
                    "graph arm dropped: %s: %s", type(e).__name__, e)
            finally:
                conn_g.close()
            first = weighted_rrf_scored(
                arms, {"lex": self.w_lex, "dense": self.w_dense,
                       "graph": self.w_graph, "trigram": self.w_trigram})
        fused = [r for r, _ in first][:fetch]

        conn = store.open_db(idx / "fusion.db")
        try:
            rows = store.chunks_by_rows(conn, fused)
            # Git-history prior boost: applied on the FINAL fused scores, not as
            # an RRF arm — a query-independent ranking injected into RRF would
            # surface the same hot files for every query. Mode-agnostic by
            # design (keyword included): a file's history is not query-specific.
            if self.w_prior > 0:
                try:
                    from ragfusion.fusion import priors as priors_mod
                    pri = priors_mod.load(conn)
                    smap = dict(first)
                    rows = sorted(
                        rows,
                        key=lambda r: -(smap.get(r["emb_row"], 0.0)
                                        * (1.0 + self.w_prior
                                           * pri.get((r["file"] or "").replace("\\", "/").lower(), 0.0))))
                except Exception as e:
                    import logging
                    logging.getLogger("ragfusion.fusion").warning(
                        "prior boost dropped: %s: %s", type(e).__name__, e)
        finally:
            conn.close()
        n = len(rows)
        hits = [Hit(repo=repo, ref=ref, file=r["file"], line=r["line"],
                    symbol=r["name"], score=float(n - i),  # rank-derived; order is authoritative
                    snippet=r["snippet"], kind=r["kind"])
                for i, r in enumerate(rows)]

        if active_rerank:
            hits = rerank_hits(self.reranker, text, hits)
        if code_only:
            hits = demote_docs(hits)
        do_dedup = self.dedup_file if dedup is None else dedup
        if do_dedup:
            hits = dedup_by_file(hits)
        return hits[:limit]

    def _code_rows(self, idx: Path, rows: list[int]) -> list[int]:
        from ragfusion.fusion import store
        from ragfusion.fusion.fuse import DOC_KINDS, DOC_EXTS
        conn = store.open_db(idx / "fusion.db")
        try:
            doc = {r["emb_row"] for r in store.chunks_by_rows(conn, rows)
                   if (r["kind"] or "").lower() in DOC_KINDS
                   or (r["file"] or "").lower().endswith(DOC_EXTS)}
        finally:
            conn.close()
        return [r for r in rows if r not in doc]

    # ---- graph ops: pure delegation to the (untouched) srclight adapter, which
    # reads the index.db that fusion's index() already builds. Parity by reuse.

    @property
    def _delegate(self):
        if getattr(self, "_delegate_backend", None) is None:
            from ragfusion.srclight_backend import SrclightBackend
            self._delegate_backend = SrclightBackend()   # graph ops need no embeddings
        return self._delegate_backend

    def ctx(self, index_dir, repo, ref, symbol, *, file=None):
        return self._delegate.ctx(index_dir, repo, ref, symbol, file=file)

    def deps(self, index_dir, repo, ref, symbol, *, file=None,
             transitive=False, max_depth=5):
        return self._delegate.deps(index_dir, repo, ref, symbol, file=file,
                                   transitive=transitive, max_depth=max_depth)

    def file_overview(self, index_dir, repo, ref, path):
        return self._delegate.file_overview(index_dir, repo, ref, path)

    def tests(self, index_dir, repo, ref, symbol):
        return self._delegate.tests(index_dir, repo, ref, symbol)

    def structure(self, index_dir, repo, ref, *, path=None, max_depth=3):
        return self._delegate.structure(index_dir, repo, ref,
                                        path=path, max_depth=max_depth)

    def hierarchy(self, index_dir, repo, ref, symbol, *, file=None):
        return self._delegate.hierarchy(index_dir, repo, ref, symbol, file=file)
