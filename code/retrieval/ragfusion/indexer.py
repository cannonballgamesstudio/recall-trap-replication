from __future__ import annotations

import os
from dataclasses import dataclass

from ragfusion import naming
from ragfusion.indexing import register_built_index
from ragfusion.lifecycle import prepare_ref_clone


@dataclass(frozen=True)
class IndexOutcome:
    status: str                     # "indexed" | "noop" | "failed"
    repo: str
    ref: str
    sha: str
    worktree: str | None = None
    error: str | None = None


def needs_reindex(existing, sha, backend_version, config_hash) -> bool:
    if existing is None:
        return True
    return (existing.status != "ready"
            or existing.head_sha != sha
            or existing.backend_version != backend_version
            or existing.config_hash != config_hash)


def _index_dir(worktree: str) -> str:
    return os.path.join(worktree, ".srclight")


def _main_db_path(main_mp: str) -> str:
    return os.path.join(main_mp, ".srclight", "index.db")


def _safe_reap(storage, clone_dataset, origin_snapshot) -> None:
    """Best-effort reap of a clone + its origin snapshot.

    Swallows errors: stragglers from a partial/raced reap are reclaimed by the
    Phase-5 orphan sweep; a failed reap must never mask the real outcome.
    """
    try:
        if clone_dataset:
            storage.destroy(clone_dataset, recursive=True)
    except Exception:
        pass
    try:
        if origin_snapshot:
            main_ds, snap = origin_snapshot.split("@", 1)
            storage.destroy_snapshot(main_ds, snap)
    except Exception:
        pass


def index_ref(repo, ref, sha, *, registry, storage, backend, gitops,
              pool, default_branch, config_hash, indexed_at) -> IndexOutcome:
    backend_version = backend.capabilities().backend_version
    existing = registry.resolve(repo, ref)
    if not needs_reindex(existing, sha, backend_version, config_hash):
        return IndexOutcome("noop", repo, ref, sha, worktree=existing.worktree)

    main_ds = naming.main_dataset(pool, repo)
    if ref == default_branch:
        return _index_in_place(repo, ref, sha, main_ds, registry=registry,
                               storage=storage, backend=backend, gitops=gitops,
                               config_hash=config_hash, indexed_at=indexed_at,
                               existing=existing, backend_version=backend_version)
    return _index_clone(repo, ref, sha, main_ds, existing, registry=registry,
                        storage=storage, backend=backend, gitops=gitops, pool=pool,
                        config_hash=config_hash, indexed_at=indexed_at,
                        backend_version=backend_version)


def _index_in_place(repo, ref, sha, main_ds, *, registry, storage, backend, gitops,
                    config_hash, indexed_at, existing, backend_version) -> IndexOutcome:
    main_mp = storage.mountpoint(main_ds)
    try:
        gitops.fetch_and_checkout(main_mp, ref, sha)
        result = backend.index(main_mp, _index_dir(main_mp))
    except Exception as e:  # default-branch base build failed; leave any prior row intact
        if existing is None:
            registry.upsert_ref(repo, ref, sha, "", "failed", indexed_at,
                                backend_version, config_hash)
        return IndexOutcome("failed", repo, ref, sha, error=str(e))
    register_built_index(registry, repo, ref, sha, main_mp, result, config_hash,
                         indexed_at, clone_dataset=main_ds, origin_snapshot=None)
    return IndexOutcome("indexed", repo, ref, sha, worktree=main_mp)


def _index_clone(repo, ref, sha, main_ds, existing, *, registry, storage, backend,
                 gitops, pool, config_hash, indexed_at, backend_version) -> IndexOutcome:
    main_mp = storage.mountpoint(main_ds)
    snap = naming.snap_name(ref, sha, indexed_at)
    ref_ds = naming.ref_dataset(pool, repo, ref, sha, indexed_at)
    new_origin = f"{main_ds}@{snap}"
    if existing is not None and ref_ds == existing.clone_dataset:
        return IndexOutcome("failed", repo, ref, sha,
                            error="naming-token collision with the live clone; pass a fresh indexed_at")
    try:
        clone_mp = prepare_ref_clone(storage, main_ds, _main_db_path(main_mp), snap, ref_ds)
        gitops.fetch_and_checkout(clone_mp, ref, sha)
        result = backend.index(clone_mp, _index_dir(clone_mp))
    except Exception as e:
        _safe_reap(storage, ref_ds, new_origin)        # drop the partial clone+snapshot
        if existing is None:                            # brand-new ref: record failure
            registry.upsert_ref(repo, ref, sha, "", "failed", indexed_at,
                                backend_version, config_hash)
        return IndexOutcome("failed", repo, ref, sha, error=str(e))

    prev_clone = existing.clone_dataset if existing else None
    prev_origin = existing.origin_snapshot if existing else None

    register_built_index(registry, repo, ref, sha, clone_mp, result, config_hash,
                         indexed_at, clone_dataset=ref_ds, origin_snapshot=new_origin)

    if prev_origin is not None:                         # reap previous, post-swap (1:1)
        _safe_reap(storage, prev_clone, prev_origin)
    return IndexOutcome("indexed", repo, ref, sha, worktree=clone_mp)
