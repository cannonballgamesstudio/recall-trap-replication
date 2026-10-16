#!/usr/bin/env python3
"""Pre-mint provenance lint (methodology reviewer ruling 6 standing gate).

Greps a paper draft (or extracted PDF text) for pre-registration / power vocabulary and
flags every "pre-registered" / "powered" claim for manual cross-check against
docs/paper/PREREG-LEDGER.md. Run before every PDF build and before any public release.

Usage:
    python scripts/eval/prereg_lint.py paper.md
    pdftotext DRAFT-v5.pdf - | python scripts/eval/prereg_lint.py -   # lint the PDF a reviewer reads

Exit 0 if no CLAIM-bearing hits need review (only disclaimers/definitions), else 1.
The lint does not judge truth — it forces a human to confirm each claim maps to a ledger
row whose commit date precedes the arm's first data. It exists because three false anchors
survived a teardown + a fix pass; the grep is the backstop.
"""
import sys, re

# vocabulary that must always be verifiable against the ledger
CLAIM = re.compile(r"pre-?registered|pre-?registration|\bpowered\b|pre-?committed|pre-?declared|\bbinding\b|design-committed|\bconfirmatory\b|pre-?specified")
# phrasings that are DISCLAIMERS / definitions / correct branch-usage, not claims to verify
SAFE = re.compile(
    r"not (a |as )?pre-?register|no pre-?registration|not called pre-?register|"
    r"do not call|is used only for|reference is withdrawn|no such committed|"
    r"Class-?1|Class-?2|design-committed confirmatory|binding branch|no longer bind|"
    r"stops binding|budget (no longer |stops )?bind|not pre-?registered|"
    r"registered and audited|five primary|a sensitivity analysis|no committed",
    re.I,
)

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "-"
    text = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    lines = text.splitlines()
    flags = []
    for i, ln in enumerate(lines, 1):
        for m in CLAIM.finditer(ln):
            # window around the hit to judge disclaimer vs claim
            s, e = max(0, m.start() - 40), min(len(ln), m.end() + 40)
            ctx = ln[s:e]
            if SAFE.search(ctx):
                continue
            flags.append((i, m.group(0), ctx.strip()))
    if not flags:
        print("prereg-lint: OK — no unguarded provenance/power claims to review.")
        return 0
    print(f"prereg-lint: {len(flags)} claim-bearing hit(s) — confirm each maps to a PREREG-LEDGER.md row")
    print("  (a Class-1 commit dated before the arm's first data; for 'powered', a committed MDE or the §6.2 machinery)\n")
    for i, tok, ctx in flags:
        print(f"  L{i}: [{tok}]  …{ctx}…")
    return 1

if __name__ == "__main__":
    sys.exit(main())
