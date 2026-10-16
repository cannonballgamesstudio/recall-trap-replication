"""Task 0: error_instances audit of every report used in reanalysis2."""
from ra2 import REPORTS, error_audit, write_md, dump

rows = error_audit(list(REPORTS))
lines = ["## Task 0 — error_instances audit (every report used below)", "",
         "| key | report | submitted | resolved | empty | error_instances | error ids |", "|---|---|---|---|---|---|---|"]
for k, f, s, r, e, ne, ids in rows:
    flag = "**" if ne else ""
    lines.append(f"| {k} | {f} | {s} | {r} | {e} | {flag}{ne}{flag} | {', '.join(ids) if ids else ''} |")
lines.append("")
lines.append("Errored instances are scored unresolved everywhere below (the paper's convention). Nonzero counts are bolded.")
write_md("t0_audit", "\n".join(lines) + "\n")
dump("t0_audit", rows)
