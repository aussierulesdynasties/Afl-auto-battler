# fuse2: fill A's cable pixels from aligned B where B matches A's surroundings; inpaint the rest.
# python fuse2.py A Baligned "lines" out [width]
import sys,cv2,numpy as np
A=cv2.imread(sys.argv[1]).astype(np.float32);B=cv2.imread(sys.argv[2]).astype(np.float32);w=int(sys.argv[5]) if len(sys.argv)>5 else 5
h,W=A.shape[:2];m=np.zeros((h,W),np.uint8)
for s in sys.argv[3].split():
    x1,y1,x2,y2=map(float,s.split(','));cv2.line(m,(round(x1*8),round(y1*8)),(round(x2*8),round(y2*8)),255,w,cv2.LINE_8,3)
k=(m==0).astype(np.float32)
def bh(I):
    g=cv2.cvtColor(I.astype(np.uint8),cv2.COLOR_BGR2GRAY).astype(np.float32)
    return cv2.morphologyEx(g,cv2.MORPH_BLACKHAT,np.ones((7,7),np.uint8))
bA,bB=bh(A),bh(B)
bval=cv2.erode((B.sum(2)>30).astype(np.uint8),np.ones((5,5),np.uint8))
mbl=np.zeros((h,W),np.uint8)
for q in (sys.argv[6].split() if len(sys.argv)>6 else []):
    x1,y1,x2,y2=map(float,q.split(','));cv2.line(mbl,(round(x1*8),round(y1*8)),(round(x2*8),round(y2*8)),1,7,cv2.LINE_8,3)
bcab=(((bB>18)&(bA<10))|(bval==0)|(mbl>0)).astype(np.uint8)          # thin dark in B that A lacks = B's own cable
bcab=cv2.dilate(bcab,np.ones((3,3),np.uint8))
kb=k*(1-bcab)
r=31;Bt=np.zeros_like(A)
for c in range(3):
    def mom(X,K):
        n=cv2.boxFilter(K,-1,(r,r),normalize=False)+1e-3
        mu=cv2.boxFilter(X*K,-1,(r,r),normalize=False)/n
        v=cv2.boxFilter(X*X*K,-1,(r,r),normalize=False)/n-mu*mu
        return mu,np.sqrt(np.maximum(v,1))
    mA,sA=mom(A[...,c],kb);mB,sB=mom(B[...,c],kb)
    Bt[...,c]=(B[...,c]-mB)*np.clip(sA/sB,.5,2)+mA
# agreement: local mean abs diff between A and Bt on valid pixels (7x7)
d=np.abs(A-Bt).mean(2)*kb
agree=cv2.boxFilter(d,-1,(9,9),normalize=False)/(cv2.boxFilter(kb,-1,(9,9),normalize=False)+1e-3)
yy=np.arange(h)[:,None]*np.ones((1,W));solid=(yy<44)|(yy>=104)
use=(m>0)&(bcab==0)&((agree<14)|(solid&(agree<30)))
o=A.copy();o[use]=Bt[use]
rowf=(m>0)&~use&solid&~((yy>=104)&(yy<132))
for y in np.unique(np.nonzero(rowf)[0]):
    bad=(m[y]>0)&~use[y];xs=np.nonzero(~bad)[0]
    for c in range(3): o[y,bad,c]=np.interp(np.nonzero(bad)[0],xs,o[y,xs,c])
    use[y]|=rowf[y]
rest=((m>0)&~use).astype(np.uint8)*255
o=cv2.inpaint(np.clip(o,0,255).astype(np.uint8),rest,5,cv2.INPAINT_NS)
mb=cv2.GaussianBlur((m>0).astype(np.float32),(0,0),0.7)[...,None]
out=(A*(1-mb)+o*mb).clip(0,255).astype(np.uint8)
cv2.imwrite(sys.argv[4],out)
dbg=cv2.cvtColor(rest,cv2.COLOR_GRAY2BGR);dbg[use]=(0,255,0);cv2.imwrite(sys.argv[4]+'.dbg.png',dbg)
print('masked',int((m>0).sum()),'fromB',int(use.sum()),'inpaint',int((rest>0).sum()))
