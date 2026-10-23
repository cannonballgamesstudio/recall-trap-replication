## Analysis 4 — CI for the depth share (OFF−T)/(OFF−ON) (POST HOC)

Bootstraps resample the joint per-instance outcomes so numerator and denominator move together (B = 10,000 each). The ratio is undefined when G* <= 0; percentile CIs are over the draws with G* > 0 and the share of excluded draws is reported (when it exceeds 2.5% the 95% interval is effectively unbounded on one side). P(share* >= 60%) counts draws with G* > 0 and depth* >= 0.6 G*. Fieller intervals are analytic cross-checks (instance covariance with z; CR1 repository covariance with t(11)).

| row | n | G (pp) | depth (pp) | trim (pp) | **share** | instance-paired boot 95% CI | P(G*≤0) inst | repo-cluster boot 95% CI | P(G*≤0) cluster | Fieller (inst.) | Fieller (CR1, t11) | P(share* ≥ 60%) inst / cluster |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| replication, 3 seeds, scored primary | 478 | +6.14 | +5.65 | +0.49 | **92.0%** | [67%, 117%] | 0.0000 | [52%, 103%] | 0.0000 | [68%, 117%] | [76%, 104%] | 0.993 / 0.963 |
| replication, 3 seeds, exclude (paper's 92%) | 477 | +6.15 | +5.66 | +0.49 | **92.0%** | [68%, 116%] | 0.0000 | [54%, 103%] | 0.0000 | [68%, 117%] | [76%, 104%] | 0.992 / 0.967 |
| Qwen3-Coder-30B headline arms, 1 draw (paper: 104%) | 473 | +5.92 | +6.13 | -0.21 | **103.6%** | [77%, 142%] | 0.0001 | [75%, 120%] | 0.0000 | [78%, 142%] | [86%, 114%] | 0.999 / 0.992 |
| gpt vs discovery draw (paper: 81%) | 473 | +7.82 | +6.34 | +1.48 | **81.1%** | [38%, 144%] | 0.0001 | [0%, 117%] | 0.0255 | [38%, 146%] | [30%, 118%] | 0.838 / 0.837 |
| gpt vs logged re-run (paper: 100%) | 473 | +6.13 | +6.13 | +0.00 | **100.0%** | [43%, 218%] | 0.0019 | [27%, 158%] | 0.0000 | [44%, 223%] | [42%, 242%] | 0.922 / 0.828 |

