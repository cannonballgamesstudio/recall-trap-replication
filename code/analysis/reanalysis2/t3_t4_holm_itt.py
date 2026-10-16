"""Task 3: Holm over the 2-test confirmatory family (pre-registered exact McNemar), unrounded;
plus unrounded Holm for wild, CR2 and sign-flip p-values.
Task 4: ITT for never-submitted instances (scored as failures on the full 500) for Qwen3.6 K=4/12/40,
DeepSeek, dense; plus adversarial worst-case (ON never-submitted -> resolved, OFF never-submitted -> failed).
"""
import math

from ra2 import arm, paired, ALL, pp, ci, fp, write_md, dump, cra


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    m = len(ps)
    adj = [0.0] * m
    run = 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (m - r) * ps[i]))
        adj[i] = run
    return adj


fam = []
for lab, on, off in (("Qwen3.6-27B K=12", "q36_k12_ON", "q36_k12_OFF"),
                     ("gpt-5.6-sol logged re-run", "gpt_lr_ON", "gpt_lr_OFF")):
    A_on, A_off = arm(on), arm(off)
    r = paired(A_on.sub & A_off.sub, A_off.res, A_on.res, lab)
    fam.append(r)

L = ["## Task 3 — Holm over the confirmatory family (2 tests), unrounded", "",
     "Pre-registered test = exact two-sided McNemar. Wild p is Monte-Carlo (B=9,999): MC SE = √(p(1−p)/B) shown. Holm step-down: p(1)·2, max(p(1)·2, p(2)·1).", "",
     "| test | n | Δ | b/c | method | raw p | Holm-adjusted p | survives at 0.05 |", "|---|---|---|---|---|---|---|---|"]
out3 = {}
for meth, key in (("exact McNemar (pre-registered)", "mcnemar_p"), ("wild cluster (Webb)", "wild_p"),
                  ("CR2 (BM df)", "cr2_p"), ("repo sign-flip (exact)", "flip_p")):
    ps = [r[key] for r in fam]
    adj = holm(ps)
    out3[key] = dict(raw=ps, holm=adj)
    for r, p, a in zip(fam, ps, adj):
        extra = f" (MC SE {math.sqrt(p*(1-p)/9999):.4f})" if key == "wild_p" else ""
        L.append(f"| {r['label']} | {r['n']} | {pp(r['delta'], 2)} | {r['b']}/{r['c']} | {meth} | {p:.6f}{extra} | {a:.6f} | {'yes' if a < 0.05 else 'NO'} |")
L.append("")

# ---------------------------------------------------------------- Task 4
arms4 = [("Qwen3.6-27B K=4", "q36_k4_ON", "q36_k4_OFF"), ("Qwen3.6-27B K=12", "q36_k12_ON", "q36_k12_OFF"),
         ("Qwen3.6-27B K=40", "q36_k40_ON", "q36_k40_OFF"), ("DeepSeek-v4-pro", "ds_ON", "ds_OFF"),
         ("dense control (gpt)", "gpt_dense_ON", "gpt_dense_OFF")]
L += ["## Task 4 — ITT: never-submitted scored as failures on the full 500", "",
      "PP = per-protocol (pairwise exclusion of never-submitted, the paper's estimand). ITT = all 500, never-submitted = unresolved. "
      "Worst case = ITT but every ON never-submitted instance counted as resolved (OFF never-submitted stay failed): the adversarial bound against OFF−ON > 0.", "",
      "| arm | never-sub ON/OFF | estimand | n | ON | OFF | Δ | b/c | McNemar p | wild 95% CI | wild p | CR2 p | flip p |",
      "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
out4 = {}
for lab, on, off in arms4:
    A_on, A_off = arm(on), arm(off)
    ns_on, ns_off = set(ALL) - A_on.sub, set(ALL) - A_off.sub
    rs = {
        "PP": paired(A_on.sub & A_off.sub, A_off.res, A_on.res),
        "ITT": paired(ALL, A_off.res, A_on.res),
        "worst case": paired(ALL, A_off.res, A_on.res | ns_on),
    }
    out4[lab] = dict(ns_on=len(ns_on), ns_off=len(ns_off), ns_both=len(ns_on & ns_off), **rs)
    for est, r in rs.items():
        L.append(f"| {lab} | {len(ns_on)}/{len(ns_off)} (both {len(ns_on & ns_off)}) | {est} | {r['n']} | {r['B']} | {r['A']} | {pp(r['delta'], 2)} | {r['b']}/{r['c']} | "
                 f"{fp(r['mcnemar_p'])} | {ci(r['wild_ci95'])} | {fp(r['wild_p'])} | {fp(r['cr2_p'])} | {fp(r['flip_p'])} |")
L.append("")
write_md("t3_t4_holm_itt", "\n".join(L) + "\n")
dump("t3_t4_holm_itt", {"holm": out3, "family": fam, "itt": out4})
