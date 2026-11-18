import numpy as np,json,itertools
from scipy.optimize import least_squares
src=open('fitw0.py').read().split('X=[]')[0];exec(src)
res=[]
for perm in itertools.permutations(range(6)):
    X=[];U=[]
    for i,k in enumerate(perm):
        X.append([T[k,0],T[k,1],T[k,2]-5.5]);U.append(heads[i])
        if bases[i]:X.append([T[k,0],T[k,1],0]);U.append(bases[i])
    X=np.array(X);U=np.array(U,float);b=None
    for az in range(0,360,30):
      for f in (3000,6000):
        a=np.radians(az);C=np.array([1000*np.cos(a),1000*np.sin(a),600.0])
        p0=[*C,np.arctan2(-C[1],-C[0]),-0.55,0,f]
        try:r=least_squares(lambda p:(proj(p,X)-U).ravel(),p0,max_nfev=300)
        except Exception:continue
        e=np.sqrt((r.fun**2).mean())
        if r.x[6]>500 and (b is None or e<b[0]):b=(e,r.x)
    if b:res.append((b[0],perm,b[1]))
res.sort(key=lambda t:t[0])
for e,perm,p in res[:8]:print(round(e,1),perm,np.round(p[:3]).tolist(),round(np.degrees(p[3])),round(p[6]))
json.dump([list(map(float,r[2])) for r in res[:8]],open('fitall.json','w'))
