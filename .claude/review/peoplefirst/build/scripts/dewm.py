# remove the SkyePics tiled watermark: I = B(1-a) + a*C, a and C per logo pixel, solved across all tiles
import cv2,numpy as np,sys
src,dst=sys.argv[1],sys.argv[2]
I=cv2.imread(src).astype(np.float32);H,W=I.shape[:2]
g=cv2.cvtColor(I,cv2.COLOR_BGR2GRAY);hp=g-cv2.GaussianBlur(g,(0,0),3)
T=hp[640:690,915:1120]
r=cv2.matchTemplate(hp,T,cv2.TM_CCOEFF_NORMED)
# grid from detections
xs=[182,549,915,1281,1647];ys=[207,408,640,874,1109]
locs=[]
for y in ys:
    for x in xs:
        # refine within +-3
        sub=r[y-3:y+4,x-3:x+4];dy,dx=np.unravel_index(sub.argmax(),sub.shape);locs.append((x-3+dx,y-3+dy))
X0,Y0,X1,Y1=-60,-70,250,80
def tile(A,x,y):
    return A[y+Y0:y+Y1,x+X0:x+X1]
ok=[(x,y) for x,y in locs if x+X0>=0 and y+Y0>=0 and x+X1<=W and y+Y1<=H]
B=cv2.medianBlur(I.astype(np.uint8),15).astype(np.float32)
D=[];BB=[];WT=[]
for x,y in ok:
    It=tile(I,x,y);Bt=tile(B,x,y)
    var=cv2.blur((tile(g,x,y)-cv2.GaussianBlur(tile(g,x,y),(0,0),6))**2,(25,25))
    D.append(It-Bt);BB.append(Bt);WT.append(1.0/(1.0+var)[...,None].repeat(3,2))
D=np.array(D);BB=np.array(BB);WT=np.array(WT)
# white part: D = a(255-B); dark part: D = -a B. Fit both, keep the one that explains more.
Kw=255-BB
aw=(WT*D*Kw).sum((0,3))/np.maximum((WT*Kw*Kw).sum((0,3)),1e-3)
ab=-(WT*D*BB).sum((0,3))/np.maximum((WT*BB*BB).sum((0,3)),1e-3)
ew=(WT*(D-aw[None,...,None]*Kw)**2).sum((0,3));eb=(WT*(D+ab[None,...,None]*BB)**2).sum((0,3))
white=(ew<=eb)&(aw>0)
a=np.where(white,np.clip(aw,0,0.9),np.clip(ab,0,0.9));a[a<0.015]=0
Cc=np.where(white,255.0,0.0)
u=(a*Cc)[...,None].repeat(3,2)
np.save('wm_a.npy',a);np.save('wm_u.npy',u)
O=I.copy()
for x,y in locs:
    x0,y0=max(0,x+X0),max(0,y+Y0);x1,y1=min(W,x+X1),min(H,y+Y1)
    aa=a[y0-(y+Y0):y1-(y+Y0),x0-(x+X0):x1-(x+X0)][...,None];uu=u[y0-(y+Y0):y1-(y+Y0),x0-(x+X0):x1-(x+X0)]
    O[y0:y1,x0:x1]=(I[y0:y1,x0:x1]-uu)/(1-aa)
cv2.imwrite(dst,np.clip(O,0,255).astype(np.uint8))
cv2.imwrite('wm_alpha.png',(a*255*3).clip(0,255).astype(np.uint8))
print(len(ok),'tiles used; a max',a.max())
