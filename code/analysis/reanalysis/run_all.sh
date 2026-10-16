#!/bin/sh
# $0 reanalysis: no model calls, no Docker. Reads ../replication-package read-only.
# venv: python -m venv .venv && .venv/Scripts/python -m pip install numpy scipy statsmodels pandas
set -e
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
PY=${PY:-python}
$PY t1_clustered.py > /dev/null
$PY t2_dose.py > /dev/null
$PY t3_locality.py > /dev/null
$PY t4_mde.py > /dev/null
$PY t5_t6.py > /dev/null
R=../../../results/reanalysis; cat $R/t1_clustered.md $R/t2_dose.md $R/t3_locality.md $R/t4_mde.md $R/t5_t6.md > $R/RESULTS.md
echo done
