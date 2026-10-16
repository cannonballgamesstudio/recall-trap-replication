#!/usr/bin/env python3
"""Clone the 21 SWE-PolyBench repos (treeless) for the multilingual generality arm.

Pre-registered in docs/paper/NEXT-BENCHMARKS-DESIGN.md (Pre-reg 1). Treeless
(--filter=blob:none) so we get full commit history cheaply and let `git worktree
add <base_commit>` lazily fetch only the blobs each instance's snapshot needs —
essential for the large TS/JS monorepos (vscode, material-ui, svelte) and the big
Java/Python ones (trino, transformers). Clones land as <root>/<slug>__idx, the
layout p5_index_instances.py / polybench_index.py expect. Smallest-instance-count
repos first so indexing can start on ready repos early. Resumable.

  python polybench_clone.py            # clone all, smallest-first
  python polybench_clone.py --repos google/gson prettier/prettier
"""
import argparse, json, subprocess, sys, time
from collections import Counter
from pathlib import Path

MAN = Path(r"<EVAL_ROOT>\polybench\instances_polybench.json")
CLONE_ROOT = Path(r"<EVAL_ROOT>\polybench\repos")


def slug(repo): return repo.replace("/", "__")


def sh(args, check=True):
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(f"cmd failed ({r.returncode}): {' '.join(args)}\n{r.stderr[:400]}")
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", nargs="*", default=None)
    args = ap.parse_args()
    man = json.loads(MAN.read_text(encoding="utf-8"))
    order = [r for r, _ in Counter(x["repo"] for x in man).most_common()][::-1]  # small first
    if args.repos:
        order = [r for r in order if r in set(args.repos)]
    CLONE_ROOT.mkdir(parents=True, exist_ok=True)
    for repo in order:
        dest = CLONE_ROOT / f"{slug(repo)}__idx"
        if (dest / ".git").exists() or (dest / "HEAD").exists():
            print(f"[skip] {repo} already cloned at {dest}", flush=True); continue
        url = f"https://github.com/{repo}"
        t0 = time.time()
        print(f"[clone] {repo} (treeless) -> {dest}", flush=True)
        try:
            sh(["git", "clone", "--filter=blob:none", "--no-checkout", url, str(dest)])
            print(f"[done] {repo} in {time.time()-t0:.0f}s", flush=True)
        except Exception as e:
            print(f"[FAIL] {repo}: {str(e)[:200]}", flush=True)
    print("[all-cloned]", flush=True)


if __name__ == "__main__":
    sys.exit(main())
