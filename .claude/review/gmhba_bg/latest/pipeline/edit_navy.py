import json, numpy as np
B=json.load(open('out/gmhba/court_boxes.json')); out=[]
for b in B:
    b=np.array(b); e1=b[1]-b[0]; L=np.linalg.norm(e1)
    n=max(1,round(L/32))
    for i in range(n):
        a0,a1=b[0]+e1*i/n,b[0]+e1*(i+1)/n; d=b[3]-b[0]; g=(e1/L)*1.0 if n>1 else 0
        out.append([[round(float(v),1) for v in p] for p in (a0+g,a1-g,a1-g+d,a0+g+d)])
g=json.load(open('spec/gmhba.json')); g['palette']['court_navy']=[60,80,118]
g['paint_poly']=[p for p in g['paint_poly'] if p[0]!='court_navy']+[['court_navy',q] for q in out]
json.dump(g,open('spec/gmhba.json','w'),indent=1); print(len(out))
