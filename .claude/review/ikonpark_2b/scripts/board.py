# board.py RENDER SAT OUT TITLE -> left: satellite with model outline (red) and model edges (yellow); right: 50% blend
import cv2,sys,numpy as np
r=cv2.imread(sys.argv[1],cv2.IMREAD_UNCHANGED);s=cv2.imread(sys.argv[2])
a=r[:,:,3]>0;e=cv2.dilate(cv2.Canny((a*255).astype(np.uint8),50,150),np.ones((2,2)))>0
g=cv2.cvtColor(r[:,:,:3],cv2.COLOR_BGR2GRAY);e2=cv2.Canny(g,40,120)>0
L=s.copy();L[e2&a]=(0,255,255);L[e]=(0,0,255)
Rr=s.copy();Rr[a]=(0.5*s[a]+0.5*r[:,:,:3][a]).astype(np.uint8)
c=slice(100,1500)
o=np.hstack([L[c,c],np.full((1400,10,3),255,np.uint8),Rr[c,c]])
o=np.vstack([np.zeros((50,o.shape[1],3),np.uint8),o]);cv2.putText(o,sys.argv[4],(12,36),0,1.0,(255,255,255),2)
for x in range(-125,226,25):
  u=int((x+150)/0.25)-100
  if 0<=u<1400:cv2.putText(o,str(x),(u,70),0,0.45,(0,200,255),1)
cv2.imwrite(sys.argv[3],cv2.resize(o,None,fx=0.75,fy=0.75,interpolation=cv2.INTER_AREA))
