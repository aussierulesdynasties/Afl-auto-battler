import numpy as np,json,math
exec(open('fitcam.py',encoding='utf-8').read().split('def md')[0])
p=np.array(json.load(open('cam.json'))['p']);C=p[:3];M=R(*p[3:6]);fo=p[6];cx0,cy0=p[7],p[8]
def ray(u,v):
    d=np.array([(u-cx0)/fo,-(v-cy0)/fo,1.0]);w=M.T@d;return w/np.linalg.norm(w)
def at_z(u,v,z=0.0):
    w=ray(u,v);t=(z-C[2])/w[2];return C+t*w
def height(base,top):
    b=at_z(*base,0.0);w=ray(*top)
    A=np.array([[w[0]],[w[1]]]);rhs=np.array([b[0]-C[0],b[1]-C[1]]);t=np.linalg.lstsq(A,rhs,rcond=None)[0][0]
    return b,(C+t*w)[2]
def pr(X):return proj(p,np.atleast_2d(np.array(X,float)))
PP=np.array(G['pitch']);PC=PP.mean(0)
from matplotlib.path import Path as _P
_PATH=_P(PP);_A=PP;_B=np.roll(PP,-1,0)
def dpitch(x,y):
    q=np.array([x,y]);d=_B-_A;t=np.clip(((q-_A)*d).sum(1)/np.maximum((d*d).sum(1),1e-9),0,1);m=np.hypot(*(_A+d*t[:,None]-q).T).min()
    return -m if _PATH.contains_point((x,y)) else m
def rim_fit(pts,zs=np.arange(0,40,0.25)):
    best=None
    for z in zs:
        ds=[dpitch(*at_z(u,v,z)[:2]) for u,v in pts];s=np.std(ds)
        if best is None or s<best[0]:best=(s,z,np.mean(ds))
    return best
