# The oracle ceiling — pre-registered 2026-07-14, before any instance is run

> Written and committed BEFORE the first oracle instance executes. Binds the
> analysis. This experiment bounds an entire hypothesis class, so it is worth
> more than any arm we could build on top of the retriever.

## The question

The G-plane result (n=311 paired, official Docker eval) is:

| arm | resolved | vs explorer |
|---|---|---|
| explorer (tools, retrieval offered) | 80.4% | — |
| one-shot pack, no search tools | 76.2% | −4.2pp, McNemar p=0.029 |
| pack + reads restricted to pack | 73.6% | −6.8pp, p=0.0015 |

A BM25 pack scores the same as the tuned fusion pack (p=1.00). So the 4.2pp is
*not* explained by retrieval quality as we vary it. Two hypotheses remain:

- **H-loc (localization gap):** our retriever simply misses files the explorer
  finds. A better retriever — or a planner loop that queries repeatedly — would
  close the gap. Everything we might build next (planner harness, search
  sidecar, bigger packs) lives inside this hypothesis.
- **H-exp (exploration-as-reasoning):** the missing accuracy is not *finding*
  the files but the act of reading, running, and iterating in the repo. If so,
  no retrieval system at any quality closes the gap, because the gap is not
  about retrieval.

## The instrument

**ORACLE-PACK-NO-TOOLS.** Build the pack from the *gold patch's own files and
line ranges* — perfect localization, the strict upper bound of any retrieval
system that will ever exist — and give it to the solver under `PACK_SYSTEM`
with Read/Edit/Write and **no search tools**, identical to the G1 arm in every
other respect (same prompt, same turn cap, same model, same grading).

A planner cannot exceed oracle retrieval. So this single arm bounds the entire
class of "build something better on top of the retriever" proposals.

**What was NOT this experiment:** `scripts/eval/oracle_bench.py` (June) injected
perfect hits on *private-repo*, for a *file-listing* task, with *all tools still
available* ("verify or expand with more rag query calls only if needed"), and
measured *turns*. It answered "does perfect first-shot retrieval save an
exploring agent any turns?" (no). It did not, and could not, answer the ceiling
question. That distinction is why this arm is worth running.

## Protocol (binding)

- **Slice:** the same pre-declared first-100 instance_ids of SWE-bench Verified
  (sorted order) used by the G-plane arms. Controls (G0-explorer, G1-pack) are
  reused from the existing graded runs — no re-spend, and the pairing is exact.
- **Pack construction:** files touched by the gold patch; for each, the hunks'
  line ranges expanded to the enclosing symbol via the existing fusion chunk
  table. Formatted by `format_pack()` **verbatim** — byte-identical shape to G1,
  so the only variable is *which* chunks are in it.
- **Solver:** identical to G1 (`PACK_SYSTEM`, Read/Edit/Write, `--max-turns 10`,
  same model). No Bash, no Grep, no Glob.
- **Grading:** official SWE-bench Docker harness, `--cache_level instance`.
- **Analysis:** McNemar exact on the paired slice vs the explorer.
- **Cost:** ~100 × $0.45 ≈ $45; hard stop at $80.

**Contamination note (disclosed):** the pack is derived from the gold patch, so
this arm is an *oracle*, not a system. It is a ceiling measurement and will be
reported as such. It is not a leaderboard result and will never be submitted as
one.

## Decision rules (binding, applied literally)

1. **Oracle ≥ explorer − 1.0pp AND McNemar p > 0.10** → *retrieval can substitute
   for exploration; the 4.2pp is a localization gap.* **H-loc lives.** GO on the
   search-sidecar / planner arm, with the oracle as its target band.
2. **Oracle ≤ explorer − 2.0pp** → **H-loc is FALSIFIED.** Perfect retrieval plus
   no tools still loses, so the missing accuracy is exploration-as-reasoning, not
   recall. No retrieval system at any quality — no planner, no sidecar, no larger
   pack — recovers it. **Terminate the retrieval-conversion program.** This
   becomes the headline of the negative paper: *we handed the agent the answer
   and it still did worse than letting it look.*
3. **Between −1.0pp and −2.0pp** → ambiguous. Extend to n=250 before a line of
   planner code is written.

**Prior (recorded before the run, so it cannot be retrofitted):** I expect
77–79%, i.e. rule 2 — falsification. The June oracle already showed perfect
first-shot retrieval buys an exploring agent ~nothing, and the weakpack control
already showed pack quality is inert (p=1.00). If both hold, the ceiling is low.
I am running this *because* I expect it to kill the program cheaply, not because
I expect it to rescue it.

## What this does NOT test

Whether a free local model can do the *reading* on the frontier's behalf while
the frontier keeps directing (the "search sidecar", cf. SWE-Edit: +2.1pp,
−17.9% tokens). That architecture survives even under rule 2, because it keeps
exploration and only relocates its token cost. It is a *cost* claim, not a
*retrieval-conversion* claim, and it needs its own pre-registration.
