import numpy as np,json,itertools
from scipy.optimize import least_squares
T=np.array(json.load(open('geo_build.json'))['towers'])
heads=[[527,350],[1047,295],[1405,440],[445,590],[800,800],[1428,690]];bases=[None,None,None,[450,845],[795,1075],[1415,955]]
Wi,Hi=2000,1333
def R(yaw,p_,roll):
    cy,sy,cp,sp,cr,sr=np.cos(yaw),np.sin(yaw),np.cos(p_),np.sin(p_),np.cos(roll),np.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f);return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    d=(X-p[:3])@R(*p[3:6]).T;return np.c_[Wi/2+p[6]*d[:,0]/d[:,2],Hi/2-p[6]*d[:,1]/d[:,2]]
res=[]
for perm in itertools.permutations(range(6)):
  X=[];U=[]
  for i,k in enumerate(perm):
    X.append([T[k,0],T[k,1],T[k,2]-5.5]);U.append(heads[i])
    if bases[i]:X.append([T[k,0],T[k,1],0]);U.append(bases[i])
  X=np.array(X);U=np.array(U,float);best=None
  for az in np.arange(0,2*np.pi,np.pi/4):
   for d in (600,1000):
    h=0.6*d;p0=[d*np.cos(az),d*np.sin(az),h,az+np.pi,-np.arctan2(h,d),0,3500]
    r=least_squares(lambda p:(proj(p,X)-U).ravel(),p0,max_nfev=1500)
    e=np.sqrt((r.fun**2).mean())
    if (best is None or e<best[0]) and np.all((X-r.x[:3])@R(*r.x[3:6])[2]>0):best=(e,r.x)
  if best:res.append((best[0],perm,best[1]))
res.sort(key=lambda t:t[0])
for e,perm,x in res[:8]:print(round(e,1),perm,np.round(x,2).tolist())
