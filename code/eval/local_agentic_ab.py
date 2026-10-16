#!/usr/bin/env python3
"""Weak-model AGENTIC loop dedup A/B — does the recall trap persist when a weak local
model runs in a tool-using loop instead of single-shot?

Same fixed 12-slot seed pack (dedup ON vs OFF) as local_dedup_ab.py, but the model now
runs a ReAct loop: it may READ additional repository files before emitting SEARCH/REPLACE
edits, capped at --max-turns. This probes the "absorption capacity" axis: strong+uncapped
loops dissolve the effect (matched sonnet fusion null); the hypothesis is that a weak model
and/or a tight turn cap cannot read its way out, so the seed-pack composition still binds.

  python local_agentic_ab.py --arm dedupON  --endpoint http://127.0.0.1:8090 --max-turns 10
  python local_agentic_ab.py --arm dedupOFF --endpoint http://127.0.0.1:8090 --max-turns 3

Turn cap is the treatment's second axis: run each arm at a generous cap (~10) and a tight
cap (2-3). Grade the resulting preds with the same official Docker harness.
"""
from __future__ import annotations
import argparse, json, os, re, sys, time, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import swe_bench as sb
from local_dedup_ab import BLOCK, apply_edits   # reuse the exact edit-apply + path resolver

P = Path("work/p5")
CO_ROOT = P / "local_checkouts"

SYS = """You are an expert software engineer resolving a real GitHub issue in a repository. You are given the issue and a retrieved-context block with the most relevant code. You may read additional files from the repository to gather context, then make a minimal fix.

You work in numbered turns. On each turn do ONE of these two things:

(1) READ files. Output one or more lines, each exactly:
READ: path/to/file.py
(optionally a line range: READ: path/to/file.py:120-180). STOP immediately after your READ: lines — output nothing else, and never guess or write the file contents yourself. The real contents are returned to you on the next turn. Read the file you intend to edit if its exact current lines are not already shown to you.

(2) EDIT. When you have enough context, output ONLY *SEARCH/REPLACE* edit blocks and nothing else. Each block is exactly this shape:
path/to/file.py
```
<<<<<<< SEARCH
exact lines copied verbatim from the current file
=======
the replacement lines
>>>>>>> REPLACE
```
The SEARCH text must match the file byte-for-byte, so copy it from what you were shown. Make the minimal change that resolves the issue. Do not modify tests. Once you emit EDIT blocks you are finished."""

READ_RE = re.compile(r"^\s*READ:\s*(?P<path>[\w./\\-]+\.\w+)(?::(?P<a>\d+)-(?P<b>\d+))?\s*$", re.M)


def chat_once(endpoint, messages, timeout=900, max_tokens=2000, api_model=None, api_key=None):
    payload = {"messages": messages, "temperature": 0.2, "max_tokens": max_tokens, "stream": False}
    if api_model:
        payload["model"] = api_model
    url = endpoint.rstrip("/")
    if not url.endswith("/chat/completions"):
        url = url + ("/chat/completions" if url.endswith("/v1") else "/v1/chat/completions")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    # retry transient errors (429 rate-limit, 5xx) so parallel sweeps don't lose instances
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                resp = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 529) and attempt < 3:
                time.sleep(2 * (attempt + 1)); continue
            raise
        except urllib.error.URLError:
            if attempt < 3:
                time.sleep(2 * (attempt + 1)); continue
            raise
    ch = resp["choices"][0]
    return (ch.get("message", {}).get("content") or "").strip(), resp.get("usage", {})


def read_file(co: Path, rel: str, a=None, b=None, cap=3500) -> str:
    rel = rel.strip().replace("\\", "/")
    fp = co / rel
    if not fp.exists():
        base = rel.split("/")[-1]
        hits = list(co.rglob(base))
        if not hits:
            return f"(file not found: {rel})"
        fp = hits[0]
    try:
        lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return f"(could not read: {rel})"
    if a and b:
        lo, hi = max(1, a), min(len(lines), b)
        body = "\n".join(f"{i+1}: {lines[i]}" for i in range(lo - 1, hi))
    else:
        body = "\n".join(f"{i+1}: {lines[i]}" for i in range(min(len(lines), 200)))
        if len(lines) > 200:
            body += f"\n... ({len(lines)-200} more lines; use a line range to see them)"
    return body[:cap]


def solve(endpoint, pack, issue, co: Path, known: list[str], max_turns: int, api_model=None, api_key=None):
    """ReAct loop. Returns (edits_text, n_turns, n_reads, finished_bool)."""
    messages = [{"role": "system", "content": SYS},
                {"role": "user", "content": f"{pack}\n\n## Issue\n{issue}\n\nBegin. You have at most {max_turns} turns."}]
    n_reads = 0; peak_ctx = 0; total_tok = 0
    for turn in range(max_turns):
        try:
            text, usage = chat_once(endpoint, messages, api_model=api_model, api_key=api_key)
        except Exception as e:
            return "", turn, n_reads, False, peak_ctx, total_tok
        peak_ctx = max(peak_ctx, usage.get("prompt_tokens", 0))          # largest single-turn context
        total_tok += usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
        # Prioritize READ over EDIT: a weak model often emits a READ: line and then
        # hallucinates the file body plus an edit built on that guess. If it asked to
        # read, honor the read and ignore any (guess-based) edit block this turn; only
        # apply edits when the model reads nothing and commits to a SEARCH/REPLACE.
        reads = READ_RE.findall(text)
        if not reads and BLOCK.search(text):
            return text, turn + 1, n_reads, True, peak_ctx, total_tok
        if reads:
            # store only the compact READ request, not the model's hallucinated body,
            # to keep the accumulating context small over a long loop.
            picked = reads[:2]
            messages.append({"role": "assistant",
                             "content": "\n".join(f"READ: {p}" + (f":{a}-{b}" if a else "") for p, a, b in picked)})
            tool = ""
            for path, a, b in picked:
                n_reads += 1
                tool += f"### {path}\n{read_file(co, path, int(a) if a else None, int(b) if b else None)}\n\n"
            remaining = max_turns - turn - 1
            messages.append({"role": "user", "content":
                             f"{tool}\nTurns remaining: {remaining}. READ more or emit the SEARCH/REPLACE EDIT blocks."})
        else:
            messages.append({"role": "assistant", "content": text})
            messages.append({"role": "user", "content":
                             "Output either READ: lines or the SEARCH/REPLACE EDIT blocks now — nothing else."})
    return "", max_turns, n_reads, False, peak_ctx, total_tok


def main() -> int:
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["dedupON", "dedupOFF"], required=True)
    ap.add_argument("--endpoint", default="http://127.0.0.1:8090")
    ap.add_argument("--max-turns", type=int, default=10)
    ap.add_argument("--model-tag", default="qwen3coder30b")
    ap.add_argument("--api-model", default="qwen3-coder-30b", help="model id; OpenRouter e.g. qwen/qwen3-coder-30b-a3b-instruct")
    ap.add_argument("--api-key-env", default=None, help="env var holding the API key (e.g. OPENROUTER_API_KEY); omit for local llama-server")
    ap.add_argument("--concurrency", type=int, default=2)
    ap.add_argument("--ids", default=None, help="comma-sep subset, or 'all'")
    ap.add_argument("--packs-file", default="local_packs.json")
    args = ap.parse_args()
    api_key = os.environ.get(args.api_key_env) if args.api_key_env else None
    if args.api_key_env and not api_key:
        print(f"ABORT: {args.api_key_env} not set in env"); return 1

    cells = {c["instance_id"]: c for c in json.loads((P / "instances_verified.json").read_text(encoding="utf-8"))}
    packs = json.loads((P / args.packs_file).read_text(encoding="utf-8"))
    if args.ids == "all":
        ids = sorted(i for i, v in packs.items() if args.arm in v)
    elif args.ids:
        ids = args.ids.split(",")
    else:
        ids = [i for i in (P / "oracle_slice.txt").read_text().split(",") if i in packs]

    label = f"agentic_{args.model_tag}_t{args.max_turns}_{args.arm}"
    outp = P / f"preds_{label}.jsonl"
    CO_ROOT.mkdir(parents=True, exist_ok=True)
    done = set()
    if outp.exists():
        for line in outp.read_text(encoding="utf-8").splitlines():
            try: done.add(json.loads(line)["instance_id"])
            except Exception: pass
    todo = [i for i in ids if i not in done]

    import threading
    from concurrent.futures import ThreadPoolExecutor
    write_lock = threading.Lock(); clone_lock = threading.Lock()
    f = outp.open("a", encoding="utf-8")
    rawf = (P / f"raw_{label}.jsonl").open("a", encoding="utf-8")
    counter = {"n": 0}

    def work(iid):
        c = cells[iid]
        pack = packs[iid][args.arm]["pack"]
        co = CO_ROOT / label / iid
        if not (co / ".git").exists():
            with clone_lock:
                cache = sb.cache_clone(c["repo"], c["url"])
            try:
                sb.prepare_checkout(cache, c["base_commit"], co, c["url"])
            except Exception as e:
                print(f"  checkout FAIL {iid}: {str(e)[:70]}", flush=True); return
        else:
            sb.sh(["git", "-C", str(co), "checkout", "--quiet", "--", "."], check=False)
        edits, turns, reads, fin, peak_ctx, total_tok = solve(
            args.endpoint, pack, c["problem_statement"][:6000], co,
            packs[iid][args.arm]["files"], args.max_turns, args.api_model, api_key)
        applied = apply_edits(co, edits, packs[iid][args.arm]["files"])
        patch = sb.sh(["git", "-C", str(co), "diff"], check=False)
        with write_lock:
            f.write(json.dumps({"instance_id": iid, "model_name_or_path": label, "model_patch": patch}) + "\n"); f.flush()
            rawf.write(json.dumps({"instance_id": iid, "applied": applied, "turns": turns,
                                   "reads": reads, "finished": fin, "patch_len": len(patch),
                                   "peak_ctx": peak_ctx, "total_tok": total_tok}) + "\n"); rawf.flush()
            counter["n"] += 1
            print(f"  [{counter['n']}/{len(todo)}] {iid} turns={turns} reads={reads} edits={applied} "
                  f"patch={len(patch)}ch peak_ctx={peak_ctx}", flush=True)
        sb.force_rmtree(co)

    if args.concurrency <= 1:
        for iid in todo: work(iid)
    else:
        with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
            list(ex.map(work, todo))
    f.close(); rawf.close()
    print(f"[done] {label} -> {outp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
