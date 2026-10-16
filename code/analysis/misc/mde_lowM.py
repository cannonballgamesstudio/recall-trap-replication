import json, sys
sys.path.insert(0, r"code/analysis/reanalysis")
import t4_mde as T

VER = "work/p5/"
M = json.load(open("data/memorization-branchB/M_table_gpt56sol.json"))
low = {k for k, v in M.items() if v["lowM"] == 1}
print("lowM n", len(low))
arms = {"hl": ("local_gpt56sol_dedupON.local_gpt56sol_dedupON.json", "local_gpt56sol_dedupOFF.local_gpt56sol_dedupOFF.json"),
        "lr": ("local_gptsol_logrep_dedupON.gptsol_logrep_dedupON.json", "local_gptsol_logrep_dedupOFF.gptsol_logrep_dedupOFF.json")}
B = C = P = 0
for k, (on, off) in arms.items():
    a = json.load(open(VER + on)); b = json.load(open(VER + off))
    ron, son = set(a["resolved_ids"]), set(a["submitted_ids"])
    roff, soff = set(b["resolved_ids"]), set(b["submitted_ids"])
    ids = [i for i in low if i in son and i in soff]
    bb = sum(1 for i in ids if i in roff and i not in ron)
    cc = sum(1 for i in ids if i in ron and i not in roff)
    print(k, len(ids), "OFF-only", bb, "ON-only", cc)
    B += bb; C += cc; P += len(ids)
print("pooled pairs", P, "b", B, "c", C, "delta", (B - C) / P)


def mdes(n, b, c):
    D = b + c; psi = D / n; pc = c / n
    mC = T.mde_search(lambda x: T.power_cond(D, 0.5 + x / (2 * psi)) if x <= psi else 0.0, psi)
    pwA = T.power_uncond(n, (psi + mC) / 2, (psi - mC) / 2) if mC else None
    mA = T.mde_search(lambda x: T.power_uncond(n, (psi + x) / 2, (psi - x) / 2) if x <= psi else 0.0, psi)
    mB = T.mde_search(lambda x: T.power_uncond(n, pc + x, pc), 0.6)
    return dict(n=n, b=b, c=c, psi=psi, C=mC and 100 * mC, pwA_atC=pwA, A=mA and 100 * mA, B=mB and 100 * mB)

# trim rows: b = T-only (first arm), c = ON-only
print("Qwen T-ON", mdes(473, 7, 8))
print("gpt  T-ON", mdes(473, 46, 39))
# E1 at n=47 instances, using the observed Low-M discordance rate (pooled over both draws, per instance)
n = 47
b_rate, c_rate = B / P, C / P
bE = round(b_rate * n); cE = round(c_rate * n)
print("E1 per-instance scaled b,c", b_rate * n, c_rate * n)
print("E1", mdes(n, bE, cE))
# also: pooled pair count as n (upper bound on information)
print("E1 pooled-pairs", mdes(P, B, C))
