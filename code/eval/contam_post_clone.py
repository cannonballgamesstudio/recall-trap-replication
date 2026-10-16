#!/usr/bin/env python3
"""Contamination pre-reg, Branch A: full-history (treeless) clones of the post-cutoff repos.

Same recipe as polybench_clone.py: `git clone --filter=blob:none --no-checkout`, which
keeps every commit and tree (full history) and fetches blobs lazily when
`git worktree add <base_commit>` materializes a snapshot. Clones land as
<root>/<org>__<name>__idx, the layout the index driver expects. Resumable.
Verifies every manifest base_commit resolves in its clone.

  python contam_post_clone.py [--jobs 4]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(r"data/post-cutoff-branchA")
MAN = ROOT / "instances_post.json"
CLONE_ROOT = ROOT / "repos"


def slug(repo: str) -> str:
    return repo.replace("/", "__")


def sh(args, check=True):
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(f"cmd failed ({r.returncode}): {' '.join(args)}\n{r.stderr[:400]}")
    return r


def clone_one(repo: str, shas: list[str]) -> str:
    dest = CLONE_ROOT / f"{slug(repo)}__idx"
    t0 = time.time()
    if not ((dest / ".git").exists() or (dest / "HEAD").exists()):
        try:
            sh(["git", "clone", "--filter=blob:none", "--no-checkout",
                f"https://github.com/{repo}", str(dest)])
        except Exception as e:
            return f"[FAIL] {repo}: {str(e)[:200]}"
    missing = []
    for sha in shas:
        if sh(["git", "-C", str(dest), "cat-file", "-e", f"{sha}^{{commit}}"], check=False).returncode:
            # base commit may live on a non-default ref (PR head); try fetching it directly
            sh(["git", "-C", str(dest), "fetch", "--filter=blob:none", "origin", sha], check=False)
            if sh(["git", "-C", str(dest), "cat-file", "-e", f"{sha}^{{commit}}"], check=False).returncode:
                missing.append(sha)
    if missing:
        return f"[MISSING-COMMIT] {repo}: {missing}"
    return f"[done] {repo} ({len(shas)} commits ok) {time.time() - t0:.0f}s"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    args = ap.parse_args()
    man = json.loads(MAN.read_text(encoding="utf-8"))
    shas: dict[str, list[str]] = {}
    for x in man:
        shas.setdefault(x["repo"], []).append(x["base_commit"])
    order = [r for r, _ in Counter(x["repo"] for x in man).most_common()][::-1]
    CLONE_ROOT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(args.jobs) as ex:
        for msg in ex.map(lambda r: clone_one(r, shas[r]), order):
            print(msg, flush=True)
    print("[all-cloned]", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
