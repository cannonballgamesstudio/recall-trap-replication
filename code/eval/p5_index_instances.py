#!/usr/bin/env python3
"""P5 Task 1 — per-instance index driver (docs/plans/2026-07-11-legit-benchmark-program.md).

Legit, leaderboard-methodology SWE-bench indexing: every instance gets its OWN
worktree at its own base_commit (not one representative-commit index per repo),
so retrieval is scored against the exact tree the model saw. A content-hash
embedding cache makes the per-instance-index cost tractable — instances cluster
densely in each repo's history, so most chunks repeat commit-to-commit.

Modes:
  --prep                     materialize <EVAL_ROOT>/p5/instances_verified.json from
                             the cached HF parquet (princeton-nlp/SWE-bench_Verified).
  (default)                  index mode: worktree + FusionBackend.index() + registry
                             registration, per instance, resumable.
  --cleanup                  print (do not execute) the cleanup commands for the
                             registry rows / worktrees / caches this driver creates.

Usage:
  python p5_index_instances.py --prep
  python p5_index_instances.py --repos pallets/flask --limit-instances 2
  python p5_index_instances.py --cleanup
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

os.environ.setdefault("OPENAI_BASE_URL", "http://127.0.0.1:8080")
os.environ.setdefault("OPENAI_API_KEY", "sk-noauth")

EMBED_MODEL = "openai:Qwen/Qwen3-Embedding-8B"
DIMS = 4096
REGISTRY = r"<EVAL_ROOT>\registry.db"
CONFIG_HASH = "p5"

HF_HOME = Path(r"<HF_HOME>")
CLONE_ROOT = Path(r"<EVAL_ROOT>\swebench")             # <org>__<name>__idx full-history clones
P5_ROOT = Path(r"<EVAL_ROOT>\p5")
INSTANCES_JSON = P5_ROOT / "instances_verified.json"
WT_ROOT = P5_ROOT / "wt"
EMBCACHE_ROOT = P5_ROOT / "embcache"

DIFF_HEADER_RE = re.compile(r"^diff --git a/(.+?) b/(?:.+)$", re.MULTILINE)


def slug(repo: str) -> str:
    return repo.replace("/", "__")


def sh(args: list[str], check: bool = True) -> str:
    r = subprocess.run(args, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(f"cmd failed ({r.returncode}): {' '.join(args)}\n{r.stderr[:500]}")
    return r.stdout


def gold_files_from_patch(patch: str) -> list[str]:
    """Repo-relative a/ paths from each `diff --git a/<p> b/<p>` header, deduped
    in first-seen order."""
    files: list[str] = []
    seen: set[str] = set()
    for m in DIFF_HEADER_RE.finditer(patch or ""):
        p = m.group(1).strip()
        if p and p not in seen:
            seen.add(p)
            files.append(p)
    return files


# ---------------------------------------------------------------- --prep
def find_snapshot_parquet() -> Path:
    pattern = str(HF_HOME / "hub" / "datasets--princeton-nlp--SWE-bench_Verified" /
                  "snapshots" / "*" / "data" / "test-00000-of-00001.parquet")
    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(f"no cached parquet matching {pattern} "
                                "(expected a HF datasets cache snapshot dir)")
    return Path(sorted(matches)[-1])


def cmd_prep(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    p = find_snapshot_parquet()
    print(f"[prep] reading {p}", flush=True)
    table = pq.read_table(p)
    rows = table.to_pylist()

    out = []
    for r in rows:
        out.append({
            "instance_id": r["instance_id"],
            "repo": r["repo"],
            "base_commit": r["base_commit"],
            "problem_statement": r["problem_statement"],
            "gold_files": gold_files_from_patch(r["patch"]),
            "url": f"https://github.com/{r['repo']}",
        })

    INSTANCES_JSON.parent.mkdir(parents=True, exist_ok=True)
    INSTANCES_JSON.write_text(json.dumps(out, indent=2), encoding="utf-8")

    c = Counter(x["repo"] for x in out)
    print(f"wrote {INSTANCES_JSON}: {len(out)} instances across {len(c)} repos", flush=True)
    for repo, n in c.most_common():
        print(f"  {repo}: {n}", flush=True)
    return 0


# ---------------------------------------------------------------- caching provider
class CachingProvider:
    """Wraps a real srclight EmbeddingProvider with a content-hash sqlite cache.

    One instance is meant to live for exactly one repo's worth of indexing
    (fresh cache path + fresh hit/miss counters per repo) — instances of the
    same repo share huge swaths of unchanged file content across base_commits,
    so the cache turns "N instances x full repo embed" into "~1 full embed +
    N x (changed chunks only)".
    """

    def __init__(self, inner, cache_path: Path):
        self._inner = inner
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._con = sqlite3.connect(str(self.cache_path))
        self._con.execute("CREATE TABLE IF NOT EXISTS emb (h TEXT PRIMARY KEY, v BLOB)")
        self._con.commit()
        self.hits = 0
        self.misses = 0

    @property
    def dimensions(self):
        return self._inner.dimensions

    @property
    def name(self):
        return self._inner.name

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

    def _lookup(self, hashes) -> dict[str, bytes]:
        found: dict[str, bytes] = {}
        hashes = list(hashes)
        CH = 500  # sqlite default var limit is 999; stay well under it
        for i in range(0, len(hashes), CH):
            batch = hashes[i:i + CH]
            qmarks = ",".join("?" * len(batch))
            for h, v in self._con.execute(f"SELECT h, v FROM emb WHERE h IN ({qmarks})", batch):
                found[h] = v
        return found

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        import numpy as np

        hashes = [self._hash(t) for t in texts]
        cached = self._lookup(set(hashes))

        out: list[list[float] | None] = [None] * len(texts)
        miss_hash_to_text: dict[str, str] = {}
        for i, h in enumerate(hashes):
            if h in cached:
                out[i] = np.frombuffer(cached[h], dtype=np.float16).astype(np.float32).tolist()
                self.hits += 1
            else:
                self.misses += 1
                miss_hash_to_text.setdefault(h, texts[i])

        if miss_hash_to_text:
            miss_hashes = list(miss_hash_to_text.keys())
            miss_texts = [miss_hash_to_text[h] for h in miss_hashes]
            vecs = self._inner.embed_batch(miss_texts)  # only misses hit the real provider
            vec_by_hash: dict[str, "np.ndarray"] = {}
            rows = []
            for h, v in zip(miss_hashes, vecs):
                v32 = np.asarray(v, dtype=np.float32)
                vec_by_hash[h] = v32
                rows.append((h, v32.astype(np.float16).tobytes()))
            self._con.executemany("INSERT OR REPLACE INTO emb (h, v) VALUES (?, ?)", rows)
            self._con.commit()
            for i, h in enumerate(hashes):
                if out[i] is None:
                    out[i] = vec_by_hash[h].tolist()

        return out

    def embed_one(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def close(self) -> None:
        self._con.close()


# ---------------------------------------------------------------- index mode
def registry_is_ready(repo: str, ref: str) -> bool:
    con = sqlite3.connect(f"file:{REGISTRY}?mode=ro", uri=True)
    try:
        row = con.execute(
            "SELECT status FROM refs WHERE repo=? AND ref=?", (repo, ref)
        ).fetchone()
    finally:
        con.close()
    return bool(row) and row[0] == "ready"


def commit_time(clone: Path, sha: str) -> int:
    try:
        return int(sh(["git", "-C", str(clone), "log", "-1", "--format=%ct", sha]).strip())
    except Exception:
        return 0


def cmd_index(args: argparse.Namespace) -> int:
    from ragfusion.fusion.fusion_backend import FusionBackend
    from ragfusion.registry import Registry
    from srclight.embeddings import get_provider

    if not INSTANCES_JSON.exists():
        print(f"[error] {INSTANCES_JSON} missing; run --prep first", flush=True)
        return 1
    manifest = Path(args.instances_json) if args.instances_json else INSTANCES_JSON
    instances = json.loads(manifest.read_text(encoding="utf-8"))

    if args.repos:
        wanted = set(args.repos)
        instances = [x for x in instances if x["repo"] in wanted]

    by_repo: dict[str, list[dict]] = {}
    for x in instances:
        by_repo.setdefault(x["repo"], []).append(x)

    Registry.init_db(REGISTRY)  # idempotent: CREATE TABLE IF NOT EXISTS + column migration
    WT_ROOT.mkdir(parents=True, exist_ok=True)
    EMBCACHE_ROOT.mkdir(parents=True, exist_ok=True)

    for repo in sorted(by_repo):
        insts = by_repo[repo]
        clone_root = Path(args.clones_root) if args.clones_root else CLONE_ROOT
        clone = clone_root / f"{slug(repo)}__idx"
        if not clone.exists():
            print(f"[skip-repo] {repo}: no full-history clone at {clone}", flush=True)
            continue

        sh(["git", "-C", str(clone), "worktree", "prune"], check=False)

        order = sorted(insts, key=lambda x: commit_time(clone, x["base_commit"]))
        if args.limit_instances:
            order = order[: args.limit_instances]

        cache_path = EMBCACHE_ROOT / f"{slug(repo)}.sqlite"
        cp = CachingProvider(get_provider(EMBED_MODEL), cache_path)
        backend = FusionBackend(embed_model=EMBED_MODEL, dims=DIMS,
                                provider_factory=lambda model, _cp=cp: _cp)

        for x in order:
            iid = x["instance_id"]
            sha = x["base_commit"]
            wt = WT_ROOT / iid

            if (wt / ".srclight" / "fusion_emb.npy").exists() and registry_is_ready(repo, iid):
                print(f"[skip-resume] {iid}", flush=True)
                continue

            try:
                if not wt.exists():
                    sh(["git", "-C", str(clone), "worktree", "add", "--detach",
                        str(wt), sha])

                h0, m0 = cp.hits, cp.misses
                backend.index(str(wt), str(wt / ".srclight"))
                dh, dm = cp.hits - h0, cp.misses - m0
                tot = dh + dm
                rate = (dh / tot * 100.0) if tot else 0.0

                Registry(REGISTRY).atomic_swap(
                    repo=repo,
                    ref=iid,
                    worktree=str(wt),
                    head_sha=sha,
                    indexed_at=int(time.time()),
                    backend_version=backend.capabilities().backend_version,
                    config_hash=CONFIG_HASH,
                )
                print(f"[ready] {iid} embed_hits={dh} embed_misses={dm} "
                      f"hit_rate={rate:.1f}%", flush=True)
            except Exception as e:
                print(f"[FAIL] {iid}: {type(e).__name__}: {e}", flush=True)
                continue

        print(f"[repo-done] {slug(repo)} hits={cp.hits} misses={cp.misses}", flush=True)
        cp.close()

    print("[all-done]", flush=True)
    return 0


# ---------------------------------------------------------------- --cleanup
def cmd_cleanup(args: argparse.Namespace) -> int:
    """Print (never execute) the cleanup for this driver's footprint.

    Registry pollution risk (plan §Risks): this driver registers one ref per
    instance under `config_hash='p5'`, namespaced by instance_id — distinct
    from the repo-level `ref='eval'` rows used by the older per-repo harnesses.
    """
    print("# --- P5 per-instance index driver cleanup (DOCUMENTATION ONLY) ---")
    print("# Nothing below is executed; copy/paste what you actually want to run.")
    print()
    print("# 1) Registry rows this driver wrote (namespaced by config_hash='p5'):")
    print(f'sqlite3 "{REGISTRY}" "DELETE FROM refs WHERE config_hash=\'p5\';"')
    print()
    print("# 2) Worktrees: prune each repo's git worktree list, then remove the dirs.")
    print(f'for /d %W in ("{CLONE_ROOT}\\*__idx") do git -C "%W" worktree prune')
    print(f'Remove-Item -Recurse -Force "{WT_ROOT}"')
    print()
    print("# 3) Embedding caches (safe to delete any time; pure content-addressed cache,")
    print("#    rebuilt lazily on next --index run):")
    print(f'Remove-Item -Recurse -Force "{EMBCACHE_ROOT}"')
    print()
    print("# 4) instances_verified.json (regenerate any time via --prep):")
    print(f'Remove-Item -Force "{INSTANCES_JSON}"')
    return 0


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--prep", action="store_true", help="materialize instances_verified.json")
    ap.add_argument("--cleanup", action="store_true", help="print (don't run) cleanup commands")
    ap.add_argument("--clones-root", default=None,
                    help="override CLONE_ROOT (ml clones live under swebench-ml/repos)")
    ap.add_argument("--instances-json", default=None,
                    help="override the instances manifest (e.g. the ml set)")
    ap.add_argument("--repos", nargs="*", default=None, help="filter to these repo(s)")
    ap.add_argument("--limit-instances", type=int, default=None,
                    help="cap instances processed per repo (after commit-time sort)")
    args = ap.parse_args()

    if args.prep:
        return cmd_prep(args)
    if args.cleanup:
        return cmd_cleanup(args)
    return cmd_index(args)


if __name__ == "__main__":
    raise SystemExit(main())
