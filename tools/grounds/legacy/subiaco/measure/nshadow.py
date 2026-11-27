# North stands: roof front edge height from its shadow on the turf (2008-05-18), along the shadow-minus-lean direction
import cv2,numpy as np,json
mpp=0.2945;im=cv2.imread('hist_14.png').astype(np.float32);L=cv2.GaussianBlur(im.mean(2),(0,0),0.8)
s=np.array([-10.1,82.2])/65;l=np.array([2.1,-0.85])/65;d=s-l;n=np.linalg.norm(d);u=d/n
out=[]
for x0 in range(640,1250,4):
    t=np.arange(0,420,0.25);X=x0+t*u[0];Y=600+t*u[1]
    v=cv2.remap(L,X.astype(np.float32)[None],Y.astype(np.float32)[None],cv2.INTER_LINEAR)[0]
    bright=v>150;dark=v<45
    # roof front: last bright run (>=6 px) followed by a dark run (>=6 px)
    k=None
    for i in range(24,len(v)-24):
        if bright[i-24:i].mean()>0.9 and dark[i+8:i+32].mean()>0.9:k=i+4;break
    if k is None:continue
    j=None
    for i in range(k+24,len(v)-24):
        if dark[i-24:i].mean()>0.9 and (v[i+8:i+32]>50).mean()>0.9:j=i+4;break
    if j is None:continue
    h=(t[j]-t[k])*mpp/n
    out.append([x0,float(X[k]),float(Y[k]),float(X[j]),float(Y[j]),round(h,2)])
json.dump(out,open('z/north_h.json','w'))
P=cv2.imread('hist_14.png')
for o in out:
    cv2.circle(P,(int(o[1]),int(o[2])),2,(0,0,255),-1);cv2.circle(P,(int(o[3]),int(o[4])),2,(255,0,255),-1)
cv2.imwrite('z/north_h.jpg',P[600:1100,600:1300])
for o in out[::6]:print(o)
