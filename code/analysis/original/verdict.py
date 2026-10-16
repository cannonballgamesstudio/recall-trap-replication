import json, glob, sys
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
try:
    from scipy.stats import binomtest
    def exbin(k, n): return binomtest(k, n, 0.5, alternative="two-sided").pvalue if n > 0 else 1.0
except Exception:
    from math import comb
    def exbin(k, n):
        if n == 0: return 1.0
        return min(1.0, 2 * sum(comb(n, i) for i in range(0, k + 1)) / 2 ** n)

R = "data/polybench"
meta = {x["instance_id"]: x for x in json.load(open(R + "/instances_polybench.json", encoding="utf-8"))}
lang = lambda i: meta[i]["language"]

def load_nonempty(fn):
    s = set()
    for l in open(fn, encoding="utf-8"):
        if not l.strip(): continue
        r = json.loads(l)
        if (r.get("model_patch") or "").strip(): s.add(r["instance_id"])
    return s

def load_grades(d):
    g = {}
    for f in glob.glob(d + "/*_result.json"):
        x = json.load(open(f)); g[x["instance_id"]] = bool(x.get("resolved"))
    return g

def ids(fn): return [l.strip() for l in open(fn, encoding="utf-8") if l.strip()]

def mcnemar(S, rON, rOFF):
    b = c = ron = roff = 0
    for i in S:
        o = rON(i); f = rOFF(i)
        ron += o; roff += f
        if f and not o: b += 1
        elif o and not f: c += 1
    n = len(S); dpp = (roff - ron) / n * 100 if n else 0
    return dict(n=n, resON=ron, resOFF=roff, b=b, c=c, disc=b + c, dpp=dpp, p=exbin(min(b, c), b + c))

def report(tag, S, rON, rOFF, ratable=("Java", "JavaScript", "Python")):
    print(f"\n=== {tag}  (N={len(S)}) ===")
    bylang = defaultdict(list)
    for i in S: bylang[lang(i)].append(i)
    for lg in ["Java", "JavaScript", "Python", "TypeScript"]:
        if lg not in bylang: continue
        r = mcnemar(bylang[lg], rON, rOFF)
        note = "" if lg in ratable else "  [descriptive <80% producibility]"
        print(f"  {lg:11} n={r['n']:3}  ON={r['resON']:3} OFF={r['resOFF']:3}  d={r['dpp']:+6.2f}pp  b(OFF-only)={r['b']:2} c(ON-only)={r['c']:2} disc={r['disc']:2}  p={r['p']:.4f}{note}")
    r = mcnemar(S, rON, rOFF)
    print(f"  POOLED       n={r['n']:3}  ON={r['resON']:3} OFF={r['resOFF']:3}  d={r['dpp']:+6.2f}pp  b={r['b']:2} c={r['c']:2} disc={r['disc']:2}  p={r['p']:.4f}")
    return r

# ---------- A3B (sanity check vs memory: Python +10pp 8/0, pooled +2.86pp disc 11/3 p=0.0574) ----------
a3b_neON = load_nonempty(R + "/preds_local_pb_a3b_dedupON.jsonl")
a3b_neOFF = load_nonempty(R + "/preds_local_pb_a3b_dedupOFF.jsonl")
a3b_gON = load_grades("<eval_root>/pb_ab_ON"); a3b_gOFF = load_grades("<eval_root>/pb_ab_OFF")
a3b_rON = lambda i: (i in a3b_neON) and a3b_gON.get(i, False)
a3b_rOFF = lambda i: (i in a3b_neOFF) and a3b_gOFF.get(i, False)
S_a3b = ids(R + "/survivor_ids.txt")
ra3b = report("A3B (Qwen3-Coder-30B-A3B)  [SANITY vs memory]", S_a3b, a3b_rON, a3b_rOFF)

# ---------- gpt-5.6-sol ----------
gpt_neON = load_nonempty(R + "/preds_local_pb_gpt_dedupON.jsonl")
gpt_neOFF = load_nonempty(R + "/preds_local_pb_gpt_dedupOFF.jsonl")
gpt_gON = load_grades("<eval_root>/pb_gpt_ab_ON"); gpt_gOFF = load_grades("<eval_root>/pb_gpt_ab_OFF")
gpt_rON = lambda i: (i in gpt_neON) and gpt_gON.get(i, False)
gpt_rOFF = lambda i: (i in gpt_neOFF) and gpt_gOFF.get(i, False)
killed = set(ids(R + "/off_killed_ids.txt"))
S_gpt_full = ids(R + "/survivor_ids_gpt.txt")
S_gpt = [i for i in S_gpt_full if i not in killed]
print(f"\n[gpt survivor set: {len(S_gpt_full)} gold-valid − {len(killed)} infra-hang casualties excluded = {len(S_gpt)}]")
rgpt = report("gpt-5.6-sol (frontier)", S_gpt, gpt_rON, gpt_rOFF, ratable=("Java", "JavaScript", "Python"))

# ---------- TWO-MODEL POOLED G-2 (powered confirmatory) ----------
print("\n" + "=" * 70)
print("TWO-MODEL POOLED G-2  (A3B pairs + gpt pairs stacked as (model,instance) rows)")
B = C = ron = roff = 0
def acc(S, rON, rOFF):
    global B, C, ron, roff
    for i in S:
        o = rON(i); f = rOFF(i)
        ron += o; roff += f
        if f and not o: B += 1
        elif o and not f: C += 1
acc(S_a3b, a3b_rON, a3b_rOFF)
acc(S_gpt, gpt_rON, gpt_rOFF)
Ntot = len(S_a3b) + len(S_gpt)
dpp = (roff - ron) / Ntot * 100
p = exbin(min(B, C), B + C)
print(f"  Ntot={Ntot}  ON_res={ron} OFF_res={roff}  d={dpp:+.2f}pp  B(OFF-only)={B} C(ON-only)={C} disc={B+C}  exact 2-sided p={p:.4f}")
verdict = "G-3 SUPPORTED (recall-trap generalizes multilingually)" if (p < 0.05 and dpp > 0) else "G-4 HONEST BOUNDARY (direction {}, not significant)".format("+" if dpp > 0 else "-/0")
print(f"  VERDICT: {verdict}")

# ---------- SENSITIVITY: count the 5 killed as OFF-fail (not excluded) ----------
print("\n--- SENSITIVITY: killed-hung instances counted as OFF-fail (worst case for OFF) ---")
S_gpt_sens = list(S_gpt_full)
gpt_rOFF_sens = lambda i: False if i in killed else ((i in gpt_neOFF) and gpt_gOFF.get(i, False))
rs = mcnemar(S_gpt_sens, gpt_rON, gpt_rOFF_sens)
print(f"  gpt POOLED (sens) n={rs['n']} ON={rs['resON']} OFF={rs['resOFF']} d={rs['dpp']:+.2f}pp b={rs['b']} c={rs['c']} disc={rs['disc']} p={rs['p']:.4f}")
B2, C2, ron2, roff2 = 0, 0, 0, 0
def acc2(S, rON, rOFF):
    global B2, C2, ron2, roff2
    for i in S:
        o = rON(i); f = rOFF(i)
        ron2 += o; roff2 += f
        if f and not o: B2 += 1
        elif o and not f: C2 += 1
acc2(S_a3b, a3b_rON, a3b_rOFF)
acc2(S_gpt_sens, gpt_rON, gpt_rOFF_sens)
Nt2 = len(S_a3b) + len(S_gpt_sens)
print(f"  TWO-MODEL POOLED (sens) Ntot={Nt2} d={(roff2-ron2)/Nt2*100:+.2f}pp B={B2} C={C2} disc={B2+C2} p={exbin(min(B2,C2),B2+C2):.4f}")
