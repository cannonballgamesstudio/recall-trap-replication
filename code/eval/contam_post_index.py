#!/usr/bin/env python3
"""Contamination pre-reg, Branch A: per-instance fusion index build with the PINNED stack.

Pre-registered in docs/paper/CONTAMINATION-PREREG.md (Branch A, binding stack).
The retrieval code is imported from the git worktree pinned at commit 4fab615
(code/retrieval), NOT from this checkout: the worktree's src/ and
scripts/eval/ are put first on sys.path and the import origins are asserted.
srclight must be exactly 0.15.1.

Recipe = rebench_index_prefetch.py index phase (per-instance worktree at base_commit,
EXCLUDE_DIRS prune, --max-files 15000 file budget, content-hash embedding cache,
registry registration) with CONFIG_HASH='swerebench-post'. NO pack prefetch: that
waits until the pre-registration is committed.

Requires the Qwen3-Embedding-8B llama.cpp server (default http://127.0.0.1:8082).

  python contam_post_index.py                 # index all, resumable
  python contam_post_index.py --repos pallets/click --limit 1
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path

PIN_ROOT = Path(r"code/retrieval")
PIN_COMMIT = "4fab615b4fe5148a8a8b7121c2e058f47a16366d"
SRCLIGHT_VERSION = "0.15.1"

ROOT = Path(r"data/post-cutoff-branchA")
MANIFEST = ROOT / "instances_post.json"
CLONE_ROOT = ROOT / "repos"
WT_ROOT = ROOT / "wt"
EMBCACHE_ROOT = ROOT / "embcache"
INCLUSION_LOG = ROOT / "inclusion_post.jsonl"
CONFIG_HASH = "swerebench-post"

EXCLUDE_DIRS = {"node_modules", "dist", "build", "out", ".yarn", ".next", ".cache", "coverage",
                "vendor", "target", ".git", "__pycache__", ".gradle", "bower_components",
                ".venv", "venv"}
SRC_EXT = {".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".java", ".go", ".rs",
           ".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".cs", ".kt", ".php"}


def _pin_imports():
    """Put the pinned worktree first on sys.path and verify every import origin."""
    import subprocess
    head = subprocess.run(["git", "-C", str(PIN_ROOT), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(PIN_ROOT), "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True).stdout.strip()
    assert head == PIN_COMMIT, f"pinned worktree at {head}, expected {PIN_COMMIT}"
    assert not dirty, f"pinned worktree has tracked modifications:\n{dirty}"
    for p in (PIN_ROOT / "scripts" / "eval", PIN_ROOT / "src"):
        sys.path.insert(0, str(p))
    os.environ.setdefault("OPENAI_BASE_URL", "http://127.0.0.1:8082")
    os.environ.setdefault("OPENAI_API_KEY", "sk-noauth")
    import srclight
    import ragfusion
    import p5_index_instances as p5
    from ragfusion.fusion import fusion_backend
    from ragfusion import registry
    for mod in (ragfusion, p5, fusion_backend, registry):
        f = Path(mod.__file__).resolve()
        assert str(f).lower().startswith(str(PIN_ROOT).lower()), f"{mod.__name__} imported from {f}"
    assert srclight.__version__ == SRCLIGHT_VERSION, f"srclight {srclight.__version__}"
    return p5, fusion_backend.FusionBackend, registry.Registry


def prune_excludes(wt: Path) -> int:
    removed = 0
    for d in list(wt.rglob("*")):
        if d.is_dir() and d.name in EXCLUDE_DIRS:
            shutil.rmtree(d, ignore_errors=True)
            removed += 1
    return removed


def count_src(wt: Path) -> int:
    return sum(1 for p in wt.rglob("*") if p.is_file() and p.suffix.lower() in SRC_EXT)


def foreign_row(repo: str, ref: str, registry_db: str) -> str | None:
    con = sqlite3.connect(f"file:{registry_db}?mode=ro", uri=True)
    try:
        row = con.execute("SELECT config_hash FROM refs WHERE repo=? AND ref=?", (repo, ref)).fetchone()
    finally:
        con.close()
    return row[0] if row and row[0] != CONFIG_HASH else None


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-files", type=int, default=15000)
    ap.add_argument("--repos", nargs="*", default=None)
    ap.add_argument("--limit", type=int, default=None, help="cap instances per repo")
    args = ap.parse_args()

    p5, FusionBackend, Registry = _pin_imports()
    from srclight.embeddings import get_provider
    import ragfusion
    print(f"[pin] commit={PIN_COMMIT[:7]} ragfusion={ragfusion.__file__} p5={p5.__file__} "
          f"embed={os.environ['OPENAI_BASE_URL']}", flush=True)

    instances = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if args.repos:
        instances = [x for x in instances if x["repo"] in set(args.repos)]
    by_repo: dict[str, list[dict]] = {}
    for x in instances:
        by_repo.setdefault(x["repo"], []).append(x)

    Registry.init_db(p5.REGISTRY)
    WT_ROOT.mkdir(parents=True, exist_ok=True)
    EMBCACHE_ROOT.mkdir(parents=True, exist_ok=True)
    inc = INCLUSION_LOG.open("a", encoding="utf-8")
    total, done, t_start = len(instances), 0, time.time()
    for repo in sorted(by_repo):
        clone = CLONE_ROOT / f"{p5.slug(repo)}__idx"
        if not ((clone / "HEAD").exists() or (clone / ".git").exists()):
            print(f"[skip-repo] {repo}: no clone at {clone}", flush=True)
            continue
        p5.sh(["git", "-C", str(clone), "worktree", "prune"], check=False)
        cp = p5.CachingProvider(get_provider(p5.EMBED_MODEL), EMBCACHE_ROOT / f"{p5.slug(repo)}.sqlite")
        backend = FusionBackend(embed_model=p5.EMBED_MODEL, dims=p5.DIMS,
                                provider_factory=lambda model, _cp=cp: _cp)
        order = sorted(by_repo[repo], key=lambda z: p5.commit_time(clone, z["base_commit"]))
        if args.limit:
            order = order[: args.limit]
        for x in order:
            iid, sha = x["instance_id"], x["base_commit"]
            wt = WT_ROOT / iid
            done += 1
            fr = foreign_row(repo, iid, p5.REGISTRY)
            if fr:
                print(f"[REFUSE] {iid}: registry row owned by config_hash={fr}", flush=True)
                continue
            if (wt / ".srclight" / "fusion_emb.npy").exists() and p5.registry_is_ready(repo, iid):
                print(f"[skip-resume] {iid} ({done}/{total})", flush=True)
                continue
            try:
                if not wt.exists():
                    p5.sh(["git", "-C", str(clone), "worktree", "add", "--detach", str(wt), sha])
                pruned = prune_excludes(wt)
                nsrc = count_src(wt)
                if nsrc > args.max_files:
                    inc.write(json.dumps({"instance_id": iid, "included": False,
                                          "reason": "over_file_budget", "n_src": nsrc}) + "\n")
                    inc.flush()
                    print(f"[EXCLUDE] {iid} n_src={nsrc} ({done}/{total})", flush=True)
                    continue
                t0, h0, m0 = time.time(), cp.hits, cp.misses
                backend.index(str(wt), str(wt / ".srclight"))
                Registry(p5.REGISTRY).atomic_swap(
                    repo=repo, ref=iid, worktree=str(wt), head_sha=sha,
                    indexed_at=int(time.time()),
                    backend_version=backend.capabilities().backend_version,
                    config_hash=CONFIG_HASH)
                secs = time.time() - t0
                inc.write(json.dumps({"instance_id": iid, "included": True, "n_src": nsrc,
                                      "pruned_dirs": pruned, "embed_hits": cp.hits - h0,
                                      "embed_misses": cp.misses - m0, "secs": round(secs, 1),
                                      "pin": PIN_COMMIT[:7]}) + "\n")
                inc.flush()
                el = time.time() - t_start
                eta = el / done * (total - done) / 60
                print(f"[ready] {iid} n_src={nsrc} misses={cp.misses - m0} {secs:.0f}s "
                      f"({done}/{total}, elapsed {el / 60:.0f}m, naive ETA {eta:.0f}m)", flush=True)
            except Exception as e:
                inc.write(json.dumps({"instance_id": iid, "included": False,
                                      "reason": f"{type(e).__name__}: {str(e)[:160]}"}) + "\n")
                inc.flush()
                print(f"[FAIL] {iid}: {type(e).__name__}: {str(e)[:160]}", flush=True)
        cp.close()
        print(f"[repo-done] {p5.slug(repo)} hits={cp.hits} misses={cp.misses}", flush=True)
    inc.close()
    print("[all-done]", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
