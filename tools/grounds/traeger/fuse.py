# fuse: align B onto A (ECC homography), colour-match, and fill A's masked lines from B.
# python fuse.py A B "lines" out [width]
import sys,cv2,numpy as np
A=cv2.imread(sys.argv[1]);B=cv2.imread(sys.argv[2]);w=int(sys.argv[5]) if len(sys.argv)>5 else 4
ga=cv2.cvtColor(A,cv2.COLOR_BGR2GRAY).astype(np.float32)/255;gb=cv2.cvtColor(B,cv2.COLOR_BGR2GRAY).astype(np.float32)/255
Wm=np.eye(3,dtype=np.float32)
cc,Wm=cv2.findTransformECC(ga,gb,Wm,cv2.MOTION_HOMOGRAPHY,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,500,1e-6),None,5)
Bw=cv2.warpPerspective(B,Wm,(A.shape[1],A.shape[0]),flags=cv2.INTER_CUBIC|cv2.WARP_INVERSE_MAP)
print('ecc',round(cc,3))
m=np.zeros(A.shape[:2],np.uint8)
for s in sys.argv[3].split():
    x1,y1,x2,y2=map(float,s.split(','));cv2.line(m,(round(x1),round(y1)),(round(x2),round(y2)),255,w)
# colour match B to A per channel on unmasked pixels
o=A.astype(np.float32).copy();k=(m==0)
for c in range(3):
    a=A[...,c][k].astype(np.float32);b=Bw[...,c][k].astype(np.float32);p=np.polyfit(b,a,1)
    o[...,c]=np.where(m>0,np.clip(p[0]*Bw[...,c]+p[1],0,255),o[...,c])
# feather the patch edges
mb=cv2.GaussianBlur(m.astype(np.float32)/255,(0,0),0.8)[...,None]
out=(A*(1-mb)+o*mb).clip(0,255).astype(np.uint8);cv2.imwrite(sys.argv[4],out);cv2.imwrite(sys.argv[4]+'.B.png',Bw)
