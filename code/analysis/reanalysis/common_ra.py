"""Shared loaders + small-sample clustered inference for the $0 MSR reanalysis.

Read-only over the replication package. No model calls, no Docker.
"""
from __future__ import annotations

import csv
import itertools
import json
import math
import re
from pathlib import Path

import numpy as np
from scipy import stats

PKG = Path(__file__).resolve().parents[3]
SV = PKG / "data" / "swe-verified"
OUT = PKG / "results" / "reanalysis"
SEED = 20261014
B_WILD = 9999

INSTANCES = {c["instance_id"]: c for c in json.loads((SV / "inputs" / "instances_verified.json").read_text(encoding="utf-8"))}
ALL_IDS = sorted(INSTANCES)


def repo_of(iid: str) -> str:
    return INSTANCES[iid]["repo"]


def load_table():
    """(arm, side) -> {iid: {status, fin, ...}}"""
    tab = {}
    with open(PKG / "results" / "core" / "inclusion_table.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            tab.setdefault((r["arm_id"], r["side"]), {})[r["instance_id"]] = r
    return tab


def paired_rows(tab, arm, arm_off=None, side_on="ON", side_off="OFF"):
    """Pairwise exclusion of never_predicted. Returns list of dicts with on/off rows."""
    on = tab[(arm, side_on)]
    off = tab[(arm_off or arm, side_off)]
    out = []
    for iid in ALL_IDS:
        a, b = on.get(iid), off.get(iid)
        if a is None or b is None:
            continue
        if a["status"] == "never_predicted" or b["status"] == "never_predicted":
            continue
        out.append(dict(iid=iid, repo=repo_of(iid), on=a, off=b,
                        y_on=int(a["status"] == "resolved"), y_off=int(b["status"] == "resolved")))
    return out


def d_vector(rows):
    return np.array([r["y_off"] - r["y_on"] for r in rows], float), [r["repo"] for r in rows]


def mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * stats.binom.cdf(min(b, c), n, 0.5))


# ------------------------------------------------------------------ gold-file locality
_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@")
_FILE = re.compile(r"^--- (?:a/)?(.+?)\s*$")
_NEWF = re.compile(r"^\+\+\+ (?:b/)?(.+?)\s*$")


def gold_file_counts():
    """Distinct pre-image files touched by the gold patch (same rule as stratify_locality.py)."""
    gold = json.loads((SV / "inputs" / "gold_patches.json").read_text(encoding="utf-8"))
    out = {}
    for iid, patch in gold.items():
        files, path = set(), None
        for line in patch.splitlines():
            m = _FILE.match(line)
            if m:
                raw = m.group(1)
                path = None if raw == "/dev/null" else raw.replace("\\", "/")
                continue
            if _NEWF.match(line):
                continue
            if _HUNK.match(line) and path:
                files.add(path)
        out[iid] = len(files)
    return out


# ------------------------------------------------------------------ clustered inference
def _inv_sqrt_psd(M):
    w, V = np.linalg.eigh(M)
    w = np.clip(w, 1e-12, None)
    return (V / np.sqrt(w)) @ V.T


def cr2_bm(y, clusters, X=None, c=None):
    """OLS with CR2 (Bell-McCaffrey) variance and BM Satterthwaite df for contrast c'beta.

    Default: intercept-only (y = beta + e), i.e. inference on the mean paired difference.
    Returns dict(est, se, df, t, p, lo, hi).
    """
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
        # BM df ingredient: G_g = (I-H)_{g.}' A_g X_g (X'X)^-1 c
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
    return dict(est=est, se=se, df=df, t=t, p=pv, lo=est - q * se, hi=est + q * se)


def webb_weights(G, B, seed=SEED):
    rng = np.random.default_rng(seed)
    vals = np.array([-math.sqrt(1.5), -1.0, -math.sqrt(0.5), math.sqrt(0.5), 1.0, math.sqrt(1.5)])
    return vals[rng.integers(0, 6, size=(B, G))]


def _cluster_sums(y, clusters):
    cl = np.asarray(clusters)
    labs = sorted(set(cl))
    S = np.array([y[cl == g].sum() for g in labs])
    n = np.array([(cl == g).sum() for g in labs], float)
    return S, n


def wild_cluster(y, clusters, B=B_WILD, seed=SEED, alpha=0.05):
    """Wild cluster restricted (WCR) bootstrap-t for the mean, Webb 6-point weights, CR1 t-stat.

    p-value for H0: mean = 0; CI by test inversion (same weight draws at every null value).
    """
    y = np.asarray(y, float)
    N = len(y)
    S_y, n = _cluster_sums(y, clusters)
    G = len(n)
    W = webb_weights(G, B, seed)
    c1 = G / (G - 1) * (N - 1) / (N - 1)  # intercept-only: K=1
    est = y.sum() / N

    def pval(b0):
        S = S_y - b0 * n                    # cluster sums of null residuals
        resid_sums = S - n * (est - b0)     # observed residuals around est
        se = math.sqrt(c1 * (resid_sums ** 2).sum()) / N
        t = (est - b0) / se
        m_star = (W * S).sum(1) / N        # mean* - b0
        Sstar = W * S - np.outer(m_star, n)
        se_star = np.sqrt(c1 * (Sstar ** 2).sum(1)) / N
        t_star = m_star / se_star
        return float(np.mean(np.abs(t_star) >= abs(t) - 1e-12))

    p0 = pval(0.0)
    sd = max(1e-6, float(np.std(y)) * 4 / math.sqrt(N))

    def bound(direction):
        lo_, hi_ = est, est + direction * sd
        k = 0
        while pval(hi_) > alpha and k < 60:
            lo_, hi_ = hi_, hi_ + direction * sd; k += 1
        for _ in range(40):
            mid = (lo_ + hi_) / 2
            if pval(mid) > alpha:
                lo_ = mid
            else:
                hi_ = mid
        return (lo_ + hi_) / 2

    return dict(est=est, p=p0, lo=bound(-1), hi=bound(+1), B=B)


def signflip(y, clusters):
    """Exact repository-level randomization (sign-flip) test over all 2^G flips.

    Statistic = sum of instance differences (= N * mean); clusters exchangeable in sign under H0.
    Also returns the studentized (CR1-t) version.
    """
    y = np.asarray(y, float)
    S, n = _cluster_sums(y, clusters)
    G = len(S)
    N = len(y)
    flips = np.array(list(itertools.product([1, -1], repeat=G)), float)
    T = flips @ S
    T0 = S.sum()
    p = float(np.mean(np.abs(T) >= abs(T0) - 1e-9))
    p_one = float(np.mean(T >= T0 - 1e-9))
    # studentized
    def tstat(Sv):
        m = Sv.sum(-1) / N
        r = Sv - np.multiply.outer(m, n) if Sv.ndim > 1 else Sv - m * n
        se = np.sqrt((G / (G - 1)) * (r ** 2).sum(-1)) / N
        return m / se
    Tt = tstat(flips * S)
    t0 = tstat(S)
    p_t = float(np.mean(np.abs(Tt) >= abs(t0) - 1e-9))
    return dict(p=p, p_one=p_one, p_t=p_t, G=G, nflips=len(flips))


def fmt_p(p):
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return "—"
    if p < 0.001:
        return f"{p:.1e}"
    return f"{p:.4f}" if p < 0.1 else f"{p:.3f}"
