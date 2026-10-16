#!/usr/bin/env python3
"""Build gold-smoke batch CSVs for the 303 non-empty-either-arm union.

Reads the union id list, pulls the matching PB500 rows from HF, writes small
batch CSVs (default 10 instances each) that SWE-PolyBench's run_evaluation.py
consumes via --dataset-path. Small batches give the driver a free-space
checkpoint between each (D: has ~1.97TB, run is ~1.7TB — real but not lavish
headroom, and vhdx growth is jagged).
"""
import json, sys, os
from datasets import load_dataset
import pandas as pd

ROOT = "<EVAL_ROOT>/pb_gen"
BATCH = 10
ids = [l.strip() for l in open(f"{ROOT}/gold_smoke_ids.txt") if l.strip()]
idset = set(ids)
ds = load_dataset("AmazonScience/SWE-PolyBench_500", split="test").to_pandas()
sub = ds[ds["instance_id"].isin(idset)].copy()
assert len(sub) == len(idset), f"expected {len(idset)} rows, got {len(sub)} — id mismatch"
# stable, language-interleaved order so each batch mixes cheap (py/java) and
# expensive (js/ts) images -> smoother disk growth, no all-9.5GB-TS batch.
sub["__lang"] = sub["language"]
sub = sub.sort_values(["instance_id"]).reset_index(drop=True)
order = []
bylang = {L: list(sub[sub.language == L].instance_id) for L in sub.language.unique()}
while any(bylang.values()):
    for L in list(bylang):
        if bylang[L]:
            order.append(bylang[L].pop(0))
sub = sub.set_index("instance_id").loc[order].reset_index()

os.makedirs(f"{ROOT}/gold_batches", exist_ok=True)
nb = 0
for i in range(0, len(sub), BATCH):
    chunk = sub.iloc[i:i+BATCH].drop(columns=["__lang"])
    chunk.to_csv(f"{ROOT}/gold_batches/batch_{nb:02d}.csv", index=False)
    nb += 1
print(f"wrote {nb} batches ({len(sub)} instances, {BATCH}/batch) to {ROOT}/gold_batches/")
print("per-language:", sub.language.value_counts().to_dict())
