import sys,json,numpy as np
from gpaint_cam import R
p=json.load(open('cam.json'))['p'];C=np.array(p[:3]);M=R(*p[3:6]);f=p[6];W,H=2000,1333
def pr(X):
    d=M@(np.array(X,float)-C);return (round(W/2+f*d[0]/d[2],1),round(H/2-f*d[1]/d[2],1))
def un(u,v,z):
    d=np.array([(u-W/2)/f,-(v-H/2)/f,1.0]);w=M.T@d;t=(z-C[2])/w[2];X=C+t*w;return (round(X[0],1),round(X[1],1))
if __name__=='__main__':
    z=float(sys.argv[1]);pts=sys.argv[2:]
    for q in pts:u,v=map(float,q.split(','));print(q,'->',un(u,v,z))
