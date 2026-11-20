# python work/cmp2.py view out [x0,y0,x1,y1] [scale] : GE capture on top, the model render composited over it below
import sys,cv2,numpy as np
v,out=sys.argv[1],sys.argv[2];p=cv2.imread(f'ge/{v}.png');r=cv2.imread(f'rr/{v}.png',cv2.IMREAD_UNCHANGED)
a=r[:,:,3:4]/255.;c=(p*(1-a)+r[:,:,:3]*a).astype(np.uint8)
if len(sys.argv)>3: x0,y0,x1,y1=map(int,sys.argv[3].split(','));p=p[y0:y1,x0:x1];c=c[y0:y1,x0:x1]
im=np.vstack([p,c]);s=float(sys.argv[4]) if len(sys.argv)>4 else 0.6
cv2.imwrite(out,cv2.resize(im,None,fx=s,fy=s,interpolation=cv2.INTER_AREA))
