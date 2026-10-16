#!/usr/bin/env python3
"""Contamination pre-reg, Branch A: manipulation checks (outcome-blind) and estimands A1..A6.

Pre-registered in docs/paper/CONTAMINATION-PREREG.md section A. No model calls.

  python contam_post_analyze.py checks [--gold-gate PASS_IDS.txt]
      pack-only manipulation checks; writes manip_checks.json and prints its SHA-256.
      Report and commit BEFORE outcomes are joined.
  python contam_post_analyze.py join --gold-gate PASS_IDS.txt \
      --gpt ON.json OFF.json [--gpt ON_s2.json OFF_s2.json] [--qwen ON.json OFF.json]
      A1..A6 + three-label sign-consistency verdict. Two --gpt pairs = two seeds, pooled with
      the instance bootstrap (A.7 Seeds). B>C prevalence < 10% -> 'retrieval-shifted' (A.6). Refuses unless manip_checks.json's
      SHA-256 is in a committed revision of the pre-reg (use --unblinded-test to dry-run).
Branch A is descriptive and is NEVER pooled with Branch B.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import contam_common as cc  # noqa: E402
from contam_score import committed_sha  # noqa: E402

ROOT = Path(r"data/post-cutoff-branchA")
MANIFEST = ROOT / "instances_post.json"
PACKS = ROOT / "post_packs.json"
CHECKS = ROOT / "manip_checks.json"
B = 10000
LABEL_PROB = 0.80


def _load(gold_gate: str | None):
    man = {x["instance_id"]: x for x in cc.load_json(MANIFEST)}
    packs = cc.load_json(PACKS)
    ids = [i for i in sorted(man) if "dedupON" in packs.get(i, {}) and "dedupOFF" in packs.get(i, {})]
    if gold_gate:
        ok = set(Path(gold_gate).read_text(encoding="utf-8").split())
        ids = [i for i in ids if i in ok]
    return man, packs, ids


def checks(man, packs, ids) -> dict:
    cls = {i: cc.anchor_class(man[i]["patch"], packs[i]["dedupON"]["pack"]) + ">" +
           cc.anchor_class(man[i]["patch"], packs[i]["dedupOFF"]["pack"]) for i in ids}

    def mean(v):
        v = list(v)
        return sum(v) / len(v) if v else None

    def gold_hit(i, arm):
        g = set(cc.gold_files(man[i]["patch"]))
        return int(bool(g & {cc.norm(f) for f in packs[i][arm]["files"]}))
    sub = [set(map(cc.norm, packs[i]["dedupOFF"]["files"])) <= set(map(cc.norm, packs[i]["dedupON"]["files"]))
           for i in ids]
    return {
        "n": len(ids), "n_0401": sum(man[i]["stratum_0401"] for i in ids),
        "files_on_mean": mean(len(packs[i]["dedupON"]["files"]) for i in ids),
        "files_off_mean": mean(len(packs[i]["dedupOFF"]["files"]) for i in ids),
        "chars_on_mean": mean(len(packs[i]["dedupON"]["pack"]) for i in ids),
        "chars_off_mean": mean(len(packs[i]["dedupOFF"]["pack"]) for i in ids),
        "gold_file_recall_on": mean(gold_hit(i, "dedupON") for i in ids),
        "gold_file_recall_off": mean(gold_hit(i, "dedupOFF") for i in ids),
        "subset_off_in_on": mean(sub),
        "transition_counts": dict(Counter(cls.values())),
        "B>C_prevalence": mean(v == "B>C" for v in cls.values()),
        "verified_reference": {"files_on": 11.93, "B>C_prevalence": 0.16, "subset_off_in_on": 0.946},
        "classes": cls,
    }


def pairs(on: str, off: str) -> dict[str, int]:
    def rep(p):
        d = cc.load_json(p)
        return set(d["resolved_ids"]), set(d["submitted_ids"])
    onr, ons = rep(on)
    offr, offs = rep(off)
    return {i: int(i in offr) - int(i in onr) for i in ons & offs}


def est(draws, ids) -> dict:
    """draws: one dict {iid: d} per seed. Pooled point = mean d over (instance, draw) pairs;
    instance bootstrap in which all draws of a resampled instance move together."""
    if isinstance(draws, dict):
        draws = [draws]
    ids = [i for i in ids if any(i in d for d in draws)]
    if not ids:
        return {"n": 0}

    def mean_over(s):
        v = [d[i] for i in s for d in draws if i in d]
        return sum(v) / len(v) if v else 0.0
    pt = mean_over(ids)
    rng = random.Random(cc.SEED)
    bs = []
    for _ in range(B):
        bs.append(mean_over([ids[rng.randrange(len(ids))] for _ in ids]))
    bs.sort()
    b_ = sum(1 for d in draws for i in ids if d.get(i) == 1)
    c_ = sum(1 for d in draws for i in ids if d.get(i) == -1)
    p_pos = sum(x > 0 for x in bs) / B
    p_neg = sum(x < 0 for x in bs) / B
    if pt > 0 and p_pos >= LABEL_PROB:
        label = "SIGN-CONSISTENT"
    elif pt < 0 and p_neg >= LABEL_PROB:
        label = "SIGN-INCONSISTENT"
    else:
        label = "UNINFORMATIVE"
    return {"n": len(ids), "n_draws": len(draws), "delta": pt, "b_off_only": b_, "c_on_only": c_,
            "ci80": (bs[int(.1 * (B - 1))], bs[int(.9 * (B - 1))]),
            "ci95": (bs[int(.025 * (B - 1))], bs[int(.975 * (B - 1))]),
            "P_boot_delta_gt0": p_pos, "label": label}


def verified_ref(single_file_only: bool) -> float:
    """Pooled gpt Verified Delta (headline + logged re-run draws) on pairwise-attempted instances;
    single_file_only restricts to gold patches touching exactly one file (A6)."""
    from contam_score import pairs_for
    gold = cc.load_json(cc.VER / "gold_patches.json")
    v = []
    for on, off in cc.ARMS["gpt"].values():
        d = pairs_for(on, off)
        v += [x for i, x in d.items() if not single_file_only or len(cc.gold_files(gold[i])) == 1]
    return sum(v) / len(v)


def cmd_checks(args) -> int:
    man, packs, ids = _load(args.gold_gate)
    out = checks(man, packs, ids)
    CHECKS.write_text(json.dumps(out, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "classes"}, indent=1))
    print(f"[manip-checks] {CHECKS}\n[sha256] {cc.sha256_file(CHECKS)}  <- commit BEFORE `join`")
    return 0


def cmd_join(args) -> int:
    sha = cc.sha256_file(CHECKS)
    if not committed_sha(sha) and not args.unblinded_test:
        print(f"REFUSE: manip_checks sha256 {sha} not in a committed revision of {cc.PREREG}")
        return 1
    man, packs, ids = _load(args.gold_gate)
    chk = cc.load_json(CHECKS)
    cls = chk["classes"]
    draws = [pairs(on, off) for on, off in args.gpt]      # one (ON, OFF) pair per seed (A.7 Seeds)
    late = [i for i in ids if man[i]["stratum_0401"]]
    bc = [i for i in ids if cls.get(i) == "B>C"]
    single = [i for i in ids if len(cc.gold_files(man[i]["patch"])) == 1]
    out = {"checks_sha256": sha, "unblinded_test": bool(args.unblinded_test), "gpt_seeds": len(draws),
           "A1_gpt_all": est(draws, ids), "A2_gpt_0401": est(draws, late), "A3_gpt_BC": est(draws, bc)}
    ref = verified_ref(False)
    a1 = out["A1_gpt_all"]
    out["A4_vs_verified"] = {"delta_ref_verified": ref,
                             "ratio": (a1.get("delta") or 0) / ref,
                             "same_sign": (a1.get("delta") or 0) > 0}
    ref1 = verified_ref(True)
    a6 = est(draws, single)
    a6.update({"delta_ref_verified_single_file": ref1,
               "ratio": (a6.get("delta") or 0) / ref1 if ref1 else None})
    out["A6_gpt_single_gold_file"] = a6
    if args.qwen:
        out["A5_qwen3coder_all"] = est(pairs(*args.qwen), ids)
    # A.6: retrieval-shifted rule (B>C prevalence on the post packs below 10%)
    shifted = (chk.get("B>C_prevalence") or 0) < 0.10
    out["retrieval_shifted"] = shifted
    out["headline_row"] = "A3_gpt_BC" if shifted else "A1_gpt_all"
    out["verdict_A1"] = (a1.get("label") or "") + (" (retrieval-shifted)" if shifted else "")
    if chk.get("files_off_mean") is not None and chk.get("files_on_mean") is not None \
            and not chk["files_off_mean"] < chk["files_on_mean"]:
        out["verdict_A1"] = "manipulation failed (no A1-A6 verdict)"
    p = ROOT / "join_post.json"
    p.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("checks")
    c.add_argument("--gold-gate", default=None)
    j = sub.add_parser("join")
    j.add_argument("--gold-gate", required=True)
    j.add_argument("--gpt", nargs=2, action="append", required=True,
                   help="ON.json OFF.json; repeat once per seed (two seeds if the A.9 projection allows)")
    j.add_argument("--qwen", nargs=2, default=None)
    j.add_argument("--unblinded-test", action="store_true")
    args = ap.parse_args()
    return {"checks": cmd_checks, "join": cmd_join}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
