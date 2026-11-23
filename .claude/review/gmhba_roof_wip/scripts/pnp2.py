import numpy as np,cv2,json
exec(open('pnp.py').read().split('X=np.array')[0])
X=np.array([p[1] for p in P],float);U=np.array([p[2] for p in P],float)
import sys;drop=sys.argv[1:] 
idx=[i for i,p in enumerate(P) if p[0] not in drop]
best=None
for f in np.arange(400,2500,10):
 for cy in np.arange(150,500,10):
  for cx in (560,600,640,680,720):
   K=np.array([[f,0,cx],[0,f,cy],[0,0,1.]])
   try:
    ok,rv,tv=cv2.solvePnP(X[idx],U[idx],K,None,flags=cv2.SOLVEPNP_SQPNP)
    ok,rv,tv=cv2.solvePnP(X[idx],U[idx],K,None,rv,tv,True,cv2.SOLVEPNP_ITERATIVE)
   except Exception: continue
   pr,_=cv2.projectPoints(X,rv,tv,K,None);e=np.linalg.norm(pr[:,0]-U,axis=1)
   m=np.sqrt((e[idx]**2).mean())
   if tv[2]>0 and (best is None or m<best[0]):best=(m,f,cx,cy,rv,tv,e)
m,f,cx,cy,rv,tv,e=best;Rm=cv2.Rodrigues(rv)[0];C=-Rm.T@tv[:,0]
print('f',f,'cx',cx,'cy',cy,'C',C.round(2),'rms',round(m,2))
for i,(p,ee) in enumerate(zip(P,e)):print(p[0],round(ee,2),'' if i in idx else 'HELD-OUT')
json.dump({'f':float(f),'cx':float(cx),'cy':float(cy),'R':Rm.tolist(),'C':C.tolist(),'err':{p[0]:float(ee) for p,ee in zip(P,e)}},open('ge_cam.json','w'))
