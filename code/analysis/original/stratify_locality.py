#!/usr/bin/env python3
"""Multi-hunk / multi-file stratification of the single-shot dedup A/B (methodology reviewer's #3, free).
Tests whether depth>breadth (the recall trap) holds or reverses as the gold fix spans
more files / more hunks. Reuses EXISTING graded predictions; no new runs."""
import json, sys
from pathlib import Path
from scipy.stats import binomtest
P = Path(r"data/swe-verified")
sys.path.insert(0, r"code/eval")
from oracle_pack import parse_gold_hunks

gold = json.loads((P/"gold_patches.json").read_text(encoding="utf-8"))
def complexity(iid):
    hunks = parse_gold_hunks(gold.get(iid, ""))
    files = {h[0] for h in hunks}
    return len(files), len(hunks)   # (n_gold_files, n_hunks)

def load(f):
    d = json.loads((P/f).read_text())
    res = set(d["resolved_ids"])
    att = set(d["resolved_ids"])|set(d["unresolved_ids"])|set(d["empty_patch_ids"])|set(d.get("error_ids",[]))
    return res, att

ARMS = {
 "gpt-fusion": ("local_gpt56sol_dedupON.local_gpt56sol_dedupON.json","local_gpt56sol_dedupOFF.local_gpt56sol_dedupOFF.json"),
 "cc1-dense":  ("local_gptsol_dense_dedupON.cc1_gptdense_ON_rg.json","local_gptsol_dense_dedupOFF.cc1_gptdense_OFF_rg.json"),
 "deepseek":   ("local_dsv4_dedupON.dsv4_ON_rg.json","local_dsv4_dedupOFF.dsv4_OFF_rg.json"),
 "qwen3-30b":  ("local_qwen3coder30b_dedupON.qwen30b_ON_rg.json","local_qwen3coder30b_dedupOFF.qwen30b_OFF_rg.json"),
}

def mcnemar(pairs):
    # pairs: list of (on_resolved, off_resolved) bools
    b = sum(1 for on,off in pairs if off and not on)  # OFF wins (depth)
    c = sum(1 for on,off in pairs if on and not off)  # ON wins (breadth)
    n = len(pairs)
    ron = sum(1 for on,off in pairs if on); roff = sum(1 for on,off in pairs if off)
    p = binomtest(min(b,c),b+c,0.5).pvalue if b+c else 1.0
    d = (roff-ron)/n*100 if n else 0
    return n, ron, roff, d, b, c, p

# distribution
allc = {i: complexity(i) for i in gold}
nf = [v[0] for v in allc.values() if v[0]]
nh = [v[1] for v in allc.values() if v[1]]
import statistics as st
print(f"gold complexity over {len(nf)} instances: files median={st.median(nf)} mean={st.mean(nf):.2f} "
      f"| 1-file={sum(1 for x in nf if x==1)} 2+={sum(1 for x in nf if x>=2)} 3+={sum(1 for x in nf if x>=3)}")
print(f"                                    hunks median={st.median(nh)} mean={st.mean(nh):.2f} "
      f"| 1-hunk={sum(1 for x in nh if x==1)} 2+={sum(1 for x in nh if x>=2)} 3+={sum(1 for x in nh if x>=3)}")

def stratify(strata_fn, label):
    print(f"\n{'='*86}\nSTRATIFY BY {label}\n{'='*86}")
    pooled = {}  # stratum -> list of pairs across all arms
    for arm,(onf,offf) in ARMS.items():
        ron,aon = load(onf); roff,aoff = load(offf)
        both = aon & aoff
        rows = {}
        for iid in both:
            if iid not in allc or not allc[iid][0]: continue
            s = strata_fn(allc[iid])
            rows.setdefault(s, []).append((iid in ron, iid in roff))
            pooled.setdefault(s, []).append((iid in ron, iid in roff))
        parts = []
        for s in sorted(rows):
            n,ron_,roff_,d,b,c,p = mcnemar(rows[s])
            parts.append(f"{s}: n={n} ON{ron_}/OFF{roff_} d={d:+.1f} disc{b}/{c} p={p:.2f}")
        print(f"  {arm:11s} " + " | ".join(parts))
    print("  " + "-"*84)
    for s in sorted(pooled):
        n,ron_,roff_,d,b,c,p = mcnemar(pooled[s])
        print(f"  POOLED(4 arms) {s}: n={n} ON{ron_}/OFF{roff_} d={d:+.1f}pp disc(OFF/ON){b}/{c} McNemar p={p:.3f}")

stratify(lambda c: "1file" if c[0]==1 else "2+file", "GOLD FILE COUNT (1 vs 2+)")
stratify(lambda c: "1hunk" if c[1]==1 else ("2-3hunk" if c[1]<=3 else "4+hunk"), "GOLD HUNK COUNT (1 / 2-3 / 4+)")
