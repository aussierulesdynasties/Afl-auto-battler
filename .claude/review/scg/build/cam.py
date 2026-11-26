import numpy as np,json,math
G=json.load(open('osm/geo.json'))['geo']
TOW={k:G[k][0] for k in G if k[0]=='T'}
# OSM towers by compass: N,NE,SE,S,SW,W
TN=['T6806884417','T6811536969','T6811536968','T6811536967','T6811536966','T6806884418']
W,H=1200,675
def R(yaw,pitch_,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch_),math.sin(pitch_);cr,sr=math.cos(roll),math.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    X=np.atleast_2d(np.array(X,float));C=p[:3];M=R(*p[3:6]);fo=p[6];d=(X-C)@M.T
    return np.stack([p[7]+fo*d[:,0]/d[:,2],p[8]-fo*d[:,1]/d[:,2]],1)
def dens(poly,k=8):
    P=np.array(poly,float);out=[]
    for i in range(len(P)-1):
        for t in np.linspace(0,1,k,endpoint=False):out.append(P[i]*(1-t)+P[i+1]*t)
    return np.array(out)
