#!/bin/sh
# Recompute every derived table in results/ from the released data (no model calls, no Docker).
# Run from the package root. Requires Python 3.10+ with scipy (for contamination.py only).
set -e
python code/analysis/core/build_inclusion_table.py
python code/analysis/core/paired_contrasts.py      > /dev/null
python code/analysis/core/coverage_anchor.py       > /dev/null
python code/analysis/core/funnel.py                > /dev/null
python code/analysis/core/contamination.py         > /dev/null
python code/analysis/core/polybench_verdict.py     > results/core/GENERALITY-FINAL-VERDICT.rerun.txt
python code/analysis/core/polybench_clustered_sens.py >> results/core/GENERALITY-FINAL-VERDICT.rerun.txt
echo "done: see results/core/*.md"
