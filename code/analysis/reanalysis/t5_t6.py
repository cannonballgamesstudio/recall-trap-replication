"""Task 5: Holm over the 2-test confirmatory family {Qwen3.6-27B K=12, gpt logged re-run}.
Task 6: Qwen3.6-27B K=12 truncation robustness (pairwise exclusion, n=499).
"""
from __future__ import annotations

import json

from common_ra import OUT, load_table, paired_rows, mcnemar_exact, fmt_p


def holm(p):
    items = sorted(p.items(), key=lambda kv: kv[1])
    m, run, adj = len(items), 0.0, {}
    for i, (k, v) in enumerate(items):
        run = max(run, min(1.0, (m - i) * v))
        adj[k] = run
    return adj


def sub(rows):
    b = sum(1 for r in rows if r["y_off"] and not r["y_on"])
    c = sum(1 for r in rows if r["y_on"] and not r["y_off"])
    n = len(rows)
    return dict(n=n, b=b, c=c, d=100 * (b - c) / n, p=mcnemar_exact(b, c))


def main():
    tab = load_table()
    t1 = {r["arm"]: r for r in json.load(open(OUT / "t1_clustered.json"))}
    fam = {"Qwen3.6-27B K=12": "P3_qwen36_fusion_K12", "gpt logged re-run": "F1_gpt_logged_replication"}
    L = ["## Task 5 — Holm over the 2-test confirmatory family", "",
         "| test | Δ (pp) | n | raw McNemar p | Holm-adj. | wild p | Holm-adj. | CR2 p | Holm-adj. | sign-flip p | Holm-adj. |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    adj = {k: holm({lab: t1[a][k] for lab, a in fam.items()}) for k in ("mcnemar_p", "wild_p", "cr2_p", "signflip_p")}
    t5 = {}
    for lab, a in fam.items():
        r = t1[a]
        t5[lab] = {k: (r[k], adj[k][lab]) for k in adj}
        L.append(f"| {lab} | {r['est_pp']:+.2f} | {r['n']} | {fmt_p(r['mcnemar_p'])} | {fmt_p(adj['mcnemar_p'][lab])} | "
                 f"{fmt_p(r['wild_p'])} | {fmt_p(adj['wild_p'][lab])} | {fmt_p(r['cr2_p'])} | {fmt_p(adj['cr2_p'][lab])} | "
                 f"{fmt_p(r['signflip_p'])} | {fmt_p(adj['signflip_p'][lab])} |")

    # ---------------- Task 6
    arm = "P3_qwen36_fusion_K12"
    on_all, off_all = tab[(arm, "ON")], tab[(arm, "OFF")]
    sub_on = [v for v in on_all.values() if v["status"] != "never_predicted"]
    sub_off = [v for v in off_all.values() if v["status"] != "never_predicted"]
    fin_on = sum(v["raw_finish_reason"] == "length" for v in sub_on)
    fin_off = sum(v["raw_finish_reason"] == "length" for v in sub_off)
    rows = paired_rows(tab, arm)
    n = len(rows)
    T = lambda r: r["raw_finish_reason"] == "length"
    E = lambda r: r["status"] == "empty"
    fin_on_p = sum(T(r["on"]) for r in rows); fin_off_p = sum(T(r["off"]) for r in rows)
    raw = sub(rows)
    nt = sub([r for r in rows if not T(r["on"]) and not T(r["off"])])
    ne = sub([r for r in rows if not E(r["on"]) and not E(r["off"])])
    # imputation set: truncated AND empty (no gradeable patch); truncated-but-nonempty keep their grade
    U_on = [r for r in rows if T(r["on"]) and E(r["on"])]
    U_off = [r for r in rows if T(r["off"]) and E(r["off"])]
    R_on = sum(r["y_on"] for r in rows); R_off = sum(r["y_off"] for r in rows)
    sym_fail = 100 * (R_off - R_on) / n
    sym_succ = 100 * ((R_off + len(U_off)) - (R_on + len(U_on))) / n
    worst_lo = 100 * (R_off - (R_on + len(U_on))) / n
    worst_hi = 100 * ((R_off + len(U_off)) - R_on) / n
    # variant: impute every fin=length response (incl. the few truncated-nonempty graded unresolved)
    A_on = [r for r in rows if T(r["on"]) and not r["y_on"]]
    A_off = [r for r in rows if T(r["off"]) and not r["y_off"]]
    v_lo = 100 * (R_off - (R_on + len(A_on))) / n
    v_hi = 100 * ((R_off + len(A_off)) - R_on) / n
    v_sym = 100 * ((R_off + len(A_off)) - (R_on + len(A_on))) / n
    # variant: n=500 denominators (missing-as-empty), arm-level truncated counts
    n5 = 500
    ro5 = sum(v["status"] == "resolved" for v in on_all.values()); rf5 = sum(v["status"] == "resolved" for v in off_all.values())
    u5_on = sum(v["raw_finish_reason"] == "length" and v["status"] == "empty" for v in on_all.values())
    u5_off = sum(v["raw_finish_reason"] == "length" and v["status"] == "empty" for v in off_all.values())
    w5_lo = 100 * (rf5 - (ro5 + u5_on)) / n5; w5_hi = 100 * ((rf5 + u5_off) - ro5) / n5
    # differential censoring among OFF's discordant wins
    off_wins = [r for r in rows if r["y_off"] and not r["y_on"]]
    off_wins_on_trunc = sum(T(r["on"]) for r in off_wins)
    on_wins = [r for r in rows if r["y_on"] and not r["y_off"]]
    on_wins_off_trunc = sum(T(r["off"]) for r in on_wins)
    t6 = dict(n=n, raw=raw, fin_on_arm=(fin_on, len(sub_on)), fin_off_arm=(fin_off, len(sub_off)),
              fin_on_paired=fin_on_p, fin_off_paired=fin_off_p, nt=nt, ne=ne,
              U_on=len(U_on), U_off=len(U_off), sym_fail=sym_fail, sym_succ=sym_succ, worst=(worst_lo, worst_hi),
              worst_all_trunc=(v_lo, v_hi), sym_succ_all_trunc=v_sym, A_on=len(A_on), A_off=len(A_off), worst_n500=(w5_lo, w5_hi),
              off_wins=len(off_wins), off_wins_on_trunc=off_wins_on_trunc, on_wins=len(on_wins), on_wins_off_trunc=on_wins_off_trunc)
    json.dump(dict(t5=t5, t6=t6), open(OUT / "t5_t6.json", "w"), indent=1)

    L += ["", "## Task 6 — Qwen3.6-27B K=12 truncation robustness (pairwise n=499)", "",
          "| quantity | value |", "|---|---|",
          f"| raw (primary) | n={n}, Δ {raw['d']:+.2f}pp, {raw['b']}/{raw['c']}, p={fmt_p(raw['p'])} |",
          f"| fin=length rate, arm level (own submitted denominator) | ON {fin_on}/{len(sub_on)} = {100*fin_on/len(sub_on):.1f}% ; OFF {fin_off}/{len(sub_off)} = {100*fin_off/len(sub_off):.1f}% |",
          f"| fin=length rate, paired n={n} | ON {fin_on_p} = {100*fin_on_p/n:.1f}% ; OFF {fin_off_p} = {100*fin_off_p/n:.1f}% |",
          f"| both-non-truncated (neither arm fin=length) | n={nt['n']}, Δ {nt['d']:+.2f}pp, {nt['b']}/{nt['c']}, p={fmt_p(nt['p'])} |",
          f"| both-non-empty (conditional estimand) | n={ne['n']}, Δ {ne['d']:+.2f}pp, {ne['b']}/{ne['c']}, p={fmt_p(ne['p'])} |",
          f"| PRIMARY imputation set: every unresolved fin=length response | ON {len(A_on)} ; OFF {len(A_off)} |",
          f"| symmetric imputation: truncated = failure in both arms | {sym_fail:+.2f}pp |",
          f"| symmetric imputation: truncated = success in both arms | {v_sym:+.2f}pp |",
          f"| TRUE worst-case (Manski) bounds: ON-trunc→success & OFF-trunc→fail / reverse | [{v_lo:+.2f}, {v_hi:+.2f}]pp |",
          f"| sensitivity set: truncated AND empty only | ON {len(U_on)} ; OFF {len(U_off)} |",
          f"| sensitivity: symmetric success / worst-case | {sym_succ:+.2f}pp / [{worst_lo:+.2f}, {worst_hi:+.2f}]pp |",
          f"| worst-case, n=500 missing-as-empty denominators | [{w5_lo:+.2f}, {w5_hi:+.2f}]pp |",
          f"| OFF discordant wins where ON truncated | {off_wins_on_trunc} of {len(off_wins)} |",
          f"| ON discordant wins where OFF truncated | {on_wins_off_trunc} of {len(on_wins)} |"]
    txt = "\n".join(L) + "\n"
    (OUT / "t5_t6.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
