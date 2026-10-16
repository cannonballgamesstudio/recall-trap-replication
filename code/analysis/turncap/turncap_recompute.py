"""Recompute the Qwen3-Coder-30B-A3B (OpenRouter) read-budget sweep (paper Table V, Sec. V-B "Read budget")
from the released harness reports and per-instance loop metrics. No model calls. Run from the package root:

    python code/analysis/turncap/turncap_recompute.py

Reads data/turncap-sweep/ (plain or .gz) and the single-shot anchor pair in data/swe-verified/grading/summary/.
Writes results/turncap-sweep/turncap_recompute.{md,json}."""
import gzip, json, math, itertools, random, statistics
from pathlib import Path
from scipy.stats import binomtest
import numpy as np

PKG = Path(__file__).resolve().parents[3]
P5 = PKG / "data" / "turncap-sweep"
ANCHOR = PKG / "data" / "swe-verified" / "grading" / "summary"
OUT = PKG / "results" / "turncap-sweep"
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(20261016)

def load_report(path):
    r = json.load(open(path))
    return set(r["submitted_ids"]), set(r["resolved_ids"]), set(r["empty_patch_ids"]), set(r.get("error_ids", []))

def load_raw(path):
    rows = {}
    path = Path(path)
    fh = open(path, encoding="utf8") if path.exists() else gzip.open(str(path) + ".gz", "rt", encoding="utf8")
    for l in fh:
        x = json.loads(l); rows[x["instance_id"]] = x  # last row wins
    return rows

def mcnemar(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, binomtest(b, n, 0.5).pvalue)

def repo_of(iid): return iid.split("__")[0] + "__" + iid.split("__")[1].rsplit("-", 1)[0]

def wild_p(d, repos, B=9999):
    """WCR wild cluster bootstrap-t, Webb 6-point weights, CR1 studentization, null imposed (mean 0)."""
    d = np.asarray(d, float); G = sorted(set(repos)); idx = {g: np.where(np.array(repos) == g)[0] for g in G}
    n = len(d); k = len(G)
    def tstat(x):
        m = x.mean(); r = x - m
        s = np.array([r[idx[g]].sum() for g in G])
        se = math.sqrt((k / (k - 1)) * (n - 1) / (n - 1) * (s ** 2).sum()) / n
        return m / se if se > 0 else 0.0
    t0 = tstat(d)
    r0 = d - 0.0  # restricted residuals under H0: mean 0
    webb = np.array([-math.sqrt(1.5), -1, -math.sqrt(0.5), math.sqrt(0.5), 1, math.sqrt(1.5)])
    cnt = 0
    for _ in range(B):
        w = rng.choice(webb, size=k)
        x = np.empty(n)
        for gi, g in enumerate(G): x[idx[g]] = 0.0 + w[gi] * r0[idx[g]]
        if abs(tstat(x)) >= abs(t0) - 1e-12: cnt += 1
    return (cnt + 1) / (B + 1)

def flip_p(d, repos):
    G = sorted(set(repos)); s = np.array([sum(di for di, r in zip(d, repos) if r == g) for g in G])
    obs = abs(s.sum()); cnt = 0; tot = 0
    for signs in itertools.product([1, -1], repeat=len(G)):
        tot += 1
        if abs((s * np.array(signs)).sum()) >= obs - 1e-9: cnt += 1
    return cnt / tot

def boot_ci(d, B=10000):
    d = np.asarray(d, float); n = len(d)
    bs = np.array([d[rng.integers(0, n, n)].mean() for _ in range(B)]) * 100
    return np.percentile(bs, [2.5, 97.5])

def contrast(on, off):
    sub_on, res_on, emp_on, _ = on; sub_off, res_off, emp_off, _ = off
    ids = sorted(sub_on & sub_off)
    d = [(1 if i in res_off else 0) - (1 if i in res_on else 0) for i in ids]
    b = sum(1 for x in d if x > 0); c = sum(1 for x in d if x < 0)
    repos = [repo_of(i) for i in ids]
    both = [i for i in ids if i not in emp_on and i not in emp_off]
    dc = [(1 if i in res_off else 0) - (1 if i in res_on else 0) for i in both]
    bc = sum(1 for x in dc if x > 0); cc = sum(1 for x in dc if x < 0)
    out = dict(n=len(ids), on=sum(1 for i in ids if i in res_on), off=sum(1 for i in ids if i in res_off),
               delta=100 * np.mean(d), b=b, c=c, p=mcnemar(b, c), ci=boot_ci(d).round(2).tolist(),
               wild_p=round(wild_p(d, repos), 4), flip_p=round(flip_p(d, repos), 4),
               emp_on=100 * sum(1 for i in ids if i in emp_on) / len(ids), emp_off=100 * sum(1 for i in ids if i in emp_off) / len(ids),
               cond_n=len(both), cond_delta=100 * np.mean(dc) if both else float("nan"), cond_b=bc, cond_c=cc, cond_p=mcnemar(bc, cc))
    return out

rows = {}
# single-shot anchor: headline local Qwen3-Coder pair
a = contrast(load_report(ANCHOR / "local_qwen3coder30b_dedupON.qwen30b_ON_rg.json"), load_report(ANCHOR / "local_qwen3coder30b_dedupOFF.qwen30b_OFF_rg.json"))
a.update(cap=1, turns_on=None, turns_off=None, ctx_on=None, ctx_off=None, t0_on=0, t0_off=0)
rows["single-shot"] = a
for cap in [2, 3, 5, 10, 30]:
    on = load_report(P5 / f"agentic_qwen3coder30b_or_t{cap}_dedupON.or_t{cap}_dedupON.json")
    off = load_report(P5 / f"agentic_qwen3coder30b_or_t{cap}_dedupOFF.or_t{cap}_dedupOFF.json")
    r = contrast(on, off)
    ron = load_raw(P5 / f"raw_agentic_qwen3coder30b_or_t{cap}_dedupON.jsonl")
    roff = load_raw(P5 / f"raw_agentic_qwen3coder30b_or_t{cap}_dedupOFF.jsonl")
    r.update(cap=cap,
             turns_on=statistics.mean(x["turns"] for x in ron.values()), turns_off=statistics.mean(x["turns"] for x in roff.values()),
             ctx_on=statistics.mean(x["peak_ctx"] for x in ron.values()), ctx_off=statistics.mean(x["peak_ctx"] for x in roff.values()),
             t0_on=sum(1 for x in ron.values() if x["turns"] == 0), t0_off=sum(1 for x in roff.values() if x["turns"] == 0),
             err_on=len(on[3]), err_off=len(off[3]))
    rows[f"cap{cap}"] = r

lines = ["| arm | cap | n | ON% | OFF% | D | b/c | McN p | inst 95% CI | wild p | flip p | empty ON/OFF % | cond n; D; b/c; p | mean turns ON/OFF | mean peak_ctx ON/OFF | turns==0 ON/OFF | err |", "|---|" * 17]
for k, r in rows.items():
    lines.append(f"| {k} | {r['cap']} | {r['n']} | {100*r['on']/r['n']:.1f} | {100*r['off']/r['n']:.1f} | {r['delta']:+.2f} | {r['b']}/{r['c']} | {r['p']:.4f} | [{r['ci'][0]:+.2f}, {r['ci'][1]:+.2f}] | {r['wild_p']} | {r['flip_p']} | {r['emp_on']:.1f}/{r['emp_off']:.1f} | {r['cond_n']}; {r['cond_delta']:+.2f}; {r['cond_b']}/{r['cond_c']}; {r['cond_p']:.3f} | {r['turns_on'] if r['turns_on'] is None else round(r['turns_on'],1)}/{r['turns_off'] if r['turns_off'] is None else round(r['turns_off'],1)} | {r['ctx_on'] if r['ctx_on'] is None else round(r['ctx_on'])}/{r['ctx_off'] if r['ctx_off'] is None else round(r['ctx_off'])} | {r['t0_on']}/{r['t0_off']} | {r.get('err_on',1)}/{r.get('err_off',0)} |")
md = "\n".join(lines)
print(md)
(OUT / "turncap_recompute.md").write_text(md, encoding="utf8")
json.dump(rows, open(OUT / "turncap_recompute.json", "w"), indent=1, default=float)
