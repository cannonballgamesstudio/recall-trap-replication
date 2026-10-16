#!/usr/bin/env python3
"""Shared, side-effect-free helpers for the contamination pre-registration.

Pre-registered in docs/paper/CONTAMINATION-PREREG.md. Importing this module makes
NO network calls, starts no processes, and writes no files. Everything here is a
pure function over files that already exist on disk.

Contents:
  - paths and the arm -> graded-report map (outcomes are read ONLY by the join step)
  - gold-patch parsing, pack chunk parsing, A/B/C anchor classes (strat_abc.py rule)
  - the P1 filter rule (gold-file basename appears in the issue text)
  - the exact probe prompts P1/P2/P3 and the response parsers / scorers
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

VER = Path("work/p5")          # Verified substrate (read-only)
CONTAM = Path("data/memorization-branchB")   # new: probe inputs, raw logs, M tables
IDX_CLONES = Path("<EVAL_ROOT>/swebench")               # full (non-partial) <slug>__idx clones
POLY = Path("<EVAL_ROOT>/polybench")
POLY_PARQUET_GLOB = ("<HF_HOME>/hub/datasets--AmazonScience--SWE-PolyBench_500/snapshots/*/"
                     "test.csv")
PREREG = "docs/paper/CONTAMINATION-PREREG.md"
ISSUE_CHARS = 6000          # same truncation as the headline harness (local_dedup_ab.py)
SEED = 20261014

# ---------------------------------------------------------------- graded arms (join step only)
# (ON report, OFF report) under VER; "submitted_ids" / "resolved_ids" keys.
ARMS = {
    "gpt": {
        "hl": ("local_gpt56sol_dedupON.local_gpt56sol_dedupON.json",
               "local_gpt56sol_dedupOFF.local_gpt56sol_dedupOFF.json"),
        "lr": ("local_gptsol_logrep_dedupON.gptsol_logrep_dedupON.json",
               "local_gptsol_logrep_dedupOFF.gptsol_logrep_dedupOFF.json"),
    },
    "qwen36": {
        "k4": ("local_qwen36_k4_dedupON.qs2_k4_ON.json", "local_qwen36_k4_dedupOFF.qs2_k4_OFF.json"),
        "k12": ("local_qwen36_k12_dedupON.qwen36_k12_dedupON.json",
                "local_qwen36_k12_dedupOFF.qwen36_k12_dedupOFF.json"),
        "k40": ("local_qwen36_k40_dedupON.qs2_k40_ON.json", "local_qwen36_k40_dedupOFF.qs2_k40_OFF.json"),
    },
    "qwen3coder": {
        "k4": ("local_qwen3or_k4_dedupON.qwen3or_k4_dedupON.json",
               "local_qwen3or_k4_dedupOFF.qwen3or_k4_dedupOFF.json"),
        "k12": ("local_qwen3or_k12_dedupON.qwen3or_k12_dedupON.json",
                "local_qwen3or_k12_dedupOFF.qwen3or_k12_dedupOFF.json"),
        "k40": ("local_qwen3or_k40_dedupON.qwen3or_k40_dedupON.json",
                "local_qwen3or_k40_dedupOFF.qwen3or_k40_dedupOFF.json"),
    },
}
# Arm T (trimmed breadth, local Qwen3-Coder-30B) and its reference pair.
T_ARM = {
    "ref_on": "local_qwen3coder30b_dedupON.qwen30b_ON_rg.json",
    "ref_off": "local_qwen3coder30b_dedupOFF.qwen30b_OFF_rg.json",
    "T": "local_qwen3coder30b_T.trimT_qwen30b_T.json",
    "Tprime": "local_qwen3coder30b_Tprime.trimT_qwen30b_Tprime.json",
}


def load_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def polybench_python() -> dict[str, dict]:
    """The 125 SWE-PolyBench_500 Python instances: {iid: {repo, base_commit,
    problem_statement, patch}} from the HF test.csv (gold) + the local manifest."""
    import glob as _glob
    import pandas as pd
    df = pd.concat([pd.read_csv(f) for f in sorted(_glob.glob(POLY_PARQUET_GLOB))])
    df = df[df["language"] == "Python"].drop_duplicates("instance_id")
    return {r["instance_id"]: {"repo": r["repo"], "base_commit": r["base_commit"],
                               "problem_statement": r["problem_statement"], "patch": r["patch"]}
            for _, r in df.iterrows()}


def sha256_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def report(name: str) -> tuple[set, set]:
    d = load_json(VER / name)
    return set(d["resolved_ids"]), set(d["submitted_ids"])


# ---------------------------------------------------------------- gold + packs
DIFF_RE = re.compile(r"^diff --git a/(.+?) b/", re.M)


def norm(p: str) -> str:
    return p.replace("\\", "/").lstrip("./")


def gold_files(patch: str) -> list[str]:
    return [norm(p) for p in dict.fromkeys(DIFF_RE.findall(patch or ""))]


def gold_lines(patch: str) -> dict[str, set[int]]:
    from oracle_pack import parse_gold_hunks
    gl: dict[str, set[int]] = {}
    for path, start, length in parse_gold_hunks(patch):
        gl.setdefault(norm(path), set()).update(range(start, start + length))
    return gl


def chunks_of(pack: str) -> list[tuple[str, int, int]]:
    """(path, start_line, n_lines) per served chunk; identical to strat_abc.py."""
    out = []
    for part in re.split(r"^### ", pack, flags=re.M)[1:]:
        m = re.match(r"(?P<path>[^:\n]+):(?P<line>\d+)", part)
        if not m:
            continue
        code = re.search(r"```\n(.*?)```", part, re.S)
        span = code.group(1).count("\n") if code else 1
        out.append((norm(m.group("path")), int(m.group("line")), span))
    return out


def anchor_class(patch: str, pack: str) -> str:
    """A = no gold file in pack; B = gold file(s) present but some gold file's
    pre-image lines are not covered; C = every gold file has a chunk overlapping its
    gold lines. '?' = no pre-image (new-file-only patch). Rule of strat_abc.py,
    which agrees 92/92 with the on-disk failure_taxonomy.json."""
    gl = gold_lines(patch)
    if not gl:
        return "?"
    ch = chunks_of(pack)
    pf = {c[0] for c in ch}
    if not [g for g in gl if g in pf]:
        return "A"
    cov = sum(1 for g in gl if any(f == g and set(range(s, s + sp)) & gl[g] for f, s, sp in ch))
    return "C" if cov == len(gl) else "B"


def plus_lines(patch: str) -> list[str]:
    return [l[1:].strip() for l in (patch or "").splitlines()
            if l.startswith("+") and not l.startswith("+++") and l[1:].strip()]


# ---------------------------------------------------------------- P1 filter rule
def p1_filtered(problem_statement: str, patch: str) -> bool:
    """P1 is NA when ANY gold-file basename (last path component of a
    `diff --git a/<path>` header of the gold patch) occurs as a case-sensitive
    plain substring of the FULL problem_statement. Reproduces the 133-instance
    side table (issue_names_gold.json 'base') exactly."""
    return any(g.split("/")[-1] in problem_statement for g in gold_files(patch))


# ---------------------------------------------------------------- probe prompts (EXACT)
PROBE_SYSTEM = ("You are an expert software engineer who knows the source code of popular "
                "open-source Python repositories.")

P1_USER = """Repository: {repo}

## Issue
{issue}

Without seeing any code, list the files in this repository that would most likely need to be edited to resolve the issue. Output at most 3 repository-relative file paths, one per line, most likely first. Output only the paths, with no other text."""

P2_ADDED = "You are given no code; write the fix from your knowledge of this repository"

P2_USER = """Repository: {repo}

""" + P2_ADDED + """.

## Issue
{issue}

Emit the SEARCH/REPLACE edits."""

P3_USER = """Repository: {repo}
File: {path}

Below are {n} consecutive lines from this file. Output the next 8 lines of the file exactly as they appear in the file. Output only those 8 lines, with no explanation and no code fences.

{prefix}"""


def p2_system() -> str:
    """Headline SYS byte-for-byte (local_dedup_ab.SYS); the pack is removed from the
    user turn and P2_ADDED is added there instead."""
    from local_dedup_ab import SYS
    return SYS


def p1_messages(repo: str, issue: str) -> list[dict]:
    return [{"role": "system", "content": PROBE_SYSTEM},
            {"role": "user", "content": P1_USER.format(repo=repo, issue=issue[:ISSUE_CHARS])}]


def p2_messages(repo: str, issue: str) -> list[dict]:
    return [{"role": "system", "content": p2_system()},
            {"role": "user", "content": P2_USER.format(repo=repo, issue=issue[:ISSUE_CHARS])}]


def p3_messages(repo: str, path: str, prefix_lines: list[str]) -> list[dict]:
    return [{"role": "system", "content": PROBE_SYSTEM},
            {"role": "user", "content": P3_USER.format(repo=repo, path=path, n=len(prefix_lines),
                                                       prefix="\n".join(prefix_lines))}]


# ---------------------------------------------------------------- P3 input construction
def first_change_line(patch: str) -> tuple[str, int] | None:
    """(path, L): L = pre-image line number of the first changed line ('-' line, or the
    insertion point of a '+' line) in the first hunk of the first gold file that has a
    pre-image (patch order). None if the patch has no pre-image file."""
    path, old_ln, in_hunk = None, 0, False
    for line in (patch or "").splitlines():
        if line.startswith("--- "):
            raw = line[4:].strip()
            path = None if raw == "/dev/null" else norm(raw[2:] if raw.startswith("a/") else raw)
            in_hunk = False
            continue
        if line.startswith("+++ ") or line.startswith("diff --git"):
            continue
        m = re.match(r"^@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@", line)
        if m:
            in_hunk = path is not None
            old_ln = int(m.group(1))
            continue
        if not in_hunk:
            continue
        if line.startswith(" "):
            old_ln += 1
        elif line.startswith("-") or line.startswith("+"):
            return path, old_ln
        elif line.startswith("\\"):
            continue
    return None


def p3_split(file_text: str, L: int) -> tuple[list[str], list[str]]:
    lines = file_text.splitlines()
    prefix = lines[max(0, L - 1 - 8): L - 1]
    target = lines[L - 1: L - 1 + 8]
    return prefix, target


# ---------------------------------------------------------------- parsers / scorers
_PATH_TOKEN = re.compile(r"[\w.\-/\\]+\.\w+")


def parse_p1(content: str, repo: str) -> list[str]:
    """Up to 3 normalized paths, in order of appearance. Backticks and quotes are
    removed; the first path-like token on each line is taken (so bullets / numbering
    are ignored); lines without a path token are skipped; duplicates dropped."""
    out: list[str] = []
    for line in (content or "").splitlines():
        m = _PATH_TOKEN.search(line.replace("`", " ").replace("'", " ").replace('"', " "))
        if not m:
            continue
        p = norm(m.group(0).strip())
        if p not in out:
            out.append(p)
        if len(out) == 3:
            break
    return out


def score_p1(paths: list[str], gold: list[str]) -> dict:
    """Hit iff a predicted path equals a gold path, or ends with '/' + gold path (tolerates
    a leading repo-name or checkout-dir prefix). Basename hit reported separately."""
    g = {norm(x) for x in gold}
    gb = {x.split("/")[-1] for x in g}
    return {"p1_hit": int(any(p == x or p.endswith("/" + x) for p in paths for x in g)),
            "p1_base_hit": int(any(p.split("/")[-1] in gb for p in paths))}


_TOK = re.compile(r"\w+|[^\w\s]")


def _strip_fences(text: str) -> list[str]:
    lines = (text or "").splitlines()
    while lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if "```" in "\n".join(lines):
        cut = next(i for i, l in enumerate(lines) if l.strip().startswith("```"))
        lines = lines[:cut]
    return lines


def ngram_overlap(gen_lines: list[str], target_lines: list[str], n: int = 5) -> float | None:
    """Clipped n-gram recall of the target: |ngrams(gen) ∩ ngrams(target)| (multiset,
    clipped) / |ngrams(target)|, over \\w+|[^\\w\\s] tokens. None if the target has
    fewer than n tokens."""
    from collections import Counter
    t = _TOK.findall("\n".join(target_lines))
    g = _TOK.findall("\n".join(gen_lines))
    if len(t) < n:
        return None
    tg = Counter(tuple(t[i:i + n]) for i in range(len(t) - n + 1))
    gg = Counter(tuple(g[i:i + n]) for i in range(len(g) - n + 1))
    return sum(min(c, gg[k]) for k, c in tg.items()) / sum(tg.values())


def score_p3(content: str, target_lines: list[str]) -> dict:
    gen = _strip_fences(content)[: len(target_lines)]
    v = ngram_overlap(gen, target_lines)
    return {"p3_overlap": v, "p3_pos": None if v is None else int(v >= 0.5)}


def memorization_score(p1: int | None, p2_apply: int | None, p3: int | None) -> dict:
    """M = sum of available binary probes. NA probes contribute nothing. Low-M iff every
    available probe is negative (M == 0). n_avail records how many probes M is over."""
    vals = [v for v in (p1, p2_apply, p3) if v is not None]
    m = sum(vals) if vals else None
    return {"M": m, "n_avail": len(vals), "lowM": None if m is None else int(m == 0)}
