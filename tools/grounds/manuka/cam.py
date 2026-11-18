import numpy as np,math,json
G=json.load(open('osm/geo.json'))
q=np.array(json.load(open('cam4.json'))['q']);P=q[:9];HN,AL=q[10],q[11];MASTS=np.array(G['masts'])+q[12:].reshape(6,2);PC=np.array([4.7,-5.0])
def R(yaw,pitch_,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch_),math.sin(pitch_);cr,sr=math.cos(roll),math.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
C=P[:3];M=R(*P[3:6]);FO=P[6];CX,CY=P[7],P[8]
def proj(X):
    d=(np.atleast_2d(np.array(X,float))-C)@M.T;return np.stack([CX+FO*d[:,0]/d[:,2],CY-FO*d[:,1]/d[:,2]],1)
def ray(u,v):
    d=np.array([(u-CX)/FO,-(v-CY)/FO,1.0]);w=M.T@d;return w/np.linalg.norm(w)
def at_z(u,v,z=0.0):
    w=ray(u,v);t=(z-C[2])/w[2];return C+t*w
def at_xy(u,v,b):
    w=ray(u,v);A=np.array([[w[0]],[w[1]]]);rhs=np.array([b[0]-C[0],b[1]-C[1]]);t=np.linalg.lstsq(A,rhs,rcond=None)[0][0];return C+t*w
def height(base_uv,top_uv,zb=0.0):
    b=at_z(*base_uv,zb);return b,at_xy(*top_uv,b)[2]
def mast_pts(k):
    b=MASTS[k];inw=(PC-b)/np.linalg.norm(PC-b);return b,inw
def at_plane(u,v,p0,p1):
    """intersect the photo ray with the vertical plane through ground points p0,p1"""
    w=ray(u,v);p0=np.array(p0[:2],float);p1=np.array(p1[:2],float);e=p1-p0;n=np.array([-e[1],e[0]]);t=(n@(p0-C[:2]))/(n@w[:2]);return C+t*w
