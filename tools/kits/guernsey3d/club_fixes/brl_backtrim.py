# Brisbane back: armhole gold edge copied from the photo, row by row (width measured per row, both sides).
import numpy as np
from PIL import Image
from scipy.ndimage import median_filter
W='C:/kt/guernsey3d_work/'
r=np.array(Image.open(W+'ref/BRL_back.png').convert('RGB')).astype(int)
d=np.array(Image.open(W+'design_BRL_back.png').convert('RGBA'))
GOLD=np.array((0xF0,0xC0,0x5A))
def isgold(p):
    R,G,B=p; return R>190 and G>160 and B<205 and R-B>40 and not (R>235 and G>235 and B>235)
def notwhite(p): return not (p[0]>225 and p[1]>225 and p[2]>225)
Y0,Y1=300,820
for side in (1,-1):
    wid=[]
    for y in range(Y0,Y1):
        row=r[y]; xs=[x for x in range(r.shape[1]) if notwhite(row[x])]
        if not xs: wid.append(0); continue
        xo=xs[-1] if side==1 else xs[0]
        k=0; miss=0; x=xo
        while abs(x-xo)<30:
            if isgold(row[x]): k=abs(x-xo)+1; miss=0
            else:
                miss+=1
                if miss>2 and k>0: break
                if miss>4: break
            x-=side
        wid.append(k)
    wid=median_filter(np.array(wid,float),21)
    for i,y in enumerate(range(Y0,Y1)):
        a=np.where(d[y,:,3]>0)[0]
        if len(a)==0: continue
        xe=a[-1] if side==1 else a[0]
        # interior colour of this row, 45 px in
        inner=d[y,xe-side*45,:3].copy()
        for j in range(0,40):
            x=xe-side*j
            if np.abs(d[y,x,:3].astype(int)-GOLD).sum()<60: d[y,x,:3]=inner
        w=int(round(wid[i]))
        for j in range(w):
            d[y,xe-side*j,:3]=GOLD
    print('side',side,'width rows>0',int((wid>0).sum()),'max',wid.max())
Image.fromarray(d).save(W+'design_BRL_back.png')
