import sys,cv2,numpy as np
x0,y0,x1,y1=map(int,sys.argv[1].split(','));out=sys.argv[2];k=4
a=cv2.imread('refs/scg.jpg')[y0:y1,x0:x1];b=cv2.imread('out/r0.png')[y0:y1,x0:x1]
a=cv2.resize(a,None,fx=k,fy=k,interpolation=cv2.INTER_CUBIC);b=cv2.resize(b,None,fx=k,fy=k,interpolation=cv2.INTER_NEAREST)
e=cv2.Canny(cv2.cvtColor(b,cv2.COLOR_BGR2GRAY),30,90);e=cv2.dilate(e,np.ones((2,2),np.uint8))
o=a.copy();o[e>0]=(0,0,255)
for x in range(x0-x0%10,x1,10):
    X=(x-x0)*k
    if X>=0:cv2.line(o,(X,0),(X,o.shape[0]),(255,255,0) if x%50==0 else (90,90,0),1)
    if x%50==0 and X>=0:cv2.putText(o,str(x),(X+2,14),0,0.45,(255,255,0),1)
for y in range(y0-y0%10,y1,10):
    Y=(y-y0)*k
    if Y>=0:cv2.line(o,(0,Y),(o.shape[1],Y),(255,255,0) if y%50==0 else (90,90,0),1)
    if y%50==0 and Y>=0:cv2.putText(o,str(y),(2,Y-2),0,0.45,(255,255,0),1)
cv2.imwrite(out,o)
