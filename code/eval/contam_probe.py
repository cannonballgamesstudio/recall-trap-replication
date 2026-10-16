#!/usr/bin/env python3
"""Contamination pre-reg, Branch B: issue-only memorization probes P1/P2/P3.

Pre-registered in docs/paper/CONTAMINATION-PREREG.md section B.2. Importing this module
makes NO calls. Network traffic happens only inside main() for `run` / `usage-probe`.

Same model as the arm being stratified, temperature 0, ONE sample per (probe, instance),
raw responses (content AND reasoning, plus usage) logged to
data/memorization-branchB/raw_{probe}_{tag}.jsonl.

P2 follows the headline harness exactly for application: headline-model checkout at
base_commit (swe_bench.cache_clone / prepare_checkout), local_dedup_ab.apply_edits with
known = every tracked file of the checkout (`git ls-files`), then `git diff` -> preds file
for Docker grading (P2_resolve). P2_apply = applied >= 1.

  python contam_probe.py dry-run --probe P2 --id django__django-11099
  python contam_probe.py dry-run --dataset polybench --probe P3 --id <iid>

Paid calls need --tier (pre-reg B.11), which fixes tag, dataset and cap:
  1 gpt Verified P1/P2/P3 <= $50 (mandatory); 2 Qwen3.6-27B OpenRouter <= $15;
  3 gpt PolyBench P1+P3 <= $15; 4 Qwen3-Coder-30B OpenRouter <= $10. Total ceiling $90.
  python contam_probe.py usage-probe --tier 1 --endpoint https://openrouter.ai/api/v1 \
      --api-model openai/gpt-5.6-sol --api-key-env OPENROUTER_API_KEY
  python contam_probe.py run --tier 1 --probe P1 ... --approved-usd 41.20
Free, locally served (no tier):
  python contam_probe.py run --probe P1 --tag qwen3coder30b_local --endpoint http://127.0.0.1:8090
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import threading
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import contam_common as cc  # noqa: E402

MAX_TOKENS = 6000              # default = gpt headline budget; per-model values in pre-reg B.2
TEMPERATURE = 0.0

# Pre-reg B.11 cost tiers. Each tier: its own usage probe, owner approval, running guard.
# Priority order if the total must be cut: 1 > 2 > 3 > 4. Total ceiling $90 (owner's call).
TIERS = {
    1: {"cap": 50.0, "tag": "gpt56sol", "dataset": "verified", "probes": ("P1", "P2", "P3"),
        "usage": (("P1", 3), ("P2", 4), ("P3", 3)), "what": "gpt Verified P1/P2/P3 (mandatory)"},
    2: {"cap": 15.0, "tag": "qwen36_or", "dataset": "verified", "probes": ("P1", "P2", "P3"),
        "usage": (("P1", 3), ("P2", 4), ("P3", 3)), "what": "Qwen3.6-27B OpenRouter probes"},
    3: {"cap": 15.0, "tag": "gpt56sol", "dataset": "polybench", "probes": ("P1", "P3"),
        "usage": (("P1", 5), ("P3", 5)), "what": "gpt PolyBench P1+P3 (if cut, P1 only)"},
    4: {"cap": 10.0, "tag": "qwen3coder_or", "dataset": "verified", "probes": ("P1", "P2", "P3"),
        "usage": (("P1", 3), ("P2", 4), ("P3", 3)),
        "what": "Qwen3-Coder-30B OpenRouter probes (if cut, local-GGUF proxy M)"},
}
TOTAL_CEILING_USD = 90.0


def raw_name(dataset: str, probe: str, tag: str, suffix: str = "") -> str:
    pre = "raw_" if dataset == "verified" else "raw_poly_"
    return f"{pre}{probe}_{tag}{suffix}.jsonl"


# ---------------------------------------------------------------- items
def items(probe: str, dataset: str = "verified") -> list[dict]:
    """Every instance the probe is defined on, sorted by instance_id."""
    if dataset == "polybench":
        if probe == "P2":
            raise ValueError("P2 is not run on PolyBench (pre-reg B.2)")
        poly = cc.polybench_python()
        out = []
        if probe == "P3":
            rows = cc.load_json(cc.CONTAM / "poly_p3_inputs.json")["rows"]
            for i in sorted(rows):
                r = rows[i]
                out.append({"instance_id": i, "messages": cc.p3_messages(r["repo"], r["path"], r["prefix"])})
            return out
        for i in sorted(poly):
            x = poly[i]
            if cc.p1_filtered(x["problem_statement"], x["patch"]):
                continue
            out.append({"instance_id": i, "messages": cc.p1_messages(x["repo"], x["problem_statement"])})
        return out
    inst = {x["instance_id"]: x for x in cc.load_json(cc.VER / "instances_verified.json")}
    gold = cc.load_json(cc.VER / "gold_patches.json")
    out = []
    if probe == "P3":
        rows = cc.load_json(cc.CONTAM / "p3_inputs.json")["rows"]
        for i in sorted(rows):
            r = rows[i]
            out.append({"instance_id": i, "messages": cc.p3_messages(r["repo"], r["path"], r["prefix"])})
        return out
    for i in sorted(inst):
        x = inst[i]
        if probe == "P1":
            if cc.p1_filtered(x["problem_statement"], gold[i]):
                continue                                   # NA (CONTAMINATION-P1-FILTER.txt)
            out.append({"instance_id": i, "messages": cc.p1_messages(x["repo"], x["problem_statement"])})
        elif probe == "P2":
            out.append({"instance_id": i, "messages": cc.p2_messages(x["repo"], x["problem_statement"]),
                        "cell": x})
    return out


def usage_ids(probe: str, k: int, dataset: str = "verified") -> list[str]:
    """Deterministic, outcome-blind pick: lowest sha256(SEED:probe:iid)."""
    ids = [x["instance_id"] for x in items(probe, dataset)]
    return sorted(ids, key=lambda i: hashlib.sha256(f"{cc.SEED}:{probe}:{i}".encode()).hexdigest())[:k]


def tier_spend(tier: int) -> float:
    """Cumulative spend of one tier (all its probe logs, usage probe included)."""
    t = TIERS[tier]
    pre = "raw_" if t["dataset"] == "verified" else "raw_poly_"
    return sum(_cost(json.loads(l)) for f in cc.CONTAM.glob(f"{pre}P?_{t['tag']}*.jsonl")
               for l in f.read_text(encoding="utf-8").splitlines() if l.strip())


# ---------------------------------------------------------------- transport
def chat(endpoint: str, messages: list[dict], api_model=None, api_key=None, timeout=1800,
         max_tokens: int = MAX_TOKENS) -> dict:
    payload = {"messages": messages, "temperature": TEMPERATURE, "max_tokens": max_tokens,
               "stream": False}
    if api_model:
        payload["model"] = api_model
        payload["usage"] = {"include": True}          # OpenRouter usage accounting (cost)
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    url = endpoint.rstrip("/")
    if not url.endswith("/chat/completions"):
        url = url + ("/chat/completions" if url.endswith("/v1") else "/v1/chat/completions")
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.loads(r.read())
    ch = resp["choices"][0]
    msg = ch.get("message", {})
    return {"content": msg.get("content") or "",
            "reasoning": msg.get("reasoning") or msg.get("reasoning_content") or "",
            "finish_reason": ch.get("finish_reason"), "usage": resp.get("usage"),
            "model": resp.get("model"), "provider": resp.get("provider")}


# ---------------------------------------------------------------- P2 application
def p2_apply(cell: dict, content: str, reasoning: str, co_root: Path) -> tuple[int, str]:
    import swe_bench as sb
    from local_dedup_ab import BLOCK, apply_edits
    co = co_root / cell["instance_id"]
    if not (co / ".git").exists():
        cache = sb.cache_clone(cell["repo"], cell["url"])
        sb.prepare_checkout(cache, cell["base_commit"], co, cell["url"])
    else:
        sb.sh(["git", "-C", str(co), "checkout", "--quiet", "--", "."], check=False)
    text = content if BLOCK.search(content) else content + "\n" + reasoning   # headline rule
    known = sb.sh(["git", "-C", str(co), "ls-files"], check=False).splitlines()
    applied = apply_edits(co, text, known)
    patch = sb.sh(["git", "-C", str(co), "diff"], check=False)
    sb.force_rmtree(co)
    return applied, patch


# ---------------------------------------------------------------- run
def _cost(rec: dict) -> float:
    u = rec.get("usage") or {}
    return float(u.get("cost") or 0.0)


def run(probe: str, ids: list[str] | None, args, out_suffix: str = "") -> list[dict]:
    api_key = os.environ.get(args.api_key_env) if args.api_key_env else None
    todo = items(probe, args.dataset)
    if ids is not None:
        keep = set(ids)
        todo = [t for t in todo if t["instance_id"] in keep]
    cc.CONTAM.mkdir(parents=True, exist_ok=True)
    raw_p = cc.CONTAM / raw_name(args.dataset, probe, args.tag, out_suffix)
    done = set()
    if raw_p.exists():
        for line in raw_p.read_text(encoding="utf-8").splitlines():
            try:
                done.add(json.loads(line)["instance_id"])
            except Exception:
                pass
    todo = [t for t in todo if t["instance_id"] not in done]
    lock = threading.Lock()
    # running guard: cumulative spend of THIS tier (all its logs, usage probe included)
    cap = TIERS[args.tier]["cap"] if args.tier else float("inf")
    spent = {"usd": tier_spend(args.tier) if args.tier else 0.0}
    rawf = raw_p.open("a", encoding="utf-8")
    predf = (cc.CONTAM / f"preds_P2_{args.tag}{out_suffix}.jsonl").open("a", encoding="utf-8") \
        if probe == "P2" else None
    co_root = cc.CONTAM / "checkouts" / args.tag
    recs: list[dict] = []

    def work(t):
        if spent["usd"] > cap:
            return
        iid = t["instance_id"]
        t0 = time.time()
        try:
            r = chat(args.endpoint, t["messages"], args.api_model, api_key, max_tokens=args.max_tokens)
        except Exception as e:
            print(f"  gen FAIL {iid}: {str(e)[:100]}", flush=True)
            return
        rec = {"instance_id": iid, "probe": probe, "tag": args.tag, "dataset": args.dataset,
               "tier": args.tier, "temperature": TEMPERATURE, "max_tokens": args.max_tokens,
               "secs": round(time.time() - t0, 1), **r}
        patch = ""
        if probe == "P2":
            try:
                rec["applied"], patch = p2_apply(t["cell"], r["content"], r["reasoning"], co_root)
            except Exception as e:
                rec["applied"], patch = None, ""
                rec["apply_error"] = str(e)[:200]
            rec["patch_len"] = len(patch)
        with lock:
            rawf.write(json.dumps(rec) + "\n")
            rawf.flush()
            if predf is not None:
                predf.write(json.dumps({"instance_id": iid, "model_name_or_path": f"contamP2_{args.tag}",
                                        "model_patch": patch}) + "\n")
                predf.flush()
            spent["usd"] += _cost(rec)
            recs.append(rec)
            print(f"  [{len(recs)}/{len(todo)}] {probe} {iid} fin={r['finish_reason']} "
                  f"tier_usd={spent['usd']:.3f}", flush=True)

    if args.concurrency <= 1:
        for t in todo:
            work(t)
    else:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(args.concurrency) as ex:
            list(ex.map(work, todo))
    rawf.close()
    if predf:
        predf.close()
    if spent["usd"] > cap:
        print(f"[HALT] tier {args.tier} spend {spent['usd']:.2f} exceeded cap {cap:.2f}", flush=True)
    return recs


def _bind_tier(args) -> str | None:
    """Paid calls must name a tier; the tier fixes tag and dataset. Returns an error or None."""
    if not args.api_key_env:
        args.tier = None                         # locally served, free: no tier
        return None
    if args.tier not in TIERS:
        return "paid call requires --tier 1|2|3|4 (pre-reg B.11)"
    t = TIERS[args.tier]
    args.tag, args.dataset = t["tag"], t["dataset"]
    return None


def cmd_usage_probe(args) -> int:
    err = _bind_tier(args)
    if err or args.tier is None:
        print(f"ABORT: {err or 'usage-probe is for paid tiers only'}")
        return 1
    t = TIERS[args.tier]
    recs = []
    for probe, k in t["usage"]:
        recs += [(probe, r) for r in run(probe, usage_ids(probe, k, t["dataset"]), args,
                                         out_suffix="_usage10")]
    n_calls = {p: len(items(p, t["dataset"])) for p, _ in t["usage"]}
    per = {}
    for p, _ in t["usage"]:
        c = [_cost(r) for q, r in recs if q == p]
        per[p] = sum(c) / len(c) if c else None
    proj = sum((per[p] or 0.0) * n_calls[p] for p in per)
    out = {"tier": args.tier, "what": t["what"], "tag": t["tag"], "dataset": t["dataset"],
           "api_model": args.api_model, "per_call_usd": per, "n_calls": n_calls,
           "projected_usd": round(proj, 2), "cap_usd": t["cap"], "total_ceiling_usd": TOTAL_CEILING_USD,
           "gate": "PASS (still needs owner approval)" if proj <= t["cap"] else "FAIL: over tier cap",
           "note": "usage-probe responses are logged and NOT used in any analysis"}
    p = cc.CONTAM / f"usage_probe_tier{args.tier}.json"
    p.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0


def cmd_run(args) -> int:
    err = _bind_tier(args)
    if err:
        print(f"ABORT: {err}")
        return 1
    if args.tier is not None:
        t = TIERS[args.tier]
        if args.probe not in t["probes"]:
            print(f"ABORT: probe {args.probe} is not in tier {args.tier} ({t['what']})")
            return 1
        up = cc.CONTAM / f"usage_probe_tier{args.tier}.json"
        if not up.exists():
            print(f"ABORT: tier {args.tier} requires its 10-call usage probe first (usage-probe --tier).")
            return 1
        proj = cc.load_json(up)["projected_usd"]
        if proj > t["cap"] or args.approved_usd is None or args.approved_usd < proj:
            print(f"ABORT: tier {args.tier} projection ${proj} vs cap ${t['cap']}; pass --approved-usd "
                  ">= projection only after the owner approves.")
            return 1
    elif args.dataset == "polybench" and args.probe == "P2":
        print("ABORT: P2 is not run on PolyBench")
        return 1
    run(args.probe, None, args)
    return 0


def cmd_dry_run(args) -> int:
    its = items(args.probe, args.dataset)
    t = [x for x in its if x["instance_id"] == args.id]
    if not t:
        print(f"{args.id}: probe {args.probe} is NA (or absent) for {args.dataset}; "
              f"n_items={len(its)}; no call made")
        return 0
    for m in t[0]["messages"]:
        print(f"--- {m['role']}\n{m['content']}")
    print(f"[dry-run] n_items({args.dataset} {args.probe}) = {len(its)}; no call made")
    return 0


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "usage-probe", "dry-run"):
        s = sub.add_parser(name)
        s.add_argument("--probe", choices=["P1", "P2", "P3"], default="P1")
        s.add_argument("--tier", type=int, choices=sorted(TIERS), default=None,
                       help="required for paid calls; fixes tag + dataset + cap (pre-reg B.11)")
        s.add_argument("--dataset", choices=["verified", "polybench"], default="verified",
                       help="free local runs; paid runs take the tier's dataset")
        s.add_argument("--tag", default="gpt56sol", help="free local runs only (e.g. qwen3coder30b_local)")
        s.add_argument("--endpoint", default="http://127.0.0.1:8090")
        s.add_argument("--api-model", default=None)
        s.add_argument("--api-key-env", default=None)
        s.add_argument("--concurrency", type=int, default=1)
        s.add_argument("--approved-usd", type=float, default=None)
        s.add_argument("--id", default="django__django-11099")
        s.add_argument("--max-tokens", type=int, default=MAX_TOKENS)
    args = ap.parse_args()
    return {"run": cmd_run, "usage-probe": cmd_usage_probe, "dry-run": cmd_dry_run}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
