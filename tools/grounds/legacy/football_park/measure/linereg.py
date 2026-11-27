# linereg.py REF IMG OUT.json : affine IMG->REF from the painted field lines (ground level): phase correlation, then ECC
import sys,cv2,numpy as np,json
def lines(f):
    a=cv2.imread(f).astype(np.float32);g=a.mean(2)
    bg=cv2.medianBlur(g.astype(np.uint8),15).astype(np.float32);t=np.clip(g-bg,0,40)
    m=np.zeros_like(g);cv2.ellipse(m,(1000,990),(190,240),0,0,360,1,-1)
    return cv2.GaussianBlur(t*m,(0,0),1.2)
A=lines(sys.argv[1]);B=lines(sys.argv[2])
(dx,dy),r=cv2.phaseCorrelate(A,B)
W=np.array([[1,0,dx],[0,1,dy]],np.float32)
cc,W=cv2.findTransformECC(A,B,W,cv2.MOTION_AFFINE,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,500,1e-7),None,5)
print(sys.argv[2],'pc %.1f %.1f'%(dx,dy),'ecc %.3f'%cc,np.round(W,4).tolist())
json.dump({'W':W.tolist(),'cc':float(cc)},open(sys.argv[3],'w'))
