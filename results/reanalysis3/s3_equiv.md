## Analysis 3 — Equivalence under repository-clustered 90% CIs, m*, gpt trim diagnostics (POST HOC)

TOST (α = 0.05 per side) passes at margin m iff the 90% CI lies inside (−m, +m); m* = max(|lo|, |hi|) of the 90% CI is the smallest margin that passes. The ±3pp margin was chosen post hoc. Replication = seed-averaged d over 3 seeds; primary = sphinx-8475 Class-P cells scored unresolved (n = 478). Instance CI for the replication = the registered percentile instance bootstrap (b1b3_analyze.py, B = 10,000, seed 20261015), reproduced exactly.

| contrast | n | Δ (pp) | b/c | instance 90% CI | wild 90% CI | CR2-BM 90% CI (df) | registered pct-cluster 90% CI | ±3pp passes (inst / wild / CR2 / pct) | **m* (inst / wild / CR2 / pct)** |
|---|---|---|---|---|---|---|---|---|---|
| replication T−ON (trim), scored primary, n=478 | 478 | +0.49 | — | [-0.63, +1.60] | [-0.21, +1.34] | [-0.22, +1.20] (3.36) | [+0.00, +1.28] | PASS / PASS / PASS / PASS | 1.60 / 1.34 / 1.20 / 1.28 |
| replication TM−T (tokens), scored primary, n=478 | 478 | +0.14 | — | [-0.91, +1.19] | [-1.26, +0.94] | [-0.83, +1.11] (3.36) | [-1.04, +0.67] | PASS / PASS / PASS / PASS | 1.19 / 1.26 / 1.11 / 1.04 |
| replication T−ON (trim), exclude (old primary), n=477 | 477 | +0.49 | — | [-0.70, +1.68] | [-0.21, +1.34] | [-0.22, +1.20] (3.35) | [+0.00, +1.28] | PASS / PASS / PASS / PASS | 1.68 / 1.34 / 1.20 / 1.28 |
| replication TM−T (tokens), exclude (old primary), n=477 | 477 | +0.14 | — | [-0.91, +1.19] | [-1.26, +0.94] | [-0.83, +1.11] (3.35) | [-1.04, +0.68] | PASS / PASS / PASS / PASS | 1.19 / 1.26 / 1.11 / 1.04 |
| Qwen3-Coder-30B headline T−ON, n=473 | 473 | -0.21 | 7/8 | [-1.56, +1.14] | [-0.91, +0.89] | [-1.01, +0.59] (3.36) | [-0.77, +0.58] | PASS / PASS / PASS / PASS | 1.56 / 0.91 / 1.01 / 0.77 |
| gpt T−ON vs logged re-run ON, n=473 | 473 | +0.00 | 41/41 | [-3.15, +3.15] | [-3.05, +5.85] | [-5.76, +5.76] (3.36) | [-2.31, +4.92] | fail / fail / fail / fail | 3.15 / 5.85 / 5.76 / 4.92 |
| gpt T−ON vs discovery ON (registered TB §9 reference), n=473 | 473 | +1.48 | 46/39 | [-1.73, +4.69] | [-0.52, +4.38] | [-1.05, +4.01] (3.36) | [-0.46, +4.14] | fail / fail / fail / fail | 4.69 / 4.38 / 4.01 / 4.14 |

For the replication rows the Wald instance 90% CI is also in the JSON (`ci90['instance Wald']`).

Check against results_scored.json (registered instance bootstrap reproduced):

| contrast | Δ mine / file | 90% CI mine | 90% CI file | 95% CI mine | 95% CI file |
|---|---|---|---|---|---|
| T-ON | +0.4881 / +0.4881 | [-0.6276, +1.6039] | [-0.6276, +1.6039] | [-0.9066, +1.8828] | [-0.9066, +1.8828] |
| TM-T | +0.1395 / +0.1395 | [-0.9066, +1.1855] | [-0.9066, +1.1855] | [-1.0460, +1.3947] | [-1.0460, +1.3947] |

### gpt trim term (T−ON, 473 instances): django vs non-django, and both-non-empty pairs

| reference | full Δ | django: n; Δ; b/c; contribution to full Δ | non-django: n; Δ; b/c; contribution | both non-empty: n; Δ; b/c; McNemar p | empties T / ON |
|---|---|---|---|---|---|
| re-run ON | +0.00 | 217; -3.69; 16/24; -1.69 | 256; +3.12; 25/17; +1.69 | 368; +1.63; 30/24; 0.497 | 78 / 71 |
| discovery ON | +1.48 | 217; +0.92; 20/18; +0.42 | 256; +1.95; 26/21; +1.06 | 373; +4.02; 34/19; 0.0534 | 78 / 66 |
| Qwen3-Coder ON (for comparison) | -0.21 | 217; -0.46; 6/7; -0.21 | 256; +0.00; 1/1; +0.00 | 194; +0.52; 4/3; 1.000 | 225 / 206 |

