import numpy as np,json,math
W,H=747,500
G=json.load(open('osm/geo.json'))
WAYS={k:np.array(v,float) for k,v in G['ways'].items()}
pitch=WAYS['25841610']
def dens(P,k=8):
    o=[]
    for i in range(len(P)-1):
        for t in np.linspace(0,1,k,endpoint=False):o.append(P[i]*(1-t)+P[i+1]*t)
    o.append(P[-1]);return np.array(o)
def R(yaw,pt,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pt),math.sin(pt);cr,sr=math.cos(roll),math.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    X=np.atleast_2d(np.asarray(X,float))
    if X.shape[1]==2:X=np.c_[X,np.zeros(len(X))]
    C=p[:3];M=R(*p[3:6]);fo=p[6];d=(X-C)@M.T
    return np.stack([p[7]+fo*d[:,0]/d[:,2],p[8]-fo*d[:,1]/d[:,2]],1)
def ray(p,u,v):
    M=R(*p[3:6]);d=np.array([(u-p[7])/p[6],-(v-p[8])/p[6],1.0]);w=M.T@d;return w/np.linalg.norm(w)
def at_z(p,u,v,z=0.0):
    C=np.array(p[:3]);w=ray(p,u,v);t=(z-C[2])/w[2];return C+t*w
def height(p,base,top):
    C=np.array(p[:3]);b=at_z(p,*base);w=ray(p,*top)
    A=np.array([[w[0]],[w[1]]]);rhs=np.array([b[0]-C[0],b[1]-C[1]]);t=np.linalg.lstsq(A,rhs,rcond=None)[0][0]
    return b,(C+t*w)[2]
def loadcam(f='cam5.json'):
    return np.array(json.load(open(f))['p'])
