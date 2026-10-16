#!/usr/bin/env python3
"""PreToolUse hook for the G2 ("pure trust") G-plane arm.

Mirrors the stdin/stdout contract of `rag hook pretooluse`
(clients/rag/src/hook.rs::run_hook): read the ENTIRE hook-event JSON from
stdin, decide allow/deny, and on deny print a single JSON line shaped like

    {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                             "permissionDecision": "deny",
                             "permissionDecisionReason": "..."}}

to stdout; on allow, print nothing. Always exit 0 (a nonzero exit or malformed
stdout would abort the agent turn, which is never what we want here -- the
"deny" JSON itself is what blocks the tool call, not the process exit code).

Per docs/plans/2026-07-13-g-plane-design.md's amended G2: the
agent gets Read+Edit+Write, but this hook denies any Read whose target path
is not one of the files the retriever put in the pack. The pack's file list
is threaded in via the GPLANE_PACK_FILES env var (';'-separated,
repo-relative paths), written by swe_bench.py at pack-fetch time.

Fail-safe (never hard-block a run into a false null): if GPLANE_PACK_FILES is
missing/empty, or the stdin JSON doesn't parse, or the event isn't a Read --
ALLOW.
"""
from __future__ import annotations

import json
import os
import sys

DENY_REASON = (
    "outside the retrieved context pack -- the retriever's file set is your "
    "world; work from the pack"
)


def _norm(p: str) -> str:
    return p.replace("\\", "/").lower()


def _in_pack(read_path: str, allowed: list[str]) -> bool:
    """True if `read_path` matches one of `allowed` by path-boundary suffix.

    `read_path` is typically an absolute checkout path
    (<EVAL_ROOT>/.../co_trust_.../astropy/modeling/separable.py) and `allowed`
    entries are repo-relative (astropy/modeling/separable.py); comparing by
    suffix (with a '/' boundary, so `xastropy/...` cannot falsely match
    `astropy/...`) lets the two agree without either side needing to know the
    other's root.
    """
    rp = _norm(read_path)
    for a in allowed:
        an = _norm(a).lstrip("/")
        if not an:
            continue
        if rp == an or rp.endswith("/" + an):
            return True
    return False


def decide(tool_name: str, tool_input: dict, allowed: list[str]) -> str | None:
    """Return a deny reason, or None to allow."""
    if tool_name != "Read":
        return None
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not file_path:
        return None  # nothing to check -- fail open rather than guess
    if _in_pack(file_path, allowed):
        return None
    return DENY_REASON


def main() -> int:
    raw_files = os.environ.get("GPLANE_PACK_FILES") or ""
    allowed = [f for f in raw_files.split(";") if f.strip()]
    stdin_data = sys.stdin.read()

    if not allowed:
        return 0  # fail-safe: no pack list -> allow everything, never block

    try:
        event = json.loads(stdin_data)
        tool_name = event.get("tool_name", "")
        tool_input = event.get("tool_input") or {}
    except (json.JSONDecodeError, TypeError, AttributeError):
        return 0  # fail-safe: malformed event -> allow

    reason = decide(tool_name, tool_input, allowed)
    if reason:
        payload = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
        print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
