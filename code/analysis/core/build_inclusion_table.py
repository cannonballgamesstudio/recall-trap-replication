"""Build the per-instance inclusion table / manifest (results/inclusion_table.csv).

One row per (arm, side, instance) for every graded SWE-bench Verified arm in arms.json.
Columns give the mutually exclusive status (resolved, unresolved, empty, harness_error,
never_predicted) and the exact input files that row derives from (served pack file + key,
prediction file, raw-response file, official run report, per-instance report archive),
so every denominator and every table row in the paper is derivable.
"""
from __future__ import annotations

import json

from common import ARMS, ALL_IDS, SV, RESULTS, load_report, statuses_from_report, repo_of, write_csv


def load_jsonl(name):
    out = {}
    if not name:
        return out
    p = SV / ("predictions" if name.startswith("preds") else "raw_responses") / name
    if not p.exists():
        return out
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                d = json.loads(line)
                out[d["instance_id"]] = d
    return out


def main():
    rows, summary = [], []
    for a in ARMS:
        for side in ("ON", "OFF"):
            s = a.get(side)
            if not s or not s.get("report"):
                continue
            rep = load_report(s["report"])
            st = statuses_from_report(rep)
            preds = load_jsonl(s.get("preds"))
            raw = load_jsonl(s.get("raw"))
            packs = a.get("packs_" + side) or a.get("packs")
            pack_key = None
            if packs in ("local_packs.json", "dense_packs.json", "bm25_packs.json") or (packs or "").startswith("packs_k"):
                pack_key = "dedup" + side          # file[instance]["dedupON"|"dedupOFF"]["pack"]
            elif (packs or "").endswith("_wrapped.json"):
                pack_key = "dedupON"               # file[instance]["dedupON"]["pack"]
            model, run = s["report"][:-5].split(".", 1)
            counts = {k: 0 for k in ("resolved", "unresolved", "empty", "harness_error", "never_predicted")}
            for iid in ALL_IDS:
                status = st[iid]
                counts[status] += 1
                r = raw.get(iid, {})
                rows.append(dict(
                    arm_id=a["arm_id"], side=side, instance_id=iid, repo=repo_of(iid), status=status,
                    patch_nonempty=(int(bool((preds.get(iid) or {}).get("model_patch", "").strip())) if iid in preds else ""),
                    raw_applied=r.get("applied", ""), raw_finish_reason=r.get("finish_reason", ""),
                    raw_content_len=r.get("content_len", ""),
                    # "<instance>" = file[instance] is the pack string itself
                    packs_file=packs or "", pack_key=pack_key or ("<instance>" if packs else ""),
                    preds_file=s.get("preds") or "", raw_file=s.get("raw") or "", report_file=s["report"],
                    per_instance_report=(f"grading/per_instance/{run}.tar.gz:{run}/{iid}/report.json"
                                         if a.get("per_instance_reports") and status in ("resolved", "unresolved") else ""),
                ))
            summary.append(dict(arm_id=a["arm_id"], side=side, report=s["report"], **counts))
    write_csv(RESULTS / "inclusion_table.csv", rows)
    write_csv(RESULTS / "inclusion_summary.csv", summary)
    print(f"wrote {len(rows)} rows; {len(summary)} arm-sides")


if __name__ == "__main__":
    main()
