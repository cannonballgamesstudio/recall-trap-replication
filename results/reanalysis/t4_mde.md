## Task 4 — MDE at 80% power, exact McNemar (α = 0.05 two-sided)

ψ = observed discordance rate (b+c)/n; p_c = observed ON-only (breadth-wins) discordance rate. (C) = paper convention, discordant count D fixed at the observed value (conditional power). (A) = ψ fixed, D ~ Binom(n, ψ) random (unconditional). (B) = p_c fixed, p_b = p_c + Δ (discordance grows with Δ). Power is exact enumeration over (D, b); bracketed values are Monte-Carlo checks (200,000 simulated trials). 'Power at obs.' = unconditional power at the observed split (|Δ|, observed p_b and p_c).

| null arm | n | Δ obs | disc OFF/ON | ψ | raw p | paper MDE | MDE (C) | uncond. power at (C) MDE | MDE (A) [sim power] | MDE (B) [sim power] | power at obs. Δ [sim] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| agentic fusion (sonnet-5) | 499 | -1.4pp | 28/35 | 12.6% | 0.450 | 4.5pp | 4.5pp | 79% | 4.6pp [80.4%] | 5.8pp [80.5%] | 12% [12%] |
| agentic dense (sonnet-5) | 499 | -1.8pp | 18/27 | 9.0% | 0.230 | 3.8pp | 3.9pp | 80% | 3.9pp [80.7%] | 5.2pp [80.6%] | 22% [22%] |
| Qwen2.5-Coder-32B | 98 | +2.0pp | 4/2 | 6.1% | 0.690 | 5.7pp | 5.7pp | 47% | not attainable (> ψ) | 11.2pp [80.2%] | 5% [5%] |
| agentic BM25 (opus-4-8) | 100 | -2.0pp | 2/4 | 6.0% | 0.690 | 5.6pp | 5.6pp | 47% | not attainable (> ψ) | 13.2pp [80.1%] | 5% [5%] |
| agentic dense (opus-4-8) | 100 | -2.0pp | 2/4 | 6.0% | 0.690 | 5.6pp | 5.6pp | 47% | not attainable (> ψ) | 13.2pp [80.1%] | 5% [5%] |
| A3B K=4 (text, §5.9) | 500 | +2.0pp | 26/16 | 8.4% | 0.164 | 3.6pp | 3.6pp | 77% | 3.8pp [80.2%] | 4.2pp [80.1%] | 29% [29%] |
| SWE-PolyBench pooled (text, §5.10) | 617 | +2.6pp | 39/23 | 10.0% | 0.0560 | 3.6pp | 3.8pp | 82% | 3.7pp [80.5%] | 4.0pp [80.7%] | 49% [49%] |
