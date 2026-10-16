from __future__ import annotations

from dataclasses import dataclass

from ragfusion.retrievald.errors import BackendBusy


@dataclass
class RetrievaldConfig:
    backend: str = "fake"
    embed_model: str | None = None
    dims: int | None = None
    embed_queue_size: int = 4
    registry_db: str | None = None
    log_raw_text: bool = False
    default_identity: str | None = None
    rerank_endpoint: str | None = None
    rerank_model: str | None = None
    query_instruct: str | None = None
    dedup_file: bool = True
    fusion_w_lex: float = 1.0
    fusion_w_dense: float = 1.0
    fusion_lex_mode: str = "ids"
    # 1.0 since 2026-07-11: graph arm CONFIRMED on held-out swebench-ml
    # (MRR +0.143 CI [+0.030,+0.258], r@1 +0.188*) per the pre-registered
    # decision rule in docs/plans/2026-07-11-fusion-backend-p3.md.
    fusion_w_graph: float = 1.0
    fusion_seeds: int = 20
    fusion_graph_hops: int = 1
    fusion_w_trigram: float = 0.0
    # 0.3 since 2026-07-11: priors CONFIRMED per the pre-registered rule in
    # docs/plans/2026-07-11-fusion-backend-p4.md Task 2 (SWE paired
    # MRR +0.015 CI [+0.001,+0.035]; private-repo no regression, F1@8 +0.050).
    fusion_w_prior: float = 0.3

    @classmethod
    def from_env(cls, env) -> "RetrievaldConfig":
        dims = env.get("RETRIEVALD_DIMS")
        # instruct-prefixing the embedded query + file-dedup are validated free wins
        # (instruct lifts recall/MRR; dedup gives distinct-file top-K for localization),
        # so both default ON. RETRIEVALD_QUERY_INSTRUCT: unset -> the validated default
        # instruction; "0"/"off"/"" -> disabled; "1"/"on" -> default; any other value ->
        # used verbatim. RETRIEVALD_QUERY_DEDUP_FILE: "0"/"off" opts out. (code_only stays an
        # explicit per-request opt-in: an A/B showed docs HELP recall on design-doc repos.)
        from ragfusion.srclight_backend import DEFAULT_QUERY_INSTRUCT
        qi = env.get("RETRIEVALD_QUERY_INSTRUCT")
        if qi is None or qi.lower() in ("1", "true", "on", "yes"):
            qi = DEFAULT_QUERY_INSTRUCT
        elif qi.lower() in ("0", "false", "off", "no", ""):
            qi = None
        dedup = (env.get("RETRIEVALD_QUERY_DEDUP_FILE") or "on").lower() not in ("0", "false", "off", "no")
        return cls(
            backend=env.get("RETRIEVALD_BACKEND", "fake"),
            embed_model=env.get("RETRIEVALD_EMBED_MODEL"),
            dims=int(dims) if dims else None,
            embed_queue_size=int(env.get("RETRIEVALD_EMBED_QUEUE", "4")),
            registry_db=env.get("RETRIEVALD_REGISTRY_DB"),
            log_raw_text=env.get("RETRIEVALD_LOG_RAW_TEXT") == "1",
            default_identity=env.get("RETRIEVALD_DEFAULT_IDENTITY"),
            rerank_endpoint=env.get("RETRIEVALD_RERANK_ENDPOINT"),
            rerank_model=env.get("RETRIEVALD_RERANK_MODEL"),
            query_instruct=qi or None,
            dedup_file=dedup,
            fusion_w_lex=float(env.get("RETRIEVALD_FUSION_W_LEX", "1.0")),
            fusion_w_dense=float(env.get("RETRIEVALD_FUSION_W_DENSE", "1.0")),
            fusion_lex_mode=env.get("RETRIEVALD_FUSION_LEX_MODE", "ids"),
            fusion_w_graph=float(env.get("RETRIEVALD_FUSION_W_GRAPH", "1.0")),
            fusion_seeds=int(env.get("RETRIEVALD_FUSION_SEEDS", "20")),
            fusion_graph_hops=int(env.get("RETRIEVALD_FUSION_GRAPH_HOPS", "1")),
            fusion_w_trigram=float(env.get("RETRIEVALD_FUSION_W_TRIGRAM", "0.0")),
            fusion_w_prior=float(env.get("RETRIEVALD_FUSION_W_PRIOR", "0.3")),
        )


def build_backend(config: RetrievaldConfig):
    if config.backend == "srclight":
        from ragfusion.srclight_backend import SrclightBackend
        reranker = None
        if config.rerank_endpoint:
            from ragfusion.reranker import HttpReranker
            reranker = HttpReranker(config.rerank_endpoint,
                                    config.rerank_model or "reranker")
        return SrclightBackend(embed_model=config.embed_model, dims=config.dims,
                               reranker=reranker, query_instruct=config.query_instruct,
                               dedup_file=config.dedup_file)
    if config.backend == "fusion":
        from ragfusion.fusion.fusion_backend import FusionBackend
        reranker = None
        if config.rerank_endpoint:
            from ragfusion.reranker import HttpReranker
            reranker = HttpReranker(config.rerank_endpoint,
                                    config.rerank_model or "reranker")
        return FusionBackend(embed_model=config.embed_model, dims=config.dims,
                             reranker=reranker, query_instruct=config.query_instruct,
                             dedup_file=config.dedup_file,
                             w_lex=config.fusion_w_lex, w_dense=config.fusion_w_dense,
                             lex_mode=config.fusion_lex_mode, w_graph=config.fusion_w_graph,
                             seeds=config.fusion_seeds, graph_hops=config.fusion_graph_hops,
                             w_trigram=config.fusion_w_trigram, w_prior=config.fusion_w_prior)
    from ragfusion.fake_backend import FakeBackend
    return FakeBackend()


class EmbedQueue:
    """Simple bounded gate for semantic/hybrid embeds. Raises BackendBusy when full."""

    def __init__(self, maxsize: int):
        self.maxsize = maxsize
        self._inflight = 0

    def __enter__(self):
        if self._inflight >= self.maxsize:
            raise BackendBusy("embed queue saturated", details={"retryable": True})
        self._inflight += 1
        return self

    def __exit__(self, *exc):
        self._inflight -= 1
        return False
