import numpy as np,json
from scipy.optimize import least_squares
T=np.array(json.load(open('geo_build.json'))['towers'])
heads=[[527,350],[1047,295],[1405,440],[445,590],[800,800],[1428,690]];bases=[None,None,None,[450,845],[795,1075],[1415,955]]
perm=[3,5,4,1,0,2];Wi,Hi=2000,1333
def R(yaw,p_,roll):
    cy,sy,cp,sp,cr,sr=np.cos(yaw),np.sin(yaw),np.cos(p_),np.sin(p_),np.cos(roll),np.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f);return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    d=(X-p[:3])@R(*p[3:6]).T;return np.c_[Wi/2+p[6]*d[:,0]/d[:,2],Hi/2-p[6]*d[:,1]/d[:,2]]
X=[];U=[]
for i,k in enumerate(perm):
    X.append([T[k,0],T[k,1],T[k,2]-5.5]);U.append(heads[i])
    if bases[i]:X.append([T[k,0],T[k,1],0]);U.append(bases[i])
X=np.array(X);U=np.array(U,float)
best=None
for d in (600,900,1300):
  for h in (400,700,1000):
    p0=[0,d,h,-np.pi/2,-np.arctan2(h,d),0,4000]
    r=least_squares(lambda p:(proj(p,X)-U).ravel(),p0,max_nfev=2000)
    e=np.sqrt((r.fun**2).mean())
    if best is None or e<best[0]:best=(e,r.x,r.fun.reshape(-1,2))
print('rms',best[0]);print(np.round(best[2],1).tolist());print(json.dumps(list(map(float,best[1]))))
