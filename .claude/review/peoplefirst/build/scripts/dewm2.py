# watermark removal, gain/offset model: I = k*B + m per logo pixel and channel, fitted over the 25 tiles
import cv2,numpy as np,sys
src,dst=sys.argv[1],sys.argv[2]
I=cv2.imread(src).astype(np.float32);H,W=I.shape[:2]
g=cv2.cvtColor(I,cv2.COLOR_BGR2GRAY);hp=g-cv2.GaussianBlur(g,(0,0),3)
r=cv2.matchTemplate(hp,hp[640:690,915:1120],cv2.TM_CCOEFF_NORMED)
xs=[182,549,915,1281,1647];ys=[207,408,640,874,1109];locs=[]
for y in ys:
    for x in xs:
        sub=r[y-3:y+4,x-3:x+4];dy,dx=np.unravel_index(sub.argmax(),sub.shape);locs.append((x-3+dx,y-3+dy))
X0,Y0,X1,Y1=-60,-70,250,80
a0=np.load('wm_a.npy')
mask=((a0>0.01).astype(np.uint8))*255;mask=cv2.dilate(mask,np.ones((5,5),np.uint8))
M=np.zeros((H,W),np.uint8)
for x,y in locs:
    x0,y0=max(0,x+X0),max(0,y+Y0);x1,y1=min(W,x+X1),min(H,y+Y1)
    M[y0:y1,x0:x1]|=mask[y0-(y+Y0):y1-(y+Y0),x0-(x+X0):x1-(x+X0)]
B=cv2.inpaint(I.astype(np.uint8),M,5,cv2.INPAINT_TELEA).astype(np.float32)
ok=[(x,y) for x,y in locs if x+X0>=0 and y+Y0>=0 and x+X1<=W and y+Y1<=H]
T=lambda A,x,y:A[y+Y0:y+Y1,x+X0:x+X1]
Bs=np.array([T(B,x,y) for x,y in ok]);Is=np.array([T(I,x,y) for x,y in ok])
wt=np.array([1/(1+cv2.blur((T(g,x,y)-cv2.GaussianBlur(T(g,x,y),(0,0),6))**2,(31,31))) for x,y in ok])[...,None]
Sw=wt.sum(0);Sb=(wt*Bs).sum(0);Si=(wt*Is).sum(0);Sbb=(wt*Bs*Bs).sum(0);Sbi=(wt*Bs*Is).sum(0)
den=Sw*Sbb-Sb*Sb
k=np.where(den>1e-3,(Sw*Sbi-Sb*Si)/np.maximum(den,1e-3),1.0);k=np.clip(k,0.3,1.5)
m=(Si-k*Sb)/Sw
inl=(mask>0)[...,None]
k=np.where(inl,k,1.0);m=np.where(inl,m,0.0)
O=I.copy()
for x,y in locs:
    x0,y0=max(0,x+X0),max(0,y+Y0);x1,y1=min(W,x+X1),min(H,y+Y1)
    kk=k[y0-(y+Y0):y1-(y+Y0),x0-(x+X0):x1-(x+X0)];mm=m[y0-(y+Y0):y1-(y+Y0),x0-(x+X0):x1-(x+X0)]
    O[y0:y1,x0:x1]=(I[y0:y1,x0:x1]-mm)/kk
gB=cv2.cvtColor(B,cv2.COLOR_BGR2GRAY);tex=np.sqrt(cv2.blur((gB-cv2.GaussianBlur(gB,(0,0),2))**2,(9,9)))
wS=np.clip((12-tex)/8,0,1)[...,None]*(M>0)[...,None]
O=O*(1-wS)+B*wS
cv2.imwrite(dst,np.clip(O,0,255).astype(np.uint8))
print('k range',k[inl[...,0]].min(),k[inl[...,0]].max())
