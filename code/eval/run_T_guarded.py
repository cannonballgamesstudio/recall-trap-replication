#!/usr/bin/env python3
"""Cost-guarded wrapper around scripts/eval/local_dedup_ab.py for TRIMMED-BREADTH Arm T on gpt-5.6-sol.

Behaviour identical to local_dedup_ab.chat (same SYS, same user turn, temperature 0.2, max_tokens,
same parse/fallback rule) EXCEPT:
  * payload adds OpenRouter usage accounting {"usage":{"include":true}} (accounting only, no decoding effect)
  * raw record additionally logs usage / served model / provider
  * a cumulative cost guard: before each call, if spent + reserve > CAP the call is refused
    (raised -> runner prints 'gen FAIL', no pred written), so the run halts below the cap.

Spent = sum of usage.cost over every raw_local_gpt56sol_T*.jsonl in p5 (usage probe included).

usage:  python run_T_guarded.py <cap_usd> <local_dedup_ab args...>
"""
import json, os, sys, threading, urllib.request, glob
from pathlib import Path

sys.path.insert(0, r"code/eval")
import local_dedup_ab as L  # noqa: E402

CAP = float(sys.argv[1])
P5 = Path("work/p5")
_lock = threading.Lock()


def _existing_spend():
    tot = 0.0
    for fn in glob.glob(str(P5 / "raw_local_gpt56sol_T*.jsonl")):
        for line in open(fn, encoding="utf-8"):
            if line.strip():
                try:
                    tot += float((json.loads(line).get("usage") or {}).get("cost") or 0.0)
                except Exception:
                    pass
    return tot


STATE = {"spent": _existing_spend(), "max_call": 0.0, "inflight": 0, "halted": False}
print(f"[guard] cap=${CAP:.2f} starting spent=${STATE['spent']:.4f}", flush=True)


def chat(endpoint, pack, issue, timeout=900, max_tokens=6000, reason_cap=None,
         api_model=None, api_key=None):
    with _lock:
        # reserve: worst observed call (or $0.10 before any observation) for every in-flight call + this one
        per = max(STATE["max_call"], 0.10)
        if STATE["spent"] + per * (STATE["inflight"] + 1) > CAP:
            STATE["halted"] = True
            raise RuntimeError(f"COST_GUARD_HALT spent={STATE['spent']:.4f} cap={CAP}")
        STATE["inflight"] += 1
    try:
        payload = {
            "messages": [{"role": "system", "content": L.SYS},
                         {"role": "user", "content": f"{pack}\n\n## Issue\n{issue}\n\nEmit the SEARCH/REPLACE edits."}],
            "temperature": 0.2, "max_tokens": max_tokens, "stream": False,
        }
        if reason_cap:
            payload["reasoning"] = {"max_tokens": reason_cap}
        if api_model:
            payload["model"] = api_model
            payload["usage"] = {"include": True}
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
        content = msg.get("content") or ""
        reasoning = msg.get("reasoning") or msg.get("reasoning_content") or ""
        text = content if L.BLOCK.search(content) else content + "\n" + reasoning
        usage = resp.get("usage") or {}
        cost = float(usage.get("cost") or 0.0)
        raw = {"finish_reason": ch.get("finish_reason"), "content_len": len(content),
               "reasoning_len": len(reasoning), "usage": usage,
               "served_model": resp.get("model"), "provider": resp.get("provider")}
        if os.environ.get("LOG_RESPONSE_TEXT"):
            raw["content"] = content
            raw["reasoning"] = reasoning
        with _lock:
            STATE["spent"] += cost
            STATE["max_call"] = max(STATE["max_call"], cost)
        return text, raw
    finally:
        with _lock:
            STATE["inflight"] -= 1


L.chat = chat
sys.argv = ["local_dedup_ab.py"] + sys.argv[2:]
rc = L.main()
print(f"[guard] final spent=${STATE['spent']:.4f} max_call=${STATE['max_call']:.4f} halted={STATE['halted']}", flush=True)
raise SystemExit(rc)
