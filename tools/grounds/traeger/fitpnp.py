# fit a pinhole (f, pose; principal point at centre) to stand-frame points: python fitpnp.py photo picks.json out_cam.json
import sys,json,numpy as np,cv2
from scipy.optimize import least_squares
import stand
stand.build()
ph,pk,oc=sys.argv[1:4];im=cv2.imread(ph);h,w=im.shape[:2]
pk=json.load(open(pk))   # list of [s,t,z,u,v]
X=np.array([stand.W(s,t,z) for s,t,z,u,v in pk],np.float64);U=np.array([[u,v] for s,t,z,u,v in pk],np.float64)
def K(f):return np.array([[f,0,w/2],[0,f,h/2],[0,0,1.]])
best=None
for f in np.linspace(600,4000,35):
    ok,r,t=cv2.solvePnP(X,U,K(f),None,flags=cv2.SOLVEPNP_SQPNP)
    e=np.linalg.norm(cv2.projectPoints(X,r,t,K(f),None)[0][:,0]-U,axis=1).mean()
    if best is None or e<best[0]:best=(e,f,r,t)
e,f,r,t=best
def res(q):return (cv2.projectPoints(X,q[1:4],q[4:7],K(q[0]),None)[0][:,0]-U).ravel()
q=least_squares(res,np.r_[f,r.ravel(),t.ravel()]).x
rr=res(q).reshape(-1,2);print('f',round(q[0],1),'rms',round(float(np.sqrt((rr**2).sum(1).mean())),2));print(np.round(rr,1))
json.dump(dict(f=q[0],r=q[1:4].tolist(),t=q[4:7].tolist(),w=w,h=h),open(oc,'w'))
