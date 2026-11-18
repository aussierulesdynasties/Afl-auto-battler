import numpy as np,json
from scipy.optimize import least_squares
T=np.array(json.load(open('geo_build.json'))['towers'])
Wi,Hi=2000,1333
def R(yaw,p_,roll):
    cy,sy,cp,sp,cr,sr=np.cos(yaw),np.sin(yaw),np.cos(p_),np.sin(p_),np.cos(roll),np.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f);return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    d=(np.atleast_2d(X)-p[:3])@R(*p[3:6]).T;return np.c_[Wi/2+p[6]*d[:,0]/d[:,2],Hi/2-p[6]*d[:,1]/d[:,2]]
pm=json.load(open('cam.json'));pm=np.array(pm['p'] if isinstance(pm,dict) else pm)
heads=[[527,357],[1047,295],[1411,450],[447,590],[799,805],[1427,690]];bases=[None,None,None,[452,847],[796,1060],[1416,955]]
perm=[3,5,4,1,0,2];inv={k:i for i,k in enumerate(perm)}
scrU=np.array([[1078,930],[1236,900],[1078,985],[1234,955]],float)
S0=np.array([[55.6,95.3],[27.5,104.3]]);Z0=np.array([14.6,4.0])
def pts(q):
    tw=q[:18].reshape(6,3);s=q[18:22].reshape(2,2);z=q[22:24];return tw,s,z
q0=np.r_[T.ravel(),S0.ravel(),Z0]
def scr3(s,z):return np.array([[s[0,0],s[0,1],z[0]],[s[1,0],s[1,1],z[0]],[s[0,0],s[0,1],z[1]],[s[1,0],s[1,1],z[1]]])
tw0,s0,z0=pts(q0)
obsM=[proj(pm,np.c_[tw0[:,:2],tw0[:,2]-5.5]),proj(pm,np.c_[tw0[:,:2],0*tw0[:,2]]),proj(pm,scr3(s0,z0))]
def resid(x):
    pw=x[:7];tw,s,z=pts(x[7:]);out=[]
    out.append((proj(pm,np.c_[tw[:,:2],tw[:,2]-5.5])-obsM[0]).ravel());out.append((proj(pm,np.c_[tw[:,:2],0*tw[:,2]])-obsM[1]).ravel());out.append((proj(pm,scr3(s,z))-obsM[2]).ravel())
    for k in range(6):
        i=inv[k];out.append(proj(pw,[tw[k,0],tw[k,1],tw[k,2]-5.5])[0]-heads[i])
        if bases[i]:out.append(proj(pw,[tw[k,0],tw[k,1],0])[0]-bases[i])
    out.append((proj(pw,scr3(s,z))-scrU).ravel())
    return np.concatenate(out)
x0=np.r_[json.load(open('ne0.json'))['p'],q0]
r=least_squares(resid,x0,x_scale=np.r_[[50,50,50,.01,.01,.01,100],np.ones(24)])
f=r.fun;nm=12*2+4*2;print('main rms',np.sqrt((f[:2*16]**2).mean()).round(2),'w0 rms',np.sqrt((f[2*16:]**2).mean()).round(2))
print('w0 res',np.round(f[32:],1).tolist())
tw,s,z=pts(r.x[7:])
for k in range(6):print('tower',k,T[k].round(1),'->',tw[k].round(1),'d',(tw[k]-T[k]).round(1))
print('screen',S0.round(1).tolist(),'->',s.round(1).tolist(),z.round(1))
json.dump({'p':list(map(float,r.x[:7])),'towers':tw.tolist(),'screen':s.tolist(),'z':z.tolist()},open('ba1.json','w'))
