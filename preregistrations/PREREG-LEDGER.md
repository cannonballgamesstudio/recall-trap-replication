# Pre-registration ledger — "The Recall Trap"

One row per design document. **Class 1** = design committed to git before ANY of the arm's data
existed (a reviewer can verify with `git log`). **Class 2** = dated design note with no pre-data
commit (committed at release with a provenance header; a file mtime is not an anchor). The paper
uses "pre-registered" ONLY for Class-1 arms; same-day-as-unblinding orderings are called
"design-committed" instead. This ledger is the pre-mint gate: every "pre-registered" hit in the
draft must map to a Class-1 row whose commit date is verifiably before the arm's first data.

| document | commit | commit date | governs | first data | class |
|---|---|---|---|---|---|
| `2026-07-14-e1-e2-allocation.md` | 1eaab36 | 2026-07-14 12:56 | gpt + DeepSeek single-shot dedup A/B (primary estimand) | 2026-07-14 (same day unblinded) | 1 (design-committed; within-day ordering rests on run logs) |
| `CONTEXT-VAULT.md §8` | ~a3447b0 | 2026-07-14 | BM25 retriever-agnosticism direction rule + n=100 pilot | n=100 pilot 07-14; n=500 later | 1 (direction rule + pilot); TOST design is Class 2 |
| `CLEAN-CONTROL-DESIGN.md` | 470a1c7 | 2026-07-15 | dedup-OFF>ON design audit | — | 1 |
| `AGENTIC-BENCH-PREREG-2026-07-15.md` | 211261a | 2026-07-16 | agentic-harness boundary null | after 07-16 | 1 |
| `QWEN36-PREREG.md` (+Amendment 1) | adc864d | 2026-07-17 | Qwen3.6-27B open-weights replication; 16k→32k amendment | after 07-17 | 1 |
| `GENERALITY-BENCH-PREREG.md` | e3e1ef0 | 2026-08-07 | multilingual SWE-PolyBench G-1–G-5; 80% ratability floor | after 08-07; exclusions frozen b9e36b0 | 1 |
| `GPT-LOGGED-REPLICATION-PREREG.md` | c35850a | 2026-08-08 | gpt logged confirmatory replication + parse-apply-test funnel; reporting rule + failure branch (clause d) | after this commit | 1 (replication arm + funnel only; original headline stays design-committed) |
| `G2-RANDOM-CHUNK-PREREG.md` | (release) | 2026-08-08 | random-chunk selection control decision rule | run ~07-17 | 2 (mtime 07-17, no pre-data commit) |
| `BM25-AGNOSTIC-PREREG.md` | (release) | 2026-08-08 | powered BM25 TOST 5pp margin + bound rule | run after 07-14 pilot | 2 (mtime 07-17, no pre-data commit) |
| budget-sweep "pre-registration" | — | — | (claimed to govern K-sweep + clean K4/K40) | — | PHANTOM — no such file; reference withdrawn |
| `2026-07-14-oracle-ceiling.md` | eae0aeb | 2026-07-14 09:38 | oracle-ceiling program arm | after commit | 1 |
| `2026-07-14-e0-missing-cell.md` | dbc1289 | 2026-07-14 11:42 | E0 missing-cell (oracle+tools) | after commit | 1 |
| `2026-07-14-c1-delivery-mode-control.md` | 8b26d65 | 2026-07-14 15:29 | C1 delivery-mode control | after commit | 1 |
| `2026-07-13-g-plane-design.md` | b3b693d | 2026-07-13 19:34 | g-plane program design | after commit | 1 |

## Non-pre-registered analyses disclosed as such in the paper
- The 5 infrastructure-hang exclusions in the multilingual A/B + their OFF-fail sensitivity: specified
  when the hangs were found during grading (2026-08-08), NOT in advance. Labeled "a sensitivity
  analysis (specified when the hangs were found, not in advance)" in §4.7 and §5.10.
- The clean K=4/K=40 dose-response axis: no committed design doc; reported as a within-model
  replication of the exploratorily-observed A3B trend, outside the confirmatory family (§5.9, §4.5).

## Standing pre-mint gate (per methodology reviewer ruling 6)
Before every PDF build and before any public release: grep the draft for
`pre-regist|prereg|pre-committed|pre-specified|pre-declared|design-committed|confirmatory|powered|binding`
and confirm each "pre-registered"/"powered" hit maps to a ledger row with a verifiable pre-data
commit (for "powered", to a committed MDE or the §6.2 MDE machinery). No hand-waived hits.
Remaining Ruling-6 audit items before any public release: automate this grep as a lint; verify the wider-program
commit hashes (or demote); final sweep of "confirmatory"/"binding" stragglers.
