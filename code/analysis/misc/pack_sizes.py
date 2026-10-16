"""Pack-size descriptives for the trimmed-breadth section and the token-confound note:
mean served slots (chunks), characters, and o200k tokens (if tiktoken is installed) for dedup-ON,
dedup-OFF and Arm T on the 473 instances that pass the subset gate.

Run from the package root after `python code/prepare_data.py`:
    python code/analysis/misc/pack_sizes.py
"""
import json
from pathlib import Path

P5 = Path("work/p5")
viol = {l.strip() for l in open("preregistrations/TRIMMED-BREADTH-VIOLATORS.txt", encoding="utf-8")
        if l.strip() and not l.startswith("#")}
lp = json.loads((P5 / "local_packs.json").read_text(encoding="utf-8"))
T = json.loads((P5 / "packfile_T_qwen30b.json").read_text(encoding="utf-8"))
try:
    import tiktoken
    enc = tiktoken.get_encoding("o200k_base")
except Exception:  # optional
    enc = None

ids = sorted(i for i in lp if i in T and i not in viol)
arms = {"ON": lambda i: lp[i]["dedupON"], "OFF": lambda i: lp[i]["dedupOFF"], "T": lambda i: T[i]["T"]}
print(f"n = {len(ids)}")
for name, get in arms.items():
    slots = [get(i)["n_hits"] for i in ids]
    chars = [len(get(i)["pack"]) for i in ids]
    line = f"{name:4s} slots {sum(slots) / len(ids):5.2f}  chars {sum(chars) / len(ids):8.1f}"
    if enc:
        toks = [len(enc.encode(get(i)["pack"])) for i in ids]
        line += f"  o200k tokens {sum(toks) / len(ids):8.1f}"
    print(line)
