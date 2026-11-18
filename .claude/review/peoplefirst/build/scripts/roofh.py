import cv2,numpy as np,json
from meas import *
P=np.load('polar.npy');N=len(P);ang=2*np.pi*np.arange(N)/N
ok=~np.isnan(P[:,0])&(P[:,2]>18)
ph=cv2.imread('photo.png');hsv=cv2.cvtColor(ph,cv2.COLOR_BGR2HSV)
wm=((hsv[:,:,2]>175)&(hsv[:,:,1]<50)).astype(np.uint8)
def render(hi,ho):
    r=np.zeros(wm.shape,np.uint8)
    for i in range(N):
        j=(i+1)%N
        if not(ok[i] and ok[j]):continue
        Q=[]
        for k,(rr,h) in enumerate([(P[i,0],hi),(P[j,0],hi),(P[j,1],ho),(P[i,1],ho)]):
            a=ang[i] if k in(0,3) else ang[j];Q.append((rr*np.cos(a),rr*np.sin(a),h))
        q=pr(Q).astype(np.int32);cv2.fillPoly(r,[q],1)
    return r
best=None
for hi in range(14,42,3):
    for ho in range(8,42,3):
        r=render(hi,ho);inter=(r&wm).sum();uni=(r|wm)[r>0].size+0;iou=inter/(r.sum()+1e-9);fp=1-iou
        # recall of roof-white pixels near the ring: use dilated region
        reg=cv2.dilate(r,np.ones((61,61),np.uint8));rec=inter/((wm&reg).sum()+1e-9)
        s=iou*rec
        if best is None or s>best[0]:best=(s,hi,ho,iou,rec)
print(best)
s,hi,ho,_,_=best;r=render(hi,ho)
ov=ph.copy();e=cv2.Canny(r*255,50,150);ov[e>0]=(0,0,255);cv2.imwrite('roofh.jpg',cv2.resize(ov,(1400,933)))
json.dump({'hi':hi,'ho':ho},open('roofh.json','w'))
