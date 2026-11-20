# python work/polgrid.py : Esri mosaic with polar grid (bearing lines every 5 deg, rings every 10 m) -> sat/pg_*.png crops
import cv2,numpy as np,math
S=cv2.imread('sat/esri_025.png');o=S.copy();H=800
px=lambda x,y:(int(round(H+x*4)),int(round(H-y*4)))
for r in range(60,171,10):cv2.circle(o,(H,H),r*4,(0,255,255) if r%50 else (0,128,255),1)
for b in range(0,360,5):
  a=math.radians(b);cv2.line(o,px(55*math.sin(a),55*math.cos(a)),px(175*math.sin(a),175*math.cos(a)),(255,255,0) if b%15 else (255,0,255),1)
  if b%15==0:cv2.putText(o,str(b),px(58*math.sin(a),58*math.cos(a)),0,0.5,(255,0,255),1)
for r in range(60,171,10):
  for b in (0,90,180,270):cv2.putText(o,str(r),px(r*math.sin(math.radians(b+2)),r*math.cos(math.radians(b+2))),0,0.4,(0,255,255),1)
cv2.imwrite('sat/pg_full.png',o)
for n,(x0,y0,x1,y1) in dict(nw=(-150,150,0,0),ne=(0,150,150,0),sw=(-150,0,0,-150),se=(0,0,150,-150)).items():
  a=px(x0,y0);b=px(x1,y1);cv2.imwrite(f'sat/pg_{n}.png',o[a[1]:b[1],a[0]:b[0]])
