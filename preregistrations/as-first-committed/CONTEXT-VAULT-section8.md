# Context document, Section 8 only (as first committed)

## §8 Pre-registrations for the four MUST-DO runs (commit BEFORE executing)

1. **BM25-only dedup A/B** — IN FLIGHT (`kpack_bm25ON/OFF.json`, keyword-mode packs,
   packfile g-plane). Kills "is it a FusionBackend artifact?" Rule: if dedup-OFF still
   beats dedup-ON significantly on BM25, the effect is retriever-agnostic.
2. **Frontier non-Claude replication** — IN FLIGHT (GLM/DeepSeek/Kimi × dedupON/OFF,
   n=100; extend the winner to n≥300). Rule: ≥1 significant same-direction frontier
   result = tier gate cleared.
3. **REAL served k-sweep** k∈{2,3,5,8,12}, all served through Docker from the same
   ranking source, n=100-200, bootstrap CIs. Replaces the reconstruction curve;
   resolves 81-vs-76 and the k=12-recon vs real-dedup-ON cross-check.
4. **Statistical hygiene sweep** — exact McNemar; dropped-instance identity+reason+both-ways
   sensitivity; discordant counts everywhere; Wilson CIs on the n=22 taxonomy;
   slice-vs-full balance for the sorted-first-100 (or rerun mechanism on a RANDOM 100);
   per-arm apply-rates; multiplicity over 7 hyps; unit tests + dead-conditional fix;
   verify 3 unverified prior-art threads.

**Nice-to-have (accept→strong-accept):** #5 swebench-ml 2nd benchmark; #6 tools-on
seed-context bound; #7 budget sweep K∈{4,8,20} (**the crossover figure that reconciles
DeepDiscovery** — recall helps at large K, hurts at small K), budget-matched
small-to-big baseline, 2nd embedder.

---
