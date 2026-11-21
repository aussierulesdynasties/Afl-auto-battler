# generic camera fit in the field frame: python fitw.py w h picks.json out.json [fprior]
# picks: [[x,y,z,u,v],...]; principal point at centre; f free (prior weak)
import sys,json,numpy as np,cv2
from scipy.optimize import least_squares
w,h=int(sys.argv[1]),int(sys.argv[2]);pk=json.load(open(sys.argv[3]));fp=float(sys.argv[5]) if len(sys.argv)>5 else 0
X=np.array([p[:3] for p in pk],np.float64);U=np.array([p[3:5] for p in pk],np.float64)
def K(f):return np.array([[f,0,w/2],[0,f,h/2],[0,0,1.]])
best=None
for f in np.geomspace(800,12000,40):
    ok,r,t=cv2.solvePnP(X,U,K(f),None,flags=cv2.SOLVEPNP_SQPNP)
    q=least_squares(lambda q:(cv2.projectPoints(X,q[1:4],q[4:7],K(q[0]),None)[0][:,0]-U).ravel(),np.r_[f,r.ravel(),t.ravel()]).x
    e=np.sqrt(((cv2.projectPoints(X,q[1:4],q[4:7],K(q[0]),None)[0][:,0]-U)**2).sum(1).mean())
    if best is None or e<best[0]:best=(e,q)
e,q=best;R=cv2.Rodrigues(q[1:4])[0];C=-R.T@q[4:7]
rr=cv2.projectPoints(X,q[1:4],q[4:7],K(q[0]),None)[0][:,0]-U
print('f %.0f rms %.2f cam %s'%(q[0],e,C.round(2)));print(rr.round(1))
json.dump(dict(f=q[0],r=q[1:4].tolist(),t=q[4:7].tolist(),w=w,h=h),open(sys.argv[4],'w'))
