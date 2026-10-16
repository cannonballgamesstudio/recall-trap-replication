"""Reconstruct the WITHDRAWN first-pass grading reports of Arm T (both models).

The first grading of Arm T hit registry rate-limit errors on many instances. The errored instances were
regraded under the same run identifier, which overwrote the run-level summary report; instances graded
in the first pass kept their per-instance report.json untouched. The first-pass report is therefore
recoverable from the per-instance archive: a report.json whose modification time precedes the end of the
first grading pass belongs to the first pass; every other non-empty prediction was a harness error in it.

The cutoffs are the end times of the first-pass grading logs (data/trimmed-breadth/grading/logs/
eval_trimT_*_T.log, which also print the first-pass summary counts used as the check below).

Run from the package root:  python code/analysis/trimmed_breadth/reconstruct_first_pass.py
"""
import json
import tarfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

TB = Path("data/trimmed-breadth")
OUT = Path("results/trimmed-breadth")
EDT = timezone(timedelta(hours=-4))
RUNS = {
    # run id: (summary report, model dir, first-pass log end, expected first-pass counts from the log)
    "trimT_qwen30b_T": ("local_qwen3coder30b_T.trimT_qwen30b_T.json", "local_qwen3coder30b_T",
                        datetime(2026, 10, 14, 1, 28, 43, tzinfo=EDT),
                        dict(completed=112, resolved=14, errors=136, empty=225)),
    "trimT_gpt56sol_T": ("local_gpt56sol_T.trimT_gpt56sol_T.json", "local_gpt56sol_T",
                         datetime(2026, 10, 14, 20, 47, 27, tzinfo=EDT),
                         dict(completed=221, resolved=113, errors=174, empty=78)),
}

OUT.mkdir(parents=True, exist_ok=True)
for run, (summ, model, cutoff, expect) in RUNS.items():
    final = json.loads((TB / "grading/summary" / summ).read_text(encoding="utf-8"))
    sub, empty = set(final["submitted_ids"]), set(final["empty_patch_ids"])
    first_done, first_res = set(), set()
    with tarfile.open(TB / "grading/per_instance" / f"{run}.tar.gz") as tf:
        for m in tf.getmembers():
            if not m.isfile():
                continue
            iid = m.name.split("/")[-2]
            if datetime.fromtimestamp(m.mtime, timezone.utc) <= cutoff:
                first_done.add(iid)
                rep = json.loads(tf.extractfile(m).read())
                if rep.get(iid, {}).get("resolved"):
                    first_res.add(iid)
    errors = sub - empty - first_done
    got = dict(completed=len(first_done), resolved=len(first_res), errors=len(errors), empty=len(empty))
    status = "MATCHES the first-pass log" if got == expect else f"MISMATCH (log says {expect})"
    rep = dict(note="RECONSTRUCTED first-pass report (withdrawn; harness errors scored unresolved in the "
                    "withdrawn analysis). Do not use for inference.",
               run_id=run, submitted_instances=len(sub), completed_instances=len(first_done),
               resolved_instances=len(first_res), empty_patch_instances=len(empty), error_instances=len(errors),
               submitted_ids=sorted(sub), completed_ids=sorted(first_done), resolved_ids=sorted(first_res),
               empty_patch_ids=sorted(empty), error_ids=sorted(errors),
               regraded_ids_now_resolved=sorted(set(final["resolved_ids"]) - first_res))
    (OUT / f"WITHDRAWN_first-pass_{run}.reconstructed.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print(run, got, status)
