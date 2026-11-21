# python work/sb.py view [scale] : photo above render (rr/), saved to work/sb_<view>.png
import sys,cv2,numpy as np
v=sys.argv[1];s=float(sys.argv[2]) if len(sys.argv)>2 else 0.5
p=cv2.imread(f'ge/{v}.png');r=cv2.imread(f'rr/{v}.png',cv2.IMREAD_UNCHANGED)
a=r[:,:,3:4]/255.;ren=(r[:,:,:3]*a+np.array([60,60,60])*(1-a)).astype(np.uint8)
o=np.vstack([cv2.resize(p,None,fx=s,fy=s),cv2.resize(ren,None,fx=s,fy=s)]);cv2.imwrite(f'work/sb_{v}.png',o)
