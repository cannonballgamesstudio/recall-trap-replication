"""Analysis 7 (POST HOC restatement): single-retriever replication under the NEW primary
"sphinx-8475 Class-P cells scored as unresolved" (results_scored.json; n = 478 for contrasts on the T set, 500 for ON/OFF).

Two independent computations of every number:
  (1) the file of record, results/b1b3-replication/results_scored.json (b1b3_analyze.py --sphinx8475 scored);
  (2) a re-derivation here from the 13 raw arm-seed reports (resolved_ids/submitted_ids), with the registered instance
      bootstrap reproduced exactly (Python random seed 20261015), a second wild implementation (numpy, seed 20261014, CI by
      inversion), plus CR2-BM, exact sign-flip and the registered percentile cluster bootstrap (not in the file).
The old primary (exclude, results.json, n = 477) is printed alongside because the paper's current numbers come from it.
Also: funnel (empty-patch rates), nested subset, and the secondary mixed logit refit in scored mode.
"""
import json
import math
import random
import warnings

import numpy as np
import pandas as pd

from common3 import arm, repo, P5, PKG, wild, cr2_bm, signflip, pct_boot, mcnemar, pp, ci, fp, write_md, dump

warnings.filterwarnings("ignore")
RES = PKG / "results" / "b1b3-replication"
SC = json.loads((RES / "results_scored.json").read_text(encoding="utf-8"))
EX = json.loads((RES / "results.json").read_text(encoding="utf-8"))
UP = json.loads((RES / "results_upper.json").read_text(encoding="utf-8"))
T_IDS = sorted(set((P5 / "b1b3_ids_T.txt").read_text(encoding="utf-8").split()))
ALL_IDS = sorted(set((P5 / "b1b3_ids_all.txt").read_text(encoding="utf-8").split()))
SEEDS = {"ON": [0, 1, 2], "OFF": [0, 1, 2], "T": [0, 1, 2], "TM": [0, 1, 2], "P": [0]}
CONTRASTS = [("OFF", "ON"), ("OFF", "T"), ("T", "ON"), ("TM", "T"), ("OFF", "TM"), ("P", "OFF"), ("P", "T")]


def res(a, s):
    return arm(f"b_{a}_s{s}").res


def sub(a, s):
    return arm(f"b_{a}_s{s}").sub


def yavg(a, ids):
    return np.array([np.mean([i in res(a, s) for s in SEEDS[a]]) for i in ids], float)


def reg_boot(d, reps=10000, seed=20261015):
    rng = random.Random(seed)
    dl = list(d)
    bs = []
    for _ in range(reps):
        s = [dl[rng.randrange(len(dl))] for _ in dl]
        bs.append(sum(s) / len(s))
    s = sorted(bs)
    pct = lambda q: s[min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))]
    return (pct(0.025), pct(0.975)), (pct(0.05), pct(0.95))


out = {"contrasts": {}, "checks": []}
for item in CONTRASTS + [("OFF", "ON_all500")]:
    A, B = item
    Bn = "ON" if B == "ON_all500" else B
    ids0 = ALL_IDS if B == "ON_all500" else T_IDS
    key = "OFF-ON_all500" if B == "ON_all500" else f"{A}-{B}"
    ids = [i for i in ids0 if all(i in sub(A, s) for s in SEEDS[A]) and all(i in sub(Bn, s) for s in SEEDS[Bn])]
    ya, yb = yavg(A, ids), yavg(Bn, ids)
    d = ya - yb
    cl = [repo(i) for i in ids]
    c95, c90 = reg_boot(d)
    w = wild(d, cl, alphas=(0.05, 0.10))
    c2 = cr2_bm(d, cl)
    fl = signflip(d, cl)
    pb = pct_boot(d, cl)
    per = []
    pairs = list(zip(SEEDS[A], SEEDS[Bn])) if len(SEEDS[A]) == len(SEEDS[Bn]) else [(SEEDS[A][0], SEEDS[Bn][0])]
    for ja, jb in pairs:
        ii = [i for i in ids0 if i in sub(A, ja) and i in sub(Bn, jb)]
        b = sum(1 for i in ii if i in res(A, ja) and i not in res(Bn, jb))
        c = sum(1 for i in ii if i not in res(A, ja) and i in res(Bn, jb))
        per.append(dict(seeds=(ja, jb), n=len(ii), delta=(b - c) / len(ii), b=b, c=c, p=mcnemar(b, c)))
    r = dict(n=len(ids), rate_A=ya.mean(), rate_B=yb.mean(), delta=d.mean(), reg_ci95=c95, reg_ci90=c90,
             wild_p=w["p"], wild_ci95=w["ci95"], wild_ci90=w["ci90"], cr2_p=c2["p"], cr2_ci95=c2["ci95"], cr2_ci90=c2["ci90"],
             flip_p=fl["p"], pct_ci95=pb["ci95"], pct_p_le0=pb["p_le0"], per_seed=per,
             between_seed_sd=(float(np.std([x["delta"] for x in per], ddof=1)) if len(per) > 1 else None))
    out["contrasts"][key] = r
    f = SC["contrasts"][key]["pooled"]
    out["checks"].append(dict(contrast=key, n=(r["n"], f["n_inst"]), delta=(100 * r["delta"], f["delta_pp"]),
                              ci95=([100 * x for x in c95], f["ci95_pp"]), ci90=([100 * x for x in c90], f["ci90_pp"]),
                              wild_p=(r["wild_p"], f["wild_cluster_repo"]["p_two_sided"]),
                              per_seed_bc=([(x["b"], x["c"]) for x in per], [(x["b_Awins"], x["c_Bwins"]) for x in SC["contrasts"][key]["per_seed"]]),
                              match=(abs(100 * r["delta"] - f["delta_pp"]) < 1e-9 and all(abs(100 * a - b) < 1e-9 for a, b in zip(c95, f["ci95_pp"]))
                                     and [(x["b"], x["c"]) for x in per] == [(x["b_Awins"], x["c_Bwins"]) for x in SC["contrasts"][key]["per_seed"]])))

# rates per arm on the T set (pooled over seeds) and empties
rates, empt = {}, {}
for a in SEEDS:
    for setname, ids in (("T set (478)", T_IDS), ("all 500", ALL_IDS)):
        if a in ("T", "TM", "P") and setname == "all 500":
            continue
        rates[(a, setname)] = float(np.mean([np.mean([i in res(a, s) for s in SEEDS[a]]) for i in ids]))
        empt[(a, setname)] = float(np.mean([np.mean([i in arm(f"b_{a}_s{s}").empty for s in SEEDS[a]]) for i in ids]))
out["rates"] = {f"{a} | {s}": v for (a, s), v in rates.items()}
out["empty_rates"] = {f"{a} | {s}": v for (a, s), v in empt.items()}
v = SC["verdict"]
out["verdict_file"] = v
cs = out["contrasts"]
out["verdict_mine"] = dict(G=cs["OFF-ON"]["delta"], depth=cs["OFF-T"]["delta"], trim=cs["T-ON"]["delta"],
                           share=cs["OFF-T"]["delta"] / cs["OFF-ON"]["delta"],
                           identity_holds=abs(cs["OFF-T"]["delta"] + cs["T-ON"]["delta"] - cs["OFF-ON"]["delta"]) < 1e-12)

# secondary mixed logit, scored mode (same specification as b1b3_glmm.py, without the Class-P exclusion)
try:
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    gl = {}
    for A, B in [("OFF", "ON"), ("OFF", "T"), ("T", "ON"), ("TM", "T"), ("OFF", "TM")]:
        rows = []
        for j in (0, 1, 2):
            for i in T_IDS:
                if i in sub(A, j) and i in sub(B, j):
                    rows.append({"inst": i, "seed": j, "armA": 1, "y": int(i in res(A, j))})
                    rows.append({"inst": i, "seed": j, "armA": 0, "y": int(i in res(B, j))})
        df = pd.DataFrame(rows)
        m = BinomialBayesMixedGLM.from_formula("y ~ armA", {"inst": "0 + C(inst)", "seed": "0 + C(seed)", "seed_arm": "0 + C(seed):armA"}, df)
        r = m.fit_vb()
        gl[f"{A}-{B}"] = dict(n_rows=len(df), mean=float(r.fe_mean[1]), sd=float(r.fe_sd[1]), z=float(r.fe_mean[1] / r.fe_sd[1]))
    out["glmm_scored"] = gl
except Exception as e:  # noqa
    out["glmm_scored"] = {"error": str(e)}

# ---------------------------------------------------------------- markdown
L = ["## Analysis 7 — Single-retriever replication restated under the new primary (Class-P cells scored unresolved)", "",
     "File of record: `results/b1b3-replication/results_scored.json` (sha256 A008ABB5…4A9B, identical in the package and in the original run directory). "
     "Every number below was recomputed independently from the 13 raw reports; the 'match' column is the exact comparison (Δ, registered 95% CI, per-seed b/c). "
     "Δ and CIs in pp; CIs are the registered instance bootstrap (percentile, B = 10,000) unless labelled. Wild p: file = b1b3_analyze.py (Python RNG); "
     "mine = numpy implementation, independent weights (MC SE ≈ 0.0015 at p ≈ 0.02).", "",
     "| contrast | n | rate A / B | Δ | 95% CI (registered) | 90% CI | wild p (file / mine) | wild 95% CI (mine) | CR2 p; 95% CI | flip p | pct-cluster 95% CI | per-seed Δ (b/c, McNemar p) | match |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for k, r in cs.items():
    f = SC["contrasts"][k]["pooled"]
    chk = [c for c in out["checks"] if c["contrast"] == k][0]
    ps = "; ".join(f"{100*x['delta']:+.1f} ({x['b']}/{x['c']}, {fp(x['p'])})" for x in r["per_seed"])
    L.append(f"| {k} | {r['n']} | {100*r['rate_A']:.2f}% / {100*r['rate_B']:.2f}% | {pp(r['delta'], 2)} | {ci(r['reg_ci95'], 2)} | {ci(r['reg_ci90'], 2)} | "
             f"{fp(f['wild_cluster_repo']['p_two_sided'])} / {fp(r['wild_p'])} | {ci(r['wild_ci95'], 2)} | {fp(r['cr2_p'])}; {ci(r['cr2_ci95'], 2)} | {fp(r['flip_p'])} | "
             f"{ci(r['pct_ci95'], 2)} | {ps} | {'yes' if chk['match'] else 'NO'} |")
L.append("")
L += [f"Verdict (file): {v['verdict']}; G {v['G_pp']:+.2f}, depth {v['depth_pp']:+.2f}, trim {v['trim_pp']:+.2f}, depth share {100*v['depth_share']:.1f}%. "
      f"Mine: depth share {100*out['verdict_mine']['share']:.1f}%; identity depth + trim = G holds exactly: {out['verdict_mine']['identity_holds']}. "
      f"Predictions (file): {SC['predictions']}.", "",
      f"Between-seed SD of OFF−ON: {100*cs['OFF-ON']['between_seed_sd']:.2f}pp (file variance {SC['contrasts']['OFF-ON']['pooled']['between_seed_var_delta_pp2']:.3f} pp²).", ""]
L += ["Pooled resolve rates (mean over seeds) and empty-patch rates:", "", "| arm | T set (478): resolve / empty | all 500: resolve / empty |", "|---|---|---|"]
for a in SEEDS:
    t = f"{100*rates[(a, 'T set (478)')]:.2f}% / {100*empt[(a, 'T set (478)')]:.1f}%"
    al = f"{100*rates[(a, 'all 500')]:.2f}% / {100*empt[(a, 'all 500')]:.1f}%" if (a, "all 500") in rates else "—"
    L.append(f"| {a} | {t} | {al} |")
L.append("")
L += [f"Nested subset (every T chunk among its file's OFF chunks; file of record): n = {SC['nested_subset_n']}: "
      + "; ".join(f"{k} {SC['nested_subset'][k]['pooled']['delta_pp']:+.2f}" for k in SC["nested_subset"]) + ". "
      f"Exclude mode: n = {EX['nested_subset_n']}: " + "; ".join(f"{k} {EX['nested_subset'][k]['pooled']['delta_pp']:+.2f}" for k in EX["nested_subset"]) + ".", ""]
L += ["Old primary (exclude, results.json; the source of the paper's current numbers) vs new primary (scored) vs upper bound:", "",
      "| contrast | exclude (n) Δ [95% CI]; wild p | **scored (n) Δ [95% CI]; wild p** | upper (n) Δ [95% CI] |", "|---|---|---|---|"]
for k in SC["contrasts"]:
    e, s, u = EX["contrasts"][k]["pooled"], SC["contrasts"][k]["pooled"], UP["contrasts"][k]["pooled"]
    L.append(f"| {k} | ({e['n_inst']}) {e['delta_pp']:+.2f} [{e['ci95_pp'][0]:+.2f}, {e['ci95_pp'][1]:+.2f}]; {e['wild_cluster_repo']['p_two_sided']:.4f} | "
             f"**({s['n_inst']}) {s['delta_pp']:+.2f} [{s['ci95_pp'][0]:+.2f}, {s['ci95_pp'][1]:+.2f}]; {s['wild_cluster_repo']['p_two_sided']:.4f}** | "
             f"({u['n_inst']}) {u['delta_pp']:+.2f} [{u['ci95_pp'][0]:+.2f}, {u['ci95_pp'][1]:+.2f}] |")
L.append("")
if "error" not in out["glmm_scored"]:
    L += ["Secondary mixed logit (VB; same specification as b1b3_glmm.py) refit in scored mode — arm effect posterior mean / SD (log-odds) and mean/SD:", "",
          "| contrast | rows | mean | SD | mean/SD |", "|---|---|---|---|---|"]
    for k, g in out["glmm_scored"].items():
        L.append(f"| {k} | {g['n_rows']} | {g['mean']:+.3f} | {g['sd']:.3f} | {g['z']:+.1f} |")
    L.append("")
write_md("s7_replication", "\n".join(L) + "\n")
dump("s7_replication", out)
