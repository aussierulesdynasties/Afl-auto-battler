import numpy as np,json,math
from fitcam import R,proj,W,Hh
p=np.array(json.load(open('cam.json'))['p']);C=p[:3];M=R(*p[3:6]);fo=p[6]
def ray(u,v):
    d=np.array([(u-W/2)/fo,-(v-Hh/2)/fo,1.0]);w=M.T@d;return w/np.linalg.norm(w)
def at_z(u,v,z=0.0):
    w=ray(u,v);t=(z-C[2])/w[2];return C+t*w
def height(base,top,zb=0.0):
    b=at_z(*base,zb);w=ray(*top);A=np.array([[w[0]],[w[1]]]);rhs=np.array([b[0]-C[0],b[1]-C[1]]);t=np.linalg.lstsq(A,rhs,rcond=None)[0][0]
    return b,(C+t*w)[2]
def pr(X):return proj(p,np.atleast_2d(np.array(X,float)))
