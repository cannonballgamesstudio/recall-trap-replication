#!/usr/bin/env python3
"""Frozen G-plane system prompts + retrieval-pack fetcher/formatter.

Pre-registered 2026-07-13 in
docs/plans/2026-07-13-g-plane-design.md (BINDING). PACK_SYSTEM (G1)
and TRUST_SYSTEM (G2) are frozen at this commit: per the design doc's protocol,
changing either after seeing results makes it a new, disclosed arm, not a
revision of this one.

    python g_plane_prompts.py --selftest
        fetches a pack for a known-indexed instance (default:
        astropy__astropy-12907 against http://127.0.0.1:8083) and prints the
        hit count + the first 300 chars of the formatted pack.
"""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_ENDPOINT = "http://127.0.0.1:8083"
DEFAULT_INSTANCES = Path(r"work/p5/instances_verified.json")

# ---------------------------------------------------------------- G1: Context Pack
PACK_SYSTEM = """You are an autonomous coding agent operating inside a git repository, resolving a real GitHub issue.

Before you were started, a retrieval system that has been measured to outperform grep on this exact codebase already searched the repository and selected the code locations most relevant to this issue. That output is given to you below, in the user message, as a `## Retrieved context` block: each entry names a file, a line number, a symbol and its kind, followed by a code snippet.

Trust this context. The fix is almost certainly located within the files listed there. Do NOT re-explore or re-search the codebase looking for other candidate locations — you have no search tools, and re-deriving what the retriever already found would only waste turns. Your job is:

1. Read only the file(s) you must, to see whatever surrounding context the snippets don't already show you.
2. Edit the source code to fix the issue, making the minimal necessary change.

Rules (follow exactly):
- Do NOT add or modify tests.
- Do NOT run the test suite, or any other command — you have no shell access.
- Do NOT commit. Leave your edits in the working tree.
- Make the smallest change that resolves the issue; do not refactor unrelated code.

Available tools: Read, Edit, Write. You have no Bash, Grep, or Glob — do not attempt to invoke them."""

# ---------------------------------------------------------------- G2: Pure Trust
# NOTE (factual correction only, 2026-07-13, per the AMENDED §G2 in the design doc):
# the original wording below said the agent has "no way to open any other file" /
# "no Read" -- true under the pre-amendment Edit/Write-only instrument, but no longer
# true of the amended one, which restores Read so Edit/Write's prior-Read requirement
# can be satisfied. The amendment does not change the arm's INTENT (the retriever's
# pack is still the agent's entire accessible world) -- it is enforced structurally
# now, by a PreToolUse hook that denies any Read outside the pack's file list, rather
# than by omitting the Read tool. This edit only makes the prompt describe what the
# harness actually does; per the design doc's freeze rule this is disclosed here, not
# silently changed.
TRUST_SYSTEM = """You are an autonomous coding agent operating inside a git repository, resolving a real GitHub issue.

Before you were started, a retrieval system that has been measured to outperform grep on this exact codebase already searched the repository and selected the code locations most relevant to this issue. That output is given to you below, in the user message, as a `## Retrieved context` block: each entry names a file, a line number, a symbol and its kind, followed by a code snippet.

Trust this context completely. The fix is almost certainly contained within these files. You may Read a file named in the pack above to see surrounding context the snippet doesn't show — but the pack is the retriever's complete answer for this issue, and it is the entirety of your accessible world: attempting to Read anything outside the files listed in the pack will be denied, so do not try to explore, search, or open any other file.

Rules (follow exactly):
- Do NOT add or modify tests.
- Do NOT run the test suite, or any other command — you have no shell access.
- Do NOT commit. Leave your edits in the working tree.
- Make the smallest change that resolves the issue, using only the pack's files; do not invent code you have not seen.

Available tools: Read, Edit, Write. You have no Bash, Grep, or Glob — do not attempt to invoke them. Read is restricted to the files named in the pack."""


# ------------------------------------------- E0: the missing cell (oracle + TOOLS)
# Pre-registered 2026-07-14 (docs/.../2026-07-14-oracle-plus-tools.md). The oracle
# arm changed TWO things at once -- perfect context AND removal of search tools --
# so it cannot support any causal claim about tools. ORACLE-SWE (2604.07789)
# explicitly pre-rejected that design as confounded, and they are right.
#
# This prompt is PACK_SYSTEM with the tool-restriction sentences replaced by their
# permissive counterparts and NOTHING else changed (diff is 3 sentences; disclosed
# here rather than silently altered, per the G-plane freeze rule). It isolates the
# TOOLS variable at fixed (perfect) context.
PACK_TOOLS_SYSTEM = """You are an autonomous coding agent operating inside a git repository, resolving a real GitHub issue.

Before you were started, a retrieval system that has been measured to outperform grep on this exact codebase already searched the repository and selected the code locations most relevant to this issue. That output is given to you below, in the user message, as a `## Retrieved context` block: each entry names a file, a line number, a symbol and its kind, followed by a code snippet.

Trust this context. The fix is almost certainly located within the files listed there. You DO have search tools (Bash, Grep, Glob) available and you may use them if you judge it necessary, but re-deriving what the retriever already found is unlikely to be a good use of your turns. Your job is:

1. Read only the file(s) you must, to see whatever surrounding context the snippets don't already show you.
2. Edit the source code to fix the issue, making the minimal necessary change.

Rules (follow exactly):
- Do NOT add or modify tests.
- Do NOT run the test suite.
- Do NOT commit. Leave your edits in the working tree.
- Make the smallest change that resolves the issue; do not refactor unrelated code."""


# ------------------------------- C1: the delivery-mode control (prompt held fixed)
# The E1 result (fusion pack pre-injected + tools = 83.7% vs explorer 75.0%) is
# CONFOUNDED: the pack arms REPLACE the system prompt while the explorer runs the
# default one. So "delivery mode" is entangled with "prompt". This arm isolates it.
#
# TOOL_PRIMED_SYSTEM is PACK_TOOLS_SYSTEM with the SAME framing, the SAME trust
# language, and the SAME task rules -- but the retrieval is PULLED (the agent calls
# the `rag` CLI itself) instead of PUSHED (pre-injected into the prompt). Same
# retriever behind both. Same tools. Same turn cap. The ONLY variable is push vs pull.
#
# If C1 lands at E1 (~84%), the prompt was doing the work and the delivery-mode
# claim is DEAD. If C1 lands at the explorer (~75%), delivery mode is the cause.
TOOL_PRIMED_SYSTEM = """You are an autonomous coding agent operating inside a git repository, resolving a real GitHub issue.

A retrieval system that has been measured to outperform grep on this exact codebase is available to you as the `rag` CLI. Run `rag query "<what you are looking for>"` and it will return the code locations most relevant to the issue: each entry names a file, a line number, a symbol and its kind, followed by a code snippet.

Query it FIRST, before anything else, and trust what it returns. The fix is almost certainly located within the files it names. Do not re-derive by hand what the retriever can find for you. Your job is:

1. Query `rag` to find the relevant code.
2. Read only the file(s) you must, to see whatever surrounding context the snippets don't already show you.
3. Edit the source code to fix the issue, making the minimal necessary change.

Rules (follow exactly):
- Do NOT add or modify tests.
- Do NOT run the test suite.
- Do NOT commit. Leave your edits in the working tree.
- Make the smallest change that resolves the issue; do not refactor unrelated code."""


def format_pack(hits: list[dict], limit: int) -> str:
    """Render `hits` as the `## Retrieved context` block injected into the prompt.

    Deterministic: hits are kept in the order retrievald returned them (its own
    relevance ranking) and simply sliced to `limit` -- never re-sorted, and no
    snippet is truncated beyond whatever retrievald itself already applied.
    """
    kept = hits[:limit]
    lines = [f"## Retrieved context (top-{len(kept)}, from the repository's retrieval index)"]
    for h in kept:
        file_ = h.get("file", "?")
        line = h.get("line", "?")
        symbol = h.get("symbol", "?")
        kind = h.get("kind", "?")
        snippet = (h.get("snippet") or "").rstrip("\n")
        lines.append("")
        lines.append(f"### {file_}:{line} — {symbol} [{kind}]")
        lines.append("```")
        lines.append(snippet)
        lines.append("```")
    return "\n".join(lines)


def fetch_pack(endpoint: str, repo: str, ref: str, query: str, limit: int,
               mode: str = "hybrid", extra: dict | None = None) -> list[dict]:
    """POST retrievald's /v1/query and return its hit list.

    Wire shape per src/ragfusion/retrievald/wire.py QueryRequest: {repo, branch, text,
    mode, limit, code_only}; response is {served_ref, hits, staleness,
    capabilities, truncated} (src/ragfusion/retrievald/app.py). code_only=True demotes
    doc/markdown hits below code, appropriate for a fix-the-bug pack.

    Raises on ANY failure (bad HTTP status, connection error, malformed
    response) instead of degrading to an empty pack. A G-plane arm that
    silently ran with zero retrieved context would look like a *policy*
    failure (retrieval didn't help) when it was actually a *plumbing* failure
    -- the pre-registered protocol has no way to tell those apart after the
    fact, so this must fail loudly instead.
    """
    body_dict = {
        "repo": repo,
        "branch": ref,
        "text": query,
        "mode": mode,
        "limit": limit,
        "code_only": True,
    }
    if extra:
        # additive wire fields, e.g. {"max_chunks_per_file": 2} for cap arms
        # (Track B §2); wire.QueryRequest ignores unknown keys (extra="ignore").
        body_dict.update(extra)
    body = json.dumps(body_dict).encode("utf-8")
    req = urllib.request.Request(
        f"{endpoint.rstrip('/')}/v1/query", data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(
            f"retrievald /v1/query {e.code} for repo={repo!r} ref={ref!r}: {detail}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"retrievald /v1/query unreachable at {endpoint!r} for repo={repo!r} ref={ref!r}: {e}") from e
    hits = payload.get("hits")
    if hits is None:
        raise RuntimeError(
            f"retrievald /v1/query response missing 'hits' for repo={repo!r} ref={ref!r}: {payload}")
    return hits


def _selftest(args: argparse.Namespace) -> int:
    query = None
    try:
        insts = json.loads(DEFAULT_INSTANCES.read_text(encoding="utf-8"))
        for x in insts:
            if x["instance_id"] == args.ref:
                query = x["problem_statement"]
                break
    except Exception:
        pass
    if query is None:
        query = "Fix the bug described in the linked GitHub issue for this repository."
    hits = fetch_pack(args.endpoint, args.repo, args.ref, query[:6000], args.limit)
    pack = format_pack(hits, args.limit)
    print(f"repo={args.repo} ref={args.ref} endpoint={args.endpoint} limit={args.limit}")
    print(f"hits: {len(hits)}")
    print("--- pack head (300 chars) ---")
    print(pack[:300])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true",
                    help="fetch+format a real pack against a live retrievald endpoint")
    ap.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    ap.add_argument("--repo", default="astropy/astropy")
    ap.add_argument("--ref", default="astropy__astropy-12907")
    ap.add_argument("--limit", type=int, default=12)
    args = ap.parse_args()
    if args.selftest:
        return _selftest(args)
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
