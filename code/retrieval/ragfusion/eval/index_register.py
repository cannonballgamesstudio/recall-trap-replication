from __future__ import annotations

import os
import time

from ragfusion.backend import IndexResult
from ragfusion.registry import Registry
from ragfusion.srclight_backend import SrclightBackend


def index_and_register(
    repo: str,
    ref: str,
    sha: str,
    checkout: str,
    registry_db: str,
    *,
    embed_model: str | None = None,
    dims: int | None = None,
    config_hash: str = "eval",
    indexed_at: int | None = None,
    backend=None,
) -> IndexResult:
    """Build a srclight index over ``checkout`` and register it 'ready'.

    The static stand-up path for the A/B eval: no ZFS clone-off-main, no
    reconciler. The index lands at ``<checkout>/.srclight`` — exactly the
    directory ``ragfusion.retrievald.resolve.index_dir_for`` derives from the registered
    ``worktree`` — so retrievald serves it with no further wiring.

    Args:
        repo: repo identifier the client will send (e.g. "django/django").
        ref: ref name to register under (what the query's ``branch`` resolves to).
        sha: head sha recorded for the staleness check.
        checkout: path to the checked-out worktree (also the registered worktree).
        registry_db: path to the registry sqlite file retrievald reads.
        embed_model: srclight provider string (e.g. "openai:Qwen/Qwen3-Embedding-8B").
            Omit for keyword-only (FTS5) — no embedding provider needed.
        dims: embedding dimensions, if pinning a non-default vector width.
        config_hash: opaque config marker stored on the row.
        indexed_at: epoch seconds; defaults to now (injectable for deterministic tests).
        backend: a RetrievalBackend to use instead of building a SrclightBackend
            (dependency injection for tests).

    Returns:
        The ``IndexResult`` from the build (file/symbol/edge counts + index_dir).
    """
    if backend is None:
        backend = SrclightBackend(embed_model=embed_model, dims=dims)
    index_dir = os.path.join(checkout, ".srclight")
    result = backend.index(checkout, index_dir)
    registry = Registry.init_db(registry_db)
    registry.atomic_swap(
        repo=repo,
        ref=ref,
        worktree=checkout,
        head_sha=sha,
        indexed_at=indexed_at if indexed_at is not None else int(time.time()),
        backend_version=result.backend_version,
        config_hash=config_hash,
    )
    return result
