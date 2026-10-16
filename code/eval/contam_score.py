#!/usr/bin/env python3
"""Contamination pre-reg, Branch B: scoring code path (M table -> blinded join -> E1..E5).

Pre-registered in docs/paper/CONTAMINATION-PREREG.md sections B.3-B.8. No model calls.
Importing this module does nothing but define functions.

  python contam_score.py m-table --tag gpt56sol [--p2-report <swebench report json>]
      reads raw_P{1,2,3}_<tag>.jsonl ONLY (never an arm outcome file), writes
      data/memorization-branchB/M_table_<tag>.json and prints its SHA-256 plus the
      probe-validity report. The SHA-256 is committed to the pre-reg BEFORE any join.
  python contam_score.py m-table --dataset polybench --tag gpt56sol   (M_poly, P1+P3; B.2 extension)
  python contam_score.py validity-contrast --tag gpt56sol             (B.5: PolyBench vs Verified)
  python contam_score.py join --family qwen3coder --tag qwen3coder_or --t-tag qwen3coder30b_local
      (ruling 5: serving-stack M; --proxy when the OpenRouter tier was not approved)
  python contam_score.py join --family gpt --tag gpt56sol
      refuses unless the M table's SHA-256 occurs in a COMMITTED revision of the pre-reg;
      then computes E1..E4 + decision label (gpt) or E5 (qwen36 / qwen3coder).
  python contam_score.py selftest
      runs every estimator on synthetic data (no outcome files read).
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import contam_common as cc  # noqa: E402

B_BOOT = 10000
B_WILD = 9999
WEBB = [-(1.5 ** 0.5), -1.0, -(0.5 ** 0.5), 0.5 ** 0.5, 1.0, 1.5 ** 0.5]
REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------- M table (outcome-blind)
def _raw(probe: str, tag: str, dataset: str = "verified") -> dict[str, dict]:
    pre = "raw_" if dataset == "verified" else "raw_poly_"
    p = cc.CONTAM / f"{pre}{probe}_{tag}.jsonl"
    out = {}
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                out[r["instance_id"]] = r
    return out


def build_m_table(tag: str, p2_report: str | None, dataset: str = "verified") -> dict:
    """M per instance. dataset='polybench' = the B.2 PolyBench-Python extension (M_poly):
    P1 + P3 only (P2 is not run on PolyBench); never pooled with Verified estimands."""
    if dataset == "polybench":
        poly = cc.polybench_python()
        inst = {i: {"repo": x["repo"], "problem_statement": x["problem_statement"]} for i, x in poly.items()}
        gold = {i: x["patch"] for i, x in poly.items()}
        p3in = cc.load_json(cc.CONTAM / "poly_p3_inputs.json")["rows"]
    else:
        inst = {x["instance_id"]: x for x in cc.load_json(cc.VER / "instances_verified.json")}
        gold = cc.load_json(cc.VER / "gold_patches.json")
        p3in = cc.load_json(cc.CONTAM / "p3_inputs.json")["rows"]
    r1, r2, r3 = _raw("P1", tag, dataset), _raw("P2", tag, dataset), _raw("P3", tag, dataset)
    p2_res = None
    if p2_report:
        p2_res = set(cc.load_json(p2_report)["resolved_ids"])
    rows = {}
    for i in sorted(inst):
        row = {"repo": inst[i]["repo"]}
        if cc.p1_filtered(inst[i]["problem_statement"], gold[i]):
            row.update(p1=None, p1_base=None, p1_status="NA_filter")
        elif i in r1:
            paths = cc.parse_p1(r1[i]["content"], inst[i]["repo"])
            s = cc.score_p1(paths, cc.gold_files(gold[i]))
            row.update(p1=s["p1_hit"], p1_base=s["p1_base_hit"], p1_paths=paths, p1_status="ok")
        else:
            row.update(p1=None, p1_base=None, p1_status="missing")
        if i in r2 and r2[i].get("applied") is not None:
            row.update(p2_apply=int(r2[i]["applied"] >= 1), p2_applied_blocks=r2[i]["applied"],
                       p2_resolve=None if p2_res is None else int(i in p2_res))
        else:
            row.update(p2_apply=None, p2_resolve=None)
        if i in p3in and i in r3:
            s = cc.score_p3(r3[i]["content"], p3in[i]["target"])
            row.update(p3_overlap=s["p3_overlap"], p3=s["p3_pos"])
        else:
            row.update(p3_overlap=None, p3=None)
        row.update(cc.memorization_score(row["p1"], row["p2_apply"], row["p3"]))
        rows[i] = row
    return rows


def validity_report(rows: dict) -> dict:
    def rate(k):
        v = [r[k] for r in rows.values() if r.get(k) is not None]
        return (sum(v) / len(v) if v else None), len(v)
    p1, n1 = rate("p1")
    out = {"p1_hit_rate": p1, "p1_n": n1, "p1_basename_rate": rate("p1_base")[0],
           "p2_apply_rate": rate("p2_apply")[0], "p2_n": rate("p2_apply")[1],
           "p2_resolve_rate": rate("p2_resolve")[0], "p3_pos_rate": rate("p3")[0],
           "p3_n": rate("p3")[1], "lowM_share": rate("lowM")[0],
           "highM_share": (lambda v: v and 1 - v)(rate("lowM")[0]),
           "highM_share_P1P3_only": (lambda v: sum(v) / len(v) if v else None)(
               [int((r.get("p1") or 0) + (r.get("p3") or 0) > 0) for r in rows.values()
                if r.get("p1") is not None or r.get("p3") is not None]),
           "M_dist": {m: sum(1 for r in rows.values() if r["M"] == m) for m in range(4)},
           "published_band": "60-76% (file-path identification on Verified)"}
    out["p1_validity"] = ("WEAK (<30%, disclosed; not a gate)" if p1 is not None and p1 < 0.30
                          else "within/near band" if p1 is not None and p1 >= 0.60 else "below band")
    return out


# ---------------------------------------------------------------- outcome join
def committed_sha(sha: str) -> bool:
    r = subprocess.run(["git", "-C", str(REPO_ROOT), "log", "--all", "--format=%h", f"-S{sha}",
                        "--", cc.PREREG], capture_output=True, text=True)
    return bool(r.stdout.strip())


def pairs_for(on: str, off: str) -> dict[str, int]:
    """instance -> d = OFF - ON on pairwise-attempted instances (never-submitted excluded)."""
    onr, ons = cc.report(on)
    offr, offs = cc.report(off)
    return {i: int(i in offr) - int(i in onr) for i in ons & offs}


def anchor_classes() -> dict[str, str]:
    packs = cc.load_json(cc.VER / "local_packs.json")
    gold = cc.load_json(cc.VER / "gold_patches.json")
    return {i: cc.anchor_class(gold[i], packs[i]["dedupON"]["pack"]) + ">" +
            cc.anchor_class(gold[i], packs[i]["dedupOFF"]["pack"]) for i in packs}


# ---------------------------------------------------------------- estimators
def delta(draws: list[dict[str, int]], ids) -> tuple[float | None, int]:
    v = [d[i] for d in draws for i in ids if i in d]
    return (sum(v) / len(v) if v else None), len(v)


def boot(draws, ids, stat, B=B_BOOT, seed=cc.SEED):
    """Instance-clustered bootstrap: resample instances; every draw of a resampled
    instance comes with it. stat(draws, ids_list) -> float|None."""
    rng = random.Random(seed)
    ids = sorted(ids)
    out = []
    for _ in range(B):
        s = [ids[rng.randrange(len(ids))] for _ in ids]
        v = stat(draws, s)
        if v is not None:
            out.append(v)
    return out


def one_sided_p(est: float, bs: list[float]) -> float:
    """H0: theta <= 0 vs H1: theta > 0, null-centred bootstrap."""
    return (1 + sum(1 for b in bs if b - est >= est)) / (len(bs) + 1)


def ci(bs, lo=0.025, hi=0.975):
    s = sorted(bs)
    return s[int(lo * (len(s) - 1))], s[int(hi * (len(s) - 1))]


def webb_wild_p(draws, ids, repo_of: dict[str, str], B=B_WILD, seed=cc.SEED) -> float | None:
    """Wild-cluster bootstrap-t (Webb 6-point, clusters = repositories, null imposed)
    for the intercept-only model d = alpha + e; one-sided H1 alpha > 0."""
    obs = [(repo_of[i], d[i]) for d in draws for i in ids if i in d]
    if not obs:
        return None
    clusters = sorted({c for c, _ in obs})
    G, N = len(clusters), len(obs)
    if G < 2:
        return None

    def t_stat(vals):
        m = sum(v for _, v in vals) / N
        sg = {}
        for c, v in vals:
            sg[c] = sg.get(c, 0.0) + (v - m)
        var = G / (G - 1) * sum(s * s for s in sg.values()) / (N * N)
        return m / var ** 0.5 if var > 0 else 0.0

    t0 = t_stat(obs)
    rng = random.Random(seed)
    hits = 0
    for _ in range(B):
        w = {c: WEBB[rng.randrange(6)] for c in clusters}
        hits += t_stat([(c, w[c] * v) for c, v in obs]) >= t0   # null alpha=0 imposed: u = d
    return (1 + hits) / (B + 1)


def within(draws, ids_all, subset):
    ids = [i for i in ids_all if i in subset]
    est, n = delta(draws, ids)
    if est is None:
        return {"n_pairs": 0}
    bs = boot(draws, ids, lambda d, s: delta(d, s)[0])
    return {"delta": est, "n_inst": len(ids), "n_pairs": n, "ci95": ci(bs),
            "p_one_sided": one_sided_p(est, bs)}


def interaction(draws, ids_all, high, low):
    ids = [i for i in ids_all if i in high or i in low]

    def stat(d, s):
        h, _ = delta(d, [i for i in s if i in high])
        l_, _ = delta(d, [i for i in s if i in low])
        return None if h is None or l_ is None else h - l_
    est = stat(draws, ids)
    if est is None:
        return {}
    bs = boot(draws, ids, stat)
    return {"diff_high_minus_low": est, "ci95": ci(bs), "p_one_sided": one_sided_p(est, bs)}


def trend(draws, ids, M: dict[str, int]):
    def slope(d, s):
        pts = []
        for i in s:
            v = [x[i] for x in d if i in x]
            if v:
                pts.append((M[i], sum(v) / len(v)))
        if len({x for x, _ in pts}) < 2:
            return None
        mx = sum(x for x, _ in pts) / len(pts)
        my = sum(y for _, y in pts) / len(pts)
        sxx = sum((x - mx) ** 2 for x, _ in pts)
        return sum((x - mx) * (y - my) for x, y in pts) / sxx
    est = slope(draws, ids)
    bs = boot(draws, ids, slope)
    lo, hi = ci(bs)
    p2 = min(1.0, 2 * min(sum(b <= 0 for b in bs), sum(b >= 0 for b in bs)) / len(bs))
    return {"slope_per_M": est, "ci95": (lo, hi), "p_two_sided": p2,
            "by_M": {m: delta(draws, [i for i in ids if M[i] == m]) for m in range(4)}}


def analyse(draws: list[dict[str, int]], rows: dict, bc: set[str] | None):
    ids = [i for i in rows if rows[i]["lowM"] is not None and any(i in d for d in draws)]
    low = {i for i in ids if rows[i]["lowM"] == 1}
    high = {i for i in ids if rows[i]["lowM"] == 0}
    repo_of = {i: rows[i]["repo"] for i in rows}
    ref, _ = delta(draws, ids)
    res = {"delta_ref_full": ref, "n_inst": len(ids), "n_low": len(low), "n_high": len(high)}
    res["E1_low"] = within(draws, ids, low)
    res["E1_low"]["webb_wild_p_one_sided"] = webb_wild_p(draws, [i for i in ids if i in low], repo_of)
    res["high"] = within(draws, ids, high)
    res["E3_full"] = interaction(draws, ids, high, low)
    elig = [i for i in ids if rows[i]["n_avail"] == 3]
    res["E4_trend_P1eligible"] = trend(draws, elig, {i: rows[i]["M"] for i in rows})
    res["E4_trend_all_NAas0"] = trend(draws, ids, {i: rows[i]["M"] for i in rows})
    res["S1_E1_P1eligible"] = within(draws, elig, low)
    if bc is not None:
        bci = [i for i in ids if i in bc]
        res["E2_low_BC"] = within(draws, bci, low)
        res["E3_BC"] = interaction(draws, bci, high, low)
        res["BC_full"] = within(draws, bci, set(bci))
    res["per_probe_alone"] = {}
    for k in ("p1", "p2_apply", "p3"):
        neg = {i for i in ids if rows[i].get(k) == 0}
        pos = {i for i in ids if rows[i].get(k) == 1}
        res["per_probe_alone"][k] = {"neg": within(draws, ids, neg), "pos": within(draws, ids, pos),
                                     "interaction": interaction(draws, ids, pos, neg)}
    return res


def decide(res: dict) -> str:
    ref = res["delta_ref_full"]
    e1, e2 = res["E1_low"], res.get("E2_low_BC", {})
    e3f, e3b = res.get("E3_full", {}), res.get("E3_BC", {})
    if (e1.get("p_one_sided", 1) < 0.05 and e1.get("delta", -9) >= 0.5 * ref
            and e2.get("p_one_sided", 1) < 0.05):
        return "Effect survives in unmemorized instances (not explained by measured memorization)"
    if e1.get("delta", 9) <= 0.25 * ref and (e3f.get("p_one_sided", 1) < 0.05
                                             or e3b.get("p_one_sided", 1) < 0.05):
        return "Measured memorization explains the effect"
    return "Inconclusive"


def cmd_m_table(args) -> int:
    rows = build_m_table(args.tag, args.p2_report, args.dataset)
    name = f"M_table_{args.tag}.json" if args.dataset == "verified" else f"M_poly_table_{args.tag}.json"
    out = cc.CONTAM / name
    out.write_text(json.dumps(rows, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps(validity_report(rows), indent=1))
    print(f"[M-table] {out}\n[M-table sha256] {cc.sha256_file(out)}  <- commit this to the pre-reg "
          "BEFORE running `join`")
    return 0


def cmd_join(args) -> int:
    mt = cc.CONTAM / f"M_table_{args.tag}.json"
    sha = cc.sha256_file(mt)
    if not committed_sha(sha):
        if not args.unblinded_test:
            print(f"REFUSE: M-table sha256 {sha} is not in any committed revision of {cc.PREREG}.")
            return 1
        print("WARNING: --unblinded-test: output is NOT reportable.")
    rows = cc.load_json(mt)
    out = {"family": args.family, "tag": args.tag, "m_table_sha256": sha,
           "unblinded_test": bool(args.unblinded_test)}
    if args.family == "gpt":
        draws = [pairs_for(*cc.ARMS["gpt"][k]) for k in ("hl", "lr")]
        cls = anchor_classes()
        bc = {i for i, c in cls.items() if c == "B>C"}
        res = analyse(draws, rows, bc)
        res["decision"] = decide(res)
        out["gpt_pooled_hl_lr"] = res
    else:
        # Ruling 5: M is measured on the stack that served the arm. --tag = the M table for the
        # OpenRouter-served K arms (OpenRouter-measured at the same slug), or the local-GGUF table
        # with --proxy when that tier was not approved ("proxy M" in every table).
        out["m_label"] = "proxy M (local GGUF)" if args.proxy else "serving-stack M"
        for k, (on, off) in cc.ARMS[args.family].items():
            out[k] = analyse([pairs_for(on, off)], rows, None)
        if args.family == "qwen3coder":
            # Primary E5 cell: the local T triple with local-GGUF M (--t-tag).
            if not args.t_tag:
                print("REFUSE: qwen3coder needs --t-tag <local-GGUF M table tag> for the T triple.")
                return 1
            tmt = cc.CONTAM / f"M_table_{args.t_tag}.json"
            tsha = cc.sha256_file(tmt)
            if not committed_sha(tsha) and not args.unblinded_test:
                print(f"REFUSE: M-table sha256 {tsha} ({args.t_tag}) not in a committed pre-reg revision.")
                return 1
            trows = cc.load_json(tmt)
            T = cc.T_ARM
            out["T_triple_m_table_sha256"] = tsha
            for name, (a, b) in {"OFF_minus_ON": (T["ref_on"], T["ref_off"]),
                                 "OFF_minus_T": (T["T"], T["ref_off"]),
                                 "T_minus_ON": (T["ref_on"], T["T"])}.items():
                out["E5_primary_T_" + name] = analyse([pairs_for(a, b)], trows, None)
    p = cc.CONTAM / f"join_{args.family}_{args.tag}.json"
    p.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(json.dumps(out, indent=1, default=str)[:6000])
    print(f"[join] -> {p}")
    return 0


def cmd_validity_contrast(args) -> int:
    """B.5 (E4 extension): P1 hit rate and High-M share on PolyBench Python beside Verified's.
    Outcome-free; reads only the two M tables. M_poly is never pooled with Verified."""
    v = validity_report(cc.load_json(cc.CONTAM / f"M_table_{args.tag}.json"))
    pb = validity_report(cc.load_json(cc.CONTAM / f"M_poly_table_{args.tag}.json"))
    keys = ("p1_hit_rate", "p1_n", "p1_basename_rate", "p3_pos_rate", "p3_n", "highM_share",
            "highM_share_P1P3_only")
    out = {k: {"verified": v.get(k), "polybench_python": pb.get(k)} for k in keys}
    out["note"] = ("Verified High-M includes P2; PolyBench has no P2, so compare highM_share_P1P3_only. "
                   "Memorization-account prediction: both markedly lower on PolyBench Python.")
    print(json.dumps(out, indent=1))
    return 0


def cmd_selftest(args) -> int:
    rng = random.Random(1)
    ids = [f"r{j % 12}__x-{j}" for j in range(500)]
    rows = {}
    for i in ids:
        p1, p2, p3 = (rng.random() < .5), (rng.random() < .3), (rng.random() < .2)
        rows[i] = {"repo": i.split("__")[0], **cc.memorization_score(int(p1), int(p2), int(p3)),
                   "p1": int(p1), "p2_apply": int(p2), "p3": int(p3)}
    draws = [{i: rng.choice([-1, 0, 0, 0, 0, 1, 1]) for i in ids} for _ in range(2)]
    bc = set(ids[:80])
    res = analyse(draws, rows, bc)
    res["decision"] = decide(res)
    print(json.dumps({k: res[k] for k in ("delta_ref_full", "n_low", "E1_low", "E2_low_BC",
                                           "E3_full", "decision")}, indent=1, default=str))
    return 0


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("m-table")
    a.add_argument("--tag", required=True)
    a.add_argument("--p2-report", default=None)
    a.add_argument("--dataset", choices=["verified", "polybench"], default="verified")
    b = sub.add_parser("join")
    b.add_argument("--family", choices=["gpt", "qwen36", "qwen3coder"], required=True)
    b.add_argument("--tag", required=True)
    b.add_argument("--unblinded-test", action="store_true")
    b.add_argument("--t-tag", default=None, help="qwen3coder: local-GGUF M table for the T triple")
    b.add_argument("--proxy", action="store_true",
                   help="K-arm M table is the local-GGUF proxy (tier not approved; ruling 5)")
    sub.add_parser("selftest")
    vc = sub.add_parser("validity-contrast")
    vc.add_argument("--tag", default="gpt56sol")
    args = ap.parse_args()
    return {"m-table": cmd_m_table, "join": cmd_join, "selftest": cmd_selftest,
            "validity-contrast": cmd_validity_contrast}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
