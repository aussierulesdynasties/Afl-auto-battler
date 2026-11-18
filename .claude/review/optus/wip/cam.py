import numpy as np,json,math
G=json.load(open('osm/geo.json'))['ways']
W,H=1920,1079
def R(yaw,pitch_,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch_),math.sin(pitch_);cr,sr=math.cos(roll),math.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    C=p[:3];M=R(*p[3:6]);fo=p[6];d=(np.atleast_2d(X)-C)@M.T
    return np.stack([p[7]+fo*d[:,0]/d[:,2],p[8]-fo*d[:,1]/d[:,2]],1)
def dens(P,n=10):
    P=np.asarray(P,float);out=[]
    for i in range(len(P)-1):
        for t in np.linspace(0,1,n,endpoint=False):out.append(P[i]*(1-t)+P[i+1]*t)
    return np.array(out)
