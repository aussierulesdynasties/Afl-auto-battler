import numpy as np,math
def R(yaw,pitch_,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch_),math.sin(pitch_);cr,sr=math.cos(roll),math.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    X=np.atleast_2d(np.asarray(X,float))
    C=np.array(p[:3]);M=R(*p[3:6]);fo=p[6];d=(X-C)@M.T
    return np.stack([p[7]+fo*d[:,0]/d[:,2],p[8]-fo*d[:,1]/d[:,2]],1)
def ray(p,u,v):
    M=R(*p[3:6]);fo=p[6];dc=np.array([(u-p[7])/fo,-(v-p[8])/fo,1.0]);d=M.T@dc;return np.array(p[:3]),d/np.linalg.norm(d)
def at_z(p,u,v,z=0.0):
    C,d=ray(p,u,v);t=(z-C[2])/d[2];return C+t*d
def height(p,base_uv,top_uv,zb=0.0):
    B=at_z(p,*base_uv,zb);C,d=ray(p,*top_uv)
    # closest point on vertical line through B to the ray: solve in xy
    w=np.array([d[0],d[1]]);q=B[:2]-C[:2];t=(q@w)/(w@w);P=C+t*d;return P[2]
def ellipse(a,b,n=360,z=0.0):
    t=np.linspace(0,2*math.pi,n,endpoint=False);return np.stack([a*np.cos(t),b*np.sin(t),np.full(n,z)],1)
