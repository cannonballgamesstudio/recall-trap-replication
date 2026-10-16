#!/usr/bin/env python3
"""Contamination pre-reg, Branch A: build the post-cutoff SWE-rebench manifest.

Pre-registered in docs/paper/CONTAMINATION-PREREG.md (Branch A, section A.2).
No network, no model calls. Reads the locally downloaded parquet of
nebius/SWE-rebench-leaderboard (test split) and writes
data/post-cutoff-branchA/instances_post.json.

Inclusion rule (binding):
  1. split == test of nebius/SWE-rebench-leaderboard (parquet sha256 recorded below)
  2. Python: every leaderboard row carries a Python install_config (asserted)
  3. created_at >= 2026-02-16 (UTC; parsed with pandas format='mixed')
  4. instance_id does NOT end with '_interface' (the interface-annotated duplicates)
Flag: stratum_0401 = created_at >= 2026-04-01 (sensitivity stratum).

  python contam_post_manifest.py [--parquet PATH] [--out PATH]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

DEFAULT_PARQUET = Path(
    r"<scratch>"
    r"\scratchpad\contam\web\pq\nebius_SWE-rebench-leaderboard_data_test-00000-of-00001.parquet")
DEFAULT_OUT = Path(r"data/post-cutoff-branchA\instances_post.json")
EXPECTED_SHA256 = "1497b218db0a8259d22471812f0de12b779c699daf741b930d68bc717636f0bf"
CUTOFF = "2026-02-16"
SENS_CUTOFF = "2026-04-01"
DIFF_HEADER_RE = re.compile(r"^diff --git a/(.+?) b/(?:.+)$", re.MULTILINE)


def gold_files_from_patch(patch: str) -> list[str]:
    out, seen = [], set()
    for m in DIFF_HEADER_RE.finditer(patch or ""):
        p = m.group(1).strip()
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _tolist(v):
    try:
        return [str(x) for x in list(v)]
    except TypeError:
        return []


def build(parquet: Path) -> list[dict]:
    import pandas as pd

    df = pd.read_parquet(parquet)
    df["ts"] = pd.to_datetime(df["created_at"], utc=True, format="mixed", errors="coerce")
    assert df["ts"].notna().all(), "unparseable created_at"
    assert df["install_config"].apply(lambda c: bool((c or {}).get("python"))).all(), \
        "non-Python row in leaderboard"
    s = df[(df["ts"] >= pd.Timestamp(CUTOFF, tz="UTC"))
           & (~df["instance_id"].str.endswith("_interface"))]
    s = s.sort_values(["ts", "instance_id"])
    out = []
    for _, r in s.iterrows():
        out.append({
            "instance_id": r["instance_id"],
            "repo": r["repo"],
            "base_commit": r["base_commit"],
            "created_at": str(r["created_at"]),
            "stratum_0401": bool(r["ts"] >= pd.Timestamp(SENS_CUTOFF, tz="UTC")),
            "problem_statement": r["problem_statement"],
            "gold_files": gold_files_from_patch(r["patch"]),
            "patch": r["patch"],
            "test_patch": r["test_patch"],
            "FAIL_TO_PASS": _tolist(r["FAIL_TO_PASS"]),
            "PASS_TO_PASS": _tolist(r["PASS_TO_PASS"]),
            "docker_image": r.get("docker_image"),
            "python": (r["install_config"] or {}).get("python"),
            "url": f"https://github.com/{r['repo']}",
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", default=str(DEFAULT_PARQUET))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    pq = Path(args.parquet)
    sha = hashlib.sha256(pq.read_bytes()).hexdigest()
    print(f"[parquet] {pq}\n[sha256] {sha} {'OK' if sha == EXPECTED_SHA256 else 'MISMATCH'}")
    out = build(pq)
    n0401 = sum(x["stratum_0401"] for x in out)
    print(f"[manifest] n={len(out)} repos={len({x['repo'] for x in out})} >=2026-04-01: {n0401}")
    p = Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1), encoding="utf-8")
    ids = "\n".join(x["instance_id"] for x in out) + "\n"
    print(f"[ids-sha256] {hashlib.sha256(ids.encode()).hexdigest()}")
    (p.parent / "instance_ids_post.txt").write_text(ids, encoding="utf-8")
    print(f"[wrote] {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
