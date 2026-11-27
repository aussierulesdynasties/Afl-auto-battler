# reg.py REF IMG OUT.png : similarity IMG->REF from template matches on the gradient image outside the oval; writes the warped IMG
import cv2,numpy as np,sys
def prep(f):
    g=cv2.GaussianBlur(cv2.imread(f,0).astype(np.float32),(0,0),1.5);return g-cv2.GaussianBlur(g,(0,0),12)
A=prep(sys.argv[1]);B=prep(sys.argv[2]);P=[]
sa=cv2.resize(A,None,fx=0.25,fy=0.25);sb=cv2.resize(B,None,fx=0.25,fy=0.25);w=cv2.createHanningWindow(sa.shape[::-1],cv2.CV_32F)
(dx,dy),_=cv2.phaseCorrelate(sa,sb,w);dx=int(round(dx*4));dy=int(round(dy*4))
for y in range(300,1700,70):
    for x in range(300,1700,70):
        if ((x-880)/300)**2+((y-960)/300)**2<1.1: continue
        t=A[y-50:y+50,x-50:x+50]
        if t.std()<6: continue
        yy,xx=y+dy,x+dx
        if not (110<=yy<B.shape[0]-110 and 110<=xx<B.shape[1]-110): continue
        S=B[yy-110:yy+110,xx-110:xx+110];res=cv2.matchTemplate(S,t,cv2.TM_CCOEFF_NORMED);_,mx,_,ml=cv2.minMaxLoc(res)
        if mx>0.4: P.append((xx-110+ml[0]+50,yy-110+ml[1]+50,x,y))
P=np.float32(P);M,inl=cv2.estimateAffinePartial2D(np.ascontiguousarray(P[:,:2]),np.ascontiguousarray(P[:,2:]),ransacReprojThreshold=2)
r=np.hypot(*((P[:,:2]@M[:,:2].T+M[:,2])-P[:,2:]).T)[inl[:,0]>0]
print(sys.argv[2],len(P),int(inl.sum()),'scale %.4f rot %.3f shift %.1f %.1f rms %.2f'%(np.hypot(M[0,0],M[1,0]),np.degrees(np.arctan2(M[1,0],M[0,0])),M[0,2],M[1,2],np.sqrt((r**2).mean())))
b=cv2.imread(sys.argv[2]);cv2.imwrite(sys.argv[3],cv2.warpAffine(b,M,(b.shape[1],b.shape[0])))
