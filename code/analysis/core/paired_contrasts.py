"""Recompute the paper's paired single-shot / agentic contrasts from the inclusion table.

Outputs results/paired_contrasts.csv and results/paired_contrasts.md with, per paired arm:
paired n, resolve counts/rates, Delta (OFF - ON), discordant pairs, McNemar exact p (raw,
empties as failure = primary estimand), conditional p (both arms non-empty), empty rates,
repository-cluster bootstrap 95% CI + one-sided P(Delta<=0), LORO range, and the exact
product decomposition. Also: Holm over the confirmatory family, the K=4/K=40
difference-in-differences, the random-chunk control, and the cross-retriever interactions.

Run from the package root after build_inclusion_table.py:
    python code/analysis/paired_contrasts.py
"""
from __future__ import annotations

from common import (RESULTS, load_inclusion, paired, cluster_bootstrap, delta_stat, loro, holm,
                    decomposition, write_csv, binom_two_sided)

PAIRS = [
    ("P1_gpt_fusion", "P1_gpt_fusion"), ("P2_deepseek_fusion", "P2_deepseek_fusion"),
    ("P3_qwen36_fusion_K12", "P3_qwen36_fusion_K12"), ("P4_DENSE1_gpt_dense", "P4_DENSE1_gpt_dense"),
    ("P5_qwen25coder32b", "P5_qwen25coder32b"), ("P6a_glm52_incompatible", "P6a_glm52_incompatible"),
    ("P6b_kimi_incompatible", "P6b_kimi_incompatible"), ("R1_gpt_bm25", "R1_gpt_bm25"),
    ("M1_qwen3coder30b_AC", "M1_qwen3coder30b_AC"), ("F1_gpt_logged_replication", "F1_gpt_logged_replication"),
    ("B1_qwen36_K4", "B1_qwen36_K4"), ("B1_qwen36_K40", "B1_qwen36_K40"),
    ("B2_A3B_K4", "B2_A3B_K4"), ("B2_A3B_K12", "B2_A3B_K12"), ("B2_A3B_K40", "B2_A3B_K40"),
    ("A1_agentic_sonnet5_fusion", "A1_agentic_sonnet5_fusion"), ("A2_agentic_sonnet5_dense", "A2_agentic_sonnet5_dense"),
    ("A3_agentic_opus_dense_n100", "A3_agentic_opus_dense_n100"), ("A4_bm25_n100", "A4_bm25_n100"),
    ("A5_retired_agentic_18pp", "A5_retired_agentic_18pp"),
]


def main():
    tab = load_inclusion()
    out, cache = [], {}
    for arm, _ in PAIRS:
        on, off = tab.get((arm, "ON")), tab.get((arm, "OFF"))
        if not on or not off:
            print("skip", arm)
            continue
        for mode in (False, True):
            res = paired(on, off, missing_as_empty=mode)
            if mode and res["n"] == paired(on, off)["n"]:
                continue  # no never-predicted instances: the two conventions coincide
            rows = res.pop("rows")
            lo, hi, p_le0 = cluster_bootstrap(rows, delta_stat)
            lr = loro(rows)
            dec = decomposition(rows)
            rec = dict(arm_id=arm, convention=("missing-as-empty" if mode else "pairwise-exclusion"), **res,
                       cluster_ci_lo=lo, cluster_ci_hi=hi, cluster_p_le0=p_le0,
                       loro_min=min(lr.values()), loro_max=max(lr.values()), **dec)
            out.append(rec)
            cache[(arm, mode)] = rows
    # Holm across the confirmatory family + DeepSeek + multilingual pooled (p from PolyBench verdict)
    fam = {r["arm_id"]: r["p_raw"] for r in out if r["convention"] == "pairwise-exclusion"
           and r["arm_id"] in ("P1_gpt_fusion", "P2_deepseek_fusion", "P3_qwen36_fusion_K12", "P4_DENSE1_gpt_dense")}
    fam["PolyBench_pooled"] = binom_two_sided(23, 62)  # 39 OFF-only vs 23 ON-only wins (results/GENERALITY-FINAL-VERDICT.txt)
    adj = holm(fam)
    write_csv(RESULTS / "paired_contrasts.csv", out)

    lines = ["# Paired contrasts (recomputed from results/inclusion_table.csv)", "",
             "Delta = dedup-OFF minus dedup-ON, percentage points. p = exact McNemar. CI = repository-cluster "
             "bootstrap (5000 reps, seed 20260714, percentile). Convention: never-predicted instances excluded "
             "pairwise; where an arm has never-predicted instances a second row counts them as empty failures.", "",
             "| arm | convention | n | ON | OFF | Delta | disc OFF/ON | p raw | p cond | empty ON/OFF | cluster 95% CI | P(D<=0) | LORO |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in out:
        lines.append(f"| {r['arm_id']} | {r['convention']} | {r['n']} | {100*r['rate_on']:.1f}% ({r['res_on']}) | "
                     f"{100*r['rate_off']:.1f}% ({r['res_off']}) | {r['delta_pp']:+.2f} | {r['disc_off']}/{r['disc_on']} | "
                     f"{r['p_raw']:.2g} | {r['p_cond']:.2g} | {100*r['empty_on']/r['n']:.1f}/{100*r['empty_off']/r['n']:.1f}% | "
                     f"[{r['cluster_ci_lo']:+.1f}, {r['cluster_ci_hi']:+.1f}] | {r['cluster_p_le0']:.3f} | "
                     f"{r['loro_min']:+.1f}..{r['loro_max']:+.1f} |")
    lines += ["", "## Product decomposition (reference = ON)", "",
              "| arm | dA | dR | Q_on*dA | A_on*dQ | dA*dQ |", "|---|---|---|---|---|---|"]
    for r in out:
        if r["convention"] != "pairwise-exclusion":
            continue
        lines.append(f"| {r['arm_id']} | {r['dA_pp']:+.1f} | {r['dR_pp']:+.1f} | {r['prod_pp']:+.1f} ({100*r['prod_share']:.0f}%) | "
                     f"{r['qual_pp']:+.1f} ({100*r['qual_share']:.0f}%) | {r['inter_pp']:+.1f} ({100*r['inter_share']:.0f}%) |")
    lines += ["", "## Holm-Bonferroni over the five primary raw p-values", ""]
    for k, p in sorted(fam.items(), key=lambda kv: kv[1]):
        lines.append(f"- {k}: raw p = {p:.4g}, Holm-adjusted = {adj[k]:.4g}")

    # Difference-in-differences K=40 vs K=4 (Qwen3.6-27B), clustered over repositories
    lines += ["", "## Budget x dedup difference-in-differences (Qwen3.6-27B, K=40 minus K=4)", ""]
    for mode in (False, True):
        r4, r40 = cache.get(("B1_qwen36_K4", mode)), cache.get(("B1_qwen36_K40", mode))
        if not r4 or not r40:
            continue
        joint = [("k4", x) for x in r4] + [("k40", x) for x in r40]

        def dd(sample):
            a = [x for t, x in sample if t == "k4"]
            b = [x for t, x in sample if t == "k40"]
            if not a or not b:
                return 0.0
            return delta_stat(b) - delta_stat(a)

        # cluster on repository of the instance (both budgets resampled together)
        lo, hi, p = cluster_bootstrap([(x[0], (t, x)) for t, x in joint], lambda s: dd([v for _, v in s]))
        lines.append(f"- {'missing-as-empty' if mode else 'pairwise-exclusion'}: DiD = {delta_stat(r40) - delta_stat(r4):+.2f}pp, "
                     f"cluster 95% CI [{lo:+.2f}, {hi:+.2f}], one-sided P(DiD<=0) = {p:.4f}")

    # Random-chunk control: arm B (3 seeds) vs A (M1 ON) and C (M1 OFF)
    lines += ["", "## Random-chunk selection control (Qwen3-Coder-30B-A3B)", ""]
    A, C = tab.get(("M1_qwen3coder30b_AC", "ON")), tab.get(("M1_qwen3coder30b_AC", "OFF"))
    tot_b, tot_n = 0, 0
    for s in ("20260717", "20260718", "20260719"):
        B = tab.get((f"M2_random_chunk_B_seed{s}", "ON"))
        if not B:
            continue
        ba = paired(A, B)   # "OFF" slot = B: Delta = B - A
        bc = paired(C, B)   # Delta = B - C
        ba.pop("rows"); bc.pop("rows")
        tot_b += ba["res_off"]; tot_n += ba["n"]
        lines.append(f"- seed {s}: B {ba['res_off']}/{ba['n']} ({100*ba['rate_off']:.1f}%); B-A {ba['delta_pp']:+.1f}pp "
                     f"(disc {ba['disc_off']}/{ba['disc_on']}, p={ba['p_raw']:.3g}); B-C {bc['delta_pp']:+.1f}pp (p={bc['p_raw']:.2g})")
    if tot_n:
        lines.append(f"- pooled B: {100*tot_b/tot_n:.1f}%")

    # Cross-retriever interactions (gpt-5.6-sol): Delta_fusion - Delta_BM25, Delta_dense - Delta_BM25
    lines += ["", "## Cross-retriever interaction (gpt-5.6-sol, single-shot)", ""]
    rf, rd, rb = cache.get(("P1_gpt_fusion", False)), cache.get(("P4_DENSE1_gpt_dense", False)), cache.get(("R1_gpt_bm25", False))
    for name, x in (("fusion - BM25", rf), ("dense - BM25", rd), ("fusion - dense", rf)):
        y = rd if name == "fusion - dense" else rb
        if not x or not y:
            continue
        joint = [(r[0], ("x", r)) for r in x] + [(r[0], ("y", r)) for r in y]

        def inter(sample):
            a = [v for _, (t, v) in sample if t == "x"]
            b = [v for _, (t, v) in sample if t == "y"]
            return delta_stat(a) - delta_stat(b) if a and b else 0.0

        lo, hi, p = cluster_bootstrap(joint, inter)
        lines.append(f"- {name}: {delta_stat(x) - delta_stat(y):+.1f}pp, cluster 95% CI [{lo:+.1f}, {hi:+.1f}]")
    (RESULTS / "paired_contrasts.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
