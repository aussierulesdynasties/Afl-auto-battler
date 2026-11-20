import numpy as np,json,math
W,H=800,581
def R(yaw,pit,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pit),math.sin(pit);cr,sr=math.cos(roll),math.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    X=np.atleast_2d(np.asarray(X,float));C=p[:3];M=R(*p[3:6]);fo=p[6];d=(X-C)@M.T
    return np.stack([p[7]+fo*d[:,0]/d[:,2],p[8]-fo*d[:,1]/d[:,2]],1)
def ray(p,u,v):
    M=R(*p[3:6]);d=np.array([(u-p[7])/p[6],-(v-p[8])/p[6],1.0]);w=M.T@d;return w/np.linalg.norm(w)
def at_z(p,u,v,z=0.0):
    C=p[:3];w=ray(p,u,v);t=(z-C[2])/w[2];return C+t*w
def height(p,base,top):
    C=p[:3];b=at_z(p,*base);w=ray(p,*top);A=np.array([[w[0]],[w[1]]]);rhs=np.array([b[0]-C[0],b[1]-C[1]]);t=np.linalg.lstsq(A,rhs,rcond=None)[0][0];return b,(C+t*w)[2]
G=json.load(open('geo.json'))
def dens(pts,n=10):
    pts=np.array(pts,float);o=[]
    for i in range(len(pts)-1):
        for t in np.linspace(0,1,n,endpoint=False):o.append(pts[i]*(1-t)+pts[i+1]*t)
    return np.array(o)
