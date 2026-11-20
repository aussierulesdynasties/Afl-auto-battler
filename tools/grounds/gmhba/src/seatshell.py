# Seat shells drawn by hand for the 3D seat rows (photo p12): blue and white plastic shells with a rolled top lip,
# a cup holder on the back's top corner, sitting almost touching. No crowd (director 2026-11-19).
# 2 m tile across = 4 seats (blue pair, white pair) (aisles are gaps in the 3D rows, every 8 degrees, so they run straight down the tier); four row bands, the colour pairs shift one seat per row.
# Alpha cuts each shell out, so the concrete row shows between seats and in the aisle.
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
W=1024;TILE=2.0;SW=0.5;PXM=W/TILE;CW=SW*PXM;AX=W
BLUE=np.array((20,88,150.));WHITE=np.array((226,228,230.))
rg=np.random.default_rng(7)
def colour(c,r):return BLUE if ((c+r)//2)%2==0 else WHITE
def grain(a,s=2.0):a[...,:3]+=rg.normal(0,s,a.shape[:2])[...,None];return a
def back_band(r,H=512):
    a=np.zeros((H,W,4))
    m=Image.new('L',(W,H),0);d=ImageDraw.Draw(m)
    nseat=int(AX//CW)
    for c in range(nseat):
        x0=c*CW+5;x1=(c+1)*CW-5
        d.rounded_rectangle([x0,8,x1,H-1],radius=36,fill=255)
    mk=np.asarray(m).astype(float)/255
    yy=np.arange(H)[:,None]/H;xx=(np.arange(W)%CW)[None,:]/CW
    for c in range(nseat):
        col=colour(c,r);sl=slice(int(c*CW),int((c+1)*CW))
        a[:,sl,:3]=col
    sh=np.ones((H,W))
    sh*=np.where(yy<0.10,1.10,np.where(yy<0.14,0.78,1.0))              # rolled top lip, shadow line under it
    sh*=1.0-0.10*yy                                                        # shell darkens toward the pan
    sh*=1.0-0.16*np.clip(1-np.minimum(xx,1-xx)/0.10,0,1)                   # the curved shell darkens at its sides
    a[...,:3]*=sh[...,None]
    im=Image.fromarray(np.clip(a[...,:3],0,255).astype(np.uint8));d=ImageDraw.Draw(im)
    for c in range(nseat):                                                 # cup holder on the back's right top corner
        col=tuple(int(v) for v in colour(c,r));dk=tuple(int(v*0.45) for v in col)
        cx=(c+1)*CW-40;d.rounded_rectangle([cx-24,30,cx+24,110],radius=12,fill=tuple(int(v*0.9) for v in col))
        d.ellipse([cx-22,22,cx+22,44],fill=dk);d.arc([cx-24,20,cx+24,46],0,360,fill=col,width=4)
        m2=ImageDraw.Draw(m);m2.rounded_rectangle([cx-24,20,cx+24,110],radius=12,fill=255)
    a[...,:3]=np.asarray(im).astype(float);a[...,3]=np.asarray(m).astype(float)
    a[...,:3]*=(a[...,3:]>0);return grain(a,0.6)
def pan_band(r,H=256):
    a=np.zeros((H,W,4));m=Image.new('L',(W,H),0);d=ImageDraw.Draw(m)
    nseat=int(AX//CW);yy=np.arange(H)[:,None]/H
    for c in range(nseat):
        d.rounded_rectangle([c*CW+5,0,(c+1)*CW-5,H-1],radius=40,fill=255)
        a[:,int(c*CW):int((c+1)*CW),:3]=colour(c,r)
    sh=np.where(yy<0.12,1.08,1.0)*(1.0-0.30*yy)                           # v 0 = the front lip, darker under the back
    a[...,:3]*=sh[...,None];a[...,3]=np.asarray(m).astype(float);a[...,:3]*=(a[...,3:]>0);return grain(a,0.6)
def tread(H=256):
    a=np.full((H,W,4),255.);base=np.array((150,152,156.))
    a[...,:3]=base;a[...,:3]+=rg.normal(0,1,(H,W))[...,None]*0+np.repeat(np.asarray(Image.fromarray((rg.random((H//8,W//8))*255).astype(np.uint8)).resize((W,H),Image.BICUBIC)).astype(float)[...,None]/255*52-26,3,2)
    a[:,:4,:3]*=0.62                                                       # expansion joint every 2 m
    a[int(H*0.86):,:,:3]*=0.80                                             # the riser's shadow line at the back
    yy=np.arange(H)[:,None]/H
    a[...,:3]*=np.where(yy<0.06,1.18,1.0)[...,None]                        # tread nosing
    return grain(a)
def aisle(H=256):
    a=tread(H);a[...,:3]=(a[...,:3]-150)*1.25+170                          # paler concrete steps
    a[:int(H*0.10),:,:3]=np.array((206,186,60.))+rg.normal(0,6,(int(H*0.10),W))[...,None]   # yellow step nosing
    return a
def save(a,n,k=1.0):
    b=a.copy();b[...,:3]*=k;Image.fromarray(np.clip(b,0,255).astype(np.uint8),'RGBA').save(f'tex/{n}.png')
    sd=np.asarray(Image.fromarray(np.clip(b[...,:3],0,255).astype(np.uint8)).convert('L'))[b[...,3]>128].std();print(n,'stddev',round(float(sd),1))
B=np.concatenate([back_band(r) for r in range(4)],0);P_=np.concatenate([pan_band(r) for r in range(4)],0);T=tread();AI=aisle()
for sfx,k in(('',1.0),('_d',0.55)):save(B,'seatback'+sfx,k);save(P_,'seatpan'+sfx,k);save(T,'tread'+sfx,k);save(AI,'aisle'+sfx,k)
