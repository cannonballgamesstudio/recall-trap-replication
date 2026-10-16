## Task 11 — Per-stratum point estimates, memorization section

Δ = OFF−ON (pp) unless stated; gpt pooled = mean over (instance, draw) for the discovery draw + logged re-run (the pre-registered estimator). Empty strata shown as —. Non-positive strata are listed under each table.

### Branch B, gpt-5.6-sol

| stratum | n inst | pooled (2 draws) | discovery draw | logged re-run |
|---|---|---|---|---|
| full | 500 | +6.5 | +7.6 | +5.4 |
| Low-M (E1) | 47 | +6.4 | +2.1 | +10.6 |
| High-M | 453 | +6.5 | +8.2 | +4.9 |
| M=0 (NA as 0) | 47 | +6.4 | +2.1 | +10.6 |
| M=1 (NA as 0) | 182 | +5.5 | +6.6 | +4.4 |
| M=2 (NA as 0) | 191 | +5.0 | +6.8 | +3.1 |
| M=3 (NA as 0) | 80 | +12.5 | +15.0 | +10.0 |
| M=0 (P1-eligible) | 14 | +10.7 | +0.0 | +21.4 |
| M=1 (P1-eligible) | 119 | +5.9 | +9.2 | +2.5 |
| M=2 (P1-eligible) | 153 | +6.2 | +9.2 | +3.3 |
| M=3 (P1-eligible) | 80 | +12.5 | +15.0 | +10.0 |
| S1: Low-M ∩ P1-eligible | 14 | +10.7 | +0.0 | +21.4 |
| p1 negative | 42 | +7.1 | +4.8 | +9.5 |
| p1 positive | 325 | +7.7 | +10.8 | +4.6 |
| p2_apply negative | 238 | +5.7 | +5.9 | +5.5 |
| p2_apply positive | 262 | +7.3 | +9.2 | +5.3 |
| p3 negative | 282 | +6.2 | +8.2 | +4.3 |
| p3 positive | 217 | +6.9 | +6.9 | +6.9 |
| B→C full | 80 | +25.6 | +26.2 | +25.0 |
| E2: Low-M ∩ B→C | 9 | +55.6 | +44.4 | +66.7 |
| High-M ∩ B→C | 71 | +21.8 | +23.9 | +19.7 |

Non-positive strata — pooled: none; discovery draw: [('M=0 (P1-eligible)', 0.0), ('S1: Low-M ∩ P1-eligible', 0.0)]; logged re-run: none.
Range of pooled stratum estimates: +5.0 to +55.6pp (paper text says 'no stratum ... outside +5.7 to +7.3' — that range holds only for E1/High and the single-probe P2/P3 strata; see surprises).

### E5, Qwen3-Coder-30B (local-GGUF M; one draw)

| stratum | n inst | OFF−ON | OFF−T | T−ON | K=4 (OR, proxy M) | K=12 (OR) | K=40 (OR) |
|---|---|---|---|---|---|---|---|
| full | 500 | +5.8 | +6.1 | -0.2 | +2.0 | +4.2 | +6.2 |
| Low-M (E1) | 222 | +8.6 | +8.6 | +0.5 | +3.2 | +7.7 | +7.2 |
| High-M | 278 | +3.6 | +4.2 | -0.8 | +1.1 | +1.4 | +5.4 |
| M=0 (NA as 0) | 222 | +8.6 | +8.6 | +0.5 | +3.2 | +7.7 | +7.2 |
| M=1 (NA as 0) | 258 | +2.7 | +2.9 | -0.4 | +0.4 | +1.2 | +3.1 |
| M=2 (NA as 0) | 20 | +15.0 | +21.1 | -5.3 | +10.0 | +5.0 | +35.0 |
| M=3 (NA as 0) | 0 | — | — | — | — | — | — |
| M=0 (P1-eligible) | 111 | +4.5 | +3.0 | +2.0 | +2.7 | +4.5 | +7.2 |
| M=1 (P1-eligible) | 235 | +3.0 | +3.2 | -0.5 | -0.4 | +0.9 | +3.4 |
| M=2 (P1-eligible) | 20 | +15.0 | +21.1 | -5.3 | +10.0 | +5.0 | +35.0 |
| M=3 (P1-eligible) | 0 | — | — | — | — | — | — |
| S1: Low-M ∩ P1-eligible | 111 | +4.5 | +3.0 | +2.0 | +2.7 | +4.5 | +7.2 |
| p1 negative | 116 | +4.3 | +2.8 | +1.9 | +1.7 | +4.3 | +6.9 |
| p1 positive | 251 | +4.0 | +4.7 | -0.8 | +0.8 | +1.2 | +6.0 |
| p2_apply negative | 473 | +5.9 | +5.8 | +0.2 | +1.5 | +4.2 | +6.1 |
| p2_apply positive | 27 | +3.7 | +11.5 | -7.7 | +11.1 | +3.7 | +7.4 |
| p3 negative | 479 | +5.6 | +6.2 | -0.4 | +2.1 | +4.2 | +5.4 |
| p3 positive | 20 | +10.0 | +5.0 | +5.0 | +0.0 | +5.0 | +25.0 |
| B→C full | 80 | +30.0 | +30.4 | +0.0 | +20.0 | +31.2 | +32.5 |
| E2: Low-M ∩ B→C | 33 | +39.4 | +39.4 | +0.0 | +33.3 | +42.4 | +42.4 |
| High-M ∩ B→C | 47 | +23.4 | +23.9 | +0.0 | +10.6 | +23.4 | +25.5 |

- OFF−ON: non-positive strata (stratum, Δ, n): none
- OFF−T: non-positive strata (stratum, Δ, n): none
- T−ON: non-positive strata (stratum, Δ, n): [('High-M', -0.8, 263), ('M=1 (NA as 0)', -0.4, 244), ('M=2 (NA as 0)', -5.3, 19), ('M=1 (P1-eligible)', -0.5, 221), ('M=2 (P1-eligible)', -5.3, 19), ('p1 positive', -0.8, 236), ('p2_apply positive', -7.7, 26), ('p3 negative', -0.4, 452), ('B→C full', 0.0, 79), ('E2: Low-M ∩ B→C', 0.0, 33), ('High-M ∩ B→C', 0.0, 46)]
- k4: non-positive strata (stratum, Δ, n): [('M=1 (P1-eligible)', -0.4, 235), ('p3 positive', 0.0, 20)]
- k12: non-positive strata (stratum, Δ, n): none
- k40: non-positive strata (stratum, Δ, n): none

