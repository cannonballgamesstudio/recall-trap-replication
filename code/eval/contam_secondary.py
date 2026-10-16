#!/usr/bin/env python3
"""Contamination pre-reg: free secondary analyses reported regardless of outcome (B.10).

No model calls, no Docker. Reads already-graded reports, served packs and gold patches.

  python contam_secondary.py        -> prints all three tables, writes
                                       data/memorization-branchB/secondary.json

1. Anchor-transition table: Delta = OFF - ON per ON->OFF anchor-class transition, for the
   four K=12 arms (gpt headline, gpt logged re-run, Qwen3.6-27B K=12, Qwen3-Coder-30B K=12).
   Classes are computed on the K=12 served packs (local_packs.json), so K=4/K=40 arms are
   not eligible (their packs differ).
2. Verbatim-gold table: OFF-only wins (pairwise attempted) whose gold patch has >= 3
   non-empty '+' lines; "reproduces gold" = the model patch's ordered list of non-empty,
   stripped '+' lines equals the gold patch's. Pooled over the two gpt draws.
3. PolyBench Python B->C prevalence: share of SWE-PolyBench_500 Python instances whose
   served dedupON pack is class B and dedupOFF pack is class C (same classifier).
4. Delta within PolyBench-Python B->C for gpt-5.6-sol and Qwen3-Coder-30B, with b/c and McNemar p,
   from the graded PolyBench reports (population rules of data/polybench/verdict.py).
"""
from __future__ import annotations

import glob
import json
import sys
from collections import Counter
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import contam_common as cc  # noqa: E402
from contam_score import anchor_classes, pairs_for  # noqa: E402

FOUR = {"gpt_headline": cc.ARMS["gpt"]["hl"], "gpt_logrep": cc.ARMS["gpt"]["lr"],
        "qwen36_k12": cc.ARMS["qwen36"]["k12"], "qwen3coder_k12": cc.ARMS["qwen3coder"]["k12"]}


def mcnemar(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def anchor_table() -> dict:
    cls = anchor_classes()
    side = Path(r"<TMP>\class_abc_500.json")
    if side.exists():
        s = cc.load_json(side)
        agree = sum(cls[i] == s["on"][i] + ">" + s["off"][i] for i in cls)
        print(f"[check] classes agree with design-authority side table: {agree}/{len(cls)}")
    out = {"transition_counts": dict(Counter(cls.values()))}
    for arm, (on, off) in FOUR.items():
        d = pairs_for(on, off)
        rows = {}
        for t in sorted(set(cls.values())):
            ids = [i for i in d if cls[i] == t]
            if len(ids) < 5:
                continue
            onr, _ = cc.report(on)
            offr, _ = cc.report(off)
            b = sum(1 for i in ids if i in offr and i not in onr)
            c = sum(1 for i in ids if i in onr and i not in offr)
            rows[t] = {"n": len(ids), "on": sum(i in onr for i in ids) / len(ids),
                       "off": sum(i in offr for i in ids) / len(ids),
                       "delta_pp": 100 * sum(d[i] for i in ids) / len(ids), "b": b, "c": c,
                       "mcnemar_p": mcnemar(b, c)}
        out[arm] = rows
        bc = rows.get("B>C", {})
        print(f"  {arm:15} B>C n={bc.get('n')} delta={bc.get('delta_pp', 0):+.1f}pp "
              f"b/c={bc.get('b')}/{bc.get('c')} p={bc.get('mcnemar_p', 1):.3g}")
    return out


def verbatim_table() -> dict:
    gold = cc.load_json(cc.VER / "gold_patches.json")
    preds = {"hl": "preds_local_gpt56sol_dedupOFF.jsonl", "lr": "preds_local_gptsol_logrep_dedupOFF.jsonl"}
    out, tot_n, tot_k = {}, 0, 0
    for k, pf in preds.items():
        on, off = cc.ARMS["gpt"][k]
        onr, ons = cc.report(on)
        offr, offs = cc.report(off)
        pr = {}
        for line in (cc.VER / pf).read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            pr[r["instance_id"]] = r["model_patch"] or ""
        wins = sorted((offr - onr) & ons & offs)
        w3 = [i for i in wins if len(cc.plus_lines(gold[i])) >= 3]
        rep = [i for i in w3 if cc.plus_lines(pr.get(i, "")) == cc.plus_lines(gold[i])]
        out[k] = {"off_only_wins": len(wins), "with_ge3_gold_plus": len(w3),
                  "reproduce_gold": len(rep), "ids": rep}
        tot_n += len(w3)
        tot_k += len(rep)
    out["pooled"] = f"{tot_k}/{tot_n}"
    print(f"  verbatim-gold pooled: {tot_k}/{tot_n}  {out['hl']['ids'] + out['lr']['ids']}")
    return out


def polybench_bc() -> dict:
    import pandas as pd
    files = sorted(glob.glob(cc.POLY_PARQUET_GLOB))
    df = pd.concat([pd.read_csv(f) if f.endswith(".csv") else pd.read_parquet(f) for f in files])
    df = df.drop_duplicates("instance_id")
    lang_col = "language" if "language" in df.columns else None
    packs = cc.load_json(cc.POLY / "polybench_packs.json")
    man = {x["instance_id"]: x for x in cc.load_json(cc.POLY / "instances_polybench.json")}
    py = [i for i, x in man.items() if x.get("language") == "Python"]
    gold = dict(zip(df["instance_id"], df["patch"]))
    cls = {}
    for i in py:
        if i in packs and i in gold and "dedupON" in packs[i] and "dedupOFF" in packs[i]:
            cls[i] = (cc.anchor_class(gold[i], packs[i]["dedupON"]["pack"]) + ">" +
                      cc.anchor_class(gold[i], packs[i]["dedupOFF"]["pack"]))
    n = len(cls)
    bc = sum(1 for v in cls.values() if v == "B>C")
    out = {"n_python_with_packs": n, "n_python_manifest": len(py), "B>C": bc,
           "prevalence": bc / n if n else None, "transition_counts": dict(Counter(cls.values())),
           "verified_reference": "80/500 = 16.0%", "lang_col": lang_col, "parquets": files}
    print(f"  PolyBench Python B>C: {bc}/{n} = {100 * bc / max(n, 1):.1f}% (Verified 80/500 = 16.0%)")
    out["classes"] = cls
    return out


PB = "data/polybench"


def polybench_bc_delta(cls: dict[str, str]) -> dict:
    """Item 4: Delta = OFF - ON within PolyBench-Python B>C for gpt-5.6-sol and Qwen3-Coder-30B,
    from the graded PolyBench reports, with the exact population rules of pb_gen/verdict.py:
    resolved = non-empty prediction AND graded resolved; analysed set = the model's gold-valid
    survivor list (gpt: minus the infra-hang casualties in off_killed_ids.txt)."""
    def nonempty(fn):
        s = set()
        for line in open(fn, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                if (r.get("model_patch") or "").strip():
                    s.add(r["instance_id"])
        return s

    def grades(d):
        g = {}
        for f in glob.glob(d + "/*_result.json"):
            x = json.load(open(f))
            g[x["instance_id"]] = bool(x.get("resolved"))
        return g

    def ids(fn):
        return [l.strip() for l in open(fn, encoding="utf-8") if l.strip()]

    models = {
        "gpt-5.6-sol": ("gpt", "data/polybench/grading/pb_gpt_ab_ON", "data/polybench/grading/pb_gpt_ab_OFF", "survivor_ids_gpt.txt", True),
        "Qwen3-Coder-30B": ("a3b", "data/polybench/grading/pb_ab_ON", "data/polybench/grading/pb_ab_OFF", "survivor_ids.txt", False),
    }
    bc_all = {i for i, v in cls.items() if v == "B>C"}
    out = {"n_BC_python": len(bc_all)}
    for name, (tag, gon, goff, surv, drop_killed) in models.items():
        neon = nonempty(f"{PB}/preds_local_pb_{tag}_dedupON.jsonl")
        neoff = nonempty(f"{PB}/preds_local_pb_{tag}_dedupOFF.jsonl")
        g_on, g_off = grades(gon), grades(goff)
        S = ids(f"{PB}/{surv}")
        if drop_killed:
            killed = set(ids(f"{PB}/off_killed_ids.txt"))
            S = [i for i in S if i not in killed]
        S = [i for i in S if i in bc_all]
        ron = {i for i in S if i in neon and g_on.get(i, False)}
        roff = {i for i in S if i in neoff and g_off.get(i, False)}
        b = len(roff - ron)
        c = len(ron - roff)
        out[name] = {"n": len(S), "on": len(ron), "off": len(roff),
                     "delta_pp": 100 * (len(roff) - len(ron)) / len(S) if S else None,
                     "b": b, "c": c, "mcnemar_p": mcnemar(b, c),
                     "excluded_from_24": sorted(bc_all - set(S))}
        print(f"  PolyBench-Python B>C {name:16} n={len(S)} ON={len(ron)} OFF={len(roff)} "
              f"delta={out[name]['delta_pp'] if S else float('nan'):+.1f}pp b/c={b}/{c} p={mcnemar(b, c):.3g}")
    return out


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("[1] anchor-transition table")
    a = anchor_table()
    print("[2] verbatim-gold table")
    v = verbatim_table()
    print("[3] PolyBench Python B->C prevalence")
    p = polybench_bc()
    print("[4] Delta within PolyBench-Python B->C (graded PolyBench reports)")
    d = polybench_bc_delta(p["classes"])
    cc.CONTAM.mkdir(parents=True, exist_ok=True)
    out = cc.CONTAM / "secondary.json"
    out.write_text(json.dumps({"anchor": a, "verbatim": v, "polybench": p, "polybench_bc_delta": d},
                              indent=1), encoding="utf-8")
    print(f"[wrote] {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
