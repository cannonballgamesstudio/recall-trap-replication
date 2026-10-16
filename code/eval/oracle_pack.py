#!/usr/bin/env python3
"""Build the ORACLE pack: the gold patch's own files and line ranges.

Pre-registered 2026-07-14 in docs/plans/2026-07-14-oracle-ceiling.md.

This is the strict UPPER BOUND of any retrieval system: perfect localization,
handed to the solver under exactly the G1 policy (PACK_SYSTEM, Read/Edit/Write,
no search tools, 10 turns). A planner, a sidecar, a bigger index -- none can
exceed it. So this one arm bounds the whole "build something better on top of
the retriever" hypothesis class.

Hits are emitted in the SAME dict shape retrievald returns (file/line/symbol/kind/
snippet) and rendered by g_plane_prompts.format_pack VERBATIM, so the pack the
solver sees is byte-identical in structure to G1's. The only variable is which
chunks are in it.

CONTAMINATION IS THE POINT, and is disclosed: this arm reads the gold patch. It
is a ceiling measurement, never a leaderboard submission.

    python oracle_pack.py --selftest --checkout <repo-at-base-commit> --instance <iid>
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# Same budget as G1's PACK_LIMIT -- the comparison is "same pack size, perfect
# selection", not "perfect selection AND a bigger pack". Raising it here would
# confound content quality with context volume.
ORACLE_LIMIT = 12

_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@")
_FILE = re.compile(r"^--- (?:a/)?(.+?)\s*$")
_NEWF = re.compile(r"^\+\+\+ (?:b/)?(.+?)\s*$")

# Nearest enclosing definition, scanning backwards. Covers the Python-heavy
# Verified split plus the common C-family/JS shapes; falls back to the file
# itself, which is still a perfectly good "here is the location" signal.
_DEF = re.compile(
    r"^\s*(?:(?:async\s+)?def|class|function|fn|func|impl|struct|interface)\s+([A-Za-z_][\w]*)")

CONTEXT_BEFORE = 6
CONTEXT_AFTER = 6
MAX_SNIPPET_LINES = 60


def parse_gold_hunks(patch: str) -> list[tuple[str, int, int]]:
    """(path, old_start, old_len) per hunk, against the PRE-patch file.

    The repo is checked out at base_commit, so the gold patch's `-` side is what
    exists on disk. New files (--- /dev/null) have no pre-image and are skipped:
    a retriever could not have surfaced a file that does not yet exist, so
    including them would hand the oracle something even an oracle can't have.
    """
    out: list[tuple[str, int, int]] = []
    path: str | None = None
    for line in patch.splitlines():
        m = _FILE.match(line)
        if m:
            raw = m.group(1)
            path = None if raw == "/dev/null" else raw.replace("\\", "/")
            continue
        if _NEWF.match(line):
            continue
        m = _HUNK.match(line)
        if m and path:
            start = int(m.group(1))
            length = int(m.group(2)) if m.group(2) else 1
            out.append((path, start, max(1, length)))
    return out


def _merge(regions: list[tuple[int, int]], gap: int = 12) -> list[tuple[int, int]]:
    """Merge hunk regions that are close enough that separate snippets would just
    duplicate each other's context."""
    if not regions:
        return []
    regions = sorted(regions)
    merged = [list(regions[0])]
    for lo, hi in regions[1:]:
        if lo <= merged[-1][1] + gap:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    return [(a, b) for a, b in merged]


def build_oracle_hits(gold_patch: str, checkout: str,
                      limit: int = ORACLE_LIMIT) -> tuple[list[dict], dict]:
    """-> (hits in retrievald's dict shape, meta).

    meta.oracle_hunks     = hunk regions the gold patch actually touches
    meta.oracle_truncated = regions dropped by `limit` (0 in the overwhelming
                            majority; logged because a truncated oracle is no
                            longer an oracle and the analysis must know)
    meta.oracle_missing   = gold files not present in the checkout (should be 0)
    """
    root = Path(checkout)
    by_file: dict[str, list[tuple[int, int]]] = {}
    for path, start, length in parse_gold_hunks(gold_patch):
        by_file.setdefault(path, []).append((start, start + length - 1))

    hits: list[dict] = []
    missing = 0
    total_regions = 0
    for path in sorted(by_file):
        fp = root / path
        try:
            lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            missing += 1
            continue
        for lo, hi in _merge(by_file[path]):
            total_regions += 1
            s = max(1, lo - CONTEXT_BEFORE)
            e = min(len(lines), hi + CONTEXT_AFTER)
            if e - s + 1 > MAX_SNIPPET_LINES:
                e = s + MAX_SNIPPET_LINES - 1
            symbol, kind = "?", "region"
            for i in range(min(lo, len(lines)) - 1, -1, -1):
                m = _DEF.match(lines[i])
                if m:
                    symbol = m.group(1)
                    kw = lines[i].strip().split()[0]
                    kind = "class" if kw == "class" else "function"
                    break
            if symbol == "?":
                symbol = fp.stem
                kind = "file"
            hits.append({
                "file": path,
                "line": lo,
                "symbol": symbol,
                "kind": kind,
                "snippet": "\n".join(lines[s - 1:e]),
            })
    kept = hits[:limit]
    return kept, {
        "oracle_hunks": total_regions,
        "oracle_truncated": max(0, len(hits) - len(kept)),
        "oracle_missing": missing,
        "oracle_files": len({h["file"] for h in kept}),
    }


def _selftest(args: argparse.Namespace) -> int:
    from g_plane_prompts import DEFAULT_INSTANCES, format_pack
    insts = json.loads(Path(args.instances or DEFAULT_INSTANCES).read_text(encoding="utf-8"))
    cell = next((c for c in insts if c["instance_id"] == args.instance), None)
    if cell is None:
        print(f"instance {args.instance} not in manifest")
        return 1
    gold = cell.get("patch") or ""
    if not gold:
        print(f"instance {args.instance} has no gold 'patch' field -- ORACLE ARM CANNOT RUN")
        return 1
    hits, meta = build_oracle_hits(gold, args.checkout)
    print(f"instance={args.instance}")
    print(f"gold files: {sorted({h['file'] for h in hits})}")
    print(f"meta: {meta}")
    print(f"hits: {len(hits)}")
    pack = format_pack(hits, ORACLE_LIMIT)
    print(f"pack chars: {len(pack)}")
    print("--- pack head (600 chars) ---")
    print(pack[:600])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--instance", default="astropy__astropy-12907")
    ap.add_argument("--checkout", required=False, help="repo checked out at base_commit")
    ap.add_argument("--instances", default=None)
    args = ap.parse_args()
    if args.selftest:
        if not args.checkout:
            ap.error("--selftest needs --checkout")
        return _selftest(args)
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
