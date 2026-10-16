"""Export instance_id, repo, difficulty, gold patch from the SWE-bench Verified parquet (system Python has pyarrow)."""
import json
import pandas as pd
import os
PQ = os.environ.get("HF_HOME", "<HF_HOME>") + "/hub/datasets--princeton-nlp--SWE-bench_Verified/snapshots/c104f840cc67f8b6eec6f759ebc8b2693d585d4a/data/test-00000-of-00001.parquet"
d = pd.read_parquet(PQ)
out = {r.instance_id: {"repo": r.repo, "difficulty": r.difficulty, "patch": r.patch} for r in d.itertuples()}
json.dump(out, open("data/swe-verified/inputs/verified_meta.json", "w", encoding="utf-8"))
print(len(out))
