import sys, numpy as np, cv2
sys.path.insert(0,'tools')
from esri import m2px, ways
from planreg import m2pl
page=sys.argv[1]; x0,x1,y0,y1=map(int,sys.argv[2:6]); S=float(sys.argv[6]); out=sys.argv[7]
pl=cv2.imread('hplans/%s.png'%page,0)
W=int((x1-x0)*S); H=int((y1-y0)*S)
xs,ys=np.meshgrid(x0+np.arange(W)/S, y0+np.arange(H)/S)
a0=np.array(m2px(0,0)); ax=np.array(m2px(1,0))-a0; ay=np.array(m2px(0,1))-a0; J=np.linalg.inv(np.c_[ax,ay])
d=np.stack([xs-a0[0],ys-a0[1]],-1)@J.T; u,v=m2pl(d[...,0],d[...,1])
warp=cv2.remap(pl,u.astype(np.float32),v.astype(np.float32),cv2.INTER_LINEAR,borderValue=255)
o=cv2.cvtColor(warp,cv2.COLOR_GRAY2BGR)
for k,pts in ways().items():
    try: P=np.array([m2px(p[0],p[1]) for p in pts])
    except Exception: continue
    if not ((P[:,0]>x0)&(P[:,0]<x1)&(P[:,1]>y0)&(P[:,1]<y1)).any(): continue
    Q=((P-[x0,y0])*S).astype(np.int32); cv2.polylines(o,[Q],False,(0,160,0),2)
cv2.imwrite(out,o)
