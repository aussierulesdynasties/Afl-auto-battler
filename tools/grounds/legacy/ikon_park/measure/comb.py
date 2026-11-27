import json,numpy as np
fr={'33':None,'31':None,'29':None,'19':None,'20':None}
R={}
for k in fr:
    d=json.load(open('h%s.json'%k));R[k]=np.array([x[1] if x[1] else np.nan for x in d])
A=np.array([x[0] for x in json.load(open('h31.json'))])
R['20'][(A>=210)&(A<=330)]=np.nan
M=np.vstack([R[k] for k in fr]);med=np.nanmedian(M,0)
for s in range(0,360,30):
    m=(A>=s)&(A<s+30)
    print(s,' '.join('%s:%+.2f(%d)'%(k,np.nanmedian(R[k][m]-med[m]),np.isfinite(R[k][m]).sum()) for k in fr),'spread %.2f'%np.nanmedian(np.nanstd(M[:,m],0)))
ok=np.isfinite(med)&(np.isfinite(M).sum(0)>=3)
json.dump([[float(a),float(r) if o else None,True] for a,r,o in zip(A,med,ok)],open('hmed.json','w'))
