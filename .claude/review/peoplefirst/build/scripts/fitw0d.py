import numpy as np,json
from scipy.optimize import least_squares
T=np.array(json.load(open('geo_build.json'))['towers'])
Wi,Hi=2000,1333
def R(yaw,p_,roll):
    cy,sy,cp,sp,cr,sr=np.cos(yaw),np.sin(yaw),np.cos(p_),np.sin(p_),np.cos(roll),np.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f);return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    d=(X-p[:3])@R(*p[3:6]).T;return np.c_[Wi/2+p[6]*d[:,0]/d[:,2],Hi/2-p[6]*d[:,1]/d[:,2]]
heads=[[527,357],[1047,295],[1411,450],[447,590],[799,805],[1427,690]];bases=[None,None,None,[452,847],[796,1060],[1416,955]]
perm=[3,5,4,1,0,2]
# screen corners (crop 1040,860 scaled x4): TL (152,282)->(1078,930) TR (785,162)->(1236,900) BL(152,500)->(1078,985) BR(775,380)->(1234,955)
scrU=[[1078,930],[1236,900],[1078,985],[1234,955]];scrX=[[55.6,95.3,14.6],[27.5,104.3,14.6],[55.6,95.3,4.0],[27.5,104.3,4.0]]
def resid(q,freeh):
    p=q[:7];hs=q[7:] if freeh else np.zeros(6);out=[]
    for i,k in enumerate(perm):
        out.append(proj(p,np.array([[T[k,0],T[k,1],T[k,2]-5.5+hs[i]]]))[0]-heads[i])
        if bases[i]:out.append(proj(p,np.array([[T[k,0],T[k,1],0]]))[0]-bases[i])
    out.append((proj(p,np.array(scrX,float))-scrU).ravel()*1.0)
    return np.concatenate([np.ravel(o) for o in out])
p0=json.load(open('ne0.json'))['p']
for freeh in (False,True):
    q0=np.r_[p0,np.zeros(6)] if freeh else np.array(p0)
    r=least_squares(lambda q:resid(q,freeh),q0)
    print('freeh',freeh,'rms',np.sqrt((r.fun**2).mean()).round(2),np.round(r.fun,1).tolist());print(json.dumps(list(map(float,r.x[:7]))));
    if freeh:print('dh',np.round(r.x[7:],1))
    json.dump({'p':list(map(float,r.x[:7]))},open('ne_d%d.json'%freeh,'w'))
