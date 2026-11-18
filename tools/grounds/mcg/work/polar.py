# polar unwrap of the satellite around (cx,cy): rows = bearing (deg from north, clockwise) 4 px/deg, cols = radius 0.25 m/px
import cv2,numpy as np,sys
cx,cy=float(sys.argv[1]),float(sys.argv[2]);r0,r1=50,190
I=cv2.imread('sat/esri_025.png');H=260;R=0.25
az=np.arange(0,360,0.25);rr=np.arange(r0,r1,0.25)
A,RR=np.meshgrid(np.radians(az),rr,indexing='ij')
X=cx+RR*np.sin(A);Y=cy+RR*np.cos(A)
P=cv2.remap(I,((X+H)/R).astype(np.float32),((H-Y)/R).astype(np.float32),cv2.INTER_LINEAR)
for i,a in enumerate(range(0,360,90)):
  seg=P[a*4:(a+90)*4].copy()
  for d in range(0,91,5):
    y=d*4;cv2.line(seg,(0,y),(seg.shape[1],y),(0,255,255) if d%15==0 else (160,160,160),1);cv2.putText(seg,str(a+d),(2,y+11),0,0.4,(0,255,255),1)
  for r in range(r0,r1,10):
    x=int((r-r0)/0.25);cv2.line(seg,(x,0),(x,seg.shape[0]),(0,255,255) if r%50==0 else (160,160,160),1);cv2.putText(seg,str(r),(x+2,12),0,0.4,(0,255,255),1)
  cv2.imwrite(f'work/polar{a:03d}.png',seg)
np.save('work/polar.npy',P)
