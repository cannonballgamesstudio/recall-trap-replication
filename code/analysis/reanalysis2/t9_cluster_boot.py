"""Task 9: repository-cluster bootstrap for Branch A (post-cutoff SWE-rebench, 105 gold-gated instances)
and for SWE-PolyBench (two-model pooled, 617 model x instance pairs).

Point estimate = mean paired d over (instance, draw) rows (the pre-registered pooled estimator).
Instance bootstrap reproduces the published analysis (seed 20261014 for Branch A as in contam_post_analyze.py;
seed 20260808 for PolyBench as in polybench_clustered_sens.py). Repository-cluster bootstrap resamples
repositories with replacement, carrying every instance and draw of a sampled repository (B=10,000, seed 20261014).
"""
import json
import random
from collections import defaultdict
from pathlib import Path

import numpy as np

from ra2 import cra, write_md, dump

B = 10000
ROOT = __import__("ra2").PKG / "data" / "post-cutoff-branchA"
man = {x["instance_id"]: x for x in json.loads((ROOT / "instances_post.json").read_text(encoding="utf-8"))}
gold_ok = set((ROOT / "gold_pass_ids_post.txt").read_text(encoding="utf-8").split())
packs = json.loads((ROOT / "post_packs.json").read_text(encoding="utf-8"))
ids = [i for i in sorted(man) if "dedupON" in packs.get(i, {}) and "dedupOFF" in packs.get(i, {}) and i in gold_ok]
chk = json.loads((ROOT / "manip_checks.json").read_text(encoding="utf-8"))
cls = chk["classes"]


def rep(p):
    d = json.loads((ROOT / "grade" / p).read_text(encoding="utf-8"))
    return set(d["resolved_ids"]), set(d["submitted_ids"]), d.get("error_instances", 0)


def pairs(on, off):
    onr, ons, e1 = rep(on)
    offr, offs, e2 = rep(off)
    return {i: int(i in offr) - int(i in onr) for i in ons & offs}, (e1, e2)


gpt_draws_files = [("report_gpt56sol_post_dedupON.json", "report_gpt56sol_post_dedupOFF.json"),
                   ("report_gpt56sol_post_s2_dedupON.json", "report_gpt56sol_post_s2_dedupOFF.json")]
gpt = [pairs(*f) for f in gpt_draws_files]
qwen = pairs("report_qwen3coder30b_post_dedupON.json", "report_qwen3coder30b_post_dedupOFF.json")
errs = {"gpt_s1": gpt[0][1], "gpt_s2": gpt[1][1], "qwen": qwen[1]}
gpt = [g[0] for g in gpt]
qwen = [qwen[0]]


def boot(draws, idset, cluster_of, seed, B=B, by_cluster=True):
    idset = [i for i in idset if any(i in d for d in draws)]
    rows = defaultdict(list)
    for i in idset:
        for d in draws:
            if i in d:
                rows[cluster_of(i) if by_cluster else i].append(d[i])
    units = sorted(rows)
    S = np.array([sum(rows[u]) for u in units], float)
    N = np.array([len(rows[u]) for u in units], float)
    pt = S.sum() / N.sum()
    rng = random.Random(seed)
    bs = []
    for _ in range(B):
        k = [rng.randrange(len(units)) for _ in units]
        bs.append(S[k].sum() / N[k].sum())
    bs = np.sort(bs)
    b_ = sum(1 for d in draws for i in idset if d.get(i) == 1)
    c_ = sum(1 for d in draws for i in idset if d.get(i) == -1)
    return dict(n=len(idset), units=len(units), delta=pt, b=b_, c=c_,
                ci80=(bs[int(.1 * (B - 1))], bs[int(.9 * (B - 1))]), ci95=(bs[int(.025 * (B - 1))], bs[int(.975 * (B - 1))]),
                P_gt0=float(np.mean(bs > 0)))


def label(r):
    if r["delta"] > 0 and r["P_gt0"] >= 0.80:
        return "SIGN-CONSISTENT"
    if r["delta"] < 0 and (1 - r["P_gt0"]) >= 0.80:
        return "SIGN-INCONSISTENT"
    return "UNINFORMATIVE"


repo_post = lambda i: man[i]["repo"]
late = [i for i in ids if man[i]["stratum_0401"]]
single = []
import sys
sys.path.insert(0, str(__import__("ra2").PKG / "code" / "eval"))
import contam_common as cc  # noqa: E402
single = [i for i in ids if len(cc.gold_files(man[i]["patch"])) == 1]

out = {"branchA_errors": errs}
L = ["## Task 9 — Repository-cluster bootstrap: Branch A and SWE-PolyBench", "",
     f"Branch A: {len(ids)} gold-gated instances in {len({repo_post(i) for i in ids})} repositories; gpt-5.6-sol 2 seeds pooled; error_instances in all 6 Branch A reports: "
     f"{sum(sum(v) for v in errs.values())}. Instance bootstrap reproduces the published A1–A6 (seed 20261014); repo-cluster bootstrap resamples repositories (B=10,000).", "",
     "| estimand | n | clusters | Δ (pp) | disc b/c | instance boot 95% CI; P(Δ*>0) | repo-cluster boot 80% CI | repo-cluster 95% CI | repo P(Δ*>0) | label (instance → cluster, 0.80 rule) |",
     "|---|---|---|---|---|---|---|---|---|---|"]
for lab, draws, S in (("A1 gpt all", gpt, ids), ("A2 gpt ≥2026-04-01", gpt, late), ("A6 gpt single gold file", gpt, single),
                      ("A3 gpt B→C", gpt, [i for i in ids if cls.get(i) == "B>C"]), ("A5 Qwen3-Coder all", qwen, ids)):
    ri = boot(draws, S, repo_post, 20261014, by_cluster=False)
    rc = boot(draws, S, repo_post, 20261014, by_cluster=True)
    out[lab] = dict(instance=ri, cluster=rc)
    L.append(f"| {lab} | {ri['n']} | {rc['units']} | {100*ri['delta']:+.2f} | {ri['b']}/{ri['c']} | [{100*ri['ci95'][0]:+.1f}, {100*ri['ci95'][1]:+.1f}]; {ri['P_gt0']:.3f} | "
             f"[{100*rc['ci80'][0]:+.1f}, {100*rc['ci80'][1]:+.1f}] | [{100*rc['ci95'][0]:+.1f}, {100*rc['ci95'][1]:+.1f}] | {rc['P_gt0']:.3f} | {label(ri)} → {label(rc)} |")
L.append("")

# ---------------- PolyBench
PB = __import__("ra2").PKG / "data" / "polybench"
import glob


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
        x = json.load(open(f))
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
da = {i: int((i in a_neOFF) and a_gOFF.get(i, False)) - int((i in a_neON) and a_gON.get(i, False)) for i in S_a}
dg = {i: int((i in g_neOFF) and g_gOFF.get(i, False)) - int((i in g_neON) and g_gON.get(i, False)) for i in S_g}
repo_pb = lambda i: meta[i]["repo"]
L += [f"SWE-PolyBench: A3B {len(S_a)} + gpt {len(S_g)} = {len(S_a)+len(S_g)} model×instance pairs. Instance bootstrap = published analysis (seed 20260808); repo-cluster bootstrap resamples repositories (B=10,000, seed 20261014). "
      "Exact repo sign-flip and WCR wild (Webb) on per-row d clustered by repository added for comparison (pairs of the same instance share a cluster).", "",
      "| cell | n pairs | repos | Δ (pp) | b/c | instance boot 95% CI; P(Δ*≤0) | repo-cluster 95% CI | repo P(Δ*≤0) | wild 95% CI; p | flip p |",
      "|---|---|---|---|---|---|---|---|---|---|"]
for lab, draws, S in (("pooled (A3B + gpt)", [da, dg], sorted(set(S_a) | set(S_g))), ("A3B", [da], S_a), ("gpt-5.6-sol", [dg], S_g)):
    ri = boot(draws, S, repo_pb, 20260808, by_cluster=False)
    rc = boot(draws, S, repo_pb, 20261014, by_cluster=True)
    y, cl = [], []
    for i in S:
        for d in draws:
            if i in d:
                y.append(d[i]); cl.append(repo_pb(i))
    y = np.array(y, float)
    pf, est = __import__("ra2").wild_pfun(y, cl)
    grid = np.arange(est - 0.2, est + 0.2, 0.0005)
    ps = np.array([pf(b) for b in grid]); acc = grid[ps > 0.05]
    fl = cra.signflip(y, cl) if len(set(cl)) <= 21 else None
    out["poly " + lab] = dict(instance=ri, cluster=rc, wild=(float(acc.min()), float(acc.max()), pf(0.0)), flip=fl)
    L.append(f"| {lab} | {len(y)} | {rc['units']} | {100*ri['delta']:+.2f} | {ri['b']}/{ri['c']} | [{100*ri['ci95'][0]:+.2f}, {100*ri['ci95'][1]:+.2f}]; {1-ri['P_gt0']:.4f} | "
             f"[{100*rc['ci95'][0]:+.2f}, {100*rc['ci95'][1]:+.2f}] | {1-rc['P_gt0']:.4f} | [{100*acc.min():+.1f}, {100*acc.max():+.1f}]; {pf(0.0):.3f} | {fl['p']:.3f} |")
L.append("")
L.append("Note: the instance-bootstrap row is a re-implementation (resampling order differs), so it reproduces the published [0.00, +5.31], P(Δ*≤0)=0.0309 only to Monte-Carlo error ([+0.00, +5.37], 0.0296).")
write_md("t9_cluster_boot", "\n".join(L) + "\n")
dump("t9_cluster_boot", out)
