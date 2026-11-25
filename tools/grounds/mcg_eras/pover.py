# Polar strip with traced points overlaid (bearing,r) in green.
import cv2,numpy as np,sys,json
import pview
def over(f,b0,b1,r0,r1,pts,out,db=0.1,dr=0.2):
    pview.view(f,b0,b1,r0,r1,out); p=cv2.imread(out)
    for b,r in pts:
        bb=b if b>=b0 else b+360
        if not(b0<=bb<=b1): continue
        x=int((bb-b0)/db); y=int((r1-r)/dr); cv2.circle(p,(x,y),3,(0,255,0),-1)
    p=cv2.resize(p,(p.shape[1]*2,p.shape[0]*2),interpolation=cv2.INTER_NEAREST); cv2.imwrite(out,p)
if __name__=='__main__':
    pts=np.loadtxt(sys.argv[7])[:,:2]
    over(sys.argv[1],*map(float,sys.argv[2:6]),pts,sys.argv[6])
