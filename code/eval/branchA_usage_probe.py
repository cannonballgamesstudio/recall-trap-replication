"""Branch A (pre-reg A.9) 10-call usage probe: 5 dedupON + 5 dedupOFF on outcome-blind survivors.
Payload = local_dedup_ab.chat legacy payload byte-for-byte + OpenRouter usage accounting
(usage:{include:true}) so cost is returned. Responses are logged and DISCARDED from analysis.
Pick: lowest sha256('20261014:A9:{arm}:{iid}') among gold survivors (outcome-blind).
Usage: python branchA_usage_probe.py SURVIVORS.txt [--dry]"""
import hashlib, json, os, sys, urllib.request
from pathlib import Path
sys.path.insert(0, r"code/eval")
import local_dedup_ab as L

ROOT = Path(r"data/post-cutoff-branchA")
surv = Path(sys.argv[1]).read_text(encoding="utf-8").split()
dry = "--dry" in sys.argv
man = {x["instance_id"]: x for x in json.loads((ROOT / "instances_post.json").read_text(encoding="utf-8"))}
packs = json.loads((ROOT / "post_packs.json").read_text(encoding="utf-8"))
key = os.environ.get("OPENROUTER_API_KEY")
out = ROOT / "gen" / "usage_probe_A9_raw.jsonl"
out.parent.mkdir(exist_ok=True)
recs = []
for arm in ("dedupON", "dedupOFF"):
    pick = sorted(surv, key=lambda i: hashlib.sha256(f"20261014:A9:{arm}:{i}".encode()).hexdigest())[:5]
    for iid in pick:
        payload = {"messages": [{"role": "system", "content": L.SYS},
                                {"role": "user", "content": L.user_content(packs[iid][arm]["pack"],
                                                                           man[iid]["problem_statement"][:6000])}],
                   "temperature": 0.2, "max_tokens": 6000, "stream": False,
                   "model": "openai/gpt-5.6-sol", "usage": {"include": True}}
        if dry:
            print(arm, iid, len(json.dumps(payload))); continue
        req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
                                     data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=900) as r:
            resp = json.loads(r.read())
        ch = resp["choices"][0]
        rec = {"arm": arm, "instance_id": iid, "finish_reason": ch.get("finish_reason"),
               "usage": resp.get("usage"), "provider": resp.get("provider"), "model": resp.get("model"),
               "content": (ch.get("message") or {}).get("content")}
        recs.append(rec)
        with out.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
        print(arm, iid, rec["finish_reason"], (rec["usage"] or {}).get("cost"), flush=True)
if not dry:
    n = len(surv)
    per = {a: sum(float((r["usage"] or {}).get("cost") or 0) for r in recs if r["arm"] == a) / 5 for a in ("dedupON", "dedupOFF")}
    one_seed = n * (per["dedupON"] + per["dedupOFF"])
    probe_cost = sum(float((r["usage"] or {}).get("cost") or 0) for r in recs)
    res = {"n_survivors": n, "per_call_usd": per, "projected_one_seed_usd": round(one_seed, 3),
           "projected_two_seeds_usd": round(2 * one_seed, 3), "usage_probe_usd": round(probe_cost, 4),
           "cap_usd": 30.0, "note": "usage-probe responses are logged and NOT used in any analysis"}
    (ROOT / "gen" / "usage_probe_A9.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))
