import sqlite3


def checkpoint_truncate(db_path: str) -> None:
    """Fold the WAL into the main DB file before snapshotting (§8).

    Raises RuntimeError if the checkpoint was blocked (busy) and therefore did
    not fully fold the WAL — a subsequent snapshot would otherwise be inconsistent.
    """
    con = sqlite3.connect(db_path)
    try:
        busy, log, checkpointed = con.execute(
            "PRAGMA wal_checkpoint(TRUNCATE)"
        ).fetchone()
        if busy:
            raise RuntimeError(
                f"WAL checkpoint blocked: {log} frames logged, {checkpointed} checkpointed"
            )
    finally:
        con.close()
