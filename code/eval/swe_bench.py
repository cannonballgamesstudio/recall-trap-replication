#!/usr/bin/env python3
"""SWE-bench Verified A/B localization harness: rag-only vs grep-only.

The fair fight. Two arms, grep and rag never coexist:
  - grep arm: Bash/Grep/Read, no rag on PATH.
  - rag  arm: rag CLI + Read, Grep tool disabled, broad bash-grep hard-blocked
              by the `rag hook pretooluse` hook -> the agent MUST discover code
              via rag. (A targeted single-file grep is still allowed; blocking it
              would only force costlier full-file Reads and unfairly inflate the
              arm's tokens.)

Task per instance = LOCALIZATION: name the file(s)+symbol(s) that must change to
resolve the issue. Scored objectively against the gold patch's changed files
(straight from the dataset, never hand-traced). No Docker (that's Stage 2).

Subcommands:
  prep  : pull SWE-bench Verified, build a stratified ~N-instance subset, parse
          gold files from each instance's patch -> subset.json.
  index : per repo, cache-clone + checkout a representative base + srclight
          index + register under (owner/repo, eval). ~12 one-time indexes.
  run   : the A/B matrix (instance x arm x seed); score recall vs gold files;
          print the localization map.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from statistics import median

RAG_BIN = r"<repo>\clients\rag\target\release\rag.exe"
ENDPOINT = "http://127.0.0.1:8081"
REGISTRY = r"<EVAL_ROOT>\registry.db"
EMBED_MODEL = "openai:Qwen/Qwen3-Embedding-8B"
EMBED_BASE = "http://127.0.0.1:8080"
WORK = Path(r"<EVAL_ROOT>\swebench")            # caches + checkouts (off the full C:)
BENCH = Path(r"<EVAL_ROOT>\swebench-verified")   # subset.json + results + run checkouts (C: is full)
PREDICT_MODEL = os.environ.get("SWE_CLAUDE_MODEL", "claude-opus-4-8")  # Claude model for the resolve arms

POLICY = (
    "Grep and recursive search are DISABLED in this environment. A code-retrieval "
    "CLI named `rag` is your ONLY way to discover code; use it instead of grep. "
    "Commands: `rag query \"<intent>\"` finds code by meaning (start here); "
    "`rag file <path>` lists a file's symbols+signatures without opening it; "
    "`rag ctx <symbol>` gives callers/callees; `rag deps <symbol> [--file F]` what "
    "depends on it; `rag hierarchy <class>` base/sub/implementors; `rag map [dir]` "
    "structure+hotspots. Treat rag as authoritative; you may Read a specific file "
    "once rag has pointed you to it."
)


def sh(args: list[str], cwd: str | None = None, check: bool = True) -> str:
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(f"cmd failed ({r.returncode}): {' '.join(args)}\n{r.stderr[:500]}")
    return r.stdout


def force_rmtree(path: Path) -> None:
    if not path.exists():
        return
    def onerr(func, p, _exc):
        os.chmod(p, stat.S_IWRITE); func(p)
    try:
        shutil.rmtree(path, onexc=onerr)
    except TypeError:
        shutil.rmtree(path, onerror=lambda f, p, e: onerr(f, p, e))


def patch_files(patch: str) -> list[str]:
    """Repo-relative source files changed by a unified-diff patch (the gold target)."""
    files = []
    for m in re.finditer(r'^\+\+\+ b/(.+)$', patch, re.MULTILINE):
        p = m.group(1).strip()
        if p and p != "/dev/null":
            files.append(p)
    return sorted(set(files))


# ---------------------------------------------------------------- prep
def cmd_prep(args: argparse.Namespace) -> int:
    os.environ.setdefault("HF_HOME", r"<HF_HOME>")  # keep the dataset cache off the full C:
    from datasets import load_dataset
    ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
    by_repo: dict[str, list] = {}
    for x in ds:
        by_repo.setdefault(x["repo"], []).append(x)
    total = len(ds)
    target = args.instances
    cells = []
    for repo in sorted(by_repo):
        insts = sorted(by_repo[repo], key=lambda r: r["instance_id"])
        quota = max(args.min_per_repo, round(target * len(insts) / total))
        quota = min(quota, args.max_per_repo, len(insts))
        # deterministic evenly-spaced pick (reproducible, no RNG)
        if quota >= len(insts):
            pick = insts
        else:
            step = len(insts) / quota
            pick = [insts[int(i * step)] for i in range(quota)]
        for x in pick:
            gold = patch_files(x["patch"])
            if not gold:
                continue
            cells.append({
                "instance_id": x["instance_id"], "repo": repo,
                "base_commit": x["base_commit"],
                "url": f"https://github.com/{repo}.git",
                "problem_statement": x["problem_statement"],
                "gold_files": gold,
            })
    BENCH.mkdir(parents=True, exist_ok=True)
    out = BENCH / "subset.json"
    out.write_text(json.dumps(cells, indent=2), encoding="utf-8")
    from collections import Counter
    c = Counter(x["repo"] for x in cells)
    print(f"wrote {out}: {len(cells)} instances across {len(c)} repos")
    for repo, n in c.most_common():
        print(f"  {repo}: {n}")
    return 0


# ---------------------------------------------------------------- index
def cache_clone(repo: str, url: str) -> Path:
    cache = WORK / (repo.replace("/", "__") + ".cache")
    if not (cache / "HEAD").exists() and not (cache / ".git").exists():
        force_rmtree(cache)
        print(f"  cloning {url} -> {cache.name} (bare cache) ...", flush=True)
        sh(["git", "clone", "--bare", "--quiet", url, str(cache)])
    return cache


def representative_commit(cache: Path, commits: list[str]) -> str:
    """Newest by committer date among the subset's base commits (most files present)."""
    best, best_t = commits[0], -1
    for c in commits:
        try:
            t = int(sh(["git", "-C", str(cache), "show", "-s", "--format=%ct", c]).strip())
        except Exception:
            t = -1
        if t > best_t:
            best, best_t = c, t
    return best


def index_present(repo: str) -> bool:
    """Registered AND the index.db actually exists on disk (registry rows can dangle)."""
    import sqlite3
    if not os.path.exists(REGISTRY):
        return False
    con = sqlite3.connect(f"file:{REGISTRY}?mode=ro", uri=True)
    try:
        row = con.execute("SELECT worktree FROM refs WHERE repo=? AND ref='eval' AND status='ready'",
                          (repo,)).fetchone()
    except sqlite3.OperationalError:
        return False
    finally:
        con.close()
    return bool(row) and os.path.exists(os.path.join(row[0], ".srclight", "index.db"))


def cmd_index(args: argparse.Namespace) -> int:
    cells = json.loads((BENCH / "subset.json").read_text(encoding="utf-8"))
    repos: dict[str, list[str]] = {}
    url_of: dict[str, str] = {}
    for c in cells:
        repos.setdefault(c["repo"], []).append(c["base_commit"])
        url_of[c["repo"]] = c["url"]
    env = dict(os.environ)
    env.update(OPENAI_BASE_URL=EMBED_BASE, OPENAI_API_KEY="sk-noauth",
               SRCLIGHT_EMBED_REQUEST_TIMEOUT="120")
    for repo in sorted(repos):
        if index_present(repo) and not args.force:
            print(f"[skip] {repo} index present under ref=eval", flush=True)
            continue
        cache = cache_clone(repo, url_of[repo])
        commit = representative_commit(cache, sorted(set(repos[repo])))
        co = WORK / (repo.replace("/", "__") + "__idx")
        force_rmtree(co)
        print(f"[index] {repo} @ {commit[:10]} -> {co.name}", flush=True)
        sh(["git", "clone", "--quiet", "--local", str(cache), str(co)])
        sh(["git", "-C", str(co), "remote", "set-url", "origin", url_of[repo]])
        sh(["git", "-C", str(co), "checkout", "--quiet", "-b", "eval", commit])
        r = subprocess.run(
            [sys.executable, "-m", "ragfusion.eval", "--repo", repo, "--ref", "eval",
             "--sha", commit, "--checkout", str(co), "--registry", REGISTRY,
             "--embed-model", EMBED_MODEL],
            cwd=r"<repo>", env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace")
        tail = (r.stdout or "")[-300:] + (r.stderr or "")[-300:]
        print(f"   {'ok' if r.returncode == 0 else 'FAIL'}: {tail.strip()[:300]}", flush=True)
    return 0


# ---------------------------------------------------------------- run
def parse_stream(out: str) -> dict:
    res, counts = {}, {"rag": 0, "grep": 0, "read": 0}
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "assistant":
            for b in ev.get("message", {}).get("content", []):
                if b.get("type") != "tool_use":
                    continue
                name, inp = b.get("name", ""), (b.get("input", {}) or {})
                if name == "Bash":
                    cmd = inp.get("command", "") or ""
                    if cmd.strip().startswith("rag ") or " rag " in cmd:
                        counts["rag"] += 1
                    if any(g in cmd for g in ("grep", "rg ", "ripgrep", "ack")):
                        counts["grep"] += 1
                elif name == "Grep":
                    counts["grep"] += 1
                elif name == "Read":
                    counts["read"] += 1
        elif ev.get("type") == "result":
            res = ev
    return {"result": res, "counts": counts}


def prepare_checkout(cache: Path, base: str, dest: Path, url: str, branch: str = "eval") -> None:
    force_rmtree(dest)
    # `git clone --local` hardlinks objects from the cache. On some volumes that
    # hardlink fails ("Function not implemented" / errno ENOSYS) for large packs
    # (e.g. django's 290MB pack under local_checkouts), aborting the clone with
    # exit 128. Fall back to --no-hardlinks (copies objects) so the checkout still
    # succeeds -- slower and more disk, but correct on any filesystem.
    try:
        sh(["git", "clone", "--quiet", "--local", str(cache), str(dest)])
    except Exception:
        force_rmtree(dest)
        sh(["git", "clone", "--quiet", "--local", "--no-hardlinks", str(cache), str(dest)])
    sh(["git", "-C", str(dest), "remote", "set-url", "origin", url])
    sh(["git", "-C", str(dest), "checkout", "--quiet", "-b", branch, base])


def run_arm(cell: dict, arm: str, seed: int, cwd: str, outdir: Path, budget: float) -> dict:
    instr = ("Identify the file(s) and the function/class/method that must be modified "
             "to resolve the issue below. Answer with exact repo-relative file path(s) "
             "and symbol name(s). Do NOT edit, create, or run anything.")
    full = f"{instr}\n\n{cell['problem_statement']}"
    env = dict(os.environ)
    cmd = ["claude", "-p", full, "--output-format", "stream-json", "--verbose",
           "--dangerously-skip-permissions", "--max-budget-usd", str(budget),
           "--disallowedTools", "Edit", "Write", "MultiEdit", "NotebookEdit"]
    if arm == "rag":
        cmd[cmd.index("Edit"):cmd.index("Edit")] = ["Grep"]  # also disable Grep tool
        rb = RAG_BIN.replace("\\", "/")
        settings = {"hooks": {"PreToolUse": [{"matcher": "Bash|Grep",
                    "hooks": [{"type": "command", "command": f'"{rb}" hook pretooluse'}]}]}}
        sp = outdir / f"{cell['instance_id']}_{arm}_s{seed}.settings.json"
        sp.write_text(json.dumps(settings))
        cmd += ["--append-system-prompt", POLICY, "--settings", str(sp)]
        env["RAG_ENDPOINT"] = ENDPOINT
        env["PATH"] = str(Path(RAG_BIN).parent) + os.pathsep + env["PATH"]
    proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=1800)
    parsed = parse_stream(proc.stdout or "")
    r = parsed["result"]
    u = r.get("usage", {}) or {}
    tot = (u.get("input_tokens", 0) + u.get("output_tokens", 0)
           + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0))
    ans = (r.get("result", "") or "").lower()
    gold = cell["gold_files"]
    hit_full = [g for g in gold if g.lower() in ans]
    hit_base = [g for g in gold if g.split("/")[-1].lower() in ans]
    return {"instance_id": cell["instance_id"], "repo": cell["repo"], "arm": arm,
            "seed": seed, "total_tokens": tot, "num_turns": r.get("num_turns"),
            "cost_usd": r.get("total_cost_usd"), "tool_counts": parsed["counts"],
            "gold_n": len(gold), "hit_full": len(hit_full), "hit_base": len(hit_base),
            "all_full": bool(gold) and len(hit_full) == len(gold),
            "any_base": len(hit_base) > 0}


def run_instance(cell: dict, seeds: int, outdir: Path, budget: float) -> list[dict]:
    cache = WORK / (cell["repo"].replace("/", "__") + ".cache")
    co = outdir / f"co_{cell['instance_id']}"
    out = []
    try:
        prepare_checkout(cache, cell["base_commit"], co, cell["url"])
        for arm in ("grep", "rag"):
            for s in range(1, seeds + 1):
                try:
                    out.append(run_arm(cell, arm, s, str(co), outdir, budget))
                except Exception as e:  # noqa: BLE001
                    print(f"  FAIL {cell['instance_id']} {arm} s{s}: {e}", flush=True)
    finally:
        force_rmtree(co)
    return out


def cmd_run(args: argparse.Namespace) -> int:
    cells = json.loads((BENCH / "subset.json").read_text(encoding="utf-8"))
    if args.limit:
        cells = cells[:args.limit]
    out = BENCH / "run"; out.mkdir(parents=True, exist_ok=True)
    print(f"running {len(cells)} instances x 2 arms x {args.seeds} seeds "
          f"(conc={args.concurrency}) ...", flush=True)
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {ex.submit(run_instance, c, args.seeds, out, args.budget): c["instance_id"]
                for c in cells}
        for f in as_completed(futs):
            iid = futs[f]
            try:
                rs = f.result()
                results.extend(rs)
                for r in rs:
                    print(f"  {iid} {r['arm']} s{r['seed']}: {r['total_tokens']}tok "
                          f"rag{r['tool_counts']['rag']} grep{r['tool_counts']['grep']} "
                          f"loc={r['hit_base']}/{r['gold_n']} all={r['all_full']}", flush=True)
            except Exception as e:  # noqa: BLE001
                print(f"  FAIL instance {iid}: {e}", flush=True)
    (out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    print("\n==== LOCALIZATION MAP (rag-only vs grep-only, SWE-bench Verified) ====")
    print("%-5s %8s %9s %9s %9s %8s %4s" %
          ("arm", "strict%", "loose%", "recall", "med_tok", "rag_use", "n"))
    agg: dict[str, list[dict]] = {}
    for r in results:
        agg.setdefault(r["arm"], []).append(r)
    summ = {}
    for arm in ("grep", "rag"):
        rs = agg.get(arm, [])
        if not rs:
            continue
        strict = sum(x["all_full"] for x in rs) / len(rs)        # all gold paths named
        loose = sum(x["any_base"] for x in rs) / len(rs)          # >=1 gold basename named
        recall = sum(x["hit_base"] / x["gold_n"] for x in rs if x["gold_n"]) / len(rs)
        mt = int(median([x["total_tokens"] for x in rs]))
        ru = sum(1 for x in rs if x["tool_counts"]["rag"] > 0) / len(rs)
        summ[arm] = (strict, loose, recall, mt)
        print("%-5s %7.0f%% %8.0f%% %9.2f %9d %7.0f%% %4d" %
              (arm, strict * 100, loose * 100, recall, mt, ru * 100, len(rs)))
    if "grep" in summ and "rag" in summ:
        sg, sr = summ["grep"], summ["rag"]
        dloc = (sr[0] - sg[0]) * 100
        dtok = sr[3] / sg[3] if sg[3] else float("nan")
        verdict = ("RAG WINS" if (sr[0] > sg[0] + 0.03 and dtok <= 1.05)
                   else "GREP WINS" if sg[0] > sr[0] + 0.03 else "mixed/~tie")
        print(f"\n  rag vs grep: strict-localization {dloc:+.0f}pts, "
              f"tokens B/A={dtok:.2f}  -> {verdict}")
    return 0


# ---------------------------------------------------------------- predict (legit SWE-bench)
# Unlike `run` (localization, Edit disabled), this lets the agent EDIT the checkout to
# actually fix the issue, then captures `git diff` as the model_patch for the official
# swebench.harness.run_evaluation (Docker: apply patch -> run FAIL_TO_PASS/PASS_TO_PASS).
# It also SAVES each agent's full stream-json transcript and records every derivable
# metric (peak context, tokens, cost, turns, per-tool counts, localization recall) so we
# can slice rag vs vanilla on any axis post-hoc.
from streamparse import deduped_messages, metrics as stream_metrics  # noqa: E402
from g_plane_prompts import (fetch_pack, format_pack, PACK_SYSTEM, PACK_TOOLS_SYSTEM,  # noqa: E402
                             TOOL_PRIMED_SYSTEM, TRUST_SYSTEM)
from oracle_pack import build_oracle_hits, ORACLE_LIMIT  # noqa: E402

RAG_INSTR = ("You are resolving a real GitHub issue in this repository. Edit the source "
             "code to fix it, making the minimal necessary change. Use the `rag` CLI to "
             "locate the relevant code. Do NOT add or modify tests, do NOT run the test "
             "suite, and do NOT commit — just leave your edits in the working tree.")
VANILLA_INSTR = ("You are resolving a real GitHub issue in this repository. Edit the source "
                 "code to fix it, making the minimal necessary change. Do NOT add or modify "
                 "tests, do NOT run the test suite, and do NOT commit — just leave your edits "
                 "in the working tree.")

# G-plane pack sizes (see docs/plans/2026-07-13-g-plane-design.md, frozen).
PACK_LIMIT = 12   # G1 context pack
TRUST_LIMIT = 20  # G2 pure trust

# ORACLE arm (pre-registered 2026-07-14, docs/.../2026-07-14-oracle-ceiling.md):
# the pack is built from the GOLD PATCH's own files and line ranges -- perfect
# localization, the strict ceiling of any retrieval system. Same policy as G1
# (PACK_SYSTEM, Read/Edit/Write, 10 turns, no search tools); only the pack's
# CONTENT differs. Contaminated BY DESIGN and disclosed: it is a ceiling
# measurement, never a leaderboard submission.
GOLD_PATCHES = Path(r"work/p5/gold_patches.json")
_gold_cache: dict[str, str] | None = None


def gold_patch_for(iid: str) -> str:
    global _gold_cache
    if _gold_cache is None:
        _gold_cache = json.loads(GOLD_PATCHES.read_text(encoding="utf-8"))
    p = _gold_cache.get(iid)
    if not p:
        # Fail loudly: an oracle arm running with an empty pack would look like
        # a retrieval null when it was a plumbing bug -- the same failure mode
        # fetch_pack() is hardened against.
        raise RuntimeError(f"no gold patch for {iid!r} in {GOLD_PATCHES} -- oracle arm cannot run")
    return p


def run_predict(cell: dict, mode: str, endpoint: str, cwd: str, outdir: Path,
                budget: float, timeout: int = 1800, g_plane: str = "explore",
                ref: str | None = None) -> tuple[str, str, dict]:
    """Run the fix agent; return (git_diff, stream_json_stdout, pack_meta).

    mode='rag' | 'vanilla' selects the retrieval policy for 'explore'/'scarce'.
    g_plane selects the AGENT POLICY (see design doc):
      explore (default) = today's behavior EXACTLY, unchanged — regression-safe.
      scarce  = same as explore, hard-capped at 4 agentic turns.
      pack    = G1 Context Pack: harness pre-fetches retrievald hits for `ref`, injects
                them into the prompt, REPLACES the system prompt, restricts
                tools to Read/Edit/Write (no Bash/Grep/Glob/rag CLI at all),
                caps at 10 turns. `mode` is ignored.
      trust   = G2 Pure Trust (AMENDED, see design doc §G2): same pack (limit=20),
                tools Read/Edit/Write, caps at 8 turns; a PreToolUse hook
                (g_plane_hook.py) denies any Read outside the pack's file list, so
                the retriever's returned files remain the agent's whole accessible
                world. `mode` is ignored.
    pack_meta = {'pack_hits': int, 'pack_chars': int}; zeros unless g_plane is
    'pack' or 'trust'.
    """
    pack_meta = {"pack_hits": 0, "pack_chars": 0}
    env = dict(os.environ)
    if g_plane == "packfile":
        # E3/dose-response: inject a PRE-BUILT pack (max-files=k reconstruction) from a
        # JSON keyed by instance_id in env GPLANE_PACKFILE. Same policy as the `pack`
        # arm (PACK_SYSTEM, Read/Edit/Write, no search tools, 10 turns); only the pack
        # CONTENT differs. Isolates the files-per-pack knob at a fixed 12-slot budget.
        import json as _json
        store = _json.loads(Path(os.environ["GPLANE_PACKFILE"]).read_text(encoding="utf-8"))
        pack = store.get(cell["instance_id"], "")
        if not pack:
            raise RuntimeError(f"no pre-built pack for {cell['instance_id']} in {os.environ['GPLANE_PACKFILE']}")
        pack_meta = {"pack_hits": pack.count("### "), "pack_chars": len(pack)}
        full = f"{pack}\n\n## Issue\n{cell['problem_statement']}"
        cmd = ["claude", "-p", full, "--model", PREDICT_MODEL, "--output-format", "stream-json",
               "--verbose", "--dangerously-skip-permissions", "--max-budget-usd", str(budget),
               "--system-prompt", PACK_SYSTEM, "--tools", "Read,Edit,Write", "--max-turns", "10"]
    elif g_plane == "oracletools":
        # E0, THE MISSING CELL: identical oracle pack, TOOLS LEFT ON. Isolates the
        # tools variable at fixed (perfect) context. Without this cell the oracle
        # arm confounds "perfect context" with "no tools" and can support NO causal
        # claim about exploration -- which is exactly what ORACLE-SWE (2604.07789)
        # said about designs like ours, correctly.
        hits, ometa = build_oracle_hits(gold_patch_for(cell["instance_id"]), cwd, ORACLE_LIMIT)
        if not hits:
            raise RuntimeError(f"oracle pack empty for {cell['instance_id']} meta={ometa}")
        pack = format_pack(hits, ORACLE_LIMIT)
        pack_meta = {"pack_hits": len(hits), "pack_chars": len(pack), **ometa}
        full = f"{pack}\n\n## Issue\n{cell['problem_statement']}"
        # Same turn cap as the explorer (10), full default toolset, no --tools restriction.
        cmd = ["claude", "-p", full, "--model", PREDICT_MODEL, "--output-format", "stream-json",
               "--verbose", "--dangerously-skip-permissions", "--max-budget-usd", str(budget),
               "--system-prompt", PACK_TOOLS_SYSTEM, "--disallowedTools", "NotebookEdit",
               "--max-turns", "10"]
    elif g_plane == "oracle":
        # Perfect localization: the gold patch's own files + line ranges, rendered
        # through the SAME format_pack() and handed to the SAME PACK_SYSTEM policy
        # as G1. A planner cannot beat this, so this arm bounds the entire class.
        hits, ometa = build_oracle_hits(gold_patch_for(cell["instance_id"]), cwd, ORACLE_LIMIT)
        if not hits:
            raise RuntimeError(
                f"oracle pack empty for {cell['instance_id']} (gold files absent from checkout?) "
                f"meta={ometa} -- refusing to run an arm that would look like a retrieval null")
        pack = format_pack(hits, ORACLE_LIMIT)
        pack_meta = {"pack_hits": len(hits), "pack_chars": len(pack), **ometa}
        full = f"{pack}\n\n## Issue\n{cell['problem_statement']}"
        cmd = ["claude", "-p", full, "--model", PREDICT_MODEL, "--output-format", "stream-json",
               "--verbose", "--dangerously-skip-permissions", "--max-budget-usd", str(budget),
               "--system-prompt", PACK_SYSTEM, "--tools", "Read,Edit,Write",
               "--max-turns", "10"]
    elif g_plane == "toolprimed":
        # C1: the delivery-mode control. Same system prompt framing and trust language
        # as E1, same tools, same turn cap, same retriever -- but retrieval is PULLED
        # (the agent calls `rag`) instead of PUSHED (pre-injected). Isolates push-vs-pull
        # from the system-prompt confound that E1 alone cannot rule out.
        full = cell["problem_statement"]
        rb = RAG_BIN.replace("\\", "/")
        settings = {"hooks": {"PreToolUse": [{"matcher": "Bash|Grep",
                    "hooks": [{"type": "command", "command": f'"{rb}" hook pretooluse'}]}]}}
        sp = outdir / f"{cell['instance_id']}_toolprimed.settings.json"
        sp.write_text(json.dumps(settings))
        cmd = ["claude", "-p", full, "--model", PREDICT_MODEL, "--output-format", "stream-json",
               "--verbose", "--dangerously-skip-permissions", "--max-budget-usd", str(budget),
               "--system-prompt", TOOL_PRIMED_SYSTEM, "--disallowedTools", "NotebookEdit",
               "--max-turns", "10", "--settings", str(sp)]
        env["RAG_ENDPOINT"] = endpoint
        env["PATH"] = str(Path(RAG_BIN).parent) + os.pathsep + env["PATH"]
    elif g_plane == "packtools":
        # E1: the cell our own failure taxonomy demanded and we never ran. 82% of the
        # pack arm's failures are "right file, wrong lines" -- exactly what a search
        # tool fixes (open the file, scroll). We measured tools at ORACLE context
        # (nothing left to rescue -> null). This measures them at a REAL pack, where
        # the theory says they should matter. Same fusion pack as `pack`, tools ON.
        hits = fetch_pack(endpoint, cell["repo"], ref or cell["instance_id"],
                          cell["problem_statement"][:6000], PACK_LIMIT, mode="hybrid")
        pack = format_pack(hits, PACK_LIMIT)
        pack_meta = {"pack_hits": len(hits), "pack_chars": len(pack)}
        full = f"{pack}\n\n## Issue\n{cell['problem_statement']}"
        cmd = ["claude", "-p", full, "--model", PREDICT_MODEL, "--output-format", "stream-json",
               "--verbose", "--dangerously-skip-permissions", "--max-budget-usd", str(budget),
               "--system-prompt", PACK_TOOLS_SYSTEM, "--disallowedTools", "NotebookEdit",
               "--max-turns", "10"]
    elif g_plane in ("pack", "trust", "weakpack"):
        limit = TRUST_LIMIT if g_plane == "trust" else PACK_LIMIT
        # weakpack = the CONTROL arm for "is the win just because OUR retriever is good?"
        # Identical policy to `pack` (same tools, same prompt, same turn cap); the ONLY
        # difference is the pack is produced by the lexical/BM25 arm alone (mode=keyword)
        # instead of the tuned multi-signal retriever (mode=hybrid).
        mode = "keyword" if g_plane == "weakpack" else "hybrid"
        hits = fetch_pack(endpoint, cell["repo"], ref or cell["instance_id"],
                          cell["problem_statement"][:6000], limit, mode=mode)
        pack = format_pack(hits, limit)
        pack_meta = {"pack_hits": len(hits), "pack_chars": len(pack)}
        full = f"{pack}\n\n## Issue\n{cell['problem_statement']}"
        if g_plane in ("pack", "weakpack"):
            # NOTE: `--tools`, not `--allowed-tools` -- --allowed-tools is a permission
            # ALLOWLIST (which tool calls get auto-approved) and has no effect once
            # --dangerously-skip-permissions is set (everything is already auto-approved).
            # `--tools` restricts which tools are REGISTERED with the model at all, which
            # is what "Read + Edit + Write only, no Bash/Grep/Glob" actually requires.
            # Verified empirically 2026-07-13: an --allowed-tools Read/Edit/Write pack-arm
            # smoke test still successfully called Glob; --tools Read,Edit,Write does not.
            cmd = ["claude", "-p", full, "--model", PREDICT_MODEL, "--output-format", "stream-json",
                   "--verbose", "--dangerously-skip-permissions", "--max-budget-usd", str(budget),
                   "--system-prompt", PACK_SYSTEM, "--tools", "Read,Edit,Write",
                   "--max-turns", "10"]
        else:  # trust
            # G2 (AMENDED 2026-07-13, see design doc §G2): the original Edit/Write-only
            # arm was an invalid instrument -- Claude Code's Edit/Write tools refuse to
            # touch a file that wasn't Read in-session, so it could never produce a
            # patch regardless of retrieval quality. The amended arm gives Read back but
            # scopes it with a PreToolUse hook (g_plane_hook.py) that denies any Read
            # outside the pack's own file list -- "the retriever's file set is the
            # agent's whole world" enforced structurally instead of by an unusable tool
            # restriction.
            pack_files = sorted({h.get("file", "") for h in hits if h.get("file")})
            hook_path = str(Path(__file__).resolve().parent / "g_plane_hook.py")
            settings = {"hooks": {"PreToolUse": [{"matcher": "Read",
                        "hooks": [{"type": "command",
                                   "command": f'"{sys.executable}" "{hook_path}"'}]}]}}
            sp = outdir / f"{cell['instance_id']}_trust.settings.json"
            sp.write_text(json.dumps(settings))
            cmd = ["claude", "-p", full, "--model", PREDICT_MODEL, "--output-format", "stream-json",
                   "--verbose", "--dangerously-skip-permissions", "--max-budget-usd", str(budget),
                   "--system-prompt", TRUST_SYSTEM, "--tools", "Read,Edit,Write",
                   "--max-turns", "8", "--settings", str(sp)]
            env["GPLANE_PACK_FILES"] = ";".join(pack_files)
        # pack: no rag CLI on PATH, no PreToolUse hook -- the agent has no search tools
        # at all. trust: Read is registered but pack-scoped by the hook above.
    elif mode == "rag":
        full = f"{RAG_INSTR}\n\n{cell['problem_statement']}"
        rb = RAG_BIN.replace("\\", "/")
        settings = {"hooks": {"PreToolUse": [{"matcher": "Bash|Grep",
                    "hooks": [{"type": "command", "command": f'"{rb}" hook pretooluse'}]}]}}
        sp = outdir / f"{cell['instance_id']}_pred.settings.json"
        sp.write_text(json.dumps(settings))
        # rag-only (Grep disabled + hook), Edit/Write ENABLED so the agent can patch.
        cmd = ["claude", "-p", full, "--model", PREDICT_MODEL, "--output-format", "stream-json", "--verbose",
               "--dangerously-skip-permissions", "--max-budget-usd", str(budget),
               "--disallowedTools", "Grep", "NotebookEdit",
               "--append-system-prompt", POLICY, "--settings", str(sp)]
        if g_plane == "scarce":
            cmd += ["--max-turns", "4"]
        env["RAG_ENDPOINT"] = endpoint
        env["PATH"] = str(Path(RAG_BIN).parent) + os.pathsep + env["PATH"]
    else:  # vanilla: default tools (Grep/Bash/Read allowed), no rag, no policy/hook.
        full = f"{VANILLA_INSTR}\n\n{cell['problem_statement']}"
        cmd = ["claude", "-p", full, "--model", PREDICT_MODEL, "--output-format", "stream-json", "--verbose",
               "--dangerously-skip-permissions", "--max-budget-usd", str(budget),
               "--disallowedTools", "NotebookEdit"]
        if g_plane == "scarce":
            cmd += ["--max-turns", "4"]
    stdout = ""
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout)
        stdout = proc.stdout or ""
    except subprocess.TimeoutExpired as e:  # keep whatever landed before the timeout
        stdout = e.stdout if isinstance(e.stdout, str) else ""
    patch = sh(["git", "-C", cwd, "diff"], check=False)
    return patch, stdout, pack_meta


def _norm(p: str) -> str:
    return p.replace("\\", "/").lower().lstrip("./")


def _tool_counts(messages: list) -> dict:
    """Per-tool usage; splits Bash into rag/grep/other by command text."""
    tc = {"rag": 0, "grep": 0, "bash": 0, "read": 0, "edit": 0, "glob": 0, "other": 0}
    for m in messages:
        for name, inp in m.get("inputs", []):
            if name == "Bash":
                c = (inp.get("command", "") or "")
                if c.strip().startswith("rag ") or " rag " in c:
                    tc["rag"] += 1
                elif any(g in c for g in ("grep", "rg ", "ripgrep", "ack")):
                    tc["grep"] += 1
                else:
                    tc["bash"] += 1
            elif name == "Grep":
                tc["grep"] += 1
            elif name == "Read":
                tc["read"] += 1
            elif name in ("Edit", "Write", "MultiEdit"):
                tc["edit"] += 1
            elif name == "Glob":
                tc["glob"] += 1
            else:
                tc["other"] += 1
    return tc


def predict_instance(cell: dict, mode: str, endpoint: str, outdir: Path,
                     budget: float, label: str, cache_dir: Path = WORK,
                     ref_mode: str = "eval", g_plane: str = "explore") -> tuple[dict, dict]:
    cache = cache_dir / (cell["repo"].replace("/", "__") + ".cache")
    iid = cell["instance_id"]
    co = outdir / f"co_{label}_{iid}"     # label-scoped so arms can run concurrently
    # ref-mode="instance": name the checkout branch after the instance_id so the rag
    # client (which resolves its ref from the checkout's current git branch, see
    # gitctx::gather) hits the per-instance registry ref that p5_index_instances.py
    # registers (repo, ref=instance_id), instead of the shared ref="eval" row. The
    # same `branch` is what g-plane pack/trust arms query retrievald's /v1/query with.
    branch = iid if ref_mode == "instance" else "eval"
    try:
        prepare_checkout(cache, cell["base_commit"], co, cell["url"], branch=branch)
        patch, stdout, pack_meta = run_predict(cell, mode, endpoint, str(co), outdir, budget,
                                               g_plane=g_plane, ref=branch)
        # save the FULL transcript so any metric is derivable later
        tpath = outdir / f"{iid}_{label}.stream.jsonl"
        tpath.write_text(stdout, encoding="utf-8")
        msgs, _answer = deduped_messages(stdout)
        m = stream_metrics(msgs)
        gold = {_norm(g) for g in cell["gold_files"]}
        pf = {_norm(f) for f in patch_files(patch)}
        hit = gold & pf
        pred = {"instance_id": iid, "model_name_or_path": label, "model_patch": patch}
        met = {"instance_id": iid, "label": label, "mode": mode, "g_plane": g_plane,
               "repo": cell["repo"],
               "patch_chars": len(patch), "patch_files": sorted(pf),
               "gold_files": sorted(gold), "loc_recall": (len(hit) / len(gold)) if gold else 0.0,
               "any_gold": bool(hit), "all_gold": bool(gold) and hit == gold,
               "turns": m["turns"], "peak_ctx": m["peak_ctx"], "new_tok": m["new_tok"],
               "out_tok": m["out_tok"], "cost_wt": m["cost_wt"],
               "pack_hits": pack_meta["pack_hits"], "pack_chars": pack_meta["pack_chars"],
               "tool_counts": _tool_counts(msgs), "transcript": str(tpath)}
        return pred, met
    finally:
        force_rmtree(co)


def _resume_done_ids(out_path: Path, keep_empty: bool = False) -> set[str]:
    """instance_ids already present in an existing predict --out file. By default
    only rows with a NON-EMPTY model_patch count as done (empty rows are re-run).
    With keep_empty=True, EVERY already-predicted iid counts as done — used when an
    arm has already been attempted once and you only want to fill never-attempted
    instances (one attempt per instance; no costly re-run of genuine empties)."""
    done: set[str] = set()
    if not out_path.exists():
        return done
    for line in out_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if keep_empty or (row.get("model_patch") or "").strip():
            done.add(row.get("instance_id"))
    return done


def cmd_predict(args: argparse.Namespace) -> int:
    subset = Path(args.subset) if args.subset else (BENCH / "subset.json")
    cache_dir = Path(args.cache_dir) if args.cache_dir else WORK
    cells = json.loads(subset.read_text(encoding="utf-8"))
    if args.ids:
        want = set(args.ids.split(","))
        cells = [c for c in cells if c["instance_id"] in want]
    if args.limit:
        cells = cells[:args.limit]
    out = subset.parent / "predict"; out.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out)
    mpath = args.out.rsplit(".jsonl", 1)[0] + ".metrics.jsonl"

    if args.resume:
        # 500-instance runs will be interrupted; --resume loads the existing out
        # (+ sibling .metrics) file, skips already-done iids, and appends rather
        # than truncating so a re-run is safe to fire repeatedly.
        done = _resume_done_ids(out_path, keep_empty=args.resume_keep_empty)
        before = len(cells)
        cells = [c for c in cells if c["instance_id"] not in done]
        kind = "any patch incl empty" if args.resume_keep_empty else "non-empty patch"
        print(f"[resume] {out_path.name}: {len(done)} already done ({kind}), "
              f"{before - len(cells)} skipped, {len(cells)} remaining", flush=True)

    print(f"generating {len(cells)} predictions (mode={args.mode}, g_plane={args.g_plane}, "
          f"endpoint={args.endpoint}, label={args.label}, subset={subset.name}, "
          f"ref_mode={args.ref_mode}, conc={args.concurrency}) ...", flush=True)
    preds: list[dict] = []
    mets: list[dict] = []
    # INCREMENTAL WRITE: long n=500 runs get reaped; append+flush each result under a
    # lock so a mid-run kill loses nothing and --resume can skip completed iids. (Prior
    # code buffered everything and wrote once at the end — a kill lost the whole run.)
    import threading
    write_lock = threading.Lock()
    write_mode = "a" if args.resume else "w"
    fh = open(out_path, write_mode, encoding="utf-8")
    mfh = open(mpath, write_mode, encoding="utf-8")
    try:
        with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
            futs = {ex.submit(predict_instance, c, args.mode, args.endpoint, out, args.budget,
                              args.label, cache_dir, args.ref_mode, args.g_plane): c["instance_id"]
                    for c in cells}
            for f in as_completed(futs):
                iid = futs[f]
                try:
                    pred, met = f.result()
                    with write_lock:
                        fh.write(json.dumps(pred) + "\n"); fh.flush()
                        mfh.write(json.dumps(met) + "\n"); mfh.flush()
                    preds.append(pred); mets.append(met)
                    empty = "  (EMPTY)" if not pred["model_patch"].strip() else ""
                    pack = f" pack={met['pack_hits']}h/{met['pack_chars']}c" if met["pack_hits"] else ""
                    print(f"  {iid}: {met['patch_chars']}ch peak_ctx={met['peak_ctx']} "
                          f"turns={met['turns']} rag={met['tool_counts']['rag']} "
                          f"grep={met['tool_counts']['grep']} recall={met['loc_recall']:.2f}{pack}{empty}",
                          flush=True)
                except Exception as e:  # noqa: BLE001
                    print(f"  FAIL {iid}: {e}", flush=True)
    finally:
        fh.close(); mfh.close()
    n_empty = sum(1 for p in preds if not p["model_patch"].strip())
    verb = "appended" if args.resume else "wrote"
    print(f"\n{verb} {len(preds)} new predictions to {args.out} ({n_empty} empty)")
    print(f"{verb} {len(mets)} new metric rows to {mpath}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prep")
    p.add_argument("--instances", type=int, default=100)
    p.add_argument("--min-per-repo", type=int, default=3)
    p.add_argument("--max-per-repo", type=int, default=20)
    p.set_defaults(func=cmd_prep)
    p = sub.add_parser("index")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_index)
    p = sub.add_parser("run")
    p.add_argument("--seeds", type=int, default=2)
    p.add_argument("--concurrency", type=int, default=3)
    p.add_argument("--budget", type=float, default=2.0)
    p.add_argument("--limit", type=int, default=0)
    p.set_defaults(func=cmd_run)
    p = sub.add_parser("predict")
    p.add_argument("--mode", choices=("rag", "vanilla"), default="rag",
                   help="rag = rag-only (grep blocked, hook); vanilla = default tools, no rag")
    p.add_argument("--endpoint", default=ENDPOINT)
    p.add_argument("--label", required=True, help="model_name_or_path in predictions")
    p.add_argument("--out", required=True)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--ids", default="", help="comma-separated instance_ids to restrict to")
    p.add_argument("--subset", default="", help="path to subset.json (default: Verified)")
    p.add_argument("--cache-dir", default="", help="dir holding <repo>.cache clones (default: Verified WORK)")
    p.add_argument("--budget", type=float, default=2.0)
    p.add_argument("--concurrency", type=int, default=3)
    p.add_argument("--resume", action="store_true",
                   help="skip instance_ids with a non-empty model_patch already in --out; "
                        "append new rows to --out and its .metrics.jsonl instead of truncating")
    p.add_argument("--resume-keep-empty", action="store_true",
                   help="with --resume, also skip instances that already have an EMPTY patch "
                        "(one attempt per instance; fills only never-attempted instances, no "
                        "re-run of genuine empties)")
    p.add_argument("--ref-mode", choices=("eval", "instance"), default="eval",
                   help="eval (default) = checkout branch 'eval' (shared per-repo registry ref); "
                        "instance = checkout branch named after instance_id, so the rag arm "
                        "resolves the per-instance registry ref (see p5_index_instances.py)")
    p.add_argument("--g-plane", choices=("explore", "pack", "trust", "scarce", "weakpack", "oracle", "oracletools", "packtools", "toolprimed", "packfile"), default="explore",
                   help="agent POLICY (see docs/plans/2026-07-13-g-plane-design.md): "
                        "explore (default) = today's behavior EXACTLY; scarce = explore + "
                        "--max-turns 4; pack = G1 context-pack (Read/Edit/Write only, "
                        "--max-turns 10, --mode ignored); trust = G2 pure-trust AMENDED "
                        "(Read/Edit/Write, Read pack-scoped by a PreToolUse hook, "
                        "--max-turns 8, --mode ignored)")
    p.set_defaults(func=cmd_predict)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
