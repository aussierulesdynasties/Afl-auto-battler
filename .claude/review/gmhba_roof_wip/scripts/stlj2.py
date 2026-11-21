import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as R
FR={'85':(85,25),'30':(30,15)}
PTS=[('85',(-120,-44.8,24),(378,197),1),('30',(-120,-3.4,24),(371,269.5),1)]
LINES=[('85',(-120,-44.8,24),(-120,-3.4,24),[(0,217),(200,207)]),           # Cats top edge
       ('85',(-120,-44.8,24),(-120,-44.8,0),[(379,300),(380,420)])]          # Cats S edge
def cam(p,k):
    h,pt=FR[k];Rm=R.from_rotvec(p[2:5]).as_matrix()@R.from_euler('ZYX',np.radians([-h,-pt,0])).as_matrix()
    return np.array([p[0],p[1],2.6]),Rm,p[5]
def proj(p,k,X):
    C,Rm,f=cam(p,k);c=Rm.T@(np.array(X,float)-C)
    # camera looks along local x; heading measured clockwise from north: build base so h=0 looks north
    return np.array([400-f*c[1]/c[0],300-f*c[2]/c[0]])
def res(p):
    r=[]
    for k,X,o,w in PTS:r+=list(w*(proj(p,k,X)-o))
    for k,A,B,obs in LINES:
        a,b=proj(p,k,A),proj(p,k,B);d=b-a;n=np.array([-d[1],d[0]])/np.linalg.norm(d)
        r+=[n@(np.array(o)-a) for o in obs]
    return np.array(r)
best=None
for x0 in(-140,-130):
  for y0 in(-45,-35,-25):
    for f0 in(250,400):
      # base frame: rotvec so that heading 0 looks north (+y): rotate x-axis to +y = Z rot 90deg
      p0=np.r_[x0,y0,0,0,np.pi/2,f0]
      r=least_squares(res,p0)
      if best is None or r.cost<best.cost:best=r
p=best.x;np.save('cam_tlj.npy',p)
print('C',p[:2].round(2),'f',round(p[5],1));print('res',np.abs(res(p)).round(1))
print('--- f fixed 391 (75 deg vertical fov over 600 px)')
r2=lambda q:res(np.r_[q,391.0])
b=min((least_squares(r2,np.r_[x0,y0,0,0,np.pi/2]) for x0 in(-140,-130) for y0 in(-45,-30)),key=lambda r:r.cost)
p=np.r_[b.x,391.0];np.save('cam_tlj.npy',p);print('C',p[:2].round(2),'res',np.abs(res(p)).round(1))
