import numpy as np,math,json
def R(yaw,pitch,roll):
    cy,sy,cp,sp,cr,sr=math.cos(yaw),math.sin(yaw),math.cos(pitch),math.sin(pitch),math.cos(roll),math.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    X=np.atleast_2d(X);C=np.array(p[:3]);M=R(*p[3:6]);fo=p[6]
    d=(X-C)@M.T
    return np.stack([p[7]+fo*d[:,0]/d[:,2],p[8]-fo*d[:,1]/d[:,2]],1)
def dens(P,step=0.5,closed=True):
    P=np.array(P);out=[]
    n=len(P)
    for i in range(n if closed else n-1):
        a,b=P[i],P[(i+1)%n];k=max(1,int(np.linalg.norm(b-a)/step))
        for j in range(k):out.append(a+(b-a)*j/k)
    return np.array(out)
