# fit a camera to another photo from the six towers (head centre z=h-5.5, base z=0); tries every tower matching
import numpy as np,json,itertools,sys
from scipy.optimize import least_squares
D=json.load(open('geo_build.json'));T=np.array(D['towers'])
heads=np.array(json.loads(sys.argv[1]));bases=json.loads(sys.argv[2]);Wi,Hi=int(sys.argv[3]),int(sys.argv[4])
def R(yaw,p_,roll):
    cy,sy,cp,sp,cr,sr=np.cos(yaw),np.sin(yaw),np.cos(p_),np.sin(p_),np.cos(roll),np.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    d=(X-p[:3])@R(*p[3:6]).T;return np.c_[Wi/2+p[6]*d[:,0]/d[:,2],Hi/2-p[6]*d[:,1]/d[:,2]]
best=None
for perm in itertools.permutations(range(6)):
    X=[];U=[]
    for i,k in enumerate(perm):
        X.append([T[k,0],T[k,1],T[k,2]-5.5]);U.append(heads[i])
        if bases[i] is not None:X.append([T[k,0],T[k,1],0]);U.append(bases[i])
    X=np.array(X);U=np.array(U,float)
    for az in range(0,360,45):
        a=np.radians(az);C=np.array([900*np.cos(a),900*np.sin(a),500.0])
        p0=[*C,np.arctan2(-C[1],-C[0]),-0.5,0,4500]
        try:r=least_squares(lambda p:(proj(p,X)-U).ravel(),p0,max_nfev=400)
        except Exception:continue
        e=np.sqrt((r.fun**2).mean())
        if r.x[6]>500 and (best is None or e<best[0]):best=(e,perm,r.x)
print('rms',best[0],'perm',best[1]);print(json.dumps(list(map(float,best[2]))))
