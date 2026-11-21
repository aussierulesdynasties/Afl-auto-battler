import numpy as np,cv2,json,sys
P=[('SWtop',(-120.33,-58.49,74.39),(822,209)),('SWbase',(-122.47,-59.21,0),(807,331)),
('NWtop',(-57.69,105.45,74.38),(467,108)),('NWbase',(-58.45,107.55,0),(473,232)),('SEbase',(25.67,-119.74,0),(874,133)),
('catsTL',(-119.76,-3.33,23.53),(693.8,289.5)),('catsTR',(-120.78,-48.37,23.91),(788,290)),
('catsBL',(-119.77,-3.5,5.9),(697,322)),('catsBR',(-120.77,-48.9,6.3),(788,322))]
drop=sys.argv[1:];idx=[i for i,p in enumerate(P) if p[0] not in drop]
X=np.array([p[1] for p in P],float);U=np.array([p[2] for p in P],float);best=None
for f in np.arange(500,2500,5):
 for cy in [292.5]:
  K=np.array([[f,0,640],[0,f,cy],[0,0,1.]])
  try:
   ok,rv,tv=cv2.solvePnP(X[idx],U[idx],K,None,flags=cv2.SOLVEPNP_SQPNP)
   ok,rv,tv=cv2.solvePnP(X[idx],U[idx],K,None,rv,tv,True,cv2.SOLVEPNP_ITERATIVE)
  except Exception:continue
  pr,_=cv2.projectPoints(X,rv,tv,K,None);e=np.linalg.norm(pr[:,0]-U,axis=1);m=np.sqrt((e[idx]**2).mean())
  if tv[2]>0 and(best is None or m<best[0]):best=(m,f,cy,rv,tv,e)
m,f,cy,rv,tv,e=best;Rm=cv2.Rodrigues(rv)[0];C=-Rm.T@tv[:,0]
print('f',f,'cy',cy,'C',C.round(1),'rms',round(m,2),'max',round(e[idx].max(),2),'vfov',round(2*np.degrees(np.arctan(292.5/f)),1))
for i,(p,ee) in enumerate(zip(P,e)):print(p[0],round(ee,2),'' if i in idx else 'HELD-OUT')
json.dump({'f':float(f),'cx':640.,'cy':float(cy),'R':Rm.tolist(),'C':C.tolist(),'err':{p[0]:float(ee) for p,ee in zip(P,e)}},open('wide_cam.json','w'))
