"""Build a swebench-style summary report from per-instance report.json files (source of truth when the
fork's aggregator crashes). submitted_ids = every prediction id (as swebench make_run_report does);
empty_patch_ids = empty model_patch; resolved_ids = report.json resolved True; error_ids = non-empty
prediction with no report.json (must be re-run before analysis).
Usage: python agg_reports.py PREDS.jsonl RUN_ID LOGS_ROOT OUT.json"""
import json, sys
from pathlib import Path
preds_p, run_id, logs_root, out = sys.argv[1:5]
preds = [json.loads(l) for l in Path(preds_p).read_text(encoding="utf-8").splitlines() if l.strip()]
sub, empty, res, unres, err = [], [], [], [], []
for p in preds:
    iid = p["instance_id"]; sub.append(iid)
    if not (p.get("model_patch") or "").strip():
        empty.append(iid); continue
    rp = Path(logs_root) / "run_evaluation" / run_id / p["model_name_or_path"] / iid / "report.json"
    if not rp.exists():
        err.append(iid); continue
    r = json.loads(rp.read_text(encoding="utf-8"))[iid]
    (res if r.get("resolved") else unres).append(iid)
d = {"total_instances": len(sub), "submitted_instances": len(sub), "completed_instances": len(res) + len(unres),
     "resolved_instances": len(res), "unresolved_instances": len(unres), "empty_patch_instances": len(empty),
     "error_instances": len(err), "submitted_ids": sorted(sub), "resolved_ids": sorted(res),
     "unresolved_ids": sorted(unres), "empty_patch_ids": sorted(empty), "error_ids": sorted(err),
     "source": "per-instance report.json (agg_reports.py)"}
Path(out).write_text(json.dumps(d, indent=1), encoding="utf-8")
print({k: v for k, v in d.items() if not k.endswith("_ids")}, "errors:", err[:20])
