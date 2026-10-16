import json, glob, os, random, sys
sys.stdout.reconfigure(encoding="utf-8")
try:
    from scipy.stats import binomtest
    def exbin(k, n): return binomtest(k, n, 0.5, alternative="less").pvalue if n > 0 else 1.0   # one-sided
    def exbin2(k, n): return binomtest(k, n, 0.5, alternative="two-sided").pvalue if n > 0 else 1.0
except Exception:
    from math import comb
    def exbin2(k, n):
        if n == 0: return 1.0
        return min(1.0, 2 * sum(comb(n, i) for i in range(0, k + 1)) / 2 ** n)
    def exbin(k, n):
        if n == 0: return 1.0
        return sum(comb(n, i) for i in range(0, k + 1)) / 2 ** n
R = "data/swe-verified"

def load_reports(arm):
    res, app = {}, {}
    for f in glob.glob(f"{R}/logs/run_evaluation/gptsol_logrep_dedup{arm}/**/report.json", recursive=True):
        d = json.load(open(f))
        for iid, r in d.items():
            res[iid] = bool(r.get("resolved")); app[iid] = bool(r.get("patch_successfully_applied"))
    return res, app

def load_preds(arm):
    ne = {}
    for l in open(f"{R}/preds_local_gptsol_logrep_dedup{arm}.jsonl", encoding="utf-8"):
        if l.strip():
            r = json.loads(l); ne[r["instance_id"]] = bool((r.get("model_patch") or "").strip())
    return ne

def repo(iid): return iid.split("__")[0]

arms = {}
for arm in ("ON", "OFF"):
    res, app = load_reports(arm)
    ne = load_preds(arm)
    ids = list(ne.keys())              # denominator = the preds id set (500 ON / 499 OFF)
    gen = sum(1 for i in ids if ne[i])                       # produced a non-empty patch
    applied = sum(1 for i in ids if app.get(i))              # patch_successfully_applied
    resolved = sum(1 for i in ids if res.get(i))            # resolved (F2P+P2P)
    n = len(ids)
    arms[arm] = dict(ids=set(ids), res=res, ne=ne, n=n, gen=gen, applied=applied, resolved=resolved)

print("=== FUNNEL (primary endpoint) ===")
print(f"{'arm':>4} {'n':>4} {'parse%':>7} {'apply%':>7} {'resolved':>9} {'test-pass|applied':>18}")
tpa = {}
for arm in ("ON", "OFF"):
    a = arms[arm]
    parse = a['gen'] / a['n'] * 100
    apply = a['applied'] / a['n'] * 100
    tpa[arm] = a['resolved'] / a['applied'] * 100 if a['applied'] else 0
    print(f"{arm:>4} {a['n']:>4} {parse:>6.1f}% {apply:>6.1f}% {a['resolved']:>4}/{a['applied']:<4} {tpa[arm]:>16.1f}%")
print(f"\ngpt test-pass|applied: dedup-ON {tpa['ON']:.1f}% -> dedup-OFF {tpa['OFF']:.1f}%  (OFF-ON = {tpa['OFF']-tpa['ON']:+.1f}pp)")
print("  [beside DeepSeek 23.9->31.9 (+8.0), DENSE-1 48.4->55.1 (+6.7)]")

print("\n=== SECONDARY: resolve Δ (paired) ===")
common = sorted(arms['ON']['ids'] & arms['OFF']['ids'])
rON, rOFF = arms['ON']['res'], arms['OFF']['res']
def resolved_of(arm, i): return bool(arms[arm]['res'].get(i))
b = sum(1 for i in common if resolved_of('OFF', i) and not resolved_of('ON', i))   # OFF-only
c = sum(1 for i in common if resolved_of('ON', i) and not resolved_of('OFF', i))   # ON-only
rateON = arms['ON']['resolved'] / arms['ON']['n'] * 100
rateOFF = arms['OFF']['resolved'] / arms['OFF']['n'] * 100
# paired Δ over common instances
onres = sum(1 for i in common if resolved_of('ON', i)); offres = sum(1 for i in common if resolved_of('OFF', i))
npair = len(common); dpp = (offres - onres) / npair * 100
p2 = exbin2(min(b, c), b + c); p1 = exbin(min(b, c) if (b < c) else b, b + c)  # one-sided toward OFF
# one-sided p for OFF>ON: P(X<=c) under 0.5 with n=b+c if b>c favors OFF
from math import comb
def one_sided_off_gt_on(b, c):
    n = b + c
    if n == 0: return 1.0
    # test statistic c (ON-only wins); small c favors OFF; one-sided p = P(C <= c)
    return sum(comb(n, i) for i in range(0, c + 1)) / 2 ** n
p_one = one_sided_off_gt_on(b, c)
print(f"resolve rate: dedup-ON {rateON:.1f}% ({arms['ON']['resolved']}/{arms['ON']['n']}) -> dedup-OFF {rateOFF:.1f}% ({arms['OFF']['resolved']}/{arms['OFF']['n']})")
print(f"paired (n={npair}): Δ(OFF-ON) = {dpp:+.2f}pp; discordant b(OFF-only)={b} c(ON-only)={c}; exact 2-sided McNemar p={p2:.4f}; one-sided P(OFF≤ON)={p_one:.4f}")

# repo-cluster bootstrap
repos = {}
for i in common: repos.setdefault(repo(i), []).append(i)
rlist = list(repos.keys()); rng = random.Random(20260809); B = 10000; deltas = []
for _ in range(B):
    on = off = m = 0
    samp = [rlist[rng.randrange(len(rlist))] for _ in range(len(rlist))]
    for rp in samp:
        for i in repos[rp]:
            on += resolved_of('ON', i); off += resolved_of('OFF', i); m += 1
    deltas.append((off - on) / m * 100)
deltas.sort(); lo, hi = deltas[int(.025*B)], deltas[int(.975*B)]; ple = sum(1 for d in deltas if d <= 0)/B
print(f"repo-cluster bootstrap 95% CI [{lo:+.2f}, {hi:+.2f}]pp; clustered one-sided P(Δ≤0)={ple:.4f}")

print("\n=== CLAUSE (d) VERDICT ===")
dir_ok = dpp > 0 and p_one < 0.05
mag_ok = 0.8 <= dpp <= 13.1
funnel_ok = tpa['OFF'] > tpa['ON']
print(f"direction confirmed (Δ>0 & one-sided p<0.05): {dir_ok}  (Δ={dpp:+.2f}pp, one-sided p={p_one:.4f})")
print(f"magnitude-consistent (est in [+0.8,+13.1]): {mag_ok}")
print(f"funnel OFF>ON on test-pass|applied: {funnel_ok}  ({tpa['OFF']:.1f}% vs {tpa['ON']:.1f}%)")
print(f"VERDICT: {'REPLICATION CONFIRMED + funnel supports depth' if (dir_ok and funnel_ok) else 'CLAUSE-d BRANCH FIRES — see rules'}")
