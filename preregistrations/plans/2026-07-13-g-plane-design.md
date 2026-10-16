# The G Plane — a generation harness that trusts the retriever

> Pre-registered 2026-07-13, BEFORE any G-plane instance is run. The R-plane
> (Rainbow Retriever) is finished and measured. This document designs, and binds
> the analysis of, the *generation* plane.

## Why the parity result does not close the question

The n=386 paired SWE-bench result (fusion 78.5% vs vanilla 78.5%, McNemar p=1.0)
was produced by a harness in which the retrieval arm and the grep arm are the
**same agent with the same instructions and the same freedom**. The tool counts
say it plainly:

| | rag calls | grep | read | bash |
|---|---|---|---|---|
| fusion arm | 1,298 | 641 | 1,819 | 1,199 |
| vanilla arm | 0 | 1,833 | 1,508 | 1,277 |

The fusion agent substituted `rag` for `grep` and **kept every other habit**: it
re-read files the retriever had already handed it (with signatures/snippets), it
shelled out to verify, it explored. Given a strong model and unlimited turns,
both arms converge on the same understanding by different roads — so of course
they resolve the same issues at the same context cost. **We measured retrieval
quality inside a policy that ignores retrieval quality.**

The question the P5 result actually answers is: *does better retrieval help an
agent that treats retrieval as one optional hint among many?* Answer: no.
The question we have never asked: *does better retrieval let us build a cheaper,
tighter agent that doesn't need to explore at all?* That is the G plane.

## What we control (verified 2026-07-13)

`claude` CLI exposes: `--system-prompt` (full base-prompt REPLACEMENT),
`--system-prompt-file`, `--append-system-prompt`,
`--exclude-dynamic-system-prompt-sections`, `--allowed-tools` /
`--disallowed-tools`, `--settings` (PreToolUse hooks), `--max-turns`,
`--max-budget-usd`. Everything needed to write a different agent.

## The design: three G-plane policies

### G0 — Explorer (control; what P5 ran)
Default Claude scaffold, all tools, retrieval offered as a tool. Already
measured on n=500. No re-run needed.

### G1 — Context Pack ("trust, then verify locally")
- **Retrieval happens before the model wakes up.** The harness queries retrievald
  itself (`mode=hybrid`, the served fusion config, `limit=12`, `--sig`), and
  injects the hits — `file:line symbol [kind]` + signature + snippet — into the
  *prompt* as a `## Retrieved context` block. Zero turns spent searching.
- **System prompt replaced** (not appended): the agent is told the pack is the
  product of a retrieval system that outperforms grep, that the fix is almost
  certainly in these files, and that its job is to read the necessary one(s) and
  edit. No exploration ritual, no "let me first understand the codebase."
- **Tools: Read + Edit + Write only.** No Bash, no Grep, no Glob. It may open
  files from the pack (or any file — Read is unrestricted, we're testing trust,
  not enforcing it) but it cannot shell out or search.
- `--max-turns 10`.

### G2 — Pure Trust ("the retriever's file set is the agent's whole world")

**AMENDED 2026-07-13, before any G2 instance was run** (disclosed): the original
G2 (`Edit`+`Write`, no `Read`) is an *invalid instrument*, not a hypothesis —
Claude's Edit tool refuses to modify a file that was not Read in-session, so
that arm could never produce a patch for any reason connected to retrieval. It
would have yielded a 100% empty-patch rate that decision rule #4 would have
misread as evidence for the null. Caught by the mandated one-instance smoke test
before spending. The amended arm preserves the original intent (can the agent
succeed inside the retriever's world, with no exploration?) with a working
instrument:

- Same pack, larger (`limit=20`), snippets included.
- **Tools: Read + Edit + Write**, with a **PreToolUse hook that DENIES any Read
  whose path is not in the pack's file list.** The retriever's returned files are
  the agent's entire accessible universe: if retrieval surfaced the right files,
  the agent can fix the issue; if it did not, the agent is structurally unable
  to. That is the sharp, falsifiable test of retrieval *sufficiency*.
- `--max-turns 8`.

### G3 — Scarcity (the sharpest test, run on both R arms)
Both a retrieval arm and a grep arm under a **hard turn cap of 4** and default
prompts. Retrieval's value should be *most* visible when the agent cannot
afford to explore. If fusion degrades more slowly than vanilla as the budget
shrinks, retrieval buys robustness the unconstrained harness hides.

## Pre-registered protocol (binding)

**Slice:** the first 100 instance_ids of SWE-bench Verified in sorted order
(pre-declared, no cherry-picking; covers astropy → django). All arms run this
identical slice. Controls (G0-fusion, G0-vanilla) are *reused from P5* — already
graded on these instances, no re-spend.

**Arms to run:** G1-pack, G2-trust, G3-scarce-fusion, G3-scarce-vanilla
(4 × 100 × ~$0.45 ≈ $180 estimated; hard stop at $300).

**Grading:** official Docker harness, `--cache_level instance`, same as P5.

**Decision rules (binding, applied literally):**

1. **Efficiency win (the branch-B world):** G1 resolves ≥ (G0-fusion − 3pp) on
   the slice AND its mean peak context is ≤ 60% of G0-fusion's →
   *retrieval converts to a cheaper agent.* This is the deployable claim: same
   outcomes, far less context, fewer turns, lower cost.
2. **Trust win (the strong claim):** G2 resolves ≥ (G0-fusion − 5pp) →
   *the retriever's output alone suffices to fix real issues* — a striking
   result about retrieval sufficiency, and the one that would make the paper's
   §6 a positive contribution rather than a null.
3. **Scarcity win:** under the 4-turn cap, (G3-fusion − G3-vanilla) resolved-rate
   delta is significant (McNemar p<0.05) → *retrieval value is real but only
   visible under budget pressure* — i.e., absorption is an artifact of
   unlimited exploration, which is itself a publishable finding about how the
   field evaluates RAG for agents.
4. If none fire: the null stands and strengthens — retrieval quality does not
   convert to agent outcomes *under any policy we can construct*, which is a
   stronger, more honest version of the P5 result and the centerpiece of the
   paper's negative contribution.

**No mid-run prompt tuning.** The G1/G2 system prompts are frozen in this
commit (see `scripts/eval/g_plane_prompts.py`). If a prompt is changed after
seeing results, it becomes a new, disclosed arm — not a revision.

## Why this is the right experiment

The RAG literature almost universally evaluates retrieval by bolting it onto a
default agent and measuring end-task deltas. Our P5 null says that measurement
is nearly uninformative for strong models: the agent's policy, not the
retriever's quality, determines the outcome. The G plane tests the complementary
hypothesis — that better retrieval's payoff is *policy simplification*: fewer
turns, less context, a smaller model's worth of reasoning, and eventually a
cheaper deployment. That is the claim HARNESS actually cares about, and it is the
one nobody has measured.

## Implementation

- `scripts/eval/g_plane_prompts.py` — frozen system prompts + pack formatter.
- `scripts/eval/swe_bench.py` — new `--g-plane {explore,pack,trust,scarce}` mode
  on `predict`; pack mode pre-queries retrievald, injects the block, replaces the
  system prompt, restricts tools, caps turns.
- `scripts/eval/p5_run_gplane.py` — chunked runner with spend checkpoints
  ($300 stop), resume, per-arm labels.
