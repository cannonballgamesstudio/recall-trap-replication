## Task 3 — Holm over the confirmatory family (2 tests), unrounded

Pre-registered test = exact two-sided McNemar. Wild p is Monte-Carlo (B=9,999): MC SE = √(p(1−p)/B) shown. Holm step-down: p(1)·2, max(p(1)·2, p(2)·1).

| test | n | Δ | b/c | method | raw p | Holm-adjusted p | survives at 0.05 |
|---|---|---|---|---|---|---|---|
| Qwen3.6-27B K=12 | 499 | +3.61 | 33/15 | exact McNemar (pre-registered) | 0.013283 | 0.020127 | yes |
| gpt-5.6-sol logged re-run | 500 | +5.40 | 65/38 | exact McNemar (pre-registered) | 0.010063 | 0.020127 | yes |
| Qwen3.6-27B K=12 | 499 | +3.61 | 33/15 | wild cluster (Webb) | 0.029103 (MC SE 0.0017) | 0.037404 | yes |
| gpt-5.6-sol logged re-run | 500 | +5.40 | 65/38 | wild cluster (Webb) | 0.018702 (MC SE 0.0014) | 0.037404 | yes |
| Qwen3.6-27B K=12 | 499 | +3.61 | 33/15 | CR2 (BM df) | 0.048618 | 0.078795 | NO |
| gpt-5.6-sol logged re-run | 500 | +5.40 | 65/38 | CR2 (BM df) | 0.039398 | 0.078795 | NO |
| Qwen3.6-27B K=12 | 499 | +3.61 | 33/15 | repo sign-flip (exact) | 0.078125 | 0.078125 | NO |
| gpt-5.6-sol logged re-run | 500 | +5.40 | 65/38 | repo sign-flip (exact) | 0.005859 | 0.011719 | yes |

## Task 4 — ITT: never-submitted scored as failures on the full 500

PP = per-protocol (pairwise exclusion of never-submitted, the paper's estimand). ITT = all 500, never-submitted = unresolved. Worst case = ITT but every ON never-submitted instance counted as resolved (OFF never-submitted stay failed): the adversarial bound against OFF−ON > 0.

| arm | never-sub ON/OFF | estimand | n | ON | OFF | Δ | b/c | McNemar p | wild 95% CI | wild p | CR2 p | flip p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3.6-27B K=4 | 18/17 (both 1) | PP | 466 | 43 | 66 | +4.94 | 30/7 | 1.9e-04 | [+0.4, +7.7] | 0.0320 | 0.0867 | 0.0625 |
| Qwen3.6-27B K=4 | 18/17 (both 1) | ITT | 500 | 43 | 67 | +4.80 | 31/7 | 1.2e-04 | [+0.6, +7.2] | 0.0315 | 0.0650 | 0.0625 |
| Qwen3.6-27B K=4 | 18/17 (both 1) | worst case | 500 | 61 | 67 | +1.20 | 30/24 | 0.497 | [-3.6, +2.9] | 0.569 | 0.443 | 0.703 |
| Qwen3.6-27B K=12 | 0/1 (both 0) | PP | 499 | 46 | 64 | +3.61 | 33/15 | 0.0133 | [+0.5, +5.2] | 0.0291 | 0.0486 | 0.0781 |
| Qwen3.6-27B K=12 | 0/1 (both 0) | ITT | 500 | 46 | 64 | +3.60 | 33/15 | 0.0133 | [+0.5, +5.2] | 0.0291 | 0.0491 | 0.0781 |
| Qwen3.6-27B K=12 | 0/1 (both 0) | worst case | 500 | 46 | 64 | +3.60 | 33/15 | 0.0133 | [+0.5, +5.2] | 0.0291 | 0.0491 | 0.0781 |
| Qwen3.6-27B K=40 | 32/12 (both 1) | PP | 457 | 43 | 89 | +10.07 | 53/7 | 7.7e-10 | [+4.0, +12.5] | 0.0107 | 0.0106 | 0.0156 |
| Qwen3.6-27B K=40 | 32/12 (both 1) | ITT | 500 | 44 | 90 | +9.20 | 54/8 | 1.7e-09 | [+3.6, +11.6] | 0.0125 | 0.0120 | 0.0156 |
| Qwen3.6-27B K=40 | 32/12 (both 1) | worst case | 500 | 76 | 90 | +2.80 | 53/39 | 0.175 | [-4.6, +6.3] | 0.567 | 0.373 | 0.635 |
| DeepSeek-v4-pro | 1/0 (both 0) | PP | 499 | 65 | 96 | +6.21 | 53/22 | 4.5e-04 | [+3.3, +11.6] | 0.0076 | 0.0101 | 0.0156 |
| DeepSeek-v4-pro | 1/0 (both 0) | ITT | 500 | 65 | 96 | +6.20 | 53/22 | 4.5e-04 | [+3.3, +11.6] | 0.0076 | 0.0103 | 0.0156 |
| DeepSeek-v4-pro | 1/0 (both 0) | worst case | 500 | 66 | 96 | +6.00 | 53/23 | 7.6e-04 | [+3.2, +11.7] | 0.0081 | 0.0128 | 0.0156 |
| dense control (gpt) | 3/3 (both 0) | PP | 494 | 205 | 233 | +5.67 | 69/41 | 0.0097 | [-2.2, +10.5] | 0.133 | 0.0502 | 0.219 |
| dense control (gpt) | 3/3 (both 0) | ITT | 500 | 206 | 233 | +5.40 | 69/42 | 0.0132 | [-2.2, +10.3] | 0.165 | 0.0605 | 0.250 |
| dense control (gpt) | 3/3 (both 0) | worst case | 500 | 209 | 233 | +4.80 | 69/45 | 0.0308 | [-3.0, +9.2] | 0.204 | 0.0812 | 0.297 |

