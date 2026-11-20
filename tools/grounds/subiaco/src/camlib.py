import numpy as np,json,math
G=json.load(open('osm/geo.json'))
def way(i):return np.array(G['ways'][str(i)]['pts'],float)
def dens(P,n=10):
    out=[]
    for i in range(len(P)-1):
        for t in np.linspace(0,1,n,endpoint=False):out.append(P[i]*(1-t)+P[i+1]*t)
    out.append(P[-1]);return np.array(out)
PITCH=way(47063803)
def R(yaw,p,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(p),math.sin(p);cr,sr=math.cos(roll),math.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(cam,X,cx,cy):
    X=np.atleast_2d(X);C=np.array(cam[:3]);M=R(*cam[3:6]);fo=cam[6];d=(X-C)@M.T
    return np.stack([cx+fo*d[:,0]/d[:,2],cy-fo*d[:,1]/d[:,2]],1)
def ray(cam,u,v,cx,cy):
    M=R(*cam[3:6]);fo=cam[6];d=np.array([(u-cx)/fo,-(v-cy)/fo,1.0]);w=M.T@d;return w/np.linalg.norm(w)
def at_z(cam,u,v,cx,cy,z=0.0):
    C=np.array(cam[:3]);w=ray(cam,u,v,cx,cy);t=(z-C[2])/w[2];return C+t*w
def on_vline(cam,u,v,cx,cy,bxy):
    C=np.array(cam[:3]);w=ray(cam,u,v,cx,cy);A=np.array([[w[0]],[w[1]]]);rhs=np.array([bxy[0]-C[0],bxy[1]-C[1]]);t=np.linalg.lstsq(A,rhs,rcond=None)[0][0];return C+t*w
def curve_d(pts,curve):
    A=curve[:-1];B=curve[1:];AB=B-A;L=(AB**2).sum(1)+1e-9
    t=(((pts[:,None,:]-A[None])*AB[None]).sum(-1)/L[None]).clip(0,1)
    Q=A[None]+t[...,None]*AB[None];return np.sqrt(((pts[:,None,:]-Q)**2).sum(-1)).min(1)
def projd(cam,X,cx,cy,k1=0.0,k2=0.0):
    X=np.atleast_2d(X);C=np.array(cam[:3]);M=R(*cam[3:6]);fo=cam[6];d=(X-C)@M.T
    x=d[:,0]/d[:,2];y=d[:,1]/d[:,2];r2=x*x+y*y;k=1+k1*r2+k2*r2*r2
    return np.stack([cx+fo*x*k,cy-fo*y*k],1)
