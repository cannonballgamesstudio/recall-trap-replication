#!/usr/bin/env python3
"""E5 — external validity: does the dedup effect replicate on a LOCAL model?

The +18.2pp dedup-OFF>dedup-ON finding is currently one model (Claude Sonnet).
This runs the SAME two packs (pre-fetched to local_packs.json) through a local
coder model with NO search tools -- the pure pack regime -- and grades via the
official Docker harness. We do NOT care that the local model scores lower in
absolute terms; we care whether the dedup-OFF minus dedup-ON DELTA reproduces.
If it does, the effect is a property of fixed-budget context, not a Claude quirk.

Local models botch raw unified diffs, so we ask for SEARCH/REPLACE edit blocks
(Aider-style) and apply them ourselves against the base_commit checkout, then
`git diff` -> the model_patch for swebench grading.

  python local_dedup_ab.py --arm dedupON  --endpoint http://127.0.0.1:8090
  python local_dedup_ab.py --arm dedupOFF --endpoint http://127.0.0.1:8090

Best-of-N fan-out mode (FANOUT-PILOT-PREREG.md). Enabled ONLY by --n-samples; every other
sampling flag requires it. Without --n-samples the request bytes, preds/raw file names and
row contents are byte-identical to the pre-fan-out script (proved by
tests/test_local_dedup_ab_equiv.py against the git-HEAD version).

  python local_dedup_ab.py --arm dedupON --ids @fanout_ids.txt --n-samples 16 \
      --temperature 0.7 --top-p 0.8 --per-sample-seed --nonce --max-tokens 6000 \
      --model-tag fanout_a3b --concurrency 8

  -> preds_local_<tag>_<arm>_sNN.jsonl   (one file per sample index j; instance_id stays unique
                                          inside each file, so each is a valid swebench preds file)
     raw_local_<tag>_<arm>_fanout.jsonl  (one row per (instance, j) attempt outcome)
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import swe_bench as sb

P = Path("work/p5")
CO_ROOT = P / "local_checkouts"          # base_commit worktrees, on E: (cross-drive clone limit)
WORK = sb.WORK

SYS = """You are an expert software engineer resolving a real GitHub issue. You are given the issue and a retrieved-context block showing the most relevant code. You have NO tools: you cannot search, read other files, or run anything — you may only edit the code shown to you.

Output ONLY *SEARCH/REPLACE* edit blocks. No explanation, no prose, no reasoning. Begin your reply directly with the first block.

Each block is EXACTLY this shape — the file path on its own line, then the fenced edit:

path/to/file.py
```
<<<<<<< SEARCH
exact lines copied verbatim from the shown code
=======
the replacement lines
>>>>>>> REPLACE
```

The SEARCH text must be copied byte-for-byte from a snippet you were shown, so it will match the file. Make the minimal change that resolves the issue. Do not modify tests.

Example of a complete reply:

src/foo/bar.py
```
<<<<<<< SEARCH
    if x > 0:
        return x
=======
    if x >= 0:
        return x
>>>>>>> REPLACE
```"""

# Standard aider block: path line, optional ``` fence, then SEARCH/=====/REPLACE.
BLOCK = re.compile(
    r"^(?P<path>[\w./\\-]+\.\w+)\s*?\n"          # a bare file path on its own line
    r"(?:```[\w]*\n)?"                             # optional opening fence
    r"<<<<<<<+\s*SEARCH\s*\n(?P<search>.*?)\n=======+\s*\n(?P<replace>.*?)\n>>>>>>>+\s*REPLACE",
    re.DOTALL | re.MULTILINE)


# ---------------------------------------------------------------- fan-out sampling helpers
# Only reached when --n-samples is given. Legacy (no --n-samples) never calls these.
NONCE_LINE = "Request nonce: {nonce} (opaque request id; ignore it)."


def sample_seed(iid: str, arm: str, j: int) -> int:
    """Per-sample RNG seed = hash(instance, arm, j), 31-bit (llama.cpp takes a uint32)."""
    h = hashlib.sha256(f"seed|{iid}|{arm}|{j}".encode("utf-8")).digest()
    return int.from_bytes(h[:4], "big") & 0x7FFFFFFF


def attempt_nonce(iid: str, arm: str, j: int, attempt: int) -> str:
    """Per-ATTEMPT nonce (a retry gets a fresh one). Deterministic, so a rerun is replayable.
    Concurrent byte-identical prompts have collided into empty slots on llama.cpp b9837
    (serve_qwen38_8090_fanout.ps1 notes); the nonce makes every in-flight prompt distinct."""
    return hashlib.sha256(f"nonce|{iid}|{arm}|{j}|{attempt}".encode("utf-8")).hexdigest()[:16]


def user_content(pack, issue, nonce=None):
    """User turn. The nonce line goes LAST so the shared pack+issue prefix stays cacheable."""
    s = f"{pack}\n\n## Issue\n{issue}\n\nEmit the SEARCH/REPLACE edits."
    if nonce is not None:
        s += "\n\n" + NONCE_LINE.format(nonce=nonce)
    return s


def chat(endpoint, pack, issue, timeout=900, max_tokens=6000, reason_cap=None,
         api_model=None, api_key=None, sampling=None):
    # sampling=None -> the exact legacy payload (same keys, same order, same bytes).
    # sampling={"temperature", "top_p", "seed", "nonce", "template_kwargs"} -> fan-out payload.
    if sampling is None:
        payload = {
            "messages": [{"role": "system", "content": SYS},
                         {"role": "user", "content": f"{pack}\n\n## Issue\n{issue}\n\nEmit the SEARCH/REPLACE edits."}],
            "temperature": 0.2, "max_tokens": max_tokens, "stream": False,
        }
    else:
        payload = {
            "messages": [{"role": "system", "content": SYS},
                         {"role": "user", "content": user_content(pack, issue, sampling.get("nonce"))}],
            "temperature": sampling["temperature"], "max_tokens": max_tokens, "stream": False,
        }
        if sampling.get("top_p") is not None:
            payload["top_p"] = sampling["top_p"]
        if sampling.get("seed") is not None:
            payload["seed"] = sampling["seed"]
        if sampling.get("template_kwargs"):
            payload["chat_template_kwargs"] = sampling["template_kwargs"]
    if reason_cap:                   # request a bound on thinking (some providers honor it, some ignore it)
        payload["reasoning"] = {"max_tokens": reason_cap}
    if api_model:                    # remote API (OpenRouter/OpenAI/DeepSeek/...) needs the model name
        payload["model"] = api_model
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    body = json.dumps(payload).encode()
    # remote endpoints already include /v1; local llama-server does not
    url = endpoint.rstrip("/")
    if not url.endswith("/chat/completions"):
        url = url + ("/chat/completions" if url.endswith("/v1") else "/v1/chat/completions")
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.loads(r.read())
    ch = resp["choices"][0]
    msg = ch.get("message", {})
    # OpenRouter returns the thinking trace in the field named `reasoning` (NOT
    # `reasoning_content` -- an earlier bug read the wrong key and silently got "").
    # SEARCH/REPLACE blocks live in `content`; `reasoning` is planning prose. Parse
    # content, but fall back to reasoning if content has no block (harmless).
    content = msg.get("content") or ""
    reasoning = msg.get("reasoning") or msg.get("reasoning_content") or ""
    text = content if BLOCK.search(content) else content + "\n" + reasoning
    raw = {"finish_reason": ch.get("finish_reason"), "content_len": len(content),
           "reasoning_len": len(reasoning)}
    if sampling is not None:          # fan-out only: token usage for truncation / instant-EOS audit
        u = resp.get("usage") or {}
        raw["completion_tokens"] = u.get("completion_tokens")
        raw["prompt_tokens"] = u.get("prompt_tokens")
    if os.environ.get("LOG_RESPONSE_TEXT"):   # producibility-mechanism audit: save the actual response
        raw["content"] = content
        raw["reasoning"] = reasoning
    return text, raw


def _resolve(co: Path, rel: str, known: list[str]) -> Path | None:
    """Map the model's claimed path to a real file. Models hallucinate prefixes
    (src/) or drop them; resolve against the pack's known real paths by longest
    common suffix, then fall back to a basename match in the checkout."""
    rel = rel.strip().replace("\\", "/")
    if (co / rel).exists():
        return co / rel
    base = rel.split("/")[-1]
    # prefer a pack file whose path shares the longest trailing segment run
    cand = [k for k in known if k.replace("\\", "/").split("/")[-1] == base]
    cand.sort(key=lambda k: len(os.path.commonprefix([k[::-1], rel[::-1]])), reverse=True)
    for k in cand:
        if (co / k).exists():
            return co / k
    return None


def apply_edits(co: Path, text: str, known: list[str]) -> int:
    applied = 0
    for m in BLOCK.finditer(text):
        search = m.group("search")
        replace = m.group("replace")
        fp = _resolve(co, m.group("path"), known)
        if fp is None:
            continue
        try:
            # newline="" disables ALL translation so git diffs ONLY the changed
            # lines, not the whole file (write_text would rewrite every line-ending
            # and produce a bogus full-file diff that breaks grading).
            with open(fp, "r", encoding="utf-8", errors="replace", newline="") as fh:
                content = fh.read()
        except OSError:
            continue
        if search and search in content:
            with open(fp, "w", encoding="utf-8", newline="") as fh:
                fh.write(content.replace(search, replace, 1))
            applied += 1
    return applied


def count_blocks(text: str) -> int:
    return sum(1 for _ in BLOCK.finditer(text))


def run_fanout(args, cells, packs, ids, api_key) -> int:
    """Best-of-N generation: N samples per instance for ONE arm. Work unit = (iid, j).

    Files (all under root):
      preds_<label>_sNN.jsonl   swebench-valid preds for sample index j (unique instance_id per file);
                                rows carry an extra "sample" field (the harness ignores extra keys).
      raw_<label>_fanout.jsonl  one row per (iid, j) FINAL outcome, incl. infra failures.
    Resume: an (iid, j) is done iff its preds row exists. Infra-failed units have a raw row but no
    preds row, so a rerun retries them (the pre-registered infra-hang rule decides exclusion).
    """
    import threading, time
    from concurrent.futures import ThreadPoolExecutor
    label = f"local_{args.model_tag}_{args.arm}"
    js = list(range(args.sample_offset, args.sample_offset + args.n_samples))
    tkw = json.loads(args.template_kwargs) if args.template_kwargs else None

    def preds_path(j):
        return P / f"preds_{label}_s{j:02d}.jsonl"

    done = set()
    for j in js:
        pp = preds_path(j)
        if pp.exists():
            for line in pp.read_text(encoding="utf-8").splitlines():
                try: done.add((json.loads(line)["instance_id"], j))
                except Exception: pass
    # j-major order: sample 0 for every instance, then sample 1, ... -- an interrupted run leaves
    # whole sample-index layers, and concurrent requests are mostly DIFFERENT instances.
    todo = [(iid, j) for j in js for iid in ids if (iid, j) not in done]
    CO_ROOT.mkdir(parents=True, exist_ok=True)
    write_lock, clone_lock = threading.Lock(), threading.Lock()
    pf = {j: preds_path(j).open("a", encoding="utf-8") for j in js}
    rawf = (P / f"raw_{label}_fanout.jsonl").open("a", encoding="utf-8")
    counter = {"n": 0}
    print(f"[fanout] {label}: {len(ids)} instances x N={args.n_samples} (j={js[0]}..{js[-1]}) "
          f"T={args.temperature} top_p={args.top_p} seed={'hash' if args.per_sample_seed else 'none'} "
          f"nonce={'on' if args.nonce else 'off'} max_tokens={args.max_tokens}; todo={len(todo)}", flush=True)

    def work(unit):
        iid, j = unit
        c = cells[iid]
        pack = packs[iid][args.arm]["pack"]
        co = CO_ROOT / label / f"{iid}__s{j:02d}"       # per-sample checkout: samples of one iid run concurrently
        base = {"instance_id": iid, "sample": j, "arm": args.arm,
                "seed": sample_seed(iid, args.arm, j) if args.per_sample_seed else None,
                "temperature": args.temperature, "top_p": args.top_p, "max_tokens": args.max_tokens}
        if not (co / ".git").exists():
            with clone_lock:
                cache = sb.cache_clone(c["repo"], c["url"])
            try:
                sb.prepare_checkout(cache, c["base_commit"], co, c["url"])
            except Exception as e:
                with write_lock:
                    rawf.write(json.dumps({**base, "infra_fail": "checkout", "error": str(e)[:200]}) + "\n"); rawf.flush()
                print(f"  checkout FAIL {iid} s{j}: {str(e)[:70]}", flush=True); return
        else:
            sb.sh(["git", "-C", str(co), "checkout", "--quiet", "--", "."], check=False)
        reply = raw = None
        errors = []
        t0 = time.time()
        for attempt in range(args.max_attempts):
            nonce = attempt_nonce(iid, args.arm, j, attempt) if args.nonce else None
            samp = {"temperature": args.temperature, "top_p": args.top_p, "seed": base["seed"],
                    "nonce": nonce, "template_kwargs": tkw}
            try:
                reply, raw = chat(args.endpoint, pack, c["problem_statement"][:6000],
                                  timeout=args.timeout, max_tokens=args.max_tokens,
                                  reason_cap=args.reason_cap, api_model=args.api_model,
                                  api_key=api_key, sampling=samp)
                base["nonce"], base["attempt"] = nonce, attempt
                break
            except Exception as e:                      # HTTP error / timeout / bad JSON = infra, not outcome
                errors.append(f"{type(e).__name__}: {str(e)[:120]}")
        if reply is None:
            with write_lock:
                rawf.write(json.dumps({**base, "infra_fail": "generation", "attempts": len(errors),
                                       "errors": errors, "wall_s": round(time.time() - t0, 1)}) + "\n"); rawf.flush()
            print(f"  gen FAIL {iid} s{j} after {len(errors)} attempts: {errors[-1][:70]}", flush=True)
            sb.force_rmtree(co); return
        blocks = count_blocks(reply)
        applied = apply_edits(co, reply, packs[iid][args.arm]["files"])
        patch = sb.sh(["git", "-C", str(co), "diff"], check=False)
        empty = not patch.strip()
        truncated = raw.get("finish_reason") == "length"
        instant_eos = (raw.get("content_len", 0) == 0 and raw.get("reasoning_len", 0) == 0)
        with write_lock:
            pf[j].write(json.dumps({"instance_id": iid, "model_name_or_path": f"{label}_s{j:02d}",
                                    "model_patch": patch, "sample": j}) + "\n")
            pf[j].flush()
            rawf.write(json.dumps({**base, "blocks": blocks, "applied": applied, "patch_len": len(patch),
                                   "empty_patch": empty, "truncated": truncated, "instant_eos": instant_eos,
                                   "retries": len(errors), "retry_errors": errors,
                                   "wall_s": round(time.time() - t0, 1), **raw}) + "\n")
            rawf.flush()
            counter["n"] += 1
            print(f"  [{counter['n']}/{len(todo)}] {iid} s{j:02d} blocks={blocks} applied={applied} "
                  f"patch={len(patch)}ch fin={raw['finish_reason']} c={raw['content_len']}"
                  f"{' EMPTY' if empty else ''}{' TRUNC' if truncated else ''}", flush=True)
        sb.force_rmtree(co)

    if args.concurrency <= 1:
        for u in todo:
            work(u)
    else:
        with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
            list(ex.map(work, todo))
    for fh in pf.values():
        fh.close()
    rawf.close()
    print(f"[done] {label} fanout -> {P}/preds_{label}_sNN.jsonl")
    return 0


def main() -> int:
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True,
                    help="pack arm key in the packs file: dedupON, dedupOFF, spillv1, cap2, ...")
    ap.add_argument("--endpoint", default="http://127.0.0.1:8090")
    ap.add_argument("--model-tag", default="qwen3coder30b", help="label for the preds filename")
    ap.add_argument("--api-model", default=None, help="remote model name, e.g. openai/gpt-5, deepseek/deepseek-chat, z-ai/glm-5.2, moonshotai/kimi-k2 (OpenRouter ids)")
    ap.add_argument("--api-key-env", default=None, help="env var holding the API key (e.g. OPENROUTER_API_KEY)")
    ap.add_argument("--concurrency", type=int, default=1, help="parallel requests (safe to raise for a remote API)")
    ap.add_argument("--ids", default=None, help="comma-sep subset for smoke tests, or 'all' for full n=500")
    ap.add_argument("--max-tokens", type=int, default=6000, help="total completion budget; raise for reasoning models (e.g. 16000 for deepseek-v4)")
    ap.add_argument("--reason-cap", type=int, default=None, help="requested reasoning token cap (honored by some providers)")
    ap.add_argument("--packs-file", default="local_packs.json", help="pack json under root dir; CC-1 uses dense_packs.json")
    # --- multilingual glue (NEXT-BENCHMARKS-DESIGN Pre-reg 1): point the harness at
    # another benchmark's root + manifest. Defaults preserve SWE-Verified behavior
    # exactly. PolyBench: --root <EVAL_ROOT>/polybench --instances-file instances_polybench.json
    ap.add_argument("--root", default="work/p5", help="dir holding instances manifest, packs, and checkouts")
    ap.add_argument("--instances-file", default="instances_verified.json", help="instance manifest under root (needs instance_id, repo, base_commit, url)")
    # --- best-of-N fan-out (FANOUT-PILOT-PREREG.md). All of these REQUIRE --n-samples; with
    # --n-samples absent the script is byte-identical to its pre-fan-out behaviour.
    fo = ap.add_argument_group("fan-out (requires --n-samples)")
    fo.add_argument("--n-samples", type=int, default=None, help="N samples per instance -> fan-out mode")
    fo.add_argument("--sample-offset", type=int, default=0, help="first sample index j (crash recovery / sharding)")
    fo.add_argument("--temperature", type=float, default=None, help="sampling temperature (fan-out default 0.7, A3B vendor setting)")
    fo.add_argument("--top-p", type=float, default=None, help="nucleus top_p (fan-out default 0.8)")
    fo.add_argument("--per-sample-seed", action="store_true", help="send seed = hash(instance, arm, j)")
    fo.add_argument("--nonce", action="store_true", help="append a per-attempt nonce line to the user turn")
    fo.add_argument("--max-attempts", type=int, default=None, help="infra retries per (instance, j); default 3")
    fo.add_argument("--timeout", type=int, default=None, help="per-request timeout seconds; default 900")
    fo.add_argument("--template-kwargs", default=None, help='JSON chat_template_kwargs, e.g. {"enable_thinking": false}')
    fo.add_argument("--ids-file", default=None, help="file of instance ids (one per line or comma-separated)")
    args = ap.parse_args()
    _fanout_only = {"sample_offset": 0, "temperature": None, "top_p": None, "per_sample_seed": False,
                    "nonce": False, "max_attempts": None, "timeout": None, "template_kwargs": None,
                    "ids_file": None}
    if args.n_samples is None:
        bad = [k for k, d in _fanout_only.items() if getattr(args, k) != d]
        if bad:
            print(f"ABORT: {', '.join('--' + b.replace('_', '-') for b in bad)} require --n-samples"); return 2
    else:
        if args.n_samples < 1:
            print("ABORT: --n-samples must be >= 1"); return 2
        args.temperature = 0.7 if args.temperature is None else args.temperature
        args.top_p = 0.8 if args.top_p is None else args.top_p
        args.max_attempts = 3 if args.max_attempts is None else args.max_attempts
        args.timeout = 900 if args.timeout is None else args.timeout
    api_key = os.environ.get(args.api_key_env) if args.api_key_env else None
    if args.api_key_env and not api_key:
        print(f"ABORT: {args.api_key_env} not set in env"); return 1

    global P, CO_ROOT
    P = Path(args.root)
    CO_ROOT = P / "local_checkouts"
    cells = {c["instance_id"]: c for c in json.loads((P / args.instances_file).read_text(encoding="utf-8"))}
    packs = json.loads((P / args.packs_file).read_text(encoding="utf-8"))
    if args.ids_file:                                       # fan-out only (guarded above)
        ids = []
        for line in Path(args.ids_file).read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0]                    # '#' starts a comment
            ids += [t for t in re.split(r"[,\s]+", line) if t]
        missing = [i for i in ids if i not in packs or args.arm not in packs[i] or i not in cells]
        if missing:
            print(f"ABORT: {len(missing)} ids lack a pack/arm/manifest entry, e.g. {missing[:3]}"); return 2
    elif args.ids == "all":                                 # full n=500 (all prefetched packs w/ this arm)
        ids = sorted(i for i, v in packs.items() if args.arm in v)
    elif args.ids:
        ids = args.ids.split(",")
    else:                                                    # default: the pre-registered 100-slice
        ids = [i for i in (P / "oracle_slice.txt").read_text().split(",")
               if i in packs and args.arm in packs[i]]

    if args.n_samples is not None:
        return run_fanout(args, cells, packs, ids, api_key)

    label = f"local_{args.model_tag}_{args.arm}"
    outp = P / f"preds_{label}.jsonl"
    CO_ROOT.mkdir(parents=True, exist_ok=True)
    done = set()
    if outp.exists():
        for line in outp.read_text(encoding="utf-8").splitlines():
            try: done.add(json.loads(line)["instance_id"])
            except Exception: pass
    todo = [i for i in ids if i not in done]

    # Thread-safety for --concurrency > 1 (safe for REMOTE APIs — no GPU contention):
    #  - write_lock: serialize appends to the single preds file (else lines interleave).
    #  - clone_lock: serialize the SHARED bare cache creation (WORK/<repo>.cache). Only
    #    contended on a repo's cold first-touch; per-instance checkout dirs are already
    #    isolated (CO_ROOT/label/iid), so the parallel work itself doesn't race.
    import threading
    from concurrent.futures import ThreadPoolExecutor
    write_lock = threading.Lock()
    clone_lock = threading.Lock()
    f = outp.open("a", encoding="utf-8")
    rawf = (P / f"raw_{label}.jsonl").open("a", encoding="utf-8")   # audit trail: full response meta
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
        try:
            reply, raw = chat(args.endpoint, pack, c["problem_statement"][:6000],
                              max_tokens=args.max_tokens, reason_cap=args.reason_cap,
                              api_model=args.api_model, api_key=api_key)
        except Exception as e:
            print(f"  gen FAIL {iid}: {str(e)[:70]}", flush=True); return
        applied = apply_edits(co, reply, packs[iid][args.arm]["files"])
        patch = sb.sh(["git", "-C", str(co), "diff"], check=False)
        with write_lock:
            f.write(json.dumps({"instance_id": iid, "model_name_or_path": label,
                                "model_patch": patch}) + "\n")
            f.flush()
            rawf.write(json.dumps({"instance_id": iid, "applied": applied,
                                   "patch_len": len(patch), **raw}) + "\n")
            rawf.flush()
            counter["n"] += 1
            print(f"  [{counter['n']}/{len(todo)}] {iid} edits={applied} patch={len(patch)}ch "
                  f"fin={raw['finish_reason']} c={raw['content_len']}", flush=True)
        # The diff is captured in preds; the checkout is now disposable. Delete it so
        # disk stays bounded to ~concurrency live checkouts. Without this, 500 instances
        # x multiple labels x copied (--no-hardlinks) objects filled E: to 0 bytes.
        sb.force_rmtree(co)

    if args.concurrency <= 1:
        for iid in todo:
            work(iid)
    else:
        with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
            list(ex.map(work, todo))
    f.close()
    rawf.close()
    print(f"[done] {label} -> {outp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
