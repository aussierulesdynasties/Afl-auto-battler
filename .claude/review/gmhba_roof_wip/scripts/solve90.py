import numpy as np
from scipy.spatial.transform import Rotation as R
from scipy.optimize import least_squares
FR={'A':(90,15,640/np.tan(np.radians(45))),'B':(125,8,640/np.tan(np.radians(37.5)))}
OBS=[('A','NWtwr_top',(-51.9,107.9,74.7),(527,165)),
     ('A','canNWtip',(-121.0,104.5,None),(382,239)),
     ('B','SWtwr_top',(-122.5,-52.6,74.7),(943.3,65)),
     ('B','CatsTR_top',(-120,-44.8,24),(951.7,268.3))]
CHK=[('A','signTL(h95)',(-125.5,17.05,18.78),(1113,245))]
def Rm(p,fr):
    h,pt,f=FR[fr];Rp=R.from_rotvec(p[3:6]);return (Rp*R.from_euler('ZYX',[np.radians(-h),np.radians(-pt),0])).as_matrix(),f
def proj(p,fr,X):
    M,f=Rm(p,fr);c=M.T@(np.array(X)-p[:3]);return np.array([640-f*c[1]/c[0],292.5-f*c[2]/c[0]])
def res(p):
    r=[]
    for fr,n,X,uv in OBS:
        X=list(X)
        if X[2] is None:X[2]=p[6]
        r+=list(proj(p,fr,X)-uv)
    return r
best=None
for yaw in np.radians(np.arange(60,140,10)):
  for cx,cy in[(-200,40),(-170,60),(-230,20)]:
    p0=np.r_[cx,cy,2.5,R.from_euler('ZYX',[yaw,0,0]).as_rotvec(),21.0]
    s=least_squares(res,p0,bounds=([-400,-100,0.5,-4,-4,-4,15],[-125,200,5,4,4,4,26]))
    if best is None or s.cost<best.cost:best=s
p=best.x;print('C',np.round(p[:3],2),'tipz',round(p[6],2),'cost',best.cost)
for fr,n,X,uv in OBS:
    X=list(X);X[2]=p[6] if X[2] is None else X[2];e=proj(p,fr,X)-uv;print(n,np.round(e,1),round(np.hypot(*e),1))
for fr,n,X,uv in CHK:e=proj(p,fr,X)-uv;print('CHECK',n,np.round(e,1),round(np.hypot(*e),1))
np.save('cam_h90.npy',p)
