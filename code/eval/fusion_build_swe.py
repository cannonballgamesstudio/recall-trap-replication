#!/usr/bin/env python3
"""Build fresh srclight + fusion indexes for the SWE-bench Verified repos.

Both arms rebuilt from the same worktree with the same srclight version so the
A/B shares one corpus (the worktrees' old .srclight indexes have drifted file
coverage). Smallest repos first so fusion_ab.py --bench swe --repos ... can
report partial results early. Designed to run DETACHED; progress to stdout
(redirect to a log).
"""
from __future__ import annotations
import json, os, sys, time, traceback
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
os.environ.setdefault("OPENAI_BASE_URL", "http://127.0.0.1:8080")
os.environ.setdefault("OPENAI_API_KEY", "sk-noauth")

from fusion_ab import (EMBED_MODEL, DIMS, FUSION_IDX_ROOT, SRCL_IDX_ROOT,
                       backends, slug, worktree)

ORDER = ["pallets/flask", "psf/requests", "mwaskom/seaborn", "pylint-dev/pylint",
         "pytest-dev/pytest", "pydata/xarray", "astropy/astropy",
         "sphinx-doc/sphinx", "matplotlib/matplotlib",
         "scikit-learn/scikit-learn", "django/django", "sympy/sympy"]


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if "--augment" in sys.argv or "--augment-graph" in sys.argv:
        from ragfusion.fusion.graph import build_adjacency
        from ragfusion.fusion.priors import build_priors
        from ragfusion.fusion.trigram import build_trigrams
        for d in sorted(FUSION_IDX_ROOT.iterdir()):
            if not (d / "fusion.db").exists():
                continue
            repo = d.name.replace("__", "/", 1)
            wt = worktree(repo)
            adj = build_adjacency(d)
            tri = build_trigrams(d)
            pri = build_priors(d, wt) if wt else 0
            print(f"[augment] {d.name}: adj={adj} tri={tri} pri={pri}", flush=True)
        print("[all-done]", flush=True)
        return 0
    subset_path = (r"<EVAL_ROOT>\swebench-ml\subset.json" if "--bench-ml" in sys.argv
                   else r"<EVAL_ROOT>\swebench-verified\subset.json")
    subset = json.loads(Path(subset_path).read_text(encoding="utf-8"))
    needed = {c["repo"] for c in subset}
    repos = [r for r in ORDER if r in needed] + sorted(needed - set(ORDER))
    srcl, fus = backends()
    for repo in repos:
        wt = worktree(repo)
        if not wt:
            print(f"[skip] {repo}: no ready worktree", flush=True)
            continue
        for arm, be, root, marker in (("srclight", srcl, SRCL_IDX_ROOT, "index.db"),
                                      ("fusion", fus, FUSION_IDX_ROOT, "fusion_emb.npy")):
            d = root / slug(repo)
            if (d / marker).exists():
                print(f"[ok] {arm} {repo} already built", flush=True)
                continue
            t0 = time.time()
            print(f"[build] {arm} {repo} -> {d}", flush=True)
            try:
                res = be.index(wt, str(d))
                print(f"[done] {arm} {repo}: {res.symbols} symbols, "
                      f"{res.files_indexed} files, {time.time()-t0:.0f}s", flush=True)
            except Exception as e:
                print(f"[FAIL] {arm} {repo}: {type(e).__name__}: {e}", flush=True)
                traceback.print_exc()
        print(f"[ready] {repo}", flush=True)
    print("[all-done]", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
