# src/ragfusion/fusion/graph.py
from __future__ import annotations

from pathlib import Path

# Type weights per spec §2, multiplied by srclight's per-edge confidence.
EDGE_WEIGHTS = {"contains": 1.0, "calls": 0.9, "inherits": 0.8,
                "implements": 0.8, "imports": 0.7}
DEFAULT_EDGE_WEIGHT = 0.6

_SCHEMA = """
DROP TABLE IF EXISTS adjacency;
CREATE TABLE adjacency(
  src INTEGER NOT NULL,
  dst INTEGER NOT NULL,
  w REAL NOT NULL,
  edge_type TEXT NOT NULL,
  PRIMARY KEY(src, dst, edge_type)
) WITHOUT ROWID;
CREATE INDEX adj_src ON adjacency(src);
"""


def build_adjacency(index_dir: Path) -> int:
    """(Re)build the graph arm's adjacency table from srclight's index.db.

    Additive + idempotent: reads srclight via its public API, maps symbol ids to
    fusion emb_rows, stores BOTH directions. Safe to run on an existing fusion.db
    without touching embeddings (the augment path for already-built indexes).
    """
    from srclight.db import Database

    from ragfusion.fusion import store

    index_dir = Path(index_dir)
    conn = store.open_db(index_dir / "fusion.db")
    sdb = Database(index_dir / "index.db")
    try:
        sdb.open()
        row_of = {r["id"]: r["emb_row"] for r in conn.execute("SELECT id, emb_row FROM chunks")}
        # Policy: max — the strongest evidence between two nodes governs expansion.
        # Two independent same-type edges (e.g. srclight-detected A->B and B->A
        # "calls" edges with different confidences) must not silently collide;
        # aggregate by max() in both directions instead of letting insert order win.
        agg: dict[tuple[int, int, str], float] = {}

        def add(src_sym: int, dst_sym: int, etype: str, conf: float) -> None:
            s, d = row_of.get(src_sym), row_of.get(dst_sym)
            if s is None or d is None or s == d:
                return
            w = EDGE_WEIGHTS.get(etype, DEFAULT_EDGE_WEIGHT) * float(conf)
            for k in ((s, d, etype), (d, s, etype)):
                agg[k] = max(agg.get(k, 0.0), w)

        for path in sdb.all_file_paths():
            for sym in sdb.symbols_in_file(path):
                if sym.parent_symbol_id is not None:
                    add(sym.id, sym.parent_symbol_id, "contains", 1.0)
                for e in sdb.get_callees(sym.id):
                    add(sym.id, e["symbol"].id, e.get("edge_type") or "calls",
                        (e.get("confidence") or 1.0))

        conn.executescript(_SCHEMA)
        conn.executemany("INSERT INTO adjacency(src, dst, edge_type, w) "
                         "VALUES(?,?,?,?)",
                         [(s, d, etype, w) for (s, d, etype), w in sorted(agg.items())])
        conn.commit()
        return len(agg)
    finally:
        conn.close()
        sdb.close()


_HOP_DAMP = 0.5


def expand(conn, seeds: list[tuple[int, float]], *, hops: int = 1,
           cap: int = 50) -> list[tuple[int, float]]:
    """Deterministic bounded expansion: score(u) = Σ seed_score(v)·w(v,u).

    hops=2 runs one more pass over the hop-1 frontier, damped ×0.5. Pure SQLite;
    raises sqlite3.OperationalError if the adjacency table is absent (caller
    fail-softs per spec §2).
    """
    scores: dict[int, float] = {}
    frontier = list(seeds)
    damp = 1.0
    for _ in range(max(1, hops)):
        nxt: dict[int, float] = {}
        for v, sv in frontier:
            for r in conn.execute("SELECT dst, w FROM adjacency WHERE src=?", (v,)):
                add = sv * r["w"] * damp
                nxt[r["dst"]] = nxt.get(r["dst"], 0.0) + add
        for u, s in nxt.items():
            scores[u] = scores.get(u, 0.0) + s
        frontier = list(nxt.items())
        damp *= _HOP_DAMP
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return ranked[:cap]
