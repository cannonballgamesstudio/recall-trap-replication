#!/usr/bin/env python3
"""Contamination pre-reg, Branch A: prefetch dedupON / dedupOFF packs with the PINNED stack.

DO NOT RUN until docs/paper/CONTAMINATION-PREREG.md is committed (the script checks).

Packs are built exactly like the headline local_packs.json (prefetch_500.py default mode):
two retrievald daemons started FROM THE PINNED WORKTREE code/retrieval (RETRIEVALD_BACKEND=fusion,
all other RetrievaldConfig defaults of 4fab615), :8083 with file-dedup ON (default) and :8084 with
RETRIEVALD_QUERY_DEDUP_FILE=0; hybrid mode, limit 12, code_only=True, query = problem_statement[:6000];
fetch_pack / format_pack imported from the pinned g_plane_prompts.py.

Launch the daemons first (from the pinned worktree; embedder on :8082):
  set PYTHONPATH=code/retrieval
  set RETRIEVALD_BACKEND=fusion & set RETRIEVALD_EMBED_MODEL=openai:Qwen/Qwen3-Embedding-8B & set RETRIEVALD_DIMS=4096
  set RETRIEVALD_REGISTRY_DB=<EVAL_ROOT>\\registry.db & set OPENAI_BASE_URL=http://127.0.0.1:8082 & set OPENAI_API_KEY=sk-noauth
  python -m uvicorn ragfusion.retrievald.server:build_app --factory --host 127.0.0.1 --port 8083
  (second shell, same env plus) set RETRIEVALD_QUERY_DEDUP_FILE=0 -> --port 8084

  python contam_post_prefetch.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PIN_ROOT = Path(r"code/retrieval")
ROOT = Path(r"data/post-cutoff-branchA")
MANIFEST = ROOT / "instances_post.json"
INCLUSION = ROOT / "inclusion_post.jsonl"
OUT = ROOT / "post_packs.json"
ARMS = [("dedupON", "http://127.0.0.1:8083"), ("dedupOFF", "http://127.0.0.1:8084")]
K = 12
REPO_ROOT = Path(__file__).resolve().parents[2]


def prereg_committed() -> bool:
    r = subprocess.run(["git", "-C", str(REPO_ROOT), "log", "--format=%h", "-1", "--",
                        "docs/paper/CONTAMINATION-PREREG.md"], capture_output=True, text=True)
    return bool(r.stdout.strip())


def main() -> int:
    if not prereg_committed():
        print("REFUSE: docs/paper/CONTAMINATION-PREREG.md has no commit yet.")
        return 1
    sys.path.insert(0, str(PIN_ROOT / "scripts" / "eval"))
    sys.path.insert(0, str(PIN_ROOT / "src"))
    import g_plane_prompts as gp
    assert str(Path(gp.__file__).resolve()).lower().startswith(str(PIN_ROOT).lower()), gp.__file__
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ok = {}
    for line in INCLUSION.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        ok[r["instance_id"]] = bool(r.get("included"))
    out = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    for x in man:
        iid = x["instance_id"]
        if not ok.get(iid):
            print(f"[skip-not-indexed] {iid}", flush=True)
            continue
        for arm, ep in ARMS:
            if arm in out.get(iid, {}):
                continue
            try:
                h = gp.fetch_pack(ep, x["repo"], iid, x["problem_statement"][:6000], K, mode="hybrid")
            except Exception as e:
                print(f"[pack-FAIL] {iid} {arm}: {str(e)[:100]}", flush=True)
                continue
            out.setdefault(iid, {})[arm] = {"pack": gp.format_pack(h, K),
                                            "files": sorted({y.get("file", "") for y in h if y.get("file")}),
                                            "n_hits": len(h)}
            print(f"[pack] {iid} {arm} hits={len(h)}", flush=True)
        OUT.write_text(json.dumps(out), encoding="utf-8")
    print(f"[prefetch-done] {len(out)} instances -> {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
