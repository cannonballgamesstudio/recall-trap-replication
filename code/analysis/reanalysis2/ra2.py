"""Shared loaders + inference for reanalysis2 (design-authority FREE analyses, 2026-10-15).

Read-only over the released data. No model calls, no Docker, no GPU.
Clustered inference reuses the earlier helpers (code/analysis/reanalysis/common_ra.py):
  wild = WCR bootstrap-t, Webb 6-point, CR1 studentization, B=9,999, seed 20261014, CI by test inversion
  CR2  = Bell-McCaffrey bias-reduced SE with BM Satterthwaite df
  flip = exact repository sign-flip over all 2^G assignments (two-sided, raw sum statistic)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
PKG = HERE.parents[2]
SCR = PKG / "code"
sys.path.insert(0, str(HERE.parent / "reanalysis"))
import common_ra as cra  # noqa: E402

P5 = PKG / "work" / "p5"   # built by code/prepare_data.py
CONTAM = PKG / "data" / "memorization-branchB"
SEED = 20261014
OUT = PKG / "results" / "reanalysis2"
OUT.mkdir(parents=True, exist_ok=True)

INST = {c["instance_id"]: c for c in json.loads((P5 / "instances_verified.json").read_text(encoding="utf-8"))}
ALL = sorted(INST)
VIOL = [l.strip() for l in open(PKG / "preregistrations" / "TRIMMED-BREADTH-VIOLATORS.txt", encoding="utf-8")
        if l.strip() and not l.startswith("#")]


def repo(i):
    return INST[i]["repo"]


REPORTS = {
    # gpt-5.6-sol
    "gpt_hl_ON": "local_gpt56sol_dedupON.local_gpt56sol_dedupON.json",
    "gpt_hl_OFF": "local_gpt56sol_dedupOFF.local_gpt56sol_dedupOFF.json",
    "gpt_lr_ON": "local_gptsol_logrep_dedupON.gptsol_logrep_dedupON.json",
    "gpt_lr_OFF": "local_gptsol_logrep_dedupOFF.gptsol_logrep_dedupOFF.json",
    "gpt_T": "local_gpt56sol_T.trimT_gpt56sol_T.json",
    "gpt_Tp": "local_gpt56sol_Tprime.trimT_gpt56sol_Tprime.json",
    "gpt_dense_ON": "local_gptsol_dense_dedupON.cc1_gptdense_ON_rg.json",
    "gpt_dense_OFF": "local_gptsol_dense_dedupOFF.cc1_gptdense_OFF_rg.json",
    "gpt_bm25_ON": "local_gpt56sol_bm25_dedupON.bm25_gptsol_ON.json",
    "gpt_bm25_OFF": "local_gpt56sol_bm25_dedupOFF.bm25_gptsol_OFF.json",
    # Qwen3-Coder-30B-A3B, local GGUF (T reference pair, random-chunk control, E5)
    "qc_ON": "local_qwen3coder30b_dedupON.qwen30b_ON_rg.json",
    "qc_OFF": "local_qwen3coder30b_dedupOFF.qwen30b_OFF_rg.json",
    "qc_T": "local_qwen3coder30b_T.trimT_qwen30b_T.json",
    "qc_Tp": "local_qwen3coder30b_Tprime.trimT_qwen30b_Tprime.json",
    # Qwen3-Coder other K=12 pairs (task 10d)
    "qor_k4_ON": "local_qwen3or_k4_dedupON.qwen3or_k4_dedupON.json",
    "qor_k4_OFF": "local_qwen3or_k4_dedupOFF.qwen3or_k4_dedupOFF.json",
    "qor_k12_ON": "local_qwen3or_k12_dedupON.qwen3or_k12_dedupON.json",
    "qor_k12_OFF": "local_qwen3or_k12_dedupOFF.qwen3or_k12_dedupOFF.json",
    "qor_k40_ON": "local_qwen3or_k40_dedupON.qwen3or_k40_dedupON.json",
    "qor_k40_OFF": "local_qwen3or_k40_dedupOFF.qwen3or_k40_dedupOFF.json",
    "c12k_ON": "local_coder30b_c12k_dedupON.coder30b_c12k_dedupON.json",
    "c12k_OFF": "local_coder30b_c12k_dedupOFF.coder30b_c12k_dedupOFF.json",
    "qc87_ON": "local_qwen3coder30b_dedupON.local_dedupON.json",
    "qc87_OFF": "local_qwen3coder30b_dedupOFF.local_dedupOFF.json",
    # Qwen3.6-27B
    "q36_k4_ON": "local_qwen36_k4_dedupON.qs2_k4_ON.json",
    "q36_k4_OFF": "local_qwen36_k4_dedupOFF.qs2_k4_OFF.json",
    "q36_k12_ON": "local_qwen36_k12_dedupON.qwen36_k12_dedupON.json",
    "q36_k12_OFF": "local_qwen36_k12_dedupOFF.qwen36_k12_dedupOFF.json",
    "q36_k40_ON": "local_qwen36_k40_dedupON.qs2_k40_ON.json",
    "q36_k40_OFF": "local_qwen36_k40_dedupOFF.qs2_k40_OFF.json",
    # DeepSeek-v4-pro
    "ds_ON": "local_dsv4_dedupON.dsv4_ON_rg.json",
    "ds_OFF": "local_dsv4_dedupOFF.dsv4_OFF_rg.json",
    # agentic sonnet-5
    "ag_fus_ON": "g_ssagent500_dedupON.ssagent500_ON.json",
    "ag_fus_OFF": "g_ssagent500_dedupOFF.ssagent500_OFF.json",
    "ag_dense_ON": "g_dense500_ON.g_dense500_ON_rg3.json",
    "ag_dense_OFF": "g_dense500_OFF.g_dense500_OFF_rg3.json",
}

_cache = {}


class Arm:
    def __init__(self, key):
        self.key = key
        self.file = REPORTS[key]
        d = json.loads((P5 / self.file).read_text(encoding="utf-8"))
        self.res = set(d["resolved_ids"])
        self.sub = set(d["submitted_ids"])
        self.err = set(d.get("error_ids", []))
        self.empty = set(d.get("empty_patch_ids", []))
        self.n_err = d.get("error_instances", len(self.err))


def arm(key) -> Arm:
    if key not in _cache:
        _cache[key] = Arm(key)
    return _cache[key]


def error_audit(keys):
    rows = []
    for k in keys:
        a = arm(k)
        rows.append((k, a.file, len(a.sub), len(a.res), len(a.empty), a.n_err, sorted(a.err)))
    return rows


# ------------------------------------------------------------------ paired contrast
def mcnemar(b, c):
    return cra.mcnemar_exact(b, c)


def paired(ids, A: set, B: set, label="", cluster=True, alpha_wild=(0.05,), cr2=True, flip=True):
    """A - B on ids (A, B = resolved sets). Returns dict with instance + clustered inference."""
    ids = sorted(ids)
    n = len(ids)
    a = np.array([i in A for i in ids], float)
    b_ = np.array([i in B for i in ids], float)
    d = a - b_
    bA = int(((a == 1) & (b_ == 0)).sum())
    cB = int(((a == 0) & (b_ == 1)).sum())
    est = d.mean()
    se = d.std(ddof=1) / math.sqrt(n) if n > 1 else float("nan")
    out = dict(label=label, n=n, A=int(a.sum()), B=int(b_.sum()), A_rate=a.mean(), B_rate=b_.mean(),
               delta=est, b=bA, c=cB, mcnemar_p=mcnemar(bA, cB), inst_se=se,
               inst_ci95=(est - 1.959964 * se, est + 1.959964 * se),
               inst_ci90=(est - 1.644854 * se, est + 1.644854 * se),
               inst_p=2 * stats.norm.sf(abs(est / se)) if se > 0 else 1.0)
    if cluster and n > 0:
        cl = [repo(i) for i in ids]
        pval, _ = wild_pfun(d, cl)
        out["wild_p"] = pval(0.0)
        hw = max(0.25, 8 * se)
        grid = np.arange(est - hw, est + hw + 0.00025, 0.0005)   # 0.05pp grid, same weight draws throughout
        ps = np.array([pval(b) for b in grid])
        for al in alpha_wild:
            idx = np.where(ps > al)[0]
            tag = f"wild_ci{int(round(100 * (1 - al)))}"
            if len(idx):
                out[tag] = (float(grid[idx[0]]), float(grid[idx[-1]]))
                out[tag + "_pieces"] = 1 + int((np.diff(idx) > 1).sum())
            else:
                out[tag] = (float("nan"), float("nan"))
        if cr2:
            r = cra.cr2_bm(d, cl)
            out.update(cr2_se=r["se"], cr2_df=r["df"], cr2_p=r["p"], cr2_ci95=(r["lo"], r["hi"]))
            q90 = stats.t.ppf(0.95, r["df"])
            out["cr2_ci90"] = (r["est"] - q90 * r["se"], r["est"] + q90 * r["se"])
        if flip:
            f = cra.signflip(d, cl)
            out.update(flip_p=f["p"], flip_p_t=f["p_t"], G=f["G"])
    out["_d"] = d
    out["_ids"] = ids
    return out


def did(ids, dA: dict, dB: dict, label=""):
    """instance-paired difference-in-differences dA - dB (dicts iid -> paired difference)."""
    ids = sorted(i for i in ids if i in dA and i in dB)
    d = np.array([dA[i] - dB[i] for i in ids], float)
    n = len(d)
    est = d.mean()
    se = d.std(ddof=1) / math.sqrt(n)
    cl = [repo(i) for i in ids]
    pval, _ = wild_pfun(d, cl)
    hw = max(0.25, 8 * se)
    grid = np.arange(est - hw, est + hw + 0.00025, 0.0005)
    ps = np.array([pval(b) for b in grid])
    def _ci(al):
        idx = np.where(ps > al)[0]
        return dict(lo=float(grid[idx[0]]), hi=float(grid[idx[-1]]), pieces=1 + int((np.diff(idx) > 1).sum()))
    w95 = dict(_ci(0.05), p=pval(0.0))
    w90 = _ci(0.10)
    r = cra.cr2_bm(d, cl)
    f = cra.signflip(d, cl)
    q90 = stats.t.ppf(0.95, r["df"])
    return dict(label=label, n=n, delta=est, inst_se=se, inst_ci95=(est - 1.959964 * se, est + 1.959964 * se),
                inst_ci90=(est - 1.644854 * se, est + 1.644854 * se), inst_p=2 * stats.norm.sf(abs(est / se)),
                wild_p=w95["p"], wild_ci95=(w95["lo"], w95["hi"]), wild_ci90=(w90["lo"], w90["hi"]), wild_pieces=(w95["pieces"], w90["pieces"]),
                cr2_p=r["p"], cr2_ci95=(r["lo"], r["hi"]), cr2_ci90=(r["est"] - q90 * r["se"], r["est"] + q90 * r["se"]),
                cr2_df=r["df"], flip_p=f["p"])


def dvec(ids, A: set, B: set):
    return {i: int(i in A) - int(i in B) for i in ids}


# ------------------------------------------------------------------ formatting
def pp(x, nd=1, sign=True):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    v = 100 * x
    return f"{v:+.{nd}f}" if sign else f"{v:.{nd}f}"


def ci(t, nd=1):
    return f"[{pp(t[0], nd)}, {pp(t[1], nd)}]"


def fp(p):
    return cra.fmt_p(p)


def strip(o):
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items() if not k.startswith("_")}
    if isinstance(o, (list, tuple)):
        return [strip(x) for x in o]
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, set):
        return sorted(o)
    return o


def dump(name, obj):
    (OUT / f"{name}.json").write_text(json.dumps(strip(obj), indent=1, default=str), encoding="utf-8")


def write_md(name, text):
    (OUT / f"{name}.md").write_text(text, encoding="utf-8")
    print(text)


# ------------------------------------------------------------------ fine-grid wild inversion (task 10c)
def wild_pfun(y, clusters, B=cra.B_WILD, seed=cra.SEED):
    """Returns p(b0) for the WCR Webb bootstrap-t, identical to common_ra.wild_cluster internals."""
    y = np.asarray(y, float)
    N = len(y)
    S_y, n = cra._cluster_sums(y, clusters)
    G = len(n)
    W = cra.webb_weights(G, B, seed)
    c1 = G / (G - 1)
    est = y.sum() / N

    def pval(b0):
        S = S_y - b0 * n
        resid_sums = S - n * (est - b0)
        se = math.sqrt(c1 * (resid_sums ** 2).sum()) / N
        t = (est - b0) / se
        m_star = (W * S).sum(1) / N
        Sstar = W * S - np.outer(m_star, n)
        se_star = np.sqrt(c1 * (Sstar ** 2).sum(1)) / N
        t_star = m_star / se_star
        return float(np.mean(np.abs(t_star) >= abs(t) - 1e-12))
    return pval, est


def wild_grid(y, clusters, alpha=0.05, half_width=0.30, step=0.0001):
    pval, est = wild_pfun(y, clusters)
    grid = np.arange(est - half_width, est + half_width + step / 2, step)
    ps = np.array([pval(b) for b in grid])
    acc = grid[ps > alpha]
    if len(acc) == 0:
        return dict(lo=float("nan"), hi=float("nan"), convex=None, n_pieces=0)
    idx = np.where(ps > alpha)[0]
    pieces = 1 + int((np.diff(idx) > 1).sum())
    return dict(lo=float(acc.min()), hi=float(acc.max()), convex=pieces == 1, n_pieces=pieces,
                est=est, grid=grid, ps=ps, at_edge=bool(idx[0] == 0 or idx[-1] == len(grid) - 1))
