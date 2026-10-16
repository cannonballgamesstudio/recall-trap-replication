"""Shared helpers for the replication analyses.

All paths are relative to the package root, so run the scripts from there:
    python code/analysis/core/build_inclusion_table.py
"""
from __future__ import annotations

import csv
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SV = ROOT / "data" / "swe-verified"
RESULTS = ROOT / "results" / "core"
ARMS = json.loads((ROOT / "data" / "arms.json").read_text(encoding="utf-8"))
INSTANCES = {c["instance_id"]: c for c in json.loads((SV / "inputs" / "instances_verified.json").read_text(encoding="utf-8"))}
ALL_IDS = sorted(INSTANCES)

STATUSES = ("resolved", "unresolved", "empty", "harness_error", "never_predicted")


def repo_of(iid: str) -> str:
    return INSTANCES[iid]["repo"] if iid in INSTANCES else iid.split("__")[0]


def load_report(name: str) -> dict:
    return json.loads((SV / "grading" / "summary" / name).read_text(encoding="utf-8"))


def statuses_from_report(rep: dict) -> dict[str, str]:
    """Mutually exclusive per-instance status from an official SWE-bench run report.

    never_predicted = not among the run's submitted predictions.
    empty           = submitted with an empty patch (counted as a failure, never dropped).
    harness_error   = submitted, non-empty, but the harness errored (counted as a failure).
    """
    sub = set(rep["submitted_ids"])
    empty = set(rep["empty_patch_ids"])
    res = set(rep["resolved_ids"])
    unres = set(rep["unresolved_ids"])
    err = set(rep["error_ids"])
    out = {}
    for iid in ALL_IDS:
        if iid not in sub:
            out[iid] = "never_predicted"
        elif iid in empty:
            out[iid] = "empty"
        elif iid in res:
            out[iid] = "resolved"
        elif iid in unres:
            out[iid] = "unresolved"
        elif iid in err:
            out[iid] = "harness_error"
        else:
            out[iid] = "harness_error"  # submitted but no outcome recorded
    return out


def load_inclusion() -> dict[tuple[str, str], dict[str, str]]:
    """(arm_id, side) -> {instance_id: status} from results/inclusion_table.csv."""
    tab: dict[tuple[str, str], dict[str, str]] = {}
    with open(RESULTS / "inclusion_table.csv", newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            tab.setdefault((row["arm_id"], row["side"]), {})[row["instance_id"]] = row["status"]
    return tab


# ---------------------------------------------------------------- statistics
def binom_two_sided(k: int, n: int) -> float:
    """Exact two-sided McNemar p (binomial, p=0.5) for k successes of n discordant pairs."""
    if n == 0:
        return 1.0
    k = min(k, n - k)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def paired(on: dict[str, str], off: dict[str, str], missing_as_empty: bool = False,
           universe: list[str] | None = None) -> dict:
    """Paired contrast OFF - ON. Empties and harness errors are failures; never-predicted
    instances are excluded pairwise (unless missing_as_empty)."""
    ids = universe or ALL_IDS
    rows = []
    for iid in ids:
        a, b = on.get(iid, "never_predicted"), off.get(iid, "never_predicted")
        if missing_as_empty:
            a = "empty" if a == "never_predicted" else a
            b = "empty" if b == "never_predicted" else b
        if a == "never_predicted" or b == "never_predicted":
            continue
        rows.append((iid, a, b))
    n = len(rows)
    r_on = sum(1 for _, a, _ in rows if a == "resolved")
    r_off = sum(1 for _, _, b in rows if b == "resolved")
    off_only = sum(1 for _, a, b in rows if b == "resolved" and a != "resolved")
    on_only = sum(1 for _, a, b in rows if a == "resolved" and b != "resolved")
    cond = [(a, b) for _, a, b in rows if a != "empty" and b != "empty"]
    c_off = sum(1 for a, b in cond if b == "resolved" and a != "resolved")
    c_on = sum(1 for a, b in cond if a == "resolved" and b != "resolved")
    e_on = sum(1 for _, a, _ in rows if a == "empty")
    e_off = sum(1 for _, _, b in rows if b == "empty")
    return dict(n=n, res_on=r_on, res_off=r_off, rate_on=r_on / n if n else float("nan"),
                rate_off=r_off / n if n else float("nan"), delta_pp=100 * (r_off - r_on) / n if n else float("nan"),
                disc_off=off_only, disc_on=on_only, p_raw=binom_two_sided(off_only, off_only + on_only),
                n_cond=len(cond), disc_off_cond=c_off, disc_on_cond=c_on,
                p_cond=binom_two_sided(c_off, c_off + c_on),
                empty_on=e_on, empty_off=e_off, rows=rows)


def cluster_bootstrap(rows, stat, reps: int = 5000, seed: int = 20260714):
    """Repository-cluster bootstrap of stat(rows); returns (lo, hi, P(stat<=0))."""
    by_repo: dict[str, list] = {}
    for r in rows:
        by_repo.setdefault(repo_of(r[0]), []).append(r)
    repos = sorted(by_repo)
    rng = random.Random(seed)
    vals = []
    for _ in range(reps):
        sample = []
        for _ in repos:
            sample.extend(by_repo[rng.choice(repos)])
        vals.append(stat(sample))
    vals.sort()
    lo = vals[int(0.025 * reps)]
    hi = vals[int(0.975 * reps) - 1]
    p_le0 = sum(1 for v in vals if v <= 0) / reps
    return lo, hi, p_le0


def delta_stat(rows) -> float:
    n = len(rows)
    return 100 * (sum(1 for _, a, b in rows if b == "resolved") - sum(1 for _, a, b in rows if a == "resolved")) / n


def loro(rows):
    repos = sorted({repo_of(r[0]) for r in rows})
    out = {}
    for rp in repos:
        sub = [r for r in rows if repo_of(r[0]) != rp]
        out[rp] = delta_stat(sub)
    return out


def holm(pvals: dict[str, float]) -> dict[str, float]:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    adj, running = {}, 0.0
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        adj[k] = running
    return adj


def decomposition(rows) -> dict:
    """Exact product decomposition dR = Q_on*dA + A_on*dQ + dA*dQ (reference = ON)."""
    n = len(rows)
    a_on = sum(1 for _, a, _ in rows if a != "empty") / n
    a_off = sum(1 for _, _, b in rows if b != "empty") / n
    q_on = sum(1 for _, a, _ in rows if a == "resolved") / max(1, sum(1 for _, a, _ in rows if a != "empty"))
    q_off = sum(1 for _, _, b in rows if b == "resolved") / max(1, sum(1 for _, _, b in rows if b != "empty"))
    dA, dQ = a_off - a_on, q_off - q_on
    dR = a_off * q_off - a_on * q_on
    t1, t2, t3 = q_on * dA, a_on * dQ, dA * dQ
    return dict(dA_pp=100 * dA, dR_pp=100 * dR, prod_pp=100 * t1, qual_pp=100 * t2, inter_pp=100 * t3,
                prod_share=t1 / dR if dR else float("nan"), qual_share=t2 / dR if dR else float("nan"),
                inter_share=t3 / dR if dR else float("nan"))


def write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    keys = list(rows[0].keys())
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
