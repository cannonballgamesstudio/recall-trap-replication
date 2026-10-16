from ragfusion.quiesce import checkpoint_truncate


def prepare_ref_clone(storage, main_dataset, main_db_path, snap, ref_dataset) -> str:
    """Quiesce main, snapshot it, clone for the ref. Returns clone mountpoint (§8 order)."""
    checkpoint_truncate(main_db_path)
    storage.snapshot(main_dataset, snap)
    return storage.clone(main_dataset, snap, ref_dataset)


def gc_ref(repo, ref, *, registry, storage) -> None:
    """Reap a ref's clone + its origin snapshot, then drop the registry row (§8, issue #3).

    Driven by (repo, ref): reads what to reap from the registry row. Refuses to touch the
    in-place base (origin_snapshot is None) so the default branch's `main` is never
    destroyed here. Reap order: clone (recursive) -> origin snapshot -> row.
    """
    existing = registry.resolve(repo, ref)
    if existing is None:
        return
    if existing.origin_snapshot is None:
        return  # in-place base (default branch) — never destroyed via GC
    storage.destroy(existing.clone_dataset, recursive=True)
    main_dataset, snap = existing.origin_snapshot.split("@", 1)
    storage.destroy_snapshot(main_dataset, snap)
    registry.delete_ref(repo, ref)
