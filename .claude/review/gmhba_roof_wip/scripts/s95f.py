import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as R
P=np.array([[-120,-3.4,24],[-120,-44.8,24],[-120,-3.4,0],[-120,-44.8,0]],float)
O=np.array([[732.5,249],[1017,255],[733,362],[1020,365]],float)
def proj(p,X):
    C=np.array([p[0],p[1],2.6]);Rm=R.from_euler('ZYX',p[2:5]).as_matrix();f=p[5]
    c=(X-C)@Rm;return np.c_[640-f*c[:,1]/c[:,0],292.5-f*c[:,2]/c[:,0]]
def res(p):return (proj(p,P)-O).ravel()
for f0 in (400,600,834):
  best=None
  for x0 in (-160,-200,-240):
    r=least_squares(res,[x0,10,np.radians(-95+90),0,0,f0],bounds=([-400,-100,-4,-1,-1,150],[-125,150,4,1,1,2000]))
    if best is None or r.cost<best.cost:best=r
  print(f0,np.round(best.x[:2],1),round(best.x[5]),np.round(np.abs(res(best.x)).reshape(-1,2).max(1),1))
# f fixed to pano value 403
def res2(q):return res(np.r_[q,403])
r=min((least_squares(res2,[x0,10,0,0,0]) for x0 in (-160,-200)),key=lambda r:r.cost)
print('f403',np.round(r.x[:2],1),np.round(np.abs(res2(r.x)).reshape(-1,2).max(1),1))
