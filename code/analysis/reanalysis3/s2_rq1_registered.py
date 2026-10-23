"""Analysis 2 (POST HOC): RQ1 under the REGISTERED structure.

Registered structure (verified against the documents):
  * GPT-LOGGED-REPLICATION-PREREG (a): the gpt headline stays the 2026-07-14 discovery run (+7.6, 196/234);
    (c) the re-run's resolve delta is a SECONDARY, direction-only endpoint; (e) the re-run is OUTSIDE the Holm family.
  * TRIMMED-BREADTH-PREREG section 9 names the discovery pair (196/234) as the gpt T reference.
  * The Holm family in force when GPT-LOGGED was committed (c35850a, 2026-08-08): draft-v5 section 4.5 at ab6f065 =
    five raw McNemar p-values {gpt discovery, Qwen3.6-27B K=12, DENSE-1 (dense), DeepSeek, PolyBench pooled};
    the section-6.1 sentence of the same draft (and draft.md 2026-07-16) speaks of "the four single-shot A/Bs" (no PolyBench).
    results/core/paired_contrasts.md reproduces the five-test version. Both are reported.
  * Clustered method in the registrations: the repository-cluster PERCENTILE bootstrap (paired_contrasts.md: 5,000 reps,
    seed 20260714). Replaced post-registration by wild/CR2/flip.
Pooled-gpt estimator = the Branch B estimator (contam_score.py::delta): mean over (instance, draw) rows; every instance has
both draws, so it equals the mean of the per-instance average d_bar_i = (d_disc,i + d_rerun,i)/2.
"""
import glob
import json
import math

import numpy as np

from common3 import (arm, dvec, repo, all_methods, holm, mcnemar, cr2_bm, wild, signflip, pct_boot, iid, DATA,
                     pp, ci, fp, write_md, dump)

out = {}


def contrast(offk, onk, label):
    A_off, A_on = arm(offk), arm(onk)
    d, ids = dvec(A_on.sub & A_off.sub, A_off.res, A_on.res)
    r = all_methods(d, ids, label)
    r["ON"], r["OFF"] = sum(i in A_on.res for i in ids), sum(i in A_off.res for i in ids)
    return r, d, ids


rows = {}
rows["gpt_disc"], d_disc, ids_disc = contrast("gpt_hl_OFF", "gpt_hl_ON", "gpt discovery draw (registered headline)")
rows["gpt_rerun"], d_lr, ids_lr = contrast("gpt_lr_OFF", "gpt_lr_ON", "gpt logged re-run (registered secondary)")
rows["qwen36"], _, _ = contrast("q36_k12_OFF", "q36_k12_ON", "Qwen3.6-27B K=12")
rows["deepseek"], _, _ = contrast("ds_OFF", "ds_ON", "DeepSeek-v4-pro")
rows["dense"], _, _ = contrast("gpt_dense_OFF", "gpt_dense_ON", "DENSE-1 dense control (gpt)")

# ------------------------------------------------ pooled gpt (both draws, per instance)
assert ids_disc == ids_lr and len(ids_disc) == 500
dbar = (d_disc + d_lr) / 2
pool = all_methods(dbar, ids_disc, "gpt both draws pooled (per-instance mean)")
b_st, c_st = rows["gpt_disc"]["b"] + rows["gpt_rerun"]["b"], rows["gpt_disc"]["c"] + rows["gpt_rerun"]["c"]
pool["stacked_bc"] = (b_st, c_st)
pool["stacked_mcnemar_p_nominal"] = mcnemar(b_st, c_st)
# exact instance-level randomization test (flip the sign of each instance's d_bar), DP in units of 0.5
u = np.round(np.abs(dbar[dbar != 0]) * 2).astype(int)
dist = {0: 1.0}
for v in u:
    nd = {}
    for k, pr in dist.items():
        nd[k + v] = nd.get(k + v, 0) + pr / 2
        nd[k - v] = nd.get(k - v, 0) + pr / 2
    dist = nd
T0 = int(round(dbar.sum() * 2))
pool["instance_randomization_p"] = float(sum(pr for k, pr in dist.items() if abs(k) >= abs(T0)))
pool["dbar_counts"] = {str(v): int((dbar == v).sum()) for v in (-1, -0.5, 0, 0.5, 1)}
rows["gpt_pooled"] = pool

# ------------------------------------------------ PolyBench pooled (19 repositories)
PB = DATA / "polybench"


def load_ne(fn):
    s = set()
    for l in open(fn, encoding="utf-8"):
        if l.strip():
            r = json.loads(l)
            if (r.get("model_patch") or "").strip():
                s.add(r["instance_id"])
    return s


def load_g(d):
    g = {}
    for f in glob.glob(str(d) + "/*_result.json"):
        x = json.load(open(f, encoding="utf-8"))
        g[x["instance_id"]] = bool(x.get("resolved"))
    return g


def ids_(fn):
    return [l.strip() for l in open(fn, encoding="utf-8") if l.strip()]


meta = {x["instance_id"]: x for x in json.loads((PB / "instances_polybench.json").read_text(encoding="utf-8"))}
a_neON, a_neOFF = load_ne(PB / "preds_local_pb_a3b_dedupON.jsonl"), load_ne(PB / "preds_local_pb_a3b_dedupOFF.jsonl")
a_gON, a_gOFF = load_g(PB / "grading/pb_ab_ON"), load_g(PB / "grading/pb_ab_OFF")
g_neON, g_neOFF = load_ne(PB / "preds_local_pb_gpt_dedupON.jsonl"), load_ne(PB / "preds_local_pb_gpt_dedupOFF.jsonl")
g_gON, g_gOFF = load_g(PB / "grading/pb_gpt_ab_ON"), load_g(PB / "grading/pb_gpt_ab_OFF")
killed = set(ids_(PB / "off_killed_ids.txt"))
S_a = ids_(PB / "survivor_ids.txt")
S_g = [i for i in ids_(PB / "survivor_ids_gpt.txt") if i not in killed]
y, cl = [], []
for i in S_a:
    y.append(int((i in a_neOFF) and a_gOFF.get(i, False)) - int((i in a_neON) and a_gON.get(i, False))); cl.append(meta[i]["repo"])
for i in S_g:
    y.append(int((i in g_neOFF) and g_gOFF.get(i, False)) - int((i in g_neON) and g_gON.get(i, False))); cl.append(meta[i]["repo"])
y = np.array(y, float)
pbr = dict(label="PolyBench pooled (2 models x 4 languages)", n=len(y), delta=float(y.mean()), b=int((y > 0).sum()), c=int((y < 0).sum()))
pbr["mcnemar_p"] = mcnemar(pbr["b"], pbr["c"])
pbr["iid"] = iid(y)
w = wild(y, cl, alphas=(0.05,), hw=0.2)
pbr["wild"] = {k: v for k, v in w.items() if not k.startswith("_")}
pbr["cr2"] = cr2_bm(y, cl)
pbr["flip"] = signflip(y, cl)
pbr["pct"] = pct_boot(y, cl)
pbr["G"] = len(set(cl))
rows["polybench"] = pbr


# ------------------------------------------------ Holm families x methods
def pv(r, m):
    # pooled gpt: the exact instance-level randomization test stands in for McNemar (the stacked McNemar ignores
    # the dependence between an instance's two draws and is shown only as a nominal figure)
    return {"McNemar": r["mcnemar_p"] if r.get("mcnemar_p") is not None else r.get("instance_randomization_p"),
            "wild": r["wild"]["p"], "CR2": r["cr2"]["p"], "flip": r["flip"]["p"], "pct (registered, 2-sided)": r["pct"]["p2"]}[m]


METHODS = ["McNemar", "wild", "CR2", "flip", "pct (registered, 2-sided)"]
FAMILIES = {
    "F5 registered (draft-v5 §4.5 at c35850a; paired_contrasts.md): gpt discovery, Qwen3.6, dense, DeepSeek, PolyBench":
        ["gpt_disc", "qwen36", "dense", "deepseek", "polybench"],
    "F4 registered (§6.1 'four single-shot A/Bs'): gpt discovery, Qwen3.6, dense, DeepSeek":
        ["gpt_disc", "qwen36", "dense", "deepseek"],
    "F2-reg (paper's 2-test family, with the registered gpt headline): Qwen3.6, gpt discovery": ["qwen36", "gpt_disc"],
    "F2-paper (as in the current paper): Qwen3.6, gpt re-run": ["qwen36", "gpt_rerun"],
    "F2-pooled (Qwen3.6, gpt both draws pooled)": ["qwen36", "gpt_pooled"],
}
hres = {}
for fname, mem in FAMILIES.items():
    hres[fname] = {}
    for m in METHODS:
        raw = {k: pv(rows[k], m) for k in mem}
        adj = holm(raw)
        hres[fname][m] = {k: (raw[k], adj[k]) for k in mem}
out["rows"] = rows
out["holm"] = hres

# ------------------------------------------------ gpt decomposition against the registered T reference (TB §9: discovery)
from common3 import VIOL  # noqa: E402
dec = {}
A_t = arm("gpt_T")
for ref, onk, offk in (("discovery (registered, TB §9)", "gpt_hl_ON", "gpt_hl_OFF"), ("re-run (paper)", "gpt_lr_ON", "gpt_lr_OFF")):
    A_on, A_off = arm(onk), arm(offk)
    ids = sorted((A_on.sub & A_off.sub & A_t.sub) - set(VIOL))
    for nm, X, Y in (("G = OFF−ON", A_off, A_on), ("depth = OFF−T", A_off, A_t), ("trim = T−ON", A_t, A_on)):
        d, ii = dvec(ids, X.res, Y.res)
        dec[(ref, nm)] = all_methods(d, ii, f"{ref}: {nm}")
out["gpt_decomposition"] = {" | ".join(k): v for k, v in dec.items()}

# ------------------------------------------------ markdown
L = ["## Analysis 2 — RQ1 under the registered structure (POST HOC re-analysis of registered estimands)", "",
     "Registered structure verified in the documents: GPT-LOGGED-REPLICATION-PREREG (a) headline = discovery draw (+7.6, 196/234); "
     "(c) re-run resolve Δ = secondary, direction-only; (e) re-run outside the Holm family. TRIMMED-BREADTH §9 names 196/234 as the gpt T reference. "
     "The Holm family in force when GPT-LOGGED was committed (c35850a, 2026-08-08) is draft-v5 §4.5 (ab6f065): five raw McNemar p "
     "{gpt discovery, Qwen3.6-27B K=12, DENSE-1, DeepSeek, PolyBench pooled}; the same draft's §6.1 (and draft.md, 2026-07-16) says “the four single-shot A/Bs”. "
     "QWEN36-PREREG itself names no Holm family (it registers McNemar exact, empties-as-failure, on n=500). "
     "Registered clustered method = repository-cluster percentile bootstrap (5,000 reps, seed 20260714).", "",
     "Methods: McNemar exact; wild = WCR Webb B=9,999 (CI by inversion); CR2-BM; exact repository sign-flip; pct = registered percentile cluster bootstrap "
     "(95% CI; P(Δ*≤0); two-sided p = 2·min(P(Δ*≤0), P(Δ*≥0))).", "",
     "| contrast | n | ON/OFF | Δ (pp) | b/c | McNemar p | iid 95% CI | wild 95% CI; p | CR2 95% CI; p (df) | flip p | **registered pct 95% CI; P(Δ*≤0); 2-sided p** |",
     "|---|---|---|---|---|---|---|---|---|---|---|"]
for k in ("gpt_disc", "gpt_rerun", "gpt_pooled", "qwen36", "deepseek", "dense", "polybench"):
    r = rows[k]
    onoff = f"{r.get('ON', '—')}/{r.get('OFF', '—')}"
    mc = fp(r["mcnemar_p"]) if r.get("mcnemar_p") is not None else f"stacked {r['stacked_bc'][0]}/{r['stacked_bc'][1]}: {fp(r['stacked_mcnemar_p_nominal'])} (nominal); instance randomization {fp(r['instance_randomization_p'])}"
    L.append(f"| {r['label']} | {r['n']} | {onoff} | {pp(r['delta'], 2)} | {r['b']}/{r['c']} | {mc} | {ci(r['iid']['ci95'])} | "
             f"{ci(r['wild']['ci95'])}; {fp(r['wild']['p'])} | {ci(r['cr2']['ci95'])}; {fp(r['cr2']['p'])} ({r['cr2']['df']:.2f}) | {fp(r['flip']['p'])} | "
             f"{ci(r['pct']['ci95'])}; {r['pct']['p_le0']:.4f}; {fp(r['pct']['p2'])} |")
L.append("")
L.append(f"Pooled-gpt per-instance mean d̄ distribution: {rows['gpt_pooled']['dbar_counts']}. b/c in that row count instances with d̄>0 / d̄<0. "
         "In the Holm tables the pooled row's 'McNemar' entry is the exact instance-level randomization p (the stacked McNemar is nominal only). "
         "A pct P(Δ*≤0) of 0.0000 means 0 of 5,000 draws (p < 2e-4). PolyBench's registered analysis was an instance bootstrap; its pct row here is the "
         "repository-cluster version (19 repositories) for comparability.")
L.append("")
L += ["### Holm-adjusted p by family and method (raw → adjusted)", ""]
for fname, mm in hres.items():
    mem = FAMILIES[fname]
    L += [f"**{fname}**", "", "| method | " + " | ".join(rows[k]["label"] for k in mem) + " | all survive α=0.05? |",
          "|---|" + "---|" * len(mem) + "---|"]
    for m in METHODS:
        cells = [f"{fp(mm[m][k][0])} → {fp(mm[m][k][1])}" for k in mem]
        surv = [mm[m][k][1] < 0.05 for k in mem]
        tag = "all" if all(surv) else ("none" if not any(surv) else "only " + ", ".join(rows[k]["label"].split(" (")[0] for k, s in zip(mem, surv) if s))
        L.append(f"| {m} | " + " | ".join(cells) + f" | {tag} |")
    L.append("")
L += ["### gpt T decomposition (473) against each reference pair, all methods", "",
      "| reference: term | Δ (pp) | b/c | McNemar p | wild 95% CI; p | CR2 p | flip p | registered pct 95% CI; P(Δ*≤0) |", "|---|---|---|---|---|---|---|---|"]
for k, r in dec.items():
    L.append(f"| {r['label']} | {pp(r['delta'], 2)} | {r['b']}/{r['c']} | {fp(r['mcnemar_p'])} | {ci(r['wild']['ci95'])}; {fp(r['wild']['p'])} | "
             f"{fp(r['cr2']['p'])} | {fp(r['flip']['p'])} | {ci(r['pct']['ci95'])}; {r['pct']['p_le0']:.4f} |")
L.append("")
write_md("s2_rq1_registered", "\n".join(L) + "\n")
dump("s2_rq1_registered", out)
