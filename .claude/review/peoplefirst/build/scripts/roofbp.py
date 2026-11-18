import cv2,numpy as np,json
from meas import *
ph=cv2.imread('photo.png');hsv=cv2.cvtColor(ph,cv2.COLOR_BGR2HSV)
wm=((hsv[:,:,2]>170)&(hsv[:,:,1]<55)).astype(np.uint8)
wm=cv2.morphologyEx(wm,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
n,lab,st,_=cv2.connectedComponentsWithStats(wm);big=np.argsort(st[:,4])[::-1][:4];wm=(lab==big[1]).astype(np.uint8);cv2.imwrite('wm_roof.png',wm*255)
P=np.load('polar.npy');N=len(P);deg=np.arange(N)/4
def edges(h,which):
    rs=np.arange(55,160,0.25);out=np.full(N,np.nan)
    for i in range(0,N,2):
        a=np.radians(deg[i]);X=np.stack([rs*np.cos(a),rs*np.sin(a),np.full_like(rs,h)],1);q=pr(X).round().astype(int)
        okk=(q[:,0]>=0)&(q[:,0]<2000)&(q[:,1]>=0)&(q[:,1]<1333);on=np.zeros(len(rs),bool);on[okk]=wm[q[okk,1],q[okk,0]]>0
        if on.sum()<10:continue
        # take the run nearest the sat radii
        d=np.diff(np.concatenate([[0],on.astype(int),[0]]));st_=np.where(d==1)[0];en=np.where(d==-1)[0];k=np.argmax(en-st_)
        out[i]=rs[st_[k]] if which==0 else rs[en[k]-1]
    return out
np.save('wm.npy',wm)
for which in (0,1):
    best=[]
    for h in range(10,44,2):
        e=edges(h,which);s=P[:,which]
        for lo,hi_ in ((105,150),(200,250),(290,340),(0,30)):
            m=(deg>=lo)&(deg<hi_)&~np.isnan(e)&~np.isnan(s)
            best.append((lo,h,np.median(np.abs(e[m]-s[m])) if m.sum() else 99))
    import collections;D=collections.defaultdict(list)
    for lo,h,v in best:D[lo].append((round(v,1),h))
    for lo in D:print('inner' if which==0 else 'outer',lo,sorted(D[lo])[:3])
