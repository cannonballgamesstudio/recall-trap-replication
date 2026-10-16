from __future__ import annotations

from ragfusion.backend import IndexResult
from ragfusion.registry import Registry


def register_built_index(registry: Registry, repo: str, ref: str, sha: str,
                         worktree: str, index_result: IndexResult,
                         config_hash: str, indexed_at: int,
                         clone_dataset: str | None = None,
                         origin_snapshot: str | None = None) -> None:
    """Record a freshly-built index in the registry (atomic swap -> 'ready').

    The adapter stays registry-agnostic; this is the seam Phase 4's indexer calls.
    `clone_dataset`/`origin_snapshot` are the storage-internal reaping metadata
    (None for the in-place default branch).
    """
    registry.atomic_swap(
        repo=repo,
        ref=ref,
        worktree=worktree,
        head_sha=sha,
        indexed_at=indexed_at,
        backend_version=index_result.backend_version,
        config_hash=config_hash,
        clone_dataset=clone_dataset,
        origin_snapshot=origin_snapshot,
    )
