# Contamination-dosage stratification (recomputed; approximate star snapshot)

- P1_gpt_fusion: Spearman rho(stars, per-repo Delta) = +0.10; high-popularity Delta +9.2pp (n=381, p=8.22e-05); low-popularity Delta +2.5pp (n=119, p=0.72); high-low +6.7pp
- P2_deepseek_fusion: Spearman rho(stars, per-repo Delta) = -0.32; high-popularity Delta +5.0pp (n=380, p=0.0163); low-popularity Delta +10.1pp (n=119, p=0.00754); high-low -5.1pp
- P3_qwen36_fusion_K12: Spearman rho(stars, per-repo Delta) = -0.18; high-popularity Delta +3.7pp (n=380, p=0.0385); low-popularity Delta +3.4pp (n=119, p=0.289); high-low +0.3pp
- P4_DENSE1_gpt_dense: Spearman rho(stars, per-repo Delta) = +0.62; high-popularity Delta +7.7pp (n=377, p=0.00279); low-popularity Delta -0.9pp (n=117, p=1); high-low +8.5pp

Mean across arms: rho = +0.05; high-minus-low = +2.6pp

Median split at 13.0k stars. Per-repository deltas in contamination_per_repo.csv.
