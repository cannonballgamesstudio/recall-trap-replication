"""Shared loaders + inference for reanalysis3 (POST-HOC robustness analyses requested by an internal pre-submission
blind statistical review). Every analysis in this folder is POST HOC.

CPU only. No model calls, no Docker, no GPU, no WSL. Reads the released replication package
(run code/prepare_data.py first; flat view work/p5). Writes only into results/reanalysis3/.

Conventions (identical to reanalysis2 / the paper):
  d = A - B per instance (resolved indicators); empty patches and harness errors are failures over full n;
  never-submitted instances are excluded pairwise unless stated.
  wild = WCR (restricted) wild-cluster bootstrap-t, Webb 6-point weights, CR1 studentisation,
         B = 9,999, seed 20261014, CI by test inversion on a 0.05pp grid (same weight draws at every b0).
  CR2  = Bell-McCaffrey bias-reduced SE with BM Satterthwaite df.
  flip = exact repository sign-flip over all 2^G assignments (raw-sum statistic, two-sided).
  pct  = the REGISTERED repository-cluster percentile bootstrap (5,000 reps, Python random seed 20260714,
         lo = v[int(.025R)], hi = v[int(.975R)-1]), exactly as code/analysis/core/common.py::cluster_bootstrap.
"""
from __future__ import annotations

import itertools
import json
import math
import os
import random
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
PKG = Path(os.environ.get("RA3_PKG", HERE.parents[2]))           # package root
P5 = PKG / "work" / "p5"                                          # built by code/prepare_data.py
DATA = PKG / "data"
META = Path(os.environ.get("RA3_META", PKG / "data" / "swe-verified" / "inputs" / "verified_meta.json"))  # difficulty, gold patch
SEED = 20261014
B_WILD = 9999
OUT = PKG / "results" / "reanalysis3"
OUT.mkdir(parents=True, exist_ok=True)

INST = {c["instance_id"]: c for c in json.loads((P5 / "instances_verified.json").read_text(encoding="utf-8"))}
ALL = sorted(INST)
VIOL = [l.strip() for l in open(PKG / "preregistrations" / "TRIMMED-BREADTH-VIOLATORS.txt", encoding="utf-8")
        if l.strip() and not l.startswith("#")]


def repo(i):
    return INST[i]["repo"]


REPORTS = {
    "gpt_hl_ON": "local_gpt56sol_dedupON.local_gpt56sol_dedupON.json",          # discovery draw
    "gpt_hl_OFF": "local_gpt56sol_dedupOFF.local_gpt56sol_dedupOFF.json",
    "gpt_lr_ON": "local_gptsol_logrep_dedupON.gptsol_logrep_dedupON.json",      # logged re-run
    "gpt_lr_OFF": "local_gptsol_logrep_dedupOFF.gptsol_logrep_dedupOFF.json",
    "gpt_T": "local_gpt56sol_T.trimT_gpt56sol_T.json",
    "gpt_dense_ON": "local_gptsol_dense_dedupON.cc1_gptdense_ON_rg.json",
    "gpt_dense_OFF": "local_gptsol_dense_dedupOFF.cc1_gptdense_OFF_rg.json",
    "qc_ON": "local_qwen3coder30b_dedupON.qwen30b_ON_rg.json",
    "qc_OFF": "local_qwen3coder30b_dedupOFF.qwen30b_OFF_rg.json",
    "qc_T": "local_qwen3coder30b_T.trimT_qwen30b_T.json",
    "q36_k12_ON": "local_qwen36_k12_dedupON.qwen36_k12_dedupON.json",
    "q36_k12_OFF": "local_qwen36_k12_dedupOFF.qwen36_k12_dedupOFF.json",
    "ds_ON": "local_dsv4_dedupON.dsv4_ON_rg.json",
    "ds_OFF": "local_dsv4_dedupOFF.dsv4_OFF_rg.json",
}
for _a in ("ON", "OFF", "T", "TM", "P"):
    for _s in range(3):
        REPORTS[f"b_{_a}_s{_s}"] = f"local_b1b3q30_{_a}_s{_s:02d}.b1b3_{_a}_s{_s:02d}.json"


class Arm:
    def __init__(self, key):
        self.key, self.file = key, REPORTS[key]
        d = json.loads((P5 / self.file).read_text(encoding="utf-8"))
        self.res = set(d["resolved_ids"])
        self.sub = set(d["submitted_ids"])
        self.err = set(d.get("error_ids", []))
        self.empty = set(d.get("empty_patch_ids", []))
        self.n_err = d.get("error_instances", len(self.err))


_cache = {}


def arm(key) -> Arm:
    if key not in _cache:
        _cache[key] = Arm(key)
    return _cache[key]


def dvec(ids, A: set, B: set):
    ids = sorted(ids)
    return np.array([int(i in A) - int(i in B) for i in ids], float), ids


# ------------------------------------------------------------------ basic tests
def mcnemar(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * stats.binom.cdf(min(b, c), n, 0.5))


def bc(d):
    d = np.asarray(d)
    return int((d > 0).sum()), int((d < 0).sum())


def iid(d):
    d = np.asarray(d, float)
    n = len(d)
    est = d.mean()
    se = d.std(ddof=1) / math.sqrt(n)
    return dict(est=est, se=se, ci95=(est - 1.959964 * se, est + 1.959964 * se),
                ci90=(est - 1.644854 * se, est + 1.644854 * se),
                p=2 * stats.norm.sf(abs(est / se)) if se > 0 else 1.0)


def cluster_sums(y, clusters):
    cl = np.asarray(clusters)
    labs = sorted(set(cl))
    S = np.array([y[cl == g].sum() for g in labs], float)
    n = np.array([(cl == g).sum() for g in labs], float)
    return S, n, labs


# ------------------------------------------------------------------ wild cluster bootstrap (WCR, Webb)
WEBB = np.array([-math.sqrt(1.5), -1.0, -math.sqrt(0.5), math.sqrt(0.5), 1.0, math.sqrt(1.5)])


def webb_weights(G, B, seed=SEED):
    rng = np.random.default_rng(seed)
    return WEBB[rng.integers(0, 6, size=(B, G))]


def wild_pfun_sums(S_y, n, W):
    """p(b0) for the WCR Webb bootstrap-t given cluster sums S_y, sizes n, weight matrix W (B x G).
    Identical algebra to reanalysis2/ra2.py::wild_pfun and common_ra.wild_cluster."""
    G = len(n)
    N = n.sum()
    c1 = G / (G - 1)
    est = S_y.sum() / N
    resid = S_y - n * est
    se = math.sqrt(c1 * (resid ** 2).sum()) / N

    def pval(b0):
        S = S_y - b0 * n
        t = (est - b0) / se
        m_star = (W * S).sum(1) / N
        Sstar = W * S - np.outer(m_star, n)
        se_star = np.sqrt(c1 * (Sstar ** 2).sum(1)) / N
        t_star = m_star / se_star
        return float(np.mean(np.abs(t_star) >= abs(t) - 1e-12))

    def tstar(b0):
        S = S_y - b0 * n
        m_star = (W * S).sum(1) / N
        Sstar = W * S - np.outer(m_star, n)
        se_star = np.sqrt(c1 * (Sstar ** 2).sum(1)) / N
        return m_star / se_star
    pval.tstar = tstar
    pval.se_cr1 = se
    pval.est = est
    return pval


def wild(y, clusters, B=B_WILD, seed=SEED, alphas=(0.05, 0.10), step=0.0005, hw=None):
    y = np.asarray(y, float)
    S, n, _ = cluster_sums(y, clusters)
    W = webb_weights(len(n), B, seed)
    pf = wild_pfun_sums(S, n, W)
    est = pf.est
    se_i = y.std(ddof=1) / math.sqrt(len(y))
    hw = hw or max(0.25, 8 * se_i)
    grid = np.arange(est - hw, est + hw + step / 2, step)
    ps = np.array([pf(b) for b in grid])
    out = dict(est=est, p=pf(0.0), se_cr1=pf.se_cr1, B=B)
    for al in alphas:
        idx = np.where(ps > al)[0]
        key = f"ci{int(round(100 * (1 - al)))}"
        if len(idx):
            out[key] = (float(grid[idx[0]]), float(grid[idx[-1]]))
            out[key + "_pieces"] = 1 + int((np.diff(idx) > 1).sum())
            out[key + "_at_edge"] = bool(idx[0] == 0 or idx[-1] == len(grid) - 1)
        else:
            out[key] = (float("nan"), float("nan"))
    out["_pf"], out["_grid"], out["_ps"] = pf, grid, ps
    return out


# ------------------------------------------------------------------ CR2 (Bell-McCaffrey)
def _inv_sqrt_psd(M):
    w, V = np.linalg.eigh(M)
    w = np.clip(w, 1e-12, None)
    return (V / np.sqrt(w)) @ V.T


def cr2_bm(y, clusters, X=None, c=None):
    """OLS with CR2 variance and BM Satterthwaite df for c'beta (copy of common_ra.cr2_bm)."""
    y = np.asarray(y, float)
    N = len(y)
    if X is None:
        X = np.ones((N, 1))
    X = np.asarray(X, float)
    p = X.shape[1]
    if c is None:
        c = np.zeros(p); c[0] = 1.0
    XtXi = np.linalg.inv(X.T @ X)
    beta = XtXi @ X.T @ y
    e = y - X @ beta
    cl = np.asarray(clusters)
    labs = sorted(set(cl))
    meat = np.zeros((p, p))
    Gcols = []
    for g in labs:
        idx = np.where(cl == g)[0]
        Xg = X[idx]
        Hgg = Xg @ XtXi @ Xg.T
        Ag = _inv_sqrt_psd(np.eye(len(idx)) - Hgg)
        u = Xg.T @ (Ag @ e[idx])
        meat += np.outer(u, u)
        v = Ag @ (Xg @ (XtXi @ c))
        col = -X @ (XtXi @ (Xg.T @ v))
        col[idx] += v
        Gcols.append(col)
    V = XtXi @ meat @ XtXi
    se = math.sqrt(float(c @ V @ c))
    G = np.column_stack(Gcols)
    M = G.T @ G
    df = float(np.trace(M) ** 2 / np.trace(M @ M))
    est = float(c @ beta)
    t = est / se if se > 0 else float("nan")
    pv = 2 * stats.t.sf(abs(t), df)
    q = stats.t.ppf(0.975, df)
    q90 = stats.t.ppf(0.95, df)
    return dict(est=est, se=se, df=df, t=t, p=pv, ci95=(est - q * se, est + q * se), ci90=(est - q90 * se, est + q90 * se))


def cr2_fast_factory(n):
    """Intercept-only CR2 from cluster sums. For X = 1, (I - H_gg)^(-1/2) acts on the cluster's
    1-direction by (1 - n_g/N)^(-1/2) and as identity elsewhere, so 1'A_g e_g = sum(e_g)/sqrt(1-n_g/N).
    BM df depends only on the cluster sizes; it is computed once (and checked against cr2_bm)."""
    n = np.asarray(n, float)
    N = n.sum()
    k = 1.0 / (1.0 - n / N)
    # df: same as cr2_bm on any y with these cluster sizes
    yy = np.zeros(int(N)); cl = np.repeat(np.arange(len(n)), n.astype(int))
    df = cr2_bm(yy + np.arange(int(N)) % 2, cl)["df"]

    def f(S):
        est = S.sum() / N
        r = S - n * est
        se = math.sqrt(float((k * r ** 2).sum())) / N
        t = est / se if se > 0 else 0.0
        return est, se, 2 * stats.t.sf(abs(t), df)
    f.df = df
    return f


# ------------------------------------------------------------------ exact repository sign-flip
def signflip(y, clusters):
    S, n, _ = cluster_sums(np.asarray(y, float), clusters)
    G = len(S)
    flips = np.array(list(itertools.product([1, -1], repeat=G)), float)
    T = flips @ S
    T0 = S.sum()
    return dict(p=float(np.mean(np.abs(T) >= abs(T0) - 1e-9)), G=G)


def signflip_sums(S, flips):
    T = flips @ S
    return float(np.mean(np.abs(T) >= abs(S.sum()) - 1e-9))


# ------------------------------------------------------------------ the REGISTERED percentile cluster bootstrap
def pct_boot(y, clusters, reps=5000, seed=20260714, stat_scale=1.0):
    """Exactly code/analysis/core/common.py::cluster_bootstrap applied to the mean of d (rows grouped by repo,
    repos sorted, rng.choice(repos) G times per rep, statistic = mean over the pooled resampled rows)."""
    y = np.asarray(y, float)
    S, n, labs = cluster_sums(y, clusters)
    rng = random.Random(seed)
    G = len(labs)
    idx = list(range(G))
    vals = []
    for _ in range(reps):
        k = [rng.choice(idx) for _ in idx]
        vals.append(S[k].sum() / n[k].sum())
    vals.sort()
    lo, hi = vals[int(0.025 * reps)], vals[int(0.975 * reps) - 1]
    lo90, hi90 = vals[int(0.05 * reps)], vals[int(0.95 * reps) - 1]
    p_le0 = sum(1 for v in vals if v <= 0) / reps
    p_ge0 = sum(1 for v in vals if v >= 0) / reps
    return dict(ci95=(lo, hi), ci90=(lo90, hi90), p_le0=p_le0, p_ge0=p_ge0, p2=min(1.0, 2 * min(p_le0, p_ge0)), reps=reps)


def inst_boot(y, reps=10000, seed=SEED, q=(0.025, 0.975)):
    y = np.asarray(y, float)
    rng = np.random.default_rng(seed)
    n = len(y)
    m = y[rng.integers(0, n, size=(reps, n))].mean(1)
    return np.quantile(m, q[0]), np.quantile(m, q[1])


def holm(p: dict):
    items = sorted(p.items(), key=lambda kv: kv[1])
    m, run, out = len(items), 0.0, {}
    for i, (k, v) in enumerate(items):
        run = max(run, min(1.0, (m - i) * v))
        out[k] = run
    return out


# ------------------------------------------------------------------ all methods on one d vector
def all_methods(d, ids, label="", pct=True, alphas=(0.05, 0.10)):
    d = np.asarray(d, float)
    cl = [repo(i) for i in ids]
    b, c = bc(d)
    r = dict(label=label, n=len(d), delta=float(d.mean()), b=b, c=c, mcnemar_p=mcnemar(b, c) if np.all(np.isin(d, (-1, 0, 1))) else None)
    r["iid"] = iid(d)
    w = wild(d, cl, alphas=alphas)
    r["wild"] = {k: v for k, v in w.items() if not k.startswith("_")}
    r["cr2"] = cr2_bm(d, cl)
    r["flip"] = signflip(d, cl)
    if pct:
        r["pct"] = pct_boot(d, cl)
    return r


# ------------------------------------------------------------------ formatting / output
def pp(x, nd=1, sign=True):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    v = 100 * x
    return f"{v:+.{nd}f}" if sign else f"{v:.{nd}f}"


def ci(t, nd=1):
    return f"[{pp(t[0], nd)}, {pp(t[1], nd)}]"


def fp(p):
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return "—"
    if p < 0.001:
        return f"{p:.1e}"
    return f"{p:.4f}" if p < 0.1 else f"{p:.3f}"


def strip(o):
    if isinstance(o, dict):
        return {str(k): strip(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (list, tuple)):
        return [strip(x) for x in o]
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, set):
        return sorted(o)
    return o


def dump(name, obj):
    (OUT / f"{name}.json").write_text(json.dumps(strip(obj), indent=1, default=str), encoding="utf-8")


def write_md(name, text):
    (OUT / f"{name}.md").write_text(text, encoding="utf-8")
    print(text)
