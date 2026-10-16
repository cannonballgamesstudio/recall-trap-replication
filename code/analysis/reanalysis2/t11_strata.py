"""Task 11: per-stratum point estimates for the memorization section (Branch B gpt, E5 Qwen3-Coder);
are all positive? Recomputed from the M tables and graded reports (cross-checked against the join files)."""
import json
import sys

import numpy as np

from ra2 import arm, P5, CONTAM, VIOL, write_md, dump

sys.path.insert(0, str(__import__("ra2").PKG / "code" / "eval"))
import contam_common as cc  # noqa: E402

gold = json.loads((P5 / "gold_patches.json").read_text(encoding="utf-8"))
packs = json.loads((P5 / "local_packs.json").read_text(encoding="utf-8"))
cls = {i: cc.anchor_class(gold[i], packs[i]["dedupON"]["pack"]) + ">" + cc.anchor_class(gold[i], packs[i]["dedupOFF"]["pack"]) for i in packs}
BC = {i for i, c in cls.items() if c == "B>C"}


def pairs(on, off):
    a, b = arm(on), arm(off)
    return {i: int(i in b.res) - int(i in a.res) for i in a.sub & b.sub}


def strata(rows):
    ids = [i for i in rows if rows[i]["lowM"] is not None]
    S = {"full": ids, "Low-M (E1)": [i for i in ids if rows[i]["lowM"] == 1], "High-M": [i for i in ids if rows[i]["lowM"] == 0]}
    for m in range(4):
        S[f"M={m} (NA as 0)"] = [i for i in ids if rows[i]["M"] == m]
    elig = [i for i in ids if rows[i]["n_avail"] == 3]
    for m in range(4):
        S[f"M={m} (P1-eligible)"] = [i for i in elig if rows[i]["M"] == m]
    S["S1: Low-M ∩ P1-eligible"] = [i for i in elig if rows[i]["lowM"] == 1]
    for k in ("p1", "p2_apply", "p3"):
        S[f"{k} negative"] = [i for i in ids if rows[i].get(k) == 0]
        S[f"{k} positive"] = [i for i in ids if rows[i].get(k) == 1]
    S["B→C full"] = [i for i in ids if i in BC]
    S["E2: Low-M ∩ B→C"] = [i for i in ids if i in BC and rows[i]["lowM"] == 1]
    S["High-M ∩ B→C"] = [i for i in ids if i in BC and rows[i]["lowM"] == 0]
    return S


def est(draws, ids):
    v = [d[i] for d in draws for i in ids if i in d]
    return (100 * np.mean(v) if v else None), len({i for i in ids if any(i in d for d in draws)})


L = ["## Task 11 — Per-stratum point estimates, memorization section", "",
     "Δ = OFF−ON (pp) unless stated; gpt pooled = mean over (instance, draw) for the discovery draw + logged re-run (the pre-registered estimator). "
     "Empty strata shown as —. Non-positive strata are listed under each table.", ""]
out = {}
# ---- gpt
Mg = json.loads((CONTAM / "M_table_gpt56sol.json").read_text(encoding="utf-8"))
dh, dl = pairs("gpt_hl_ON", "gpt_hl_OFF"), pairs("gpt_lr_ON", "gpt_lr_OFF")
Sg = strata(Mg)
L += ["### Branch B, gpt-5.6-sol", "", "| stratum | n inst | pooled (2 draws) | discovery draw | logged re-run |", "|---|---|---|---|---|"]
signs = {"pooled": [], "hl": [], "lr": []}
for k, ids in Sg.items():
    p, n = est([dh, dl], ids); h, _ = est([dh], ids); l_, _ = est([dl], ids)
    out[("gpt", k)] = dict(n=n, pooled=p, hl=h, lr=l_)
    for key, v in (("pooled", p), ("hl", h), ("lr", l_)):
        if v is not None and k != "full":
            signs[key].append((k, v))
    f = lambda v: "—" if v is None else f"{v:+.1f}"
    L.append(f"| {k} | {n} | {f(p)} | {f(h)} | {f(l_)} |")
nonpos = {key: [(k, round(float(v), 1)) for k, v in vals if v <= 0] for key, vals in signs.items()}
L.append("")
L.append(f"Non-positive strata — pooled: {nonpos['pooled'] or 'none'}; discovery draw: {nonpos['hl'] or 'none'}; logged re-run: {nonpos['lr'] or 'none'}.")
rng_p = [v for k, v in signs["pooled"]]
L.append(f"Range of pooled stratum estimates: {min(rng_p):+.1f} to {max(rng_p):+.1f}pp (paper text says 'no stratum ... outside +5.7 to +7.3' — that range holds only for E1/High and the single-probe P2/P3 strata; see surprises).")
L.append("")

# ---- Qwen3-Coder E5
Mq = json.loads((CONTAM / "M_table_qwen3coder30b_local.json").read_text(encoding="utf-8"))
dq = pairs("qc_ON", "qc_OFF")
T, on, off = arm("qc_T"), arm("qc_ON"), arm("qc_OFF")
tids = (T.sub & on.sub & off.sub)
dOT = {i: int(i in off.res) - int(i in T.res) for i in tids}
dTO = {i: int(i in T.res) - int(i in on.res) for i in tids}
dk = {k: pairs(f"qor_{k}_ON", f"qor_{k}_OFF") for k in ("k4", "k12", "k40")}
Sq = strata(Mq)
L += ["### E5, Qwen3-Coder-30B (local-GGUF M; one draw)", "",
      "| stratum | n inst | OFF−ON | OFF−T | T−ON | K=4 (OR, proxy M) | K=12 (OR) | K=40 (OR) |", "|---|---|---|---|---|---|---|---|"]
sq = {c: [] for c in ("OFF−ON", "OFF−T", "T−ON", "k4", "k12", "k40")}
for k, ids in Sq.items():
    vals = {"OFF−ON": est([dq], ids), "OFF−T": est([dOT], ids), "T−ON": est([dTO], ids),
            "k4": est([dk["k4"]], ids), "k12": est([dk["k12"]], ids), "k40": est([dk["k40"]], ids)}
    out[("qwen3coder", k)] = {c: v[0] for c, v in vals.items()} | {"n": vals["OFF−ON"][1]}
    for c, (v, n) in vals.items():
        if v is not None and k != "full":
            sq[c].append((k, v, n))
    f = lambda v: "—" if v[0] is None else f"{v[0]:+.1f}"
    L.append(f"| {k} | {vals['OFF−ON'][1]} | {f(vals['OFF−ON'])} | {f(vals['OFF−T'])} | {f(vals['T−ON'])} | {f(vals['k4'])} | {f(vals['k12'])} | {f(vals['k40'])} |")
L.append("")
for c in sq:
    np_ = [(k, round(float(v), 1), n) for k, v, n in sq[c] if v <= 0]
    L.append(f"- {c}: non-positive strata (stratum, Δ, n): {np_ or 'none'}")
L.append("")
write_md("t11_strata", "\n".join(L) + "\n")
dump("t11_strata", {" | ".join(k): v for k, v in out.items()})
