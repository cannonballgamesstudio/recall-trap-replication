#!/bin/sh
# reanalysis2: design-authority FREE analyses. No model calls, no Docker, no GPU. Read-only over the released data.
# Python 3.10+ with numpy, scipy, pandas, statsmodels. Run code/prepare_data.py once first.
# verified_meta.json is exported once from the Verified parquet with a pyarrow-capable Python (export_verified_meta.py).
set -e
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
PY=${PY:-python}
# verified_meta.json is shipped in data/swe-verified/inputs/ (export_verified_meta.py regenerates it).
for s in t0_audit t1_decomp t2_tost t3_t4_holm_itt t5_loo t6_t7_concordant t8_e5_difficulty t9_cluster_boot t10_numeric t11_strata; do
  $PY $s.py > /dev/null
done
echo done
