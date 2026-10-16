import json, glob, re, os, sys
from math import comb
from collections import Counter
sys.path.insert(0, 'code/eval')
from oracle_pack import parse_gold_hunks
P = 'work/p5/'
gold = json.load(open(P + 'gold_patches.json', encoding='utf-8'))
packs = json.load(open(P + 'local_packs.json', encoding='utf-8'))
inst = {x['instance_id']: x for x in json.load(open(P + 'instances_verified.json', encoding='utf-8'))}
names = json.load(open('data/swe-verified/auxiliary/issue_names_gold.json'))

def norm(p):
    return p.replace('\\', '/').lstrip('./')

def chunks_of(pk):
    out = []
    for part in re.split(r'^### ', pk, flags=re.M)[1:]:
        m = re.match(r'(?P<path>[^:\n]+):(?P<line>\d+)', part)
        if not m:
            continue
        code = re.search(r'```\n(.*?)```', part, re.S)
        span = code.group(1).count('\n') if code else 1
        out.append((norm(m.group('path')), int(m.group('line')), span))
    return out

def classify(iid, arm='dedupON'):
    gl = {}
    for path, start, length in parse_gold_hunks(gold[iid]):
        gl.setdefault(norm(path), set()).update(range(start, start + length))
    ch = chunks_of(packs[iid][arm]['pack'])
    pf = {c[0] for c in ch}
    present = [g for g in gl if g in pf]
    cov = sum(1 for g in gl if any(f == g and set(range(s, s + sp)) & gl[g] for f, s, sp in ch))
    if not gl:
        return '?'
    if not present:
        return 'A'
    return 'C' if cov == len(gl) else 'B'

cls = {i: classify(i) for i in packs}
cls_off = {i: classify(i, 'dedupOFF') for i in packs}
print('class counts ON-pack', Counter(cls.values()))
print('class counts OFF-pack', Counter(cls_off.values()))
print('transition ON->OFF', Counter((cls[i], cls_off[i]) for i in packs))
ft = {r['instance_id']: r['class'][0] for r in json.load(open(P + 'failure_taxonomy.json', encoding='utf-8'))}
print('agreement with on-disk taxonomy', sum(cls[i] == ft[i] for i in ft), '/', len(ft))
json.dump({'on': cls, 'off': cls_off}, open(os.environ['TEMP'] + '/class_abc_500.json', 'w'))

def rep(f):
    d = json.load(open(P + f, encoding='utf-8'))
    return set(d['resolved_ids']), set(d['submitted_ids'])

def mc(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)

arms = {
    'gpt_headline': ('local_gpt56sol_dedupON.local_gpt56sol_dedupON.json', 'local_gpt56sol_dedupOFF.local_gpt56sol_dedupOFF.json'),
    'gpt_logrep': ('local_gptsol_logrep_dedupON.gptsol_logrep_dedupON.json', 'local_gptsol_logrep_dedupOFF.gptsol_logrep_dedupOFF.json'),
    'qwen36_k12': ('local_qwen36_k12_dedupON.qwen36_k12_dedupON.json', 'local_qwen36_k12_dedupOFF.qwen36_k12_dedupOFF.json'),
    'qwen36_k40': ('local_qwen36_k40_dedupON.qs2_k40_ON.json', 'local_qwen36_k40_dedupOFF.qs2_k40_OFF.json'),
    'qwen3or_k12': ('local_qwen3or_k12_dedupON.qwen3or_k12_dedupON.json', 'local_qwen3or_k12_dedupOFF.qwen3or_k12_dedupOFF.json'),
}

def nplus(i):
    return sum(1 for l in gold[i].splitlines() if l.startswith('+') and not l.startswith('+++') and l[1:].strip())

def strat(i, key):
    if key == 'classON':
        return cls[i]
    if key == 'transition':
        return cls[i] + '>' + cls_off[i]
    if key == 'names':
        return 'Y' if names[i]['base'] else 'N'
    if key == 'nplus':
        n = nplus(i)
        return '1-2' if n <= 2 else ('3-9' if n < 10 else '10+')

for name, (a, b_) in arms.items():
    onr, ons = rep(a)
    offr, offs = rep(b_)
    ids = sorted(ons & offs)
    print(f"\n== {name} n={len(ids)} ON={sum(i in onr for i in ids)} OFF={sum(i in offr for i in ids)}")
    for key in ('classON', 'transition', 'names', 'nplus'):
        groups = {}
        for i in ids:
            groups.setdefault(strat(i, key), []).append(i)
        for g, gi in sorted(groups.items()):
            if len(gi) < 5:
                continue
            A = sum(i in onr for i in gi)
            O = sum(i in offr for i in gi)
            b = sum((i in offr) and (i not in onr) for i in gi)
            c = sum((i in onr) and (i not in offr) for i in gi)
            print(f"  {key}={g:5} n={len(gi):3} ON={A / len(gi) * 100:5.1f}% OFF={O / len(gi) * 100:5.1f}% d={(O - A) / len(gi) * 100:+5.1f}pp b/c={b}/{c} p={mc(b, c):.3g}")
