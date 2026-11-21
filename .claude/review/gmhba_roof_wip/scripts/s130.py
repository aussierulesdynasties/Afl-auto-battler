import numpy as np
from scipy.spatial.transform import Rotation as R
from scipy.optimize import least_squares
FR={'D':(100,8,0),'E':(140,8,0),'F':(60,8,0)}
OBS=[('D','NWtwr_top',(-51.9,107.9,74.7),(538.3,82.7)),
     ('F','NWtwr_top',(-51.9,107.9,74.7),(795,70.7)),
     ('E','SWtwr_top',(-122.5,-52.6,74.7),(815,155)),
     ('E','CatsTR_top',(-120,-44.8,24),(812.7,295))]
CHK=[]
def Rm(p,fr):
    h,pt,f=FR[fr];f=p[6];Rp=R.from_rotvec(p[3:6]);return (Rp*R.from_euler('ZYX',[np.radians(-h),np.radians(-pt),0])).as_matrix(),f
def proj(p,fr,X):
    M,f=Rm(p,fr);c=M.T@(np.array(X)-p[:3]);return np.array([640-f*c[1]/c[0],292.5-f*c[2]/c[0]])
def res(p):
    r=[]
    for fr,n,X,uv in OBS:
        X=list(X)
        if X[2] is None:X[2]=21.0
        r+=list(proj(p,fr,X)-uv)
    return r
best=None
for yaw in np.radians(np.arange(60,140,10)):
  for cx,cy in[(-200,100),(-170,120),(-230,80),(-160,90)]:
    p0=np.r_[cx,cy,2.6,R.from_euler('ZYX',[yaw,0,0]).as_rotvec(),600.0]
    s=least_squares(res,p0,bounds=([-400,-100,2.55,-4,-4,-4,250],[-125,200,2.65,4,4,4,1500]))
    if best is None or s.cost<best.cost:best=s
p=best.x;print('C',np.round(p[:3],2),'f',round(p[6],2),'cost',best.cost)
for fr,n,X,uv in OBS:
    X=list(X);X[2]=21.0 if X[2] is None else X[2];e=proj(p,fr,X)-uv;print(n,np.round(e,1),round(np.hypot(*e),1))
for fr,n,X,uv in CHK:e=proj(p,fr,X)-uv;print('CHECK',n,np.round(e,1),round(np.hypot(*e),1))
np.save('cam_p130.npy',p)
