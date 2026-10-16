# C1 — the delivery-mode control (push vs pull, prompt held fixed)

> Pre-registered 2026-07-14, BEFORE any C1 instance is run. Binds the analysis.
> This arm exists to KILL our own finding if it is an artifact.

## The finding under test

| arm (n=92 paired, official Docker) | resolved |
|---|---|
| E1: fusion pack **pre-injected** + tools | **83.7%** |
| explorer: same retriever offered as a **tool**, all tools | 75.0% |

+8.7pp, McNemar exact p=0.0386. And at n=500 the tool-delivered retriever was
worth *nothing* over grep (McNemar p=1.00). Claim: **retrieval-as-a-tool is
absorbed; retrieval-as-pre-injected-context converts. Delivery mode, not
retrieval quality, decides whether RAG helps an agentic coder.**

Two objections already answered:
- **Volition?** No. The explorer *called* the retriever on **84.2%** of instances
  (mean 2.6 calls, median 2, max 18) and still gained nothing. Absorption is not
  the agent ignoring its tool.
- **SHERLOC?** Not prior art. All six of its context conditions are *pre-injected
  text* into a tools-on agent; none is tool-delivery. It corroborates the
  injection half (+5.95pp).

## The objection that could still kill it

**The pack arms REPLACE the system prompt; the explorer runs the default one.**
So "delivery mode" is confounded with "prompt." A reviewer will find this
immediately, and they should.

## The instrument

**C1 = TOOL-PRIMED EXPLORER.** `TOOL_PRIMED_SYSTEM` is `PACK_TOOLS_SYSTEM` with
the same framing, the same trust language ("a retrieval system measured to
outperform grep... trust what it returns... the fix is almost certainly in the
files it names"), and the same task rules — but the retrieval is **PULLED** (the
agent runs `rag query`) instead of **PUSHED** (pre-injected into the prompt).

Same retriever. Same tools. Same turn cap (10). Same model. The only variable is
push vs pull.

- Slice: the same pre-declared first-100 instance_ids.
- Grading: official Docker harness, `--cache_level instance`.
- Analysis: McNemar exact, paired, vs E1 (83.7%) and vs the explorer (75.0%).

## Decision rules (binding, applied literally)

1. **C1 ≈ explorer (~75%), and C1 significantly BELOW E1:** the prompt is not
   doing the work. **Delivery mode is the cause.** Claim A stands, and the
   confound is answered on the page rather than in rebuttal.
2. **C1 ≈ E1 (~84%):** the *prompt* was doing the work, not the delivery
   mechanism. **Claim A is DEAD** — the finding is "tell the agent to trust the
   retriever and it does better," which is a prompting result, far smaller, and
   arguably already folklore. Report it as such and stop.
3. **C1 between, no significant difference from either:** underpowered at n=92;
   extend to n=500 before claiming anything.

**Prediction, recorded before the run:** rule 1 — C1 lands near the explorer
(74-78%). Reason: the explorer *already* had a trust-the-retriever policy
appended (`POLICY` in swe_bench.py) and already called `rag` on 84% of instances,
so the marginal effect of re-wording the instruction should be small. If the
prompt were the lever, the existing POLICY should already have moved it.

**My prediction record this week: 1 for 4.** I was right about E1 and wrong about
the oracle ceiling, the "novel" pack-size prediction, and the tools-hurt causal
story. Weight this accordingly.

## What this does NOT resolve

- **SWE-ContextBench (2602.08316)** ran a Free-vs-Oracle contrast on a coding
  agent (+12.1pp for injection) — same sign, same magnitude. We are not scooped
  (their contrast confounds delivery with *selection quality*; ours holds the
  retriever fixed on both sides) but we must cite it and state the distinction in
  the abstract, not bury it.
- **A-RAG (2602.03442) and Interact-RAG (2510.27566)** find tool-delivery WINS in
  multi-hop QA, by large margins. Our result runs backwards from theirs. The
  paper owes a mechanism: multi-hop QA needs iterative re-querying as bridge
  entities surface; single-issue code localization is closer to one-shot. The 84%
  uptake figure is what lets us pay that debt.
- **"Pack + tools" is already SHIPPED** (Copilot plan mode and others). The
  *recipe* is not novel and we must never imply it is. The measurement of *why*
  it works — and that its tool-delivered twin is worth zero — is what would be.
- **Claim B (tools x pack-quality interaction) is DEMOTED**: oracle+tools sits at
  88.0%, so "tools add nothing to a perfect pack" is what a ceiling produces
  mechanically. Two cells cannot carry an interaction. Secondary observation only.
