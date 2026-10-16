"""Parse-apply-test funnel from raw responses (paper Sec. 5.4 'Failure classes and the funnel').

For each arm with persisted raw responses: share of instances with emitted text, share whose
SEARCH/REPLACE edits applied (raw 'applied' flag), resolve rate, and test-pass conditional on
applied (resolved / applied). Writes results/funnel.md. The gpt row of the paper comes from
the pre-registered logged replication (arm F1); see also results/logrep_funnel_result_*.txt.
"""
from __future__ import annotations

from common import RESULTS, ALL_IDS, load_inclusion
import csv

ARMS = ["P2_deepseek_fusion", "P4_DENSE1_gpt_dense", "F1_gpt_logged_replication", "P3_qwen36_fusion_K12",
        "M1_qwen3coder30b_AC", "R1_gpt_bm25"]


def main():
    tab = load_inclusion()
    raw = {}
    with open(RESULTS / "inclusion_table.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            raw[(r["arm_id"], r["side"], r["instance_id"])] = r
    lines = ["# Parse-apply-test funnel (recomputed from raw responses + official reports)", "",
             "| arm | side | n (raw rows) | emitted text | applied | resolved | test-pass given applied |",
             "|---|---|---|---|---|---|---|"]
    for arm in ARMS:
        tpa = {}
        for side in ("ON", "OFF"):
            st = tab.get((arm, side))
            if not st:
                continue
            rows = [raw[(arm, side, i)] for i in ALL_IDS if raw[(arm, side, i)]["raw_applied"] != ""]
            if not rows:
                continue
            n = len(rows)
            emitted = sum(1 for r in rows if r["raw_content_len"] not in ("", "0"))
            applied = [r for r in rows if r["raw_applied"] in ("1", "True", "true")]
            res_app = sum(1 for r in applied if r["status"] == "resolved")
            res = sum(1 for r in rows if r["status"] == "resolved")
            tpa[side] = res_app / max(1, len(applied))
            lines.append(f"| {arm} | {side} | {n} | {100*emitted/n:.1f}% | {100*len(applied)/n:.1f}% | {100*res/n:.1f}% | "
                         f"{100*tpa[side]:.1f}% ({res_app}/{len(applied)}) |")
        if "ON" in tpa and "OFF" in tpa:
            lines.append(f"| {arm} | OFF-ON | | | | | {100*(tpa['OFF']-tpa['ON']):+.1f}pp |")
    (RESULTS / "funnel.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
