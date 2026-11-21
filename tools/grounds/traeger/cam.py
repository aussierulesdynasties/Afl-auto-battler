import numpy as np,math,json
W,H=1500,1074
def R(yaw,pitch_,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch_),math.sin(pitch_);cr,sr=math.cos(roll),math.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    X=np.atleast_2d(np.asarray(X,float));C=p[:3];M=R(*p[3:6]);fo=p[6];d=(X-C)@M.T
    return np.stack([p[7]+fo*d[:,0]/d[:,2],p[8]-fo*d[:,1]/d[:,2]],1)
def load():
    return np.array(json.load(open('cam.json'))['p'])
def ray(p,u,v):
    M=R(*p[3:6]);d=np.array([(u-p[7])/p[6],-(v-p[8])/p[6],1.0]);w=M.T@d;return w/np.linalg.norm(w)
def at_z(p,u,v,z=0.0):
    w=ray(p,u,v);t=(z-p[2])/w[2];return p[:3]+t*w
def at_vline(p,u,v,b):
    w=ray(p,u,v);A=np.array([[w[0]],[w[1]]]);rhs=np.array([b[0]-p[0],b[1]-p[1]]);t=np.linalg.lstsq(A,rhs,rcond=None)[0][0];return p[:3]+t*w
