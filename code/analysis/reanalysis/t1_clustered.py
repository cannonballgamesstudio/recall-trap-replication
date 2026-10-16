"""Task 1: small-sample repository-clustered inference (12 clusters) for every primary contrast.

Per contrast: instance-paired difference d_i = y_OFF - y_ON (pairwise exclusion of never-submitted),
  - wild cluster restricted bootstrap-t (Webb 6-point, 9,999 reps), p and test-inversion 95% CI
  - CR2 SE with Bell-McCaffrey Satterthwaite df, t-based 95% CI and p
  - exact repository sign-flip randomization test (all 2^12 flips)
Cross-retriever interactions use the instance-paired difference-in-differences
dd_i = d_i(X) - d_i(Y) on instances paired in both arms.
"""
from __future__ import annotations

import json
import numpy as np

from common_ra import (OUT, load_table, paired_rows, d_vector, mcnemar_exact, cr2_bm, wild_cluster,
                       signflip, fmt_p, repo_of)

CONTRASTS = [
    ("gpt-5.6-sol fusion (P1)", "P1_gpt_fusion"),
    ("gpt logged re-run (F1)", "F1_gpt_logged_replication"),
    ("Qwen3.6-27B K=12 (P3)", "P3_qwen36_fusion_K12"),
    ("DeepSeek-v4 (P2)", "P2_deepseek_fusion"),
    ("DENSE-1 (P4)", "P4_DENSE1_gpt_dense"),
    ("gpt BM25 (R1)", "R1_gpt_bm25"),
]
INTERACTIONS = [
    ("fusion − BM25", "P1_gpt_fusion", "R1_gpt_bm25"),
    ("dense − BM25", "P4_DENSE1_gpt_dense", "R1_gpt_bm25"),
    ("fusion − dense", "P1_gpt_fusion", "P4_DENSE1_gpt_dense"),
]


def analyse(d, cl):
    cr = cr2_bm(d, cl)
    wb = wild_cluster(d, cl)
    sf = signflip(d, cl)
    n = len(d)
    se_inst = float(np.std(d, ddof=1) / np.sqrt(n))
    return dict(n=n, G=len(set(cl)), est_pp=100 * float(np.mean(d)), se_inst_pp=100 * se_inst,
                wild_lo=100 * wb["lo"], wild_hi=100 * wb["hi"], wild_p=wb["p"],
                cr2_se_pp=100 * cr["se"], cr2_df=cr["df"], cr2_lo=100 * cr["lo"], cr2_hi=100 * cr["hi"], cr2_p=cr["p"],
                signflip_p=sf["p"], signflip_p_one=sf["p_one"], signflip_t_p=sf["p_t"])


def main():
    tab = load_table()
    res = []
    dvecs = {}
    for label, arm in CONTRASTS:
        rows = paired_rows(tab, arm)
        d, cl = d_vector(rows)
        dvecs[arm] = {r["iid"]: r["y_off"] - r["y_on"] for r in rows}
        b = int((d > 0).sum()); c = int((d < 0).sum())
        rec = dict(contrast=label, arm=arm, b=b, c=c, mcnemar_p=mcnemar_exact(b, c),
                   res_on=sum(r["y_on"] for r in rows), res_off=sum(r["y_off"] for r in rows), **analyse(d, cl))
        res.append(rec)
    for label, x, y in INTERACTIONS:
        ids = sorted(set(dvecs[x]) & set(dvecs[y]))
        dd = np.array([dvecs[x][i] - dvecs[y][i] for i in ids], float)
        cl = [repo_of(i) for i in ids]
        marg = 100 * (np.mean(list(dvecs[x].values())) - np.mean(list(dvecs[y].values())))
        rec = dict(contrast=f"interaction {label}", arm=f"{x} vs {y}", b=None, c=None, mcnemar_p=None,
                   marginal_did_pp=float(marg), **analyse(dd, cl))
        res.append(rec)
    (OUT / "t1_clustered.json").write_text(json.dumps(res, indent=1), encoding="utf-8")

    L = ["## Task 1 — Small-sample repository-clustered inference (G=12 repositories)", "",
         "Δ = dedup-OFF − dedup-ON (pp), instance-paired, never-submitted excluded pairwise. Wild = wild cluster "
         "restricted bootstrap-t, Webb 6-point weights, B=9,999, CR1 studentization, CI by test inversion. "
         "CR2 = Bell–McCaffrey bias-reduced SE with BM Satterthwaite df. Sign-flip = exact repository-level "
         "randomization over all 2^12 = 4,096 sign assignments of repository totals (two-sided). Interactions = "
         "instance-paired difference-in-differences on the overlapping instances.", "",
         "| contrast | n | Δ (pp) | disc OFF/ON | McNemar p | wild 95% CI | wild p | CR2 SE (df) | CR2 95% CI | CR2 p | sign-flip p |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in res:
        disc = f"{r['b']}/{r['c']}" if r["b"] is not None else "—"
        L.append(f"| {r['contrast']} | {r['n']} | {r['est_pp']:+.2f} | {disc} | {fmt_p(r['mcnemar_p'])} | "
                 f"[{r['wild_lo']:+.1f}, {r['wild_hi']:+.1f}] | {fmt_p(r['wild_p'])} | {r['cr2_se_pp']:.2f} ({r['cr2_df']:.1f}) | "
                 f"[{r['cr2_lo']:+.1f}, {r['cr2_hi']:+.1f}] | {fmt_p(r['cr2_p'])} | {fmt_p(r['signflip_p'])} |")
    L += ["", "Supplement: instance-level (unclustered) paired SE, one-sided sign-flip, studentized sign-flip.", "",
          "| contrast | instance SE (pp) | sign-flip one-sided p | studentized sign-flip p |", "|---|---|---|---|"]
    for r in res:
        L.append(f"| {r['contrast']} | {r['se_inst_pp']:.2f} | {fmt_p(r['signflip_p_one'])} | {fmt_p(r['signflip_t_p'])} |")
    txt = "\n".join(L) + "\n"
    (OUT / "t1_clustered.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
