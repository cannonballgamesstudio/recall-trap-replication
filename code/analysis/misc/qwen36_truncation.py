import json
from scipy.stats import binomtest
P='work/p5/'
def load(k,a,lab):
    raw={}
    for l in open(P+f'raw_local_qwen36_{k}_dedup{a}.jsonl'):
        r=json.loads(l); raw[r['instance_id']]=r
    g=json.load(open(P+f'local_qwen36_{k}_dedup{a}.{lab}.json'))
    preds={}
    for l in open(P+f'preds_local_qwen36_{k}_dedup{a}.jsonl'):
        r=json.loads(l); preds[r['instance_id']]=r.get('model_patch') or ''
    return raw,set(g['resolved_ids']),preds
for k,lon,loff in [('k12','qwen36_k12_dedupON','qwen36_k12_dedupOFF'),('k4','qs2_k4_ON','qs2_k4_OFF'),('k40','qs2_k40_ON','qs2_k40_OFF')]:
    ron,son,pon=load(k,'ON',lon); roff,soff,poff=load(k,'OFF',loff)
    ids=set(ron)|set(roff)|set(pon)|set(poff)
    print('==',k,'union ids',len(ids),'raw ON/OFF',len(ron),len(roff),'preds',len(pon),len(poff),'both raw',len(set(ron)&set(roff)))
    pk=json.load(open(P+'local_packs.json')) if k=='k12' else None
    def trunc(r,i): return r.get(i,{}).get('finish_reason')=='length'
    def emp(p,i): return not p.get(i)
    for name,base in [('union',ids),('both-raw',set(ron)&set(roff))]:
        n=len(base)
        b=sum(1 for i in base if i in soff and i not in son); c=sum(1 for i in base if i in son and i not in soff)
        print(name,n,'ON',len(son&base),'OFF',len(soff&base),'b(OFFwin)',b,'c',c,'d',round(100*(b-c)/n,2),'p',binomtest(b,b+c).pvalue if b+c else None)
    base=set(ron)&set(roff)
    tl_on=sum(trunc(ron,i) for i in ron); tl_off=sum(trunc(roff,i) for i in roff)
    print('fin=length ON',tl_on,len(ron),round(100*tl_on/len(ron),1),'over500',round(100*tl_on/500,1),'OFF',tl_off,len(roff),round(100*tl_off/len(roff),1),round(100*tl_off/500,1))
    eon=sum(emp(pon,i) for i in ids); eoff=sum(emp(poff,i) for i in ids)
    print('empty patches over union ON',eon,round(100*eon/len(ids),1),'OFF',eoff,round(100*eoff/len(ids),1))
    # complete case variants
    for cname,keep in [('neither truncated',lambda i: not trunc(ron,i) and not trunc(roff,i)),('both nonempty',lambda i: not emp(pon,i) and not emp(poff,i)),('neither trunc nor error',lambda i: ron.get(i,{}).get('finish_reason')=='stop' and roff.get(i,{}).get('finish_reason')=='stop')]:
        S=[i for i in base if keep(i)]
        b=sum(1 for i in S if i in soff and i not in son); c=sum(1 for i in S if i in son and i not in soff)
        print(' CC',cname,len(S),'b',b,'c',c,'d',round(100*(b-c)/len(S),2),'p',round(binomtest(b,b+c).pvalue,4))
    # Manski on base
    n=len(base)
    def res(s,r,i,mode):
        if trunc(r,i): return mode
        return i in s
    for nm,mon,moff in [('worst(ON-trunc->succ,OFF-trunc->fail)',1,0),('best',0,1),('all trunc fail',0,0),('all trunc succ',1,1)]:
        d=sum(res(soff,roff,i,moff)-res(son,ron,i,mon) for i in base)
        print(' Manski',nm,round(100*d/n,2))
    b=sum(1 for i in base if i in soff and i not in son)
    print(' OFF wins where ON truncated',sum(1 for i in base if i in soff and i not in son and trunc(ron,i)))
print('==== extra k12')
ron,son,pon=load('k12','ON','qwen36_k12_dedupON'); roff,soff,poff=load('k12','OFF','qwen36_k12_dedupOFF')
base=set(ron)&set(roff); n=len(base)
print('paired empties ON',sum(1 for i in base if not pon.get(i)),'OFF',sum(1 for i in base if not poff.get(i)))
for nm,mon,moff in [('emp->succ both',1,1),('worst emp',1,0)]:
    d=sum(((moff if not poff.get(i) else (i in soff)) - (mon if not pon.get(i) else (i in son))) for i in base); print(nm,round(100*d/n,2))
import collections
for a,r in [('ON',ron),('OFF',roff)]:
    rows=[r[i] for i in base]
    print(a,'len&content0',sum(1 for x in rows if x.get('finish_reason')=='length' and not x.get('content_len')),
      'len&reas>15000',sum(1 for x in rows if x.get('finish_reason')=='length' and (x.get('reasoning_len') or 0)>15000),
      'reas>15000 any',sum(1 for x in rows if (x.get('reasoning_len') or 0)>15000),
      'length',sum(1 for x in rows if x.get('finish_reason')=='length'))
for t in [129,128,127]: print(t, round(100*t/499,1), round(100*t/500,1))
