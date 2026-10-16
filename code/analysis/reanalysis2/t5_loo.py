"""Task 5: leave-django-out (McNemar), per-repository delta and b/c, leave-one-repo-out range.
Contrasts: confirmatory pair, gpt discovery draw (reference), DeepSeek, dense, both T decompositions."""
from collections import defaultdict

from ra2 import arm, paired, VIOL, repo, pp, fp, write_md, dump

C = []


def add(lab, ids, A, B):
    C.append((lab, sorted(ids), A, B))


def pair(lab, on, off):
    a, b = arm(on), arm(off)
    add(lab, a.sub & b.sub, b.res, a.res)


pair("Qwen3.6-27B K=12 (confirmatory)", "q36_k12_ON", "q36_k12_OFF")
pair("gpt logged re-run (confirmatory)", "gpt_lr_ON", "gpt_lr_OFF")
pair("gpt discovery draw", "gpt_hl_ON", "gpt_hl_OFF")
pair("DeepSeek-v4-pro", "ds_ON", "ds_OFF")
pair("dense control (gpt)", "gpt_dense_ON", "gpt_dense_OFF")
for m, on, off, T in (("QC", "qc_ON", "qc_OFF", "qc_T"), ("gpt(disc. refs)", "gpt_hl_ON", "gpt_hl_OFF", "gpt_T"),
                      ("gpt(re-run refs)", "gpt_lr_ON", "gpt_lr_OFF", "gpt_T")):
    a, b, t = arm(on), arm(off), arm(T)
    ids = (a.sub & b.sub & t.sub) - set(VIOL)
    add(f"{m} T: OFF−ON", ids, b.res, a.res)
    add(f"{m} T: OFF−T", ids, b.res, t.res)
    add(f"{m} T: T−ON", ids, t.res, a.res)

repos = sorted({repo(i) for _, ids, _, _ in C for i in ids})
short = {r: r.split("/")[1] for r in repos}

L = ["## Task 5 — Leave-django-out, per-repository Δ, leave-one-repo-out range", "",
     "Δ = first arm − second arm (pp); b/c = first-only/second-only. LOO = drop one repository at a time (12 fits); range over the 12. "
     "QC = Qwen3-Coder-30B; T rows on the 473.", "",
     "| contrast | full: n, Δ, b/c, p | without django: n, Δ, b/c, McNemar p | LOO Δ range (repo dropped) | LOO max McNemar p (repo dropped) | LOO sign changes? |",
     "|---|---|---|---|---|---|"]
out = {}
per_repo_tab = {}
for lab, ids, A, B in C:
    full = paired(ids, A, B, cluster=False)
    nod = paired([i for i in ids if repo(i) != "django/django"], A, B, cluster=False)
    loo = {}
    for r in repos:
        sub = [i for i in ids if repo(i) != r]
        loo[r] = paired(sub, A, B, cluster=False)
    lo_r = min(loo, key=lambda r: loo[r]["delta"]); hi_r = max(loo, key=lambda r: loo[r]["delta"])
    pmax_r = max(loo, key=lambda r: loo[r]["mcnemar_p"])
    signs = {int(v["delta"] > 0) - int(v["delta"] < 0) for v in loo.values()}
    L.append(f"| {lab} | {full['n']}, {pp(full['delta'], 2)}, {full['b']}/{full['c']}, {fp(full['mcnemar_p'])} | "
             f"{nod['n']}, {pp(nod['delta'], 2)}, {nod['b']}/{nod['c']}, {fp(nod['mcnemar_p'])} | "
             f"{pp(loo[lo_r]['delta'], 2)} ({short[lo_r]}) to {pp(loo[hi_r]['delta'], 2)} ({short[hi_r]}) | "
             f"{fp(loo[pmax_r]['mcnemar_p'])} ({short[pmax_r]}) | {'YES' if len(signs) > 1 else 'no'} |")
    pr = {}
    for r in repos:
        s = [i for i in ids if repo(i) == r]
        if s:
            x = paired(s, A, B, cluster=False)
            pr[r] = (x["n"], x["delta"], x["b"], x["c"])
    per_repo_tab[lab] = pr
    out[lab] = dict(full=full, no_django=nod, loo={r: v for r, v in loo.items()}, per_repo=pr)
L.append("")
L.append("Per-repository Δ (pp) and b/c (n in header is the confirmatory gpt re-run's n per repo; T rows use the 473):")
L.append("")
L.append("| contrast | " + " | ".join(short[r] for r in repos) + " |")
L.append("|---|" + "---|" * len(repos))
L.append("| n (gpt re-run) | " + " | ".join(str(per_repo_tab['gpt logged re-run (confirmatory)'].get(r, (0,))[0]) for r in repos) + " |")
for lab in per_repo_tab:
    cells = []
    for r in repos:
        v = per_repo_tab[lab].get(r)
        cells.append("—" if v is None else f"{100*v[1]:+.1f} ({v[2]}/{v[3]})")
    L.append(f"| {lab} | " + " | ".join(cells) + " |")
L.append("")
write_md("t5_loo", "\n".join(L) + "\n")
dump("t5_loo", out)
