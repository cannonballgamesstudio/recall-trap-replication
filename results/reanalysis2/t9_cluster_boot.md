## Task 9 — Repository-cluster bootstrap: Branch A and SWE-PolyBench

Branch A: 105 gold-gated instances in 77 repositories; gpt-5.6-sol 2 seeds pooled; error_instances in all 6 Branch A reports: 0. Instance bootstrap reproduces the published A1–A6 (seed 20261014); repo-cluster bootstrap resamples repositories (B=10,000).

| estimand | n | clusters | Δ (pp) | disc b/c | instance boot 95% CI; P(Δ*>0) | repo-cluster boot 80% CI | repo-cluster 95% CI | repo P(Δ*>0) | label (instance → cluster, 0.80 rule) |
|---|---|---|---|---|---|---|---|---|---|
| A1 gpt all | 105 | 77 | +2.38 | 11/6 | [-1.9, +6.7]; 0.843 | [-0.5, +5.4] | [-1.9, +7.1] | 0.827 | SIGN-CONSISTENT → SIGN-CONSISTENT |
| A2 gpt ≥2026-04-01 | 49 | 40 | +0.00 | 2/2 | [-4.1, +4.1]; 0.400 | [-2.4, +2.7] | [-4.2, +4.1] | 0.400 | UNINFORMATIVE → UNINFORMATIVE |
| A6 gpt single gold file | 39 | 32 | +0.00 | 5/5 | [-9.0, +9.0]; 0.450 | [-5.4, +5.7] | [-8.3, +9.4] | 0.436 | UNINFORMATIVE → UNINFORMATIVE |
| A3 gpt B→C | 9 | 9 | +5.56 | 1/0 | [+0.0, +16.7]; 0.654 | [+0.0, +11.1] | [+0.0, +16.7] | 0.654 | UNINFORMATIVE → UNINFORMATIVE |
| A5 Qwen3-Coder all | 105 | 77 | +0.95 | 2/1 | [-1.9, +4.8]; 0.613 | [-1.0, +2.9] | [-2.0, +4.3] | 0.608 | UNINFORMATIVE → UNINFORMATIVE |

SWE-PolyBench: A3B 280 + gpt 337 = 617 model×instance pairs. Instance bootstrap = published analysis (seed 20260808); repo-cluster bootstrap resamples repositories (B=10,000, seed 20261014). Exact repo sign-flip and WCR wild (Webb) on per-row d clustered by repository added for comparison (pairs of the same instance share a cluster).

| cell | n pairs | repos | Δ (pp) | b/c | instance boot 95% CI; P(Δ*≤0) | repo-cluster 95% CI | repo P(Δ*≤0) | wild 95% CI; p | flip p |
|---|---|---|---|---|---|---|---|---|---|
| pooled (A3B + gpt) | 617 | 19 | +2.59 | 39/23 | [+0.00, +5.37]; 0.0296 | [-1.19, +6.62] | 0.1003 | [-1.6, +7.1]; 0.215 | 0.254 |
| A3B | 280 | 17 | +2.86 | 11/3 | [+0.36, +5.36]; 0.0184 | [-0.36, +6.84] | 0.0536 | [-0.8, +6.9]; 0.132 | 0.203 |
| gpt-5.6-sol | 337 | 19 | +2.37 | 28/20 | [-1.48, +6.53]; 0.1426 | [-3.86, +8.36] | 0.2400 | [-4.6, +9.5]; 0.473 | 0.529 |

Note: the instance-bootstrap row is a re-implementation (resampling order differs), so it reproduces the published [0.00, +5.31], P(Δ*≤0)=0.0309 only to Monte-Carlo error ([+0.00, +5.37], 0.0296).
