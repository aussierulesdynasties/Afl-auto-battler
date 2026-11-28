# Brisbane design clean-up: no maroon above the yoke split (the collar's shadow line), islands < 40 px merged.
import sys, numpy as np
from PIL import Image
from scipy import ndimage as nd
p=sys.argv[1]; MAR=(0x6F,0x19,0x33); BLU=(8,0x4D,0xAC)
d=np.array(Image.open(p).convert('RGBA')); rgb=d[...,:3].astype(int); al=d[...,3]>0
isM=(np.abs(rgb-MAR).sum(2)<10)&al; isB=(np.abs(rgb-BLU).sum(2)<10)&al
if len(sys.argv)>2:
    # split row per column: first row where maroon dominates below blue (smoothed median)
    sp=[]
    for x in range(700,1300,10):
        col=isM[:,x]; ys=np.nonzero(col[400:1000])[0]
        if len(ys): sp.append(ys.min()+400)
    S=int(np.median(sp)); print('split row',S)
    sel=isM.copy(); sel[S-3:]=False
    d[sel,:3]=BLU
rgb=d[...,:3].astype(int)
cols=np.unique(rgb[al].reshape(-1,3),axis=0)
for c in cols:
    k=(np.abs(rgb-c).sum(2)==0)&al; lab,n=nd.label(k)
    if n==0: continue
    s=nd.sum(k,lab,range(1,n+1))
    for i,v in enumerate(s):
        if v<40:
            m=lab==i+1; ring=nd.binary_dilation(m,iterations=2)&~m&al
            if ring.any():
                rc=rgb[ring]; u,cnt=np.unique(rc,axis=0,return_counts=True); d[m,:3]=u[cnt.argmax()]
Image.fromarray(d).save(p)
