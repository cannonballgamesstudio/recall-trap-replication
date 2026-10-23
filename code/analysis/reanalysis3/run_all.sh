#!/bin/sh
# reanalysis3: POST-HOC robustness analyses requested by an internal pre-submission blind statistical review.
# CPU only: no model calls, no Docker, no GPU. Writes only into results/reanalysis3/.
# Run code/prepare_data.py once first (builds work/p5). Difficulty labels: data/swe-verified/inputs/verified_meta.json.
# Python 3.10+ with numpy, scipy, pandas, statsmodels.
set -e
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
PY=${PY:-python}
for s in s1_size s2_rq1_registered s3_equiv s4_share s5_practitioner s6_e5 s7_replication; do
  $PY $s.py > /dev/null
done
# verification re-runs of the size check (second outer seed; paper's B = 9,999 inner)
RA3_SIZE_SEED=7 $PY s1_size.py > /dev/null
RA3_SIZE_SEED=11 RA3_BSIM=9999 $PY s1_size.py > /dev/null
echo done
