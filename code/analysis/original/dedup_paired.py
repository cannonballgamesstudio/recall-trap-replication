#!/usr/bin/env python3
"""Paired dedup analysis from two swebench report JSONs (ON vs OFF).

Empties/uncompleted counted as FAILURES (a model that emits no patch did not
resolve the issue) over the INTERSECTION of submitted ids, so the McNemar pairing
is honest. Prints resolve rates, the delta, discordant cells, and exact-binomial p.
"""
import json, sys
from math import comb
from pathlib import Path

P = Path("data/swe-verified")


def resolved_set(model):
    # swebench writes <model_name_or_path>.<run_id>.json; run_id may differ from model.
    # Match the report whose name starts with the model label.
    cands = sorted(P.glob(f"{model}.*.json")) + ([P / f"{model}.json"] if (P / f"{model}.json").exists() else [])
    for f in cands:
        d = json.loads(f.read_text())
        if "resolved_ids" in d:
            return set(d.get("resolved_ids", [])), set(d.get("submitted_ids", []))
    return None, None


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * p)


def main():
    on_id, off_id = sys.argv[1], sys.argv[2]
    label = sys.argv[3] if len(sys.argv) > 3 else f"{on_id} vs {off_id}"
    on_res, on_sub = resolved_set(on_id)
    off_res, off_sub = resolved_set(off_id)
    if on_res is None or off_res is None:
        print(f"[WAIT] missing report: ON={on_res is not None} OFF={off_res is not None}")
        return 1
    ids = sorted(on_sub & off_sub)
    n = len(ids)
    on_r = sum(i in on_res for i in ids)
    off_r = sum(i in off_res for i in ids)
    # discordant: OFF resolved & ON not (b), ON resolved & OFF not (c)
    b = sum((i in off_res) and (i not in on_res) for i in ids)
    c = sum((i in on_res) and (i not in off_res) for i in ids)
    p = mcnemar_exact(b, c)
    print(f"=== {label}  (paired n={n}) ===")
    print(f"  dedup-ON  resolved: {on_r}/{n} = {on_r/n*100:.1f}%")
    print(f"  dedup-OFF resolved: {off_r}/{n} = {off_r/n*100:.1f}%")
    print(f"  delta (OFF-ON): {(off_r-on_r)/n*100:+.1f}pp")
    print(f"  discordant: OFF-only={b}  ON-only={c}")
    print(f"  McNemar exact p = {p:.4g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
