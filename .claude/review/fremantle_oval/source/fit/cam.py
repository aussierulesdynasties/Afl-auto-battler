import numpy as np, json, math
def R(yaw,pitch_,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch_),math.sin(pitch_);cr,sr=math.cos(roll),math.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X,cx,cy):
    C=np.array(p[:3]);M=R(*p[3:6]);fo=p[6];d=(np.asarray(X,float)-C)@M.T
    return np.stack([cx+fo*d[:,0]/d[:,2],cy-fo*d[:,1]/d[:,2]],1)
def dens(P,k=6):
    P=np.asarray(P,float);out=[]
    for i in range(len(P)):
        a=P[i];b=P[(i+1)%len(P)]
        for t in np.linspace(0,1,k,endpoint=False):out.append(a*(1-t)+b*t)
    return np.array(out)
