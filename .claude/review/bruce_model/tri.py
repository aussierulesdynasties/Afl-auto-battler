import numpy as np,json,math
from fit import R
def mk(path,W,H):
    p=np.array(json.load(open(path))['p']);M=R(*p[3:6])
    def ray(u,v):
        d=np.array([(u-W/2)/p[6],-(v-H/2)/p[6],1.0]);w=M.T@d;return p[:3],w/np.linalg.norm(w)
    def pr(X):
        d=(np.atleast_2d(X)-p[:3])@M.T;return np.stack([W/2+p[6]*d[:,0]/d[:,2],H/2-p[6]*d[:,1]/d[:,2]],1)
    return ray,pr
ray46,pr46=mk('cam2.json',1936,1290);ray50,pr50=mk('cam50.json',1933,1290)
def tri(a,b):
    c1,d1=ray46(*a);c2,d2=ray50(*b)
    A=np.array([[d1@d1,-d1@d2],[d1@d2,-d2@d2]]);r=c2-c1;t=np.linalg.solve(A,[d1@r,d2@r])
    X1=c1+t[0]*d1;X2=c2+t[1]*d2;X=(X1+X2)/2
    return X,np.linalg.norm(pr46(X)[0]-a),np.linalg.norm(pr50(X)[0]-b)
if __name__=='__main__':
    import sys
    pts=json.load(open(sys.argv[1]))
    for k,(a,b) in pts.items():
        X,e1,e2=tri(a,b);print(k,np.round(X,1),'err px',round(e1,1),round(e2,1))
