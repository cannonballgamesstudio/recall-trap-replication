"""Branch A gold gate (pre-reg A.4) from per-instance report.json (source of truth).
Pass iff every expected FAIL_TO_PASS test passes and no PASS_TO_PASS test fails
(a test missing from the report counts as not passing / failing, as the harness does)."""
import json, sys
from pathlib import Path

ROOT = Path(r"data/post-cutoff-branchA")
LOGS = ROOT / "gold" / "logs" / "run_evaluation" / "rebench_post_gold" / "gold"
man = json.loads((ROOT / "instances_post.json").read_text(encoding="utf-8"))
rows, passing = [], []
for x in man:
    iid = x["instance_id"]
    f2p = x["FAIL_TO_PASS"]; p2p = x["PASS_TO_PASS"]
    f2p = json.loads(f2p) if isinstance(f2p, str) else list(f2p)
    p2p = json.loads(p2p) if isinstance(p2p, str) else list(p2p)
    rp = LOGS / iid / "report.json"
    r = {"instance_id": iid, "stratum_0401": bool(x["stratum_0401"]), "n_f2p": len(f2p), "n_p2p": len(p2p)}
    if not rp.exists():
        r.update(passed=False, reason="no_report")
    else:
        rep = json.loads(rp.read_text(encoding="utf-8"))[iid]
        ts = rep.get("tests_status") or {}
        f_ok = set(ts.get("FAIL_TO_PASS", {}).get("success", []))
        p_fail = set(ts.get("PASS_TO_PASS", {}).get("failure", []))
        miss_f2p = [t for t in f2p if t not in f_ok]
        bad_p2p = [t for t in p2p if t in p_fail]
        ok = rep.get("patch_successfully_applied", False) and not miss_f2p and not bad_p2p
        r.update(passed=bool(ok), applied=rep.get("patch_successfully_applied"),
                 harness_resolved=rep.get("resolved"), f2p_not_passing=len(miss_f2p),
                 p2p_failing=len(bad_p2p),
                 reason=None if ok else ("not_applied" if not rep.get("patch_successfully_applied")
                                         else f"f2p_miss={len(miss_f2p)} p2p_fail={len(bad_p2p)}"))
    rows.append(r)
    if r["passed"]:
        passing.append(iid)
out = ROOT / "gold" / "gold_gate_post.jsonl"
out.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8", newline="\n")
(ROOT / "gold_pass_ids_post.txt").write_text("\n".join(passing) + "\n", encoding="utf-8", newline="\n")
late = [r for r in rows if r["stratum_0401"]]
print(f"pass {len(passing)}/{len(rows)}; >=2026-04-01: {sum(r['passed'] for r in late)}/{len(late)}")
print("disagree with harness 'resolved':",
      [r["instance_id"] for r in rows if "harness_resolved" in r and r["harness_resolved"] != r["passed"]])
from collections import Counter
print(Counter((r["reason"] or "pass").split(" ")[0] for r in rows))
for r in rows:
    if not r["passed"]:
        print("  FAIL", r["instance_id"], r["reason"])
