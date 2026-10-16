#!/usr/bin/env python3
"""SWE-PolyBench per-instance fusion index build + registry registration.

Pre-registered in docs/paper/NEXT-BENCHMARKS-DESIGN.md (Pre-reg 1, rule R2/B-5).
Mirrors p5_index_instances.py (the SWE-Verified per-instance pipeline) but:
  - PolyBench namespace: worktrees/embcache under <EVAL_ROOT>\\polybench, registry
    rows under config_hash='polybench' (in the SAME <EVAL_ROOT>\\registry.db the live
    retrievald daemons resolve, so no daemon restart is needed to serve PolyBench packs).
  - R2 mitigation applied BEFORE indexing: prune EXCLUDE_DIRS (node_modules, dist,
    build, ...) from each checked-out worktree, then count indexable source files;
    if an instance still exceeds --max-files it is EXCLUDED-BEFORE-MODELLING and
    logged to inclusion_polybench.jsonl (never silently dropped, never post-hoc).
  - Reuses CachingProvider/slug/sh/commit_time/registry_is_ready from
    p5_index_instances so the embedding-cache economics are identical.

  python polybench_index.py --repos google/gson            # one repo
  python polybench_index.py --langs Java TypeScript        # by language
  python polybench_index.py                                # all ready clones
"""
from __future__ import annotations
import argparse, json, os, shutil, sys, time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
os.environ.setdefault("OPENAI_BASE_URL", "http://127.0.0.1:8080")
os.environ.setdefault("OPENAI_API_KEY", "sk-noauth")

from p5_index_instances import (CachingProvider, slug, sh, commit_time,
                                registry_is_ready, EMBED_MODEL, DIMS, REGISTRY)

ROOT = Path(r"<EVAL_ROOT>\polybench")
MANIFEST = ROOT / "instances_polybench.json"
CLONE_ROOT = ROOT / "repos"
WT_ROOT = ROOT / "wt"
EMBCACHE_ROOT = ROOT / "embcache"
INCLUSION_LOG = ROOT / "inclusion_polybench.jsonl"
CONFIG_HASH = "polybench"

# R2: prune before indexing. node_modules/dist/build are usually gitignored (absent
# from a base_commit checkout) but vendored/generated trees do get committed; pruning
# bounds file count + OOM risk deterministically. Applied to EVERY dir of these names.
EXCLUDE_DIRS = {"node_modules", "dist", "build", "out", ".yarn", ".next", ".cache",
                "coverage", "vendor", "target", ".git", "__pycache__", ".gradle",
                "bower_components", ".venv", "venv"}
# indexable source extensions (srclight LANGUAGES code langs; docs/md excluded from budget)
SRC_EXT = {".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".java",
           ".go", ".rs", ".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".cs", ".kt", ".php"}


def prune_excludes(wt: Path) -> int:
    removed = 0
    for d in list(wt.rglob("*")):
        if d.is_dir() and d.name in EXCLUDE_DIRS:
            try:
                shutil.rmtree(d, ignore_errors=True); removed += 1
            except Exception:
                pass
    return removed


def count_src(wt: Path) -> int:
    n = 0
    for p in wt.rglob("*"):
        if p.is_file() and p.suffix.lower() in SRC_EXT:
            n += 1
    return n


def main() -> int:
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", nargs="*", default=None)
    ap.add_argument("--langs", nargs="*", default=None, help="filter by manifest language (Java/JavaScript/TypeScript/Python)")
    ap.add_argument("--max-files", type=int, default=15000, help="R2 source-file budget; instances over it are excluded-before-modelling")
    ap.add_argument("--limit-instances", type=int, default=None)
    ap.add_argument("--shard", default=None, help="I/N: process every Nth instance offset I (per-repo, for parallel workers on one big repo)")
    args = ap.parse_args()
    shard_i = shard_n = None
    if args.shard:
        shard_i, shard_n = (int(v) for v in args.shard.split("/"))

    from ragfusion.fusion.fusion_backend import FusionBackend
    from ragfusion.registry import Registry
    from srclight.embeddings import get_provider

    instances = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if args.repos:
        instances = [x for x in instances if x["repo"] in set(args.repos)]
    if args.langs:
        want = set(args.langs)
        instances = [x for x in instances if x.get("language") in want]

    by_repo: dict[str, list[dict]] = {}
    for x in instances:
        by_repo.setdefault(x["repo"], []).append(x)

    Registry.init_db(REGISTRY)
    WT_ROOT.mkdir(parents=True, exist_ok=True)
    EMBCACHE_ROOT.mkdir(parents=True, exist_ok=True)
    inc = INCLUSION_LOG.open("a", encoding="utf-8")

    for repo in sorted(by_repo):
        insts = by_repo[repo]
        clone = CLONE_ROOT / f"{slug(repo)}__idx"
        if not (clone / "HEAD").exists() and not (clone / ".git").exists():
            print(f"[skip-repo] {repo}: no clone at {clone} (run polybench_clone.py first)", flush=True)
            continue
        sh(["git", "-C", str(clone), "worktree", "prune"], check=False)
        order = sorted(insts, key=lambda x: commit_time(clone, x["base_commit"]))
        if args.limit_instances:
            order = order[: args.limit_instances]
        if shard_n:
            order = order[shard_i::shard_n]

        cache_path = EMBCACHE_ROOT / f"{slug(repo)}.sqlite"
        cp = CachingProvider(get_provider(EMBED_MODEL), cache_path)
        backend = FusionBackend(embed_model=EMBED_MODEL, dims=DIMS,
                                provider_factory=lambda model, _cp=cp: _cp)

        for x in order:
            iid, sha, lang = x["instance_id"], x["base_commit"], x.get("language")
            wt = WT_ROOT / iid
            if (wt / ".srclight" / "fusion_emb.npy").exists() and registry_is_ready(repo, iid):
                print(f"[skip-resume] {iid}", flush=True); continue
            try:
                if not wt.exists():
                    sh(["git", "-C", str(clone), "worktree", "add", "--detach", str(wt), sha])
                pruned = prune_excludes(wt)
                nsrc = count_src(wt)
                if nsrc > args.max_files:
                    inc.write(json.dumps({"instance_id": iid, "language": lang, "included": False,
                                          "reason": "over_file_budget", "n_src": nsrc,
                                          "budget": args.max_files, "pruned_dirs": pruned}) + "\n"); inc.flush()
                    print(f"[EXCLUDE] {iid} n_src={nsrc} > budget={args.max_files} (pre-modelling)", flush=True)
                    sh(["git", "-C", str(clone), "worktree", "remove", "--force", str(wt)], check=False)
                    shutil.rmtree(wt, ignore_errors=True)
                    continue
                h0, m0 = cp.hits, cp.misses
                backend.index(str(wt), str(wt / ".srclight"))
                dh, dm = cp.hits - h0, cp.misses - m0
                Registry(REGISTRY).atomic_swap(
                    repo=repo, ref=iid, worktree=str(wt), head_sha=sha,
                    indexed_at=int(time.time()),
                    backend_version=backend.capabilities().backend_version,
                    config_hash=CONFIG_HASH)
                inc.write(json.dumps({"instance_id": iid, "language": lang, "included": True,
                                      "n_src": nsrc, "pruned_dirs": pruned,
                                      "embed_hits": dh, "embed_misses": dm}) + "\n"); inc.flush()
                print(f"[ready] {iid} lang={lang} n_src={nsrc} hits={dh} misses={dm}", flush=True)
            except Exception as e:
                inc.write(json.dumps({"instance_id": iid, "language": lang, "included": False,
                                      "reason": f"{type(e).__name__}: {str(e)[:120]}"}) + "\n"); inc.flush()
                print(f"[FAIL] {iid}: {type(e).__name__}: {str(e)[:120]}", flush=True)
                continue
        print(f"[repo-done] {slug(repo)} cache_hits={cp.hits} cache_misses={cp.misses}", flush=True)
        cp.close()

    inc.close()
    print("[all-done]", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
