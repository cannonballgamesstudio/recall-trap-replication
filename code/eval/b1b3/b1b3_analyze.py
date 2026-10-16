#!/usr/bin/env python3
"""LOCAL-B1B3-ADDENDUM-PREREG §7-§9 analysis.

Refuses to analyse any arm-seed whose report has error_ids other than its registered Class-P set
(SPHINX8475-RULING-2026-10-16). Modes: exclude (PRIMARY) -> results.json; scored -> results_scored.json;
upper -> results_upper.json; --compare prints them side by side with robustness flags.

  python b1b3_analyze.py --sphinx8475 exclude|scored|upper ;  python b1b3_analyze.py --compare
"""
from __future__ import annotations
import json, math, random, sys
from pathlib import Path
from scipy.stats import binomtest

import os
PKG = Path(__file__).resolve().parents[3]   # package root
P = Path(os.environ.get("B1B3_ROOT", PKG / "work" / "p5"))   # flat view built by code/prepare_data.py
OUTD = Path(os.environ.get("B1B3_OUT", PKG / "results" / "b1b3-replication"))
SEEDS = {"ON": [0, 1, 2], "OFF": [0, 1, 2], "T": [0, 1, 2], "TM": [0, 1, 2], "P": [0]}
B_BOOT, B_WILD, RNG_SEED = 10000, 9999, 20261015
WEBB = [-(1.5 ** 0.5), -1.0, -(0.5 ** 0.5), 0.5 ** 0.5, 1.0, 1.5 ** 0.5]
CONTRASTS = [("OFF", "ON"), ("OFF", "T"), ("T", "ON"), ("TM", "T"), ("OFF", "TM"), ("P", "OFF"), ("P", "T")]


# SPHINX8475-RULING-2026-10-16 §4/§5.3: harness errors classified Class P (patch-induced; gold resolves in the
# same environment; identical in 3 passes; mechanism in the patch). Owner decision 2026-10-16: PRIMARY = the
# instance excluded from every arm and seed; sensitivity 1 = Class-P cells scored attempted & unresolved;
# sensitivity 2 = Class-P cells scored resolved (upper bound).
# Keyed (arm, seed) -> set of instance ids. Any error id NOT registered here aborts the analysis.
S8475 = "sphinx-doc__sphinx-8475"
CLASS_P = {("ON", 0): {S8475}, ("OFF", 2): {S8475}, ("T", 0): {S8475}, ("T", 1): {S8475},
           ("TM", 1): {S8475}}   # TM s01 classified Class P 2026-10-16 (§12 D-8475)
MODE = "exclude"            # --sphinx8475 {exclude (PRIMARY, owner 2026-10-16), scored, upper}
CLASS_P_INSTANCES = {i for v in CLASS_P.values() for i in v}


def load_arm(arm):
    """-> {seed: (submitted set, resolved set)} or None if any report missing.
    Aborts unless the report's error_ids equal exactly the registered Class-P set for (arm, seed)."""
    out = {}
    for j in SEEDS[arm]:
        tag = f"{arm}_s{j:02d}"
        preds = P / f"preds_local_b1b3q30_{tag}.jsonl"
        rep = P / f"local_b1b3q30_{tag}.b1b3_{tag}.json"
        if not (preds.exists() and rep.exists()):
            return None
        r = json.loads(rep.read_text(encoding="utf-8"))
        expected = CLASS_P.get((arm, j), set())
        got = set(r.get("error_ids", []))
        if got != expected or r.get("error_instances", 0) != len(expected):
            raise SystemExit(f"ABORT: {rep.name} error_ids={sorted(got)} != registered Class-P {sorted(expected)}"
                             " -> regrade / classify first")
        sub = {json.loads(l)["instance_id"] for l in preds.read_text(encoding="utf-8").splitlines() if l.strip()}
        res = set(r.get("resolved_ids", []))
        assert not (res & expected), f"Class-P cell unexpectedly resolved: {tag}"
        assert expected <= sub, f"Class-P instance not submitted: {tag}"
        if MODE == "upper":                     # sensitivity 2: Class-P cells scored resolved
            res |= expected
        out[j] = (sub, res)
    return out


def funnel(arm):
    """§7.3 funnel per arm-seed from reports: submitted, empty, non-empty graded, Class-P harness timeout."""
    rows = {}
    for j in SEEDS[arm]:
        tag = f"{arm}_s{j:02d}"
        rep = P / f"local_b1b3q30_{tag}.b1b3_{tag}.json"
        if not rep.exists():
            continue
        r = json.loads(rep.read_text(encoding="utf-8"))
        rows[tag] = {"submitted": r["submitted_instances"], "empty_patch": r["empty_patch_instances"],
                     "graded_completed": r["completed_instances"],
                     "applied_to_test_harness_timeout_classP": len(CLASS_P.get((arm, j), set())),
                     "resolved": r["resolved_instances"]}
    return rows


def mcnemar(a_res, b_res, ids):
    b = sum(1 for i in ids if i in a_res and i not in b_res)   # A wins
    c = sum(1 for i in ids if i not in a_res and i in b_res)   # B wins
    p = binomtest(b, b + c, 0.5).pvalue if b + c else 1.0
    return b, c, p


def pct(xs, q):
    s = sorted(xs)
    return s[min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))]


def wild_cluster(d, ids, repo_of):
    """Two-sided wild-cluster bootstrap-t p (Webb 6-pt, repo clusters, null imposed) + CR1 SE."""
    obs = [(repo_of[i], d[i]) for i in ids]
    cl = sorted({c for c, _ in obs}); G, N = len(cl), len(obs)

    def tstat(vals):
        m = sum(v for _, v in vals) / N
        sg = {}
        for c, v in vals:
            sg[c] = sg.get(c, 0.0) + (v - m)
        var = G / (G - 1) * sum(s * s for s in sg.values()) / (N * N)
        return m, (var ** 0.5 if var > 0 else 0.0)
    m0, se0 = tstat(obs)
    t0 = m0 / se0 if se0 else 0.0
    rng = random.Random(RNG_SEED)
    hits = 0
    for _ in range(B_WILD):
        w = {c: WEBB[rng.randrange(6)] for c in cl}
        m, se = tstat([(c, w[c] * v) for c, v in obs])
        hits += abs(m / se if se else 0.0) >= abs(t0)
    return {"G": G, "se_cr1": se0, "p_two_sided": (1 + hits) / (B_WILD + 1)}


def contrast(A, B, a, b, base_ids, repo_of):
    """A,B: arm names; a,b: loaded arms. Per-seed (paired j) + pooled (seed-averaged per instance)."""
    res = {"contrast": f"{A}-{B}", "per_seed": []}
    pairs = [(ja, jb) for ja, jb in zip(SEEDS[A], SEEDS[B])] if len(SEEDS[A]) == len(SEEDS[B]) else \
        [(SEEDS[A][0], SEEDS[B][0])]
    for ja, jb in pairs:
        ids = sorted(i for i in base_ids if i in a[ja][0] and i in b[jb][0])
        bb, cc, p = mcnemar(a[ja][1], b[jb][1], ids)
        ra = sum(i in a[ja][1] for i in ids) / len(ids); rb = sum(i in b[jb][1] for i in ids) / len(ids)
        res["per_seed"].append({"seeds": [ja, jb], "n": len(ids), "rate_A": ra, "rate_B": rb,
                                "delta_pp": 100 * (ra - rb), "b_Awins": bb, "c_Bwins": cc, "mcnemar_p": p})
    ids = sorted(i for i in base_ids if all(i in a[j][0] for j in SEEDS[A]) and all(i in b[j][0] for j in SEEDS[B]))
    ya = {i: sum(i in a[j][1] for j in SEEDS[A]) / len(SEEDS[A]) for i in ids}
    yb = {i: sum(i in b[j][1] for j in SEEDS[B]) / len(SEEDS[B]) for i in ids}
    d = {i: ya[i] - yb[i] for i in ids}
    est = sum(d.values()) / len(ids)
    rng = random.Random(RNG_SEED)
    dl = [d[i] for i in ids]
    bs = []
    for _ in range(B_BOOT):
        s = [dl[rng.randrange(len(dl))] for _ in dl]
        bs.append(sum(s) / len(s))
    ps = [x["delta_pp"] for x in res["per_seed"]]
    res["pooled"] = {"n_inst": len(ids), "rate_A": sum(ya.values()) / len(ids), "rate_B": sum(yb.values()) / len(ids),
                     "delta_pp": 100 * est,
                     "ci95_pp": [100 * pct(bs, 0.025), 100 * pct(bs, 0.975)],
                     "ci90_pp": [100 * pct(bs, 0.05), 100 * pct(bs, 0.95)],
                     "wild_cluster_repo": wild_cluster(d, ids, repo_of),
                     "between_seed_var_delta_pp2": (sum((x - sum(ps) / len(ps)) ** 2 for x in ps) / (len(ps) - 1))
                     if len(ps) > 1 else None}
    lo, hi = res["pooled"]["ci95_pp"]
    res["pooled"]["significant_95"] = lo > 0 or hi < 0
    lo9, hi9 = res["pooled"]["ci90_pp"]
    res["pooled"]["tost_equiv_3pp"] = lo9 > -3 and hi9 < 3
    return res, d


def nested_subset(t_ids):
    """Gate-1 instances where each T chunk (= ON chunk of an OFF file) appears among that file's OFF chunks."""
    prov = json.loads((P / "b1b3_prov.json").read_text(encoding="utf-8"))
    k = lambda h: (h["file"], h["line"], (h.get("snippet") or "").rstrip("\n"))
    keep = set()
    for iid in t_ids:
        on, off = prov[iid]["ON12"]["hits"], prov[iid]["OFF12"]["hits"]
        on_by = {h["file"]: h for h in on}
        offk = {k(h) for h in off}
        if all(k(on_by[f]) in offk for f in {h["file"] for h in off}):
            keep.add(iid)
    return keep


OUTFILE = {"exclude": "results.json", "scored": "results_scored.json", "upper": "results_upper.json"}


def predictions(out):
    """§8 verdict + §9 predictions 1-4 as comparable values (None if not computable)."""
    c = out["contrasts"]
    g = lambda k: c[k]["pooled"] if k in c else None
    return {
        "verdict_s8": out.get("verdict", {}).get("verdict"),
        "pred1_depth_carries": (out.get("verdict", {}).get("verdict") == "depth carries the effect") if "verdict" in out else None,
        "pred2_trim_TOST3": g("T-ON")["tost_equiv_3pp"] if g("T-ON") else None,
        "pred3_TM_eq_T_TOST3": g("TM-T")["tost_equiv_3pp"] if g("TM-T") else None,
        "pred4_OFF_gt_TM": (g("OFF-TM")["ci95_pp"][0] > 0) if g("OFF-TM") else None,
    }


def run(mode):
    global MODE
    MODE = mode
    cells = {c["instance_id"]: c for c in json.loads((P / "instances_verified.json").read_text(encoding="utf-8"))}
    repo_of = {i: c["repo"] for i, c in cells.items()}
    t_ids = set((P / "b1b3_ids_T.txt").read_text(encoding="utf-8").split())
    all_ids = set((P / "b1b3_ids_all.txt").read_text(encoding="utf-8").split())
    if mode == "exclude":                       # PRIMARY (owner): instance removed from every arm and seed
        t_ids -= CLASS_P_INSTANCES; all_ids -= CLASS_P_INSTANCES
    arms = {a: load_arm(a) for a in SEEDS}
    out = {"mode": mode, "class_p": {f"{a}_s{j:02d}": sorted(v) for (a, j), v in CLASS_P.items()},
           "available": {a: v is not None for a, v in arms.items()}, "contrasts": {},
           "funnel": {a: funnel(a) for a in SEEDS}}
    for A, B in CONTRASTS:
        if arms[A] is None or arms[B] is None:
            continue
        r, _ = contrast(A, B, arms[A], arms[B], t_ids, repo_of)
        out["contrasts"][f"{A}-{B}"] = r
    if arms["ON"] and arms["OFF"]:
        out["contrasts"]["OFF-ON_all500"], _ = contrast("OFF", "ON", arms["OFF"], arms["ON"], all_ids, repo_of)
    # D-TM pre-registered secondary: nested subset (every T chunk among its file's OFF chunks); no verdict.
    nested = nested_subset(t_ids)
    out["nested_subset_n"] = len(nested)
    out["nested_subset"] = {}
    for A, B in CONTRASTS:
        if ("T" in (A, B) or "TM" in (A, B)) and arms[A] is not None and arms[B] is not None:
            out["nested_subset"][f"{A}-{B}"], _ = contrast(A, B, arms[A], arms[B], nested, repo_of)
    c = out["contrasts"]
    if all(k in c for k in ("OFF-ON", "OFF-T", "T-ON")):
        G = c["OFF-ON"]["pooled"]["delta_pp"]
        dd, dt = c["OFF-T"]["pooled"]["delta_pp"], c["T-ON"]["pooled"]["delta_pp"]
        if G > 0 and dd >= 0.6 * G and c["OFF-T"]["pooled"]["significant_95"]:
            v = "depth carries the effect"
        elif G > 0 and dt >= 0.6 * G and c["T-ON"]["pooled"]["significant_95"]:
            v = "file trimming carries the effect"
        else:
            v = "both components contribute; the partition is not resolved at this n"
        out["verdict"] = {"G_pp": G, "depth_pp": dd, "trim_pp": dt, "depth_share": dd / G if G else None,
                          "trim_share": dt / G if G else None, "verdict": v}
    out["predictions"] = predictions(out)
    OUTD.mkdir(exist_ok=True)
    (OUTD / OUTFILE[mode]).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"=== mode={mode} -> {OUTFILE[mode]}")
    for k, r in list(c.items()) + [("nested:" + k2, v) for k2, v in out["nested_subset"].items()]:
        p = r["pooled"]
        print(f"{k:14s} n={p['n_inst']:3d} A={100*p['rate_A']:.2f}% B={100*p['rate_B']:.2f}% "
              f"Δ={p['delta_pp']:+.2f}pp 95%[{p['ci95_pp'][0]:+.2f},{p['ci95_pp'][1]:+.2f}] "
              f"90%[{p['ci90_pp'][0]:+.2f},{p['ci90_pp'][1]:+.2f}] wild-p={p['wild_cluster_repo']['p_two_sided']:.4f} "
              f"TOST±3={p['tost_equiv_3pp']}  per-seed=" +
              " ".join(f"{s['delta_pp']:+.1f}(b{s['b_Awins']}/c{s['c_Bwins']},p={s['mcnemar_p']:.3g})" for s in r["per_seed"]))
    if "verdict" in out:
        print("VERDICT:", json.dumps(out["verdict"]))
    return out


def compare():
    """Side-by-side exclude (primary) / scored / upper for every contrast + robustness flags (ruling §5.3)."""
    res = {m: json.loads((OUTD / f).read_text(encoding="utf-8")) for m, f in OUTFILE.items()}
    print("=== side by side: pooled Δpp [95% CI]  (PRIMARY exclude | sens1 scored-unresolved | sens2 upper)")
    rows = {}
    for k in res["exclude"]["contrasts"]:
        cells = []
        for m in OUTFILE:
            p = res[m]["contrasts"][k]["pooled"]
            cells.append(f"{p['delta_pp']:+.2f} [{p['ci95_pp'][0]:+.2f},{p['ci95_pp'][1]:+.2f}] n={p['n_inst']}")
        rows[k] = cells
        print(f"{k:14s} " + " | ".join(cells))
    print("=== robustness flags (§8 verdict, §9 predictions)")
    flags = {}
    for k in res["exclude"]["predictions"]:
        vals = [res[m]["predictions"][k] for m in OUTFILE]
        flags[k] = {"primary_exclude": vals[0], "sens1_scored": vals[1], "sens2_upper": vals[2],
                    "robust": len({json.dumps(v) for v in vals}) == 1}
        print(f"{k:22s} primary={vals[0]!s:60.60s} robust={'yes' if flags[k]['robust'] else 'NO (not robust to sphinx-8475)'}")
    (OUTD / "results_compare.json").write_text(json.dumps({"rows": rows, "flags": flags}, indent=1), encoding="utf-8")


def main() -> int:
    import argparse
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--sphinx8475", choices=["exclude", "scored", "upper"], default="exclude",
                    help="exclude = PRIMARY (owner 2026-10-16); scored = sensitivity 1; upper = sensitivity 2")
    ap.add_argument("--compare", action="store_true", help="print primary/exclude/upper side by side (after all three ran)")
    a = ap.parse_args()
    if a.compare:
        compare(); return 0
    run(a.sphinx8475)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
