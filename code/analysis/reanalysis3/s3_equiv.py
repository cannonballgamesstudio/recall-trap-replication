"""Analysis 3 (POST HOC): TOST equivalence under REPOSITORY-CLUSTERED 90% CIs, m*, and two gpt trim diagnostics.

TOST at alpha = 0.05 per side <=> the 90% CI lies inside (-m, +m). m* = max(|lo90|, |hi90|) = smallest symmetric
margin that passes (strictly: any m > m*). The +-3pp margin was itself chosen post hoc (re-review B).
Replication rows: single-retriever replication, primary = sphinx-8475 Class-P cells scored unresolved
(results_scored.json; n = 478); seed-averaged per-instance d (3 seeds per arm); the exclude-mode (n = 477) row is shown
for reference. Headline rows: one draw of T against the headline arms on the 473 gate-passing instances.
CI types: instance (registered: replication = percentile instance bootstrap B=10,000 Python random seed 20261015 as in
b1b3_analyze.py; headline = Wald paired SE), wild (WCR Webb B=9,999 inverted at alpha=0.10), CR2-BM (t_df),
registered percentile repository bootstrap (5,000 reps, seed 20260714; 5th/95th percentiles).
"""
import json
import random

import numpy as np

from common3 import (arm, dvec, repo, P5, VIOL, iid, wild, cr2_bm, pct_boot, mcnemar, bc, pp, ci, fp, write_md, dump)

T_IDS = set((P5 / "b1b3_ids_T.txt").read_text(encoding="utf-8").split())
S8475 = "sphinx-doc__sphinx-8475"


def seedavg(armname, seeds, ids):
    rs = [arm(f"b_{armname}_s{s}").res for s in seeds]
    return np.array([np.mean([i in r for r in rs]) for i in ids], float)


def registered_inst_boot(d, reps=10000, seed=20261015):
    """b1b3_analyze.py::contrast bootstrap, reproduced exactly (pct with round-half index rule)."""
    rng = random.Random(seed)
    dl = list(d)
    bs = []
    for _ in range(reps):
        s = [dl[rng.randrange(len(dl))] for _ in dl]
        bs.append(sum(s) / len(s))
    s = sorted(bs)
    pct = lambda q: s[min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))]
    return dict(ci95=(pct(0.025), pct(0.975)), ci90=(pct(0.05), pct(0.95)))


def tost_row(label, d, ids, inst90=None, inst_label="Wald"):
    cl = [repo(i) for i in ids]
    w = wild(d, cl, alphas=(0.10, 0.05))
    c2 = cr2_bm(d, cl)
    pb = pct_boot(d, cl)
    ii = iid(d)
    cis = {"instance (" + inst_label + ")": inst90 if inst90 is not None else ii["ci90"],
           "instance Wald": ii["ci90"], "wild": w["ci90"], "CR2-BM": c2["ci90"], "pct cluster (registered)": pb["ci90"]}
    r = dict(label=label, n=len(d), delta=float(d.mean()), ci90=cis, wild_pieces=w.get("ci90_pieces"),
             cr2_df=c2["df"], wild_p=w["p"], cr2_p=c2["p"])
    r["mstar"] = {k: max(abs(v[0]), abs(v[1])) for k, v in cis.items()}
    r["pass3"] = {k: (v[0] > -0.03 and v[1] < 0.03) for k, v in cis.items()}
    if np.all(np.isin(d, (-1, 0, 1))):
        b, c = bc(d)
        r.update(b=b, c=c, mcnemar_p=mcnemar(b, c))
    return r


rows = []
checks = {}
# ---------------- replication (scored primary n=478, and exclude n=477)
sc = json.loads((P5.parent.parent / "results" / "b1b3-replication" / "results_scored.json").read_text(encoding="utf-8"))
for mode, base in (("scored primary", sorted(T_IDS)), ("exclude (old primary)", sorted(T_IDS - {S8475}))):
    for A, B, lab in (("T", "ON", "replication T−ON (trim)"), ("TM", "T", "replication TM−T (tokens)")):
        d = seedavg(A, [0, 1, 2], base) - seedavg(B, [0, 1, 2], base)
        rb = registered_inst_boot(d)
        r = tost_row(f"{lab}, {mode}, n={len(base)}", d, base, inst90=rb["ci90"], inst_label="registered bootstrap")
        rows.append(r)
        if mode == "scored primary":
            p = sc["contrasts"][f"{A}-{B}"]["pooled"]
            checks[f"{A}-{B}"] = dict(mine_delta=100 * r["delta"], file_delta=p["delta_pp"], mine_ci90=[100 * x for x in rb["ci90"]],
                                      file_ci90=p["ci90_pp"], mine_ci95=[100 * x for x in rb["ci95"]], file_ci95=p["ci95_pp"])

# ---------------- headline T-ON on the 473
for lab, onk, offk, tk in (("Qwen3-Coder-30B headline T−ON", "qc_ON", "qc_OFF", "qc_T"),
                           ("gpt T−ON vs logged re-run ON", "gpt_lr_ON", "gpt_lr_OFF", "gpt_T"),
                           ("gpt T−ON vs discovery ON (registered TB §9 reference)", "gpt_hl_ON", "gpt_hl_OFF", "gpt_T")):
    A_on, A_off, A_t = arm(onk), arm(offk), arm(tk)
    ids = sorted((A_on.sub & A_off.sub & A_t.sub) - set(VIOL))
    d, ids = dvec(ids, A_t.res, A_on.res)
    r = tost_row(f"{lab}, n={len(ids)}", d, ids)
    rows.append(r)

# ---------------- gpt trim split django / non-django, and both-non-empty pairs
diag = []
for lab, onk, offk in (("re-run ON", "gpt_lr_ON", "gpt_lr_OFF"), ("discovery ON", "gpt_hl_ON", "gpt_hl_OFF"),
                       ("Qwen3-Coder ON (for comparison)", "qc_ON", "qc_OFF")):
    tk = "qc_T" if lab.startswith("Qwen") else "gpt_T"
    A_on, A_off, A_t = arm(onk), arm(offk), arm(tk)
    ids = sorted((A_on.sub & A_off.sub & A_t.sub) - set(VIOL))
    d, ids = dvec(ids, A_t.res, A_on.res)
    dj = np.array([repo(i) == "django/django" for i in ids])
    ne = np.array([(i not in A_t.empty) and (i not in A_on.empty) for i in ids])
    ent = dict(ref=lab, n=len(ids), delta=float(d.mean()))
    for nm, m in (("django", dj), ("non-django", ~dj), ("both non-empty", ne)):
        b, c = bc(d[m])
        ent[nm] = dict(n=int(m.sum()), delta=float(d[m].mean()), b=b, c=c, mcnemar_p=mcnemar(b, c),
                       contribution_to_full_pp=float(d[m].sum() / len(d)))
    # empties of each arm
    ent["empty_T"] = sum(i in A_t.empty for i in ids)
    ent["empty_ON"] = sum(i in A_on.empty for i in ids)
    ent["T_errors"] = sorted(A_t.err & set(ids))
    diag.append(ent)

out = dict(rows=rows, check_vs_results_scored=checks, gpt_trim_diagnostics=diag)

L = ["## Analysis 3 — Equivalence under repository-clustered 90% CIs, m*, gpt trim diagnostics (POST HOC)", "",
     "TOST (α = 0.05 per side) passes at margin m iff the 90% CI lies inside (−m, +m); m* = max(|lo|, |hi|) of the 90% CI is the smallest margin that passes. "
     "The ±3pp margin was chosen post hoc. Replication = seed-averaged d over 3 seeds; primary = sphinx-8475 Class-P cells scored unresolved (n = 478). "
     "Instance CI for the replication = the registered percentile instance bootstrap (b1b3_analyze.py, B = 10,000, seed 20261015), reproduced exactly.", "",
     "| contrast | n | Δ (pp) | b/c | instance 90% CI | wild 90% CI | CR2-BM 90% CI (df) | registered pct-cluster 90% CI | ±3pp passes (inst / wild / CR2 / pct) | **m* (inst / wild / CR2 / pct)** |",
     "|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    k_inst = [k for k in r["ci90"] if k.startswith("instance (")][0]
    keys = [k_inst, "wild", "CR2-BM", "pct cluster (registered)"]
    passes = " / ".join("PASS" if r["pass3"][k] else "fail" for k in keys)
    ms = " / ".join(f"{100*r['mstar'][k]:.2f}" for k in keys)
    bcs = f"{r['b']}/{r['c']}" if "b" in r else "—"
    L.append(f"| {r['label']} | {r['n']} | {pp(r['delta'], 2)} | {bcs} | {ci(r['ci90'][k_inst], 2)} | {ci(r['ci90']['wild'], 2)} | "
             f"{ci(r['ci90']['CR2-BM'], 2)} ({r['cr2_df']:.2f}) | {ci(r['ci90']['pct cluster (registered)'], 2)} | {passes} | {ms} |")
L.append("")
L.append("For the replication rows the Wald instance 90% CI is also in the JSON (`ci90['instance Wald']`).")
L.append("")
L += ["Check against results_scored.json (registered instance bootstrap reproduced):", "",
      "| contrast | Δ mine / file | 90% CI mine | 90% CI file | 95% CI mine | 95% CI file |", "|---|---|---|---|---|---|"]
for k, v in checks.items():
    L.append(f"| {k} | {v['mine_delta']:+.4f} / {v['file_delta']:+.4f} | [{v['mine_ci90'][0]:+.4f}, {v['mine_ci90'][1]:+.4f}] | "
             f"[{v['file_ci90'][0]:+.4f}, {v['file_ci90'][1]:+.4f}] | [{v['mine_ci95'][0]:+.4f}, {v['mine_ci95'][1]:+.4f}] | [{v['file_ci95'][0]:+.4f}, {v['file_ci95'][1]:+.4f}] |")
L.append("")
L += ["### gpt trim term (T−ON, 473 instances): django vs non-django, and both-non-empty pairs", "",
      "| reference | full Δ | django: n; Δ; b/c; contribution to full Δ | non-django: n; Δ; b/c; contribution | both non-empty: n; Δ; b/c; McNemar p | empties T / ON |",
      "|---|---|---|---|---|---|"]
for e in diag:
    a, b_, c_ = e["django"], e["non-django"], e["both non-empty"]
    L.append(f"| {e['ref']} | {pp(e['delta'], 2)} | {a['n']}; {pp(a['delta'], 2)}; {a['b']}/{a['c']}; {pp(a['contribution_to_full_pp'], 2)} | "
             f"{b_['n']}; {pp(b_['delta'], 2)}; {b_['b']}/{b_['c']}; {pp(b_['contribution_to_full_pp'], 2)} | "
             f"{c_['n']}; {pp(c_['delta'], 2)}; {c_['b']}/{c_['c']}; {fp(c_['mcnemar_p'])} | {e['empty_T']} / {e['empty_ON']} |")
L.append("")
write_md("s3_equiv", "\n".join(L) + "\n")
dump("s3_equiv", out)
