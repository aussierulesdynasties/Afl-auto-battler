import numpy as np,cv2,json
P=[('catsTL',(-119.76,-3.33,23.53),(693.3,180.7)),('catsTR',(-120.78,-48.37,23.91),(921.7,180.7)),
('catsBL',(-119.77,-3.5,5.9),(698.3,262.7)),('catsBR',(-120.77,-48.9,6.3),(915,262.7)),
('logo',(-120.92,-18.0,15.55),(763.3,208.3)),('gmhba',(-124.76,16.15,18.39),(590,225)),('twrbase',(-122.47,-59.21,0),(975,283)),('pk1',(-84.2,-7.3,21.7),(690,140.5)),('pk2',(-85.7,-15.6,21.7),(730,141.25)),('pk3',(-86.7,-24.0,21.6),(768.75,142)),('pk4',(-87.1,-32.5,21.6),(807.5,143)),('pk5',(-86.9,-41.0,21.6),(846.25,143))]
X=np.array([p[1] for p in P],float);U=np.array([p[2] for p in P],float)
best=None
for f in np.arange(300,3000,5):
 for cy in np.arange(240,421,5):
  K=np.array([[f,0,640],[0,f,cy],[0,0,1.]])
  ok,rv,tv=cv2.solvePnP(X,U,K,None,flags=cv2.SOLVEPNP_SQPNP)
  ok,rv,tv=cv2.solvePnP(X,U,K,None,rv,tv,True,cv2.SOLVEPNP_ITERATIVE)
  pr,_=cv2.projectPoints(X,rv,tv,K,None);e=np.linalg.norm(pr[:,0]-U,axis=1)
  if tv[2]>0 and (best is None or e.mean()<best[0]):best=(e.mean(),f,cy,rv,tv,e)
m,f,cy,rv,tv,e=best;Rm=cv2.Rodrigues(rv)[0];C=-Rm.T@tv[:,0]
print('f',f,'cy',cy,'C',C.round(2),'mean',round(m,2),'max',round(e.max(),2))
for p,ee in zip(P,e):print(p[0],round(ee,2))
json.dump({'f':float(f),'cx':640,'cy':float(cy),'R':Rm.tolist(),'C':C.tolist(),'err':{p[0]:float(ee) for p,ee in zip(P,e)}},open('ge_cam.json','w'))
