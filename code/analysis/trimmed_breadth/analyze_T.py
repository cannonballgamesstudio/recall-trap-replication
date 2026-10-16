#!/usr/bin/env python3
"""TRIMMED-BREADTH-PREREG §7 + Deviation-1 consequences (a)-(d), Qwen3-Coder-30B."""
import json, sys
from math import comb
from pathlib import Path
import numpy as np

P = Path("work/p5")
V = [l.strip() for l in open("preregistrations/TRIMMED-BREADTH-VIOLATORS.txt")
     if l.strip() and not l.startswith("#")]
REP = {
    "ON": "local_qwen3coder30b_dedupON.qwen30b_ON_rg.json",
    "OFF": "local_qwen3coder30b_dedupOFF.qwen30b_OFF_rg.json",
    "T": "local_qwen3coder30b_T.trimT_qwen30b_T.json",
    "Tp": "local_qwen3coder30b_Tprime.trimT_qwen30b_Tprime.json",
}
PRED = {"ON": "preds_local_qwen3coder30b_dedupON.jsonl", "OFF": "preds_local_qwen3coder30b_dedupOFF.jsonl",
        "T": "preds_local_qwen3coder30b_T.jsonl", "Tp": "preds_local_qwen3coder30b_Tprime.jsonl"}
RAW = {k: v.replace("preds_", "raw_") for k, v in PRED.items()}


def load(arm):
    d = json.loads((P / REP[arm]).read_text())
    return set(d["resolved_ids"]), set(d["submitted_ids"]), set(d.get("error_ids", [])), set(d.get("empty_patch_ids", []))


def mcnemar(b, c):
    n = b + c
    if n == 0: return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


rng = np.random.default_rng(20261014)
WEBB = np.array([-np.sqrt(1.5), -1, -np.sqrt(.5), np.sqrt(.5), 1, np.sqrt(1.5)])
B = 99999


def cluster_stats(d, g):
    """d: paired differences (A-B, 0/±1), g: repo labels. CR2 SE + wild cluster (Webb, WCR) p and CI."""
    d = np.asarray(d, float); N = len(d)
    labs = sorted(set(g)); G = len(labs)
    idx = np.array([labs.index(x) for x in g])
    ng = np.bincount(idx, minlength=G).astype(float)
    a2 = 1.0 / (1.0 - ng / N)                     # CR2 intercept-only: (1-h_gg)^-1 on cluster sums
    est = d.mean()

    def cr2_se(dd):
        e = dd - dd.mean()
        Eg = np.bincount(idx, weights=e, minlength=G)
        return np.sqrt((a2 * Eg ** 2).sum()) / N

    se = cr2_se(d)
    W = WEBB[rng.integers(0, 6, size=(B, G))]

    def boot_p(delta0):
        S = np.bincount(idx, weights=d - delta0, minlength=G)     # restricted residual cluster sums
        sumg = ng * delta0 + W * S                                  # B x G cluster sums of d*
        mean_ = sumg.sum(1) / N
        Eg = sumg - ng * mean_[:, None]
        se_ = np.sqrt((a2 * Eg ** 2).sum(1)) / N
        t_ = np.where(se_ > 0, (mean_ - delta0) / np.where(se_ > 0, se_, 1), 0)
        t0 = (est - delta0) / se if se > 0 else 0
        return float(np.mean(np.abs(t_) >= abs(t0)))

    p0 = boot_p(0.0)
    grid = np.linspace(est - 0.15, est + 0.15, 601)
    acc = [x for x in grid if boot_p(x) > 0.05]
    ci = (min(acc), max(acc)) if acc else (float("nan"), float("nan"))
    return {"est_pp": 100 * est, "cr2_se_pp": 100 * se,
            "cr2_ci_pp": (100 * (est - 2.201 * se), 100 * (est + 2.201 * se)),   # t(G-1=11) 0.975
            "wild_p": p0, "wild_ci_pp": (100 * ci[0], 100 * ci[1]), "G": G}


def contrast(name, ids, A, Bset, cl=True):
    """A - B on ids. A,Bset: resolved sets."""
    ids = sorted(ids); n = len(ids)
    a = np.array([i in A for i in ids], float); b_ = np.array([i in Bset for i in ids], float)
    bA = int(((a == 1) & (b_ == 0)).sum()); cB = int(((a == 0) & (b_ == 1)).sum())
    d = a - b_
    out = {"contrast": name, "n": n, "A": int(a.sum()), "B": int(b_.sum()),
           "delta_pp": 100 * d.mean(), "paired_se_pp": 100 * d.std(ddof=1) / np.sqrt(n),
           "b(A-only)": bA, "c(B-only)": cB, "mcnemar_p": mcnemar(bA, cB)}
    if cl:
        out.update({"cl_" + k: v for k, v in cluster_stats(d, [i.split("__")[0] for i in ids]).items()})
    return out


def fmt(o):
    s = (f"{o['contrast']:<34} n={o['n']:<3} A={o['A']:<3} B={o['B']:<3} Δ={o['delta_pp']:+.2f}pp "
         f"(paired SE {o['paired_se_pp']:.2f}) b/c={o['b(A-only)']}/{o['c(B-only)']} McNemar p={o['mcnemar_p']:.4g}")
    if "cl_wild_p" in o:
        s += (f"\n{'':36}CR2 SE {o['cl_cr2_se_pp']:.2f}pp, CR2 95%CI [{o['cl_cr2_ci_pp'][0]:+.2f},{o['cl_cr2_ci_pp'][1]:+.2f}]; "
              f"wild-cluster(Webb,G={o['cl_G']}) p={o['cl_wild_p']:.4f} CI [{o['cl_wild_ci_pp'][0]:+.2f},{o['cl_wild_ci_pp'][1]:+.2f}]")
    return s


def main():
    R, S = {}, {}
    for k in REP:
        R[k], S[k], _, _ = load(k)
    out = {}
    lines = []
    # --- (a) primary decomposition on the 473, pairwise-attempted
    ids473 = (S["ON"] & S["OFF"] & S["T"]) - set(V)
    lines.append(f"pairwise-attempted on the 473: {len(ids473)}  (T submitted {len(S['T'])}, T' submitted {len(S['Tp'])})")
    G = contrast("G = OFF-ON  [473]", ids473, R["OFF"], R["ON"])
    Dd = contrast("Δdepth = OFF-T  [473]", ids473, R["OFF"], R["T"])
    Dt = contrast("Δtrim = T-ON  [473]", ids473, R["T"], R["ON"])
    out["primary"] = [G, Dd, Dt]
    for o in out["primary"]: lines.append(fmt(o))
    g = G["delta_pp"]
    sh_d = Dd["delta_pp"] / g if g else float("nan"); sh_t = Dt["delta_pp"] / g if g else float("nan")
    lines.append(f"identity check: Δdepth+Δtrim = {Dd['delta_pp']+Dt['delta_pp']:+.3f} vs G {g:+.3f}")
    lines.append(f"shares of G: depth {100*sh_d:.1f}%  trim {100*sh_t:.1f}%")
    # --- §4 rule, literal
    if sh_d >= 0.6 and Dd["mcnemar_p"] < 0.05:
        verdict = "depth carries the effect"
    elif sh_t >= 0.6 and Dt["mcnemar_p"] < 0.05:
        verdict = "file trimming carries the effect"
    else:
        verdict = "both components contribute; the partition is not resolved at this n"
    lines.append(f"§4 VERDICT: {verdict}")
    # --- (b) full-500 reference
    ids500 = S["ON"] & S["OFF"]
    out["ref500"] = contrast("Reference OFF-ON [full 500]", ids500, R["OFF"], R["ON"])
    lines.append(fmt(out["ref500"]))
    # --- (c) pooled n=500 secondary with T' on the 27
    RTp = R["T"] | R["Tp"]; STp = (S["T"] - set(V)) | (S["Tp"] & set(V))
    idsP = S["ON"] & S["OFF"] & STp
    lines.append("--- pooled secondary (T on 473 + T' on 27; NON-IDENTICAL construction on 27; gold-file violator = matplotlib__matplotlib-23314)")
    out["pooled"] = [contrast("pooled OFF-T*", idsP, R["OFF"], RTp), contrast("pooled T*-ON", idsP, RTp, R["ON"])]
    for o in out["pooled"]: lines.append(fmt(o))
    tp_ids = sorted(S["Tp"] & set(V))
    lines.append(f"T' on 27: resolved {len(R['Tp'] & set(V))}/{len(tp_ids)}; ON {len(R['ON'] & set(V))}, OFF {len(R['OFF'] & set(V))}; "
                 f"matplotlib-23314 T'={'matplotlib__matplotlib-23314' in R['Tp']}")
    # --- (d) worst-case bounds on the 27
    lines.append("--- worst-case bounds on the 27 (n=500)")
    for lab, imp in (("T:=ON on 27", R["ON"] & set(V)), ("T:=OFF on 27", R["OFF"] & set(V))):
        RT = (R["T"] - set(V)) | imp
        ids = S["ON"] & S["OFF"] & ((S["T"] - set(V)) | set(V))
        a = contrast(f"[{lab}] OFF-T", ids, R["OFF"], RT, cl=False)
        b = contrast(f"[{lab}] T-ON", ids, RT, R["ON"], cl=False)
        out.setdefault("bounds", []).extend([a, b]); lines += [fmt(a), fmt(b)]
    # --- secondary: rates, both-non-empty conditional, funnel
    lines.append("--- per-arm rates on the 473 (ref arms restricted) and full")
    preds = {k: {json.loads(l)["instance_id"]: json.loads(l)["model_patch"] for l in open(P / PRED[k], encoding="utf-8")} for k in PRED}
    raws = {}
    for k in RAW:
        raws[k] = {}
        for l in open(P / RAW[k], encoding="utf-8"):
            r = json.loads(l); raws[k][r["instance_id"]] = r      # last row wins
    def rates(k, ids):
        ids = [i for i in ids if i in preds[k]]
        n = len(ids)
        emp = sum(not (preds[k][i] or "").strip() for i in ids)
        fl = sum(raws[k].get(i, {}).get("finish_reason") == "length" for i in ids)
        parsed = sum(raws[k].get(i, {}).get("applied", 0) > 0 or (preds[k][i] or "").strip() != "" for i in ids)
        appl = sum((preds[k][i] or "").strip() != "" for i in ids)
        res = sum(i in R[k] for i in ids)
        return f"n={n} empty={emp} ({100*emp/n:.1f}%) fin=length={fl} ({100*fl/n:.1f}%) applied>0={sum(raws[k].get(i,{}).get('applied',0)>0 for i in ids)} nonempty-patch={appl} resolved={res}"
    for k in ("ON", "OFF", "T"):
        lines.append(f"  {k:<4}[473] " + rates(k, ids473))
    lines.append(f"  T'  [27]  " + rates("Tp", tp_ids))
    for k in ("ON", "OFF"):
        lines.append(f"  {k:<4}[500] " + rates(k, sorted(ids500)))
    ne = lambda k, i: bool((preds[k].get(i) or "").strip())
    for A, Bk in (("OFF", "T"), ("T", "ON"), ("OFF", "ON")):
        ids = [i for i in ids473 if ne(A, i) and ne(Bk, i)]
        o = contrast(f"both-non-empty {A}-{Bk} [473]", ids, R[A], R[Bk], cl=False)
        lines.append(fmt(o)); out.setdefault("bne", []).append(o)
    txt = "\n".join(lines)
    print(txt)
    Path(sys.argv[1] if len(sys.argv) > 1 else "results/trimmed-breadth/T_analysis.txt").write_text(txt, encoding="utf-8")
    json.dump(out, open(Path("results/trimmed-breadth/T_analysis.json"), "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
