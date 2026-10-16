import json, glob, random, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "data/polybench"
def load_ne(fn):
    s = set()
    for l in open(fn, encoding="utf-8"):
        if l.strip():
            r = json.loads(l)
            if (r.get("model_patch") or "").strip(): s.add(r["instance_id"])
    return s
def load_g(d):
    g = {}
    for f in glob.glob(d + "/*_result.json"):
        x = json.load(open(f)); g[x["instance_id"]] = bool(x.get("resolved"))
    return g
def ids(fn): return [l.strip() for l in open(fn, encoding="utf-8") if l.strip()]

a_neON, a_neOFF = load_ne(R+"/preds_local_pb_a3b_dedupON.jsonl"), load_ne(R+"/preds_local_pb_a3b_dedupOFF.jsonl")
a_gON, a_gOFF = load_g("data/polybench/grading/pb_ab_ON"), load_g("data/polybench/grading/pb_ab_OFF")
g_neON, g_neOFF = load_ne(R+"/preds_local_pb_gpt_dedupON.jsonl"), load_ne(R+"/preds_local_pb_gpt_dedupOFF.jsonl")
g_gON, g_gOFF = load_g("data/polybench/grading/pb_gpt_ab_ON"), load_g("data/polybench/grading/pb_gpt_ab_OFF")
killed = set(ids(R+"/off_killed_ids.txt"))
S_a = ids(R+"/survivor_ids.txt")
S_g = [i for i in ids(R+"/survivor_ids_gpt.txt") if i not in killed]

# build (instance -> list of (on,off)) pooled rows, clustered by instance
rows = {}  # instance_id -> list of (on_res, off_res)
for i in S_a:
    on = (i in a_neON) and a_gON.get(i, False); off = (i in a_neOFF) and a_gOFF.get(i, False)
    rows.setdefault(i, []).append((on, off))
for i in S_g:
    on = (i in g_neON) and g_gON.get(i, False); off = (i in g_neOFF) and g_gOFF.get(i, False)
    rows.setdefault(i, []).append((on, off))

insts = list(rows.keys())
def delta(sample_insts):
    on = off = n = 0
    for i in sample_insts:
        for (o, f) in rows[i]:
            on += o; off += f; n += 1
    return (off - on) / n * 100 if n else 0.0

point = delta(insts)
rng = random.Random(20260808)
B = 10000
deltas = []
for _ in range(B):
    samp = [insts[rng.randrange(len(insts))] for _ in range(len(insts))]
    deltas.append(delta(samp))
deltas.sort()
lo, hi = deltas[int(0.025*B)], deltas[int(0.975*B)]
p_le0 = sum(1 for d in deltas if d <= 0) / B
print(f"pooled point Δ = {point:+.2f}pp over {sum(len(v) for v in rows.values())} pairs in {len(insts)} instance-clusters")
print(f"instance-clustered bootstrap (B={B}): 95% CI [{lo:+.2f}, {hi:+.2f}]pp, one-sided P(Δ<=0) = {p_le0:.4f}")
print(f"instances contributing 2 model-pairs: {sum(1 for v in rows.values() if len(v)==2)}; 1 pair: {sum(1 for v in rows.values() if len(v)==1)}")