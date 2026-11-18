# generic SkyePics de-watermark: find the logo grid by template, estimate the logo mask from the tiles, then the dewm2 gain/offset fit
# python dewm3.py in out "x0,y0,w,h of one logo" "xs" "ys"
import cv2,numpy as np,sys
src,dst=sys.argv[1],sys.argv[2];bx,by,bw,bh=map(int,sys.argv[3].split(','))
xs=list(map(int,sys.argv[4].split(',')));ys=list(map(int,sys.argv[5].split(',')))
I=cv2.imread(src).astype(np.float32);H,W=I.shape[:2]
g=cv2.cvtColor(I,cv2.COLOR_BGR2GRAY);hp=g-cv2.GaussianBlur(g,(0,0),3)
P=12;X0,Y0,X1,Y1=-P,-P,bw+P,bh+P
tpl=hp[by:by+bh,bx:bx+bw];r=cv2.matchTemplate(hp,tpl,cv2.TM_CCOEFF_NORMED)
locs=[]
for y in ys:
    for x in xs:
        y0,x0=max(0,y-3),max(0,x-3);sub=r[y0:y+4,x0:x+4]
        if sub.size==0:continue
        dy,dx=np.unravel_index(sub.argmax(),sub.shape);locs.append((x0+dx,y0+dy,float(sub.max())))
print('match scores',np.round([l[2] for l in locs],2).tolist())
locs=[(x,y) for x,y,s in locs]
ok=[(x,y) for x,y in locs if x+X0>=0 and y+Y0>=0 and x+X1<=W and y+Y1<=H]
T=lambda A,x,y:A[y+Y0:y+Y1,x+X0:x+X1]
# logo mask: the consistent part of the high-pass across tiles (median), plus the bright text core
med=np.median(np.array([T(hp,x,y) for x,y in ok]),0)
mask=(np.abs(med)>8).astype(np.uint8)*255
n,lab,st,_=cv2.connectedComponentsWithStats(mask)
for i in range(1,n):
    if st[i,4]<20:mask[lab==i]=0
mask=cv2.dilate(mask,np.ones((5,5),np.uint8));print('mask share',(mask>0).mean())
cv2.imwrite(dst+'_mask.png',mask)
M=np.zeros((H,W),np.uint8)
for x,y in locs:
    x0,y0=max(0,x+X0),max(0,y+Y0);x1,y1=min(W,x+X1),min(H,y+Y1)
    M[y0:y1,x0:x1]|=mask[y0-(y+Y0):y1-(y+Y0),x0-(x+X0):x1-(x+X0)]
B=cv2.inpaint(I.astype(np.uint8),M,5,cv2.INPAINT_TELEA).astype(np.float32)
Bs=np.array([T(B,x,y) for x,y in ok]);Is=np.array([T(I,x,y) for x,y in ok])
wt=np.array([1/(1+cv2.blur((T(g,x,y)-cv2.GaussianBlur(T(g,x,y),(0,0),6))**2,(31,31))) for x,y in ok])[...,None]
Sw=wt.sum(0);Sb=(wt*Bs).sum(0);Si=(wt*Is).sum(0);Sbb=(wt*Bs*Bs).sum(0);Sbi=(wt*Bs*Is).sum(0)
den=Sw*Sbb-Sb*Sb
k=np.where(den>1e-3,(Sw*Sbi-Sb*Si)/np.maximum(den,1e-3),1.0);k=np.clip(k,0.3,1.5)
m=(Si-k*Sb)/Sw
inl=(mask>0)[...,None];k=np.where(inl,k,1.0);m=np.where(inl,m,0.0)
O=I.copy()
for x,y in locs:
    x0,y0=max(0,x+X0),max(0,y+Y0);x1,y1=min(W,x+X1),min(H,y+Y1)
    kk=k[y0-(y+Y0):y1-(y+Y0),x0-(x+X0):x1-(x+X0)];mm=m[y0-(y+Y0):y1-(y+Y0),x0-(x+X0):x1-(x+X0)]
    O[y0:y1,x0:x1]=(I[y0:y1,x0:x1]-mm)/kk
gB=cv2.cvtColor(B,cv2.COLOR_BGR2GRAY);tex=np.sqrt(cv2.blur((gB-cv2.GaussianBlur(gB,(0,0),2))**2,(9,9)))
wS=np.clip((12-tex)/8,0,1)[...,None]*(M>0)[...,None]
O=O*(1-wS)+B*wS
cv2.imwrite(dst,np.clip(O,0,255).astype(np.uint8));print('tiles',len(locs),'fit tiles',len(ok))
