# bright roof regions on the z19 satellite -> polygons in field metres (x east, y north)
import cv2,numpy as np,json
from geo import *
im=cv2.imread('sat/sat19.png');hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
v=hsv[...,2].astype(int);s=hsv[...,1].astype(int)
mask=((v>185)&(s<40)).astype(np.uint8)*255
mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
c0=m2px(0,0);m=J['mpp']
def px2m(u,w):return ((u-c0[0])*m,(c0[1]-w)*m)
cs,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
out=[];vis=im.copy()
for c in cs:
    a=cv2.contourArea(c)*m*m
    if a<25:continue
    ap=cv2.approxPolyDP(c,0.6/m,True)[:,0,:]
    P=[px2m(u,w) for u,w in ap];cx=np.mean([p[0] for p in P]);cy=np.mean([p[1] for p in P])
    if abs(cx)>160 or abs(cy)>160:continue
    out.append({'area':round(a),'c':[round(cx,1),round(cy,1)],'pts':[[round(x,2),round(y,2)] for x,y in P]})
    cv2.polylines(vis,[ap.reshape(-1,1,2)],True,(0,0,255),2);cv2.putText(vis,str(len(out)-1),tuple(ap[0]),0,1.2,(0,255,255),2)
json.dump(out,open('sat/roofs.json','w'),indent=0)
for i,o in enumerate(out):print(i,o['area'],o['c'],len(o['pts']))
cx,cy=map(int,c0);cv2.imwrite('sat/roofs_vis.jpg',vis[cy-620:cy+620,cx-620:cx+620])
