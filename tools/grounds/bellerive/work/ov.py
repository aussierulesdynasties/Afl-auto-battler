# python work/ov.py view out [x0,y0,x1,y1] : GE capture with the model render's edges (red) and a 50% blend side by side
import sys,cv2,numpy as np
v,out=sys.argv[1],sys.argv[2];p=cv2.imread(f'ge/{v}.png');r=cv2.imread(f'rr/{v}.png',cv2.IMREAD_UNCHANGED)
a=r[:,:,3:4]/255.;bl=(p*(1-0.6*a)+r[:,:,:3]*0.6*a).astype(np.uint8)
e=cv2.Canny(cv2.cvtColor(r[:,:,:3],cv2.COLOR_BGR2GRAY),40,120)|cv2.Canny(r[:,:,3],50,150);ov=p.copy();ov[e>0]=(0,0,255)
if len(sys.argv)>3:
  x0,y0,x1,y1=map(int,sys.argv[3].split(','));ov=ov[y0:y1,x0:x1];bl=bl[y0:y1,x0:x1]
cv2.imwrite(out,np.vstack([ov,bl]) if ov.shape[1]>ov.shape[0]*1.3 else np.hstack([ov,bl]))
