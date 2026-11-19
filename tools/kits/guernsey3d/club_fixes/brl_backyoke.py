# Rebuild the Brisbane back yoke (gold collar, blue yoke, maroon below) from the photo, per column.
import numpy as np
from PIL import Image
from scipy.ndimage import median_filter
W='C:/kt/guernsey3d_work/'
r=np.array(Image.open(W+'ref/BRL_back.png').convert('RGB')).astype(int)
d=np.array(Image.open(W+'design_BRL_back.png').convert('RGBA'))
H,Wd=r.shape[:2]
R,G,B=r[...,0],r[...,1],r[...,2]
white=(R>225)&(G>225)&(B>225)
gold=(R>200)&(G>180)&(B<195)&(R-B>45)&~white
mar=(R>G+40)&(R>B)&~gold
GOLD=(0xF0,0xC0,0x5A);BLUE=(0x08,0x4D,0xAC);MAR=(0x6F,0x19,0x33)
xs=[x for x in range(Wd) if d[:700,x,3].any()]
seam={};gb={}
for x in xs:
    col=~white[:700,x]
    if not col.any(): continue
    top=int(np.argmax(col))
    m=mar[:,x]; s=None
    for y in range(top,700):
        if m[y:y+6].all(): s=y;break
    if s is None: continue
    seam[x]=s
    g=0
    if gold[top:top+14,x].sum()>=4:
        y=top
        while y<s and (gold[y,x] or gold[y+1,x] or gold[y+2,x]): y+=1
        g=y
    gb[x]=g
x0,x1=min(seam),max(seam)
sa=np.array([seam.get(x,0) for x in range(x0,x1+1)],float)
sa=median_filter(sa,31)
ga=np.array([gb.get(x,0) for x in range(x0,x1+1)],float)
ga=median_filter(ga,41)
for i,x in enumerate(range(x0,x1+1)):
    a=d[:,x,3]>0
    if not a[:700].any(): continue
    t=int(np.argmax(a)); s=int(round(sa[i])); g=int(round(ga[i]))
    for y in range(t,min(s+12,700)):
        if not a[y]: continue
        c=GOLD if y<g else (BLUE if y<s else MAR)
        d[y,x,:3]=c
Image.fromarray(d).save(W+'design_BRL_back.png')
print('cols',x0,x1,'seam mid',sa[len(sa)//2],'gold mid',ga[len(ga)//2])
