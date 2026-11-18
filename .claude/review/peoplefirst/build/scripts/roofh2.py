import cv2,numpy as np,json
from meas import *
P=np.load('polar.npy');N=len(P);ang=2*np.pi*np.arange(N)/N;deg=np.degrees(ang)
ok=~np.isnan(P[:,0])&(P[:,2]>12)&~((deg>36)&(deg<104))
ph=cv2.imread('photo.png');hsv=cv2.cvtColor(ph,cv2.COLOR_BGR2HSV)
wm=((hsv[:,:,2]>175)&(hsv[:,:,1]<50)).astype(np.uint8)
def quads(i0,i1,hi,ho,pad=0.0):
    r=np.zeros(wm.shape,np.uint8)
    for i in range(i0,i1):
        i%=N;j=(i+1)%N
        if not(ok[i] and ok[j]):continue
        Q=[]
        for k,(rr,h) in enumerate([(P[i,0]-pad,hi),(P[j,0]-pad,hi),(P[j,1]+pad,ho),(P[i,1]+pad,ho)]):
            a=ang[i] if k in(0,3) else ang[j];Q.append((rr*np.cos(a),rr*np.sin(a),h))
        cv2.fillPoly(r,[pr(Q).astype(np.int32)],1)
    return r
res=[]
B=20  # 5 degree bins of 0.25 deg
for b0 in range(0,N,B):
    if ok[b0:b0+B].sum()<B*0.6:res.append((b0,None,None,0));continue
    best=None
    for hi in range(10,46,2):
        for ho in range(6,46,2):
            r=quads(b0,b0+B,hi,ho);reg=quads(b0,b0+B,hi,ho,pad=8)
            tp=(r&wm).sum();fp=r.sum()-tp;fn=((reg-r)&wm).sum()*0  # whites outside but near
            fn=((reg>0)&(r==0)&(wm>0)).sum()
            s=tp-fp-fn
            if best is None or s>best[0]:best=(s,hi,ho)
    res.append((b0,best[1],best[2],best[0]));print(b0/4,best[1:],flush=True)
json.dump(res,open('roofh2.json','w'))
