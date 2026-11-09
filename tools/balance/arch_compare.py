# Scratch probe for rows 119 and 127: paired margin of the archetype side (seed i%2), arm A against arm B. Not for main.
import json,glob,sys,math
D=sys.argv[1]
def load(n):
    d={}
    for f in glob.glob(f'{D}/{n}_*.jsonl'):
        for l in open(f):
            if not l.strip().endswith('}'): continue
            o=json.loads(l); d[o['i']]=o['teams'][o['i']%2],o['teams'][1-o['i']%2]
    return d
keys=['tackles','clangers','frees_against','metres_gained','inside50','clearances','goals','score','effective_disposals','disposals','pressure_acts']
cache={}
def L(n):
    if n not in cache: cache[n]=load(n)
    return cache[n]
win=lambda t:1 if t[0]['score']>t[1]['score'] else .5 if t[0]['score']==t[1]['score'] else 0
for spec in ['a:b']:
    b,n=spec.split(':')
    A=L(b);B=L(n);ids=[i for i in B if i in A]
    if not ids: print(n,'none');continue
    dm=[(B[i][0]['score']-B[i][1]['score'])-(A[i][0]['score']-A[i][1]['score']) for i in ids]
    m=sum(dm)/len(dm);se=math.sqrt(sum((x-m)**2 for x in dm)/(len(dm)-1)/len(dm))
    wa=sum(win(A[i]) for i in ids)/len(ids);wb=sum(win(B[i]) for i in ids)/len(ids)
    sd=lambda D:(lambda ms:math.sqrt(sum((x-sum(ms)/len(ms))**2 for x in ms)/(len(ms)-1)))([D[i][0]['score']-D[i][1]['score'] for i in ids])
    st=[]
    for k in keys:
        x=sum(A[i][0].get(k,0) for i in ids)/len(ids);y=sum(B[i][0].get(k,0) for i in ids)/len(ids)
        if x: st.append(f"{k} {100*(y/x-1):+.1f}%({y-x:+.1f})")
    legs=sum(B[i][0]['legs_q'][3]-A[i][0]['legs_q'][3] for i in ids)/len(ids)
    inj=sum(B[i][0].get('inj_n',0) for i in ids)/len(ids);injw=sum(B[i][0].get('inj_w',0) for i in ids)/len(ids)
    print(f"{n} (v {b}) n={len(ids)} margin {m:+.2f} se {se:.2f} win {100*wa:.1f}->{100*wb:.1f} sd {sd(A):.1f}->{sd(B):.1f} legsQ4 {legs:+.2f} inj {inj:.2f} injwk {injw:.2f} | "+' '.join(st))
