# hand-made textures (procedural, no photo pixels). Sizes in metres per tile follow build.py's tile arguments.
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
R=np.random.default_rng(7);N=1024
def save(a,n):Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(f'tex/{n}.png')
def grain(a,s=4):return a+R.normal(0,s,a.shape[:2])[...,None]
def seats(n,crowd,dark,blue=(28,74,160),pb=0.55):
    # tile 6 m: rows every 0.8 m down the rake (7.5 rows -> use 8), seats 0.5 m wide (12 across)
    im=Image.new('RGB',(N,N),(150,152,156));d=ImageDraw.Draw(im);rows=8;cols=12;rh=N/rows;cw=N/cols
    BLUE=blue;WHITE=(236,239,243);NAVY=(18,36,80)
    for r in range(rows):
        y=r*rh;d.rectangle([0,y,N,y+rh*0.18],fill=(118,120,124))            # riser face
        d.rectangle([0,y+rh*0.18,N,y+rh*0.22],fill=(175,177,180))           # tread nosing
        for c in range(cols):
            x=c*cw;col=BLUE if R.random()<pb else WHITE
            d.rounded_rectangle([x+cw*0.08,y+rh*0.26,x+cw*0.92,y+rh*0.62],radius=8,fill=col)          # back
            sh=tuple(int(v*0.78) for v in col);d.rounded_rectangle([x+cw*0.12,y+rh*0.62,x+cw*0.88,y+rh*0.80],radius=6,fill=sh)  # pan
            if crowd and R.random()<crowd:
                skin=[(236,196,160),(210,160,120),(150,105,75),(240,210,180)][R.integers(4)]
                shirt=[NAVY,WHITE,(30,30,34),NAVY,(60,90,150),(240,240,240),(110,110,115),WHITE,NAVY,(200,40,40)][R.integers(10)]
                ox=R.uniform(-0.08,0.08)*cw;cx=x+cw/2+ox
                d.rounded_rectangle([cx-cw*0.34,y+rh*0.30,cx+cw*0.34,y+rh*0.86],radius=10,fill=shirt)
                d.ellipse([cx-cw*0.17,y+rh*0.06,cx+cw*0.17,y+rh*0.40],fill=skin)
                hair=[(40,30,20),(90,60,30),(20,20,20),(160,130,80),(200,200,200)][R.integers(5)]
                d.chord([cx-cw*0.18,y+rh*0.04,cx+cw*0.18,y+rh*0.38],180,360,fill=hair)
        d.line([0,y+rh-1,N,y+rh-1],fill=(95,97,100),width=3)
    a=grain(np.asarray(im).astype(float),3)
    if dark is True:a=a*0.55
    elif dark:a=a*(np.array(dark)/a.reshape(-1,3).mean(0))   # scale to a target mean colour
    save(a,n)
seats('seats',0,False);seats('seats_dark',0,True)   # no crowd (director 2026-11-19); texdetail.py overwrites these
# p1 north upper tier: a near-full crowd deep in the roof's shade (photo mean 11,14,23); render lift ~0.6 -> target 18,23,38
seats('crowd_shade',0,True)
def seats_empty(n):
    # p1 SE pocket zoom: empty seats in a navy/white mosaic of patches ~2-3 seats across; seats fill most of each row
    im=Image.new('RGB',(N,N),(119,121,124));d=ImageDraw.Draw(im);rows=8;cols=12;rh=N/rows;cw=N/cols
    NAVY=(30,44,96);WHITE=(172,175,181);k=np.arange(1,4)   # x0.86: p1 pocket mean 125 vs render 143
    ph=R.uniform(0,2*np.pi,(3,3,2))
    def f(c,r):  # periodic over the tile, so the patches wrap
        u,v=2*np.pi*c/cols,2*np.pi*r/rows
        return sum(np.cos(i*u+ph[i-1,j-1,0])*np.cos(j*v+ph[i-1,j-1,1])/(i+j) for i in k for j in k)+R.normal(0,0.12)
    F=np.array([[f(c+0.5,r+0.5) for c in range(cols)] for r in range(rows)]);th=np.quantile(F,0.40)   # p1 pocket: dark 39% of pixels vs render 19% -> 60% navy seats
    for r in range(rows):
        y=r*rh;d.rectangle([0,y,N,y+rh*0.10],fill=(95,96,100))
        for c in range(cols):
            x=c*cw;col=NAVY if F[r,c]>th else WHITE
            d.rounded_rectangle([x+cw*0.05,y+rh*0.12,x+cw*0.95,y+rh*0.70],radius=8,fill=col)
            sh=tuple(int(v*0.80) for v in col);d.rounded_rectangle([x+cw*0.08,y+rh*0.70,x+cw*0.92,y+rh*0.94],radius=6,fill=sh)
    save(grain(np.asarray(im).astype(float),3),n)
seats_empty('seats_empty')
def sheet(n,base,rib_px,shade=18,dark=False):
    # standing-seam metal sheeting: ribs every rib_px across u, faint lengthwise variation
    a=np.ones((N,N,3))*np.array(base,float);x=np.arange(N)
    ph=(x%rib_px)/rib_px
    prof=np.where(ph<0.06,+shade,np.where(ph<0.11,-shade*1.3,0.0))+np.where((ph>0.5)&(ph<0.52),-3,0)
    a+=prof[None,:,None];a+=np.linspace(-4,4,N)[:,None,None];save(grain(a,1.5),n)
sheet('roof',(214,217,221),N//13)          # tile 8 m, rib 0.6 m
sheet('roofdark',(70,74,80),N//13,10)
sheet('roofgrey',(187,197,205),N//13)      # back slopes of the Selwood canopy folds (p1 grey sheeting)
sheet('under',(176,180,186),N//8,10)
def panels(n,base,pw,ph_,joint=(0,0,0),jw=4,var=5):
    a=np.ones((N,N,3))*np.array(base,float)
    for i in range(0,N,pw):
        for j in range(0,N,ph_):a[j:j+ph_,i:i+pw]+=R.normal(0,var)
    jc=np.array(joint,float)
    for i in range(0,N,pw):a[:,i:i+jw]=a[:,i:i+jw]*0.4+jc*0.6
    for j in range(0,N,ph_):a[j:j+jw,:]=a[j:j+jw,:]*0.4+jc*0.6
    save(grain(a,2),n)
panels('wall',(196,198,192),N//4,N//6,(120,122,118))      # precast panels 2 m x 1.2 m on an 8 m tile
panels('fascia',(240,242,244),N//4,N,(190,194,198),3,2)   # white fascia, joints every 2 m
panels('tower',(242,244,246),N,N//6,(200,204,208),3,1)
panels('teal',(38,104,126),N//4,N//3,(24,70,86),4,3)
def glass(n):
    a=np.zeros((N,N,3));y=np.linspace(0,1,N)[:,None,None]
    a+=np.array([42,52,66])*(1-y)+np.array([70,84,100])*y        # sky reflection lighter low
    for k in range(6):                                              # soft diagonal reflections
        x0=R.integers(0,N);w=R.integers(30,90);xx=np.arange(N)[None,:];yy=np.arange(N)[:,None]
        m=np.abs((xx-x0)-(yy*0.35))%N<w;a[m]+=12
    mw=6
    for i in range(0,N,N//8):a[:,i:i+mw]=(140,146,152)                 # mullions every 1 m
    for j in range(0,N,N//3):a[j:j+mw,:]=(120,126,132)                 # transoms
    save(grain(a,1.5),n)
glass('glass')
def aglass(n):
    # annex curtain wall (p1 zoom x 115-230): dark interior through clear glass, dark grey frames every 1.6 m, floor line
    a=np.ones((N,N,3))*np.array([34,38,44],float);xx=np.arange(N)[None,:];yy=np.arange(N)[:,None]
    for k in range(5):
        x0=R.integers(0,N);w=R.integers(20,60);m=np.abs((xx-x0)-(yy*0.35))%N<w;a[m]+=8
    for i in range(0,N,N//5):a[:,i:i+8]=(58,62,68)
    for j in(0,N//2):a[j:j+10,:]=(62,66,72)
    save(grain(a,2),n)
aglass('aglass')
def pave(n):
    # plaza paving under the low canopy (p1 sunlit median ~(175,160,135)): 0.6 x 0.3 m tan pavers, 8 m tile, thin joints
    a=np.ones((N,N,3))*np.array([184,169,145],float);a+=R.normal(0,4,(N,N,1))
    pw=int(N*0.6/8);ph=int(N*0.3/8)
    for j in range(0,N,ph):
        a[j:j+1,:]-=28;off=(j//ph%2)*pw//2
        for i in range(off,N,pw):a[j:j+ph,i:i+1]-=28
    save(grain(np.clip(a,0,255),2),n)
pave('pave')
def solar(n):
    a=np.ones((N,N,3))*np.array([26,34,62],float);c=N//16
    for i in range(N):
        pass
    yy,xx=np.mgrid[0:N,0:N];cell=((xx%c)<2)|((yy%c)<2);a[cell]=(70,80,110)
    frame=((xx%(c*4))<5)|((yy%(c*8))<6);a[frame]=(190,194,200)
    a+=((xx+yy)%c<c//2)[...,None]*4;save(grain(a,2),n)
solar('solar')
def lamp(n):
    a=np.ones((N,N,3))*np.array([60,64,70],float);c=N//8;yy,xx=np.mgrid[0:N,0:N]
    cx=(xx%c)-c/2;cy=(yy%c)-c/2;r=np.hypot(cx,cy);a[r<c*0.38]=(225,230,236);a[r<c*0.30]=(250,252,255)
    a[(r>c*0.38)&(r<c*0.42)]=(30,32,36);save(grain(a,1.5),n)
lamp('lamp')
# turf (p1 rectified, 2026-11-18): two crossing sets of 10 m mowing bands. Across-ground bands (constant S) are strong,
# bright band centred on the centre; along-ground bands (constant T) weak, bright centred on T=1.5. One tile = 40 x 40 m.
# Tones measured on p1 (BB 80,92,42 / BD ~72,85,37 / DB 61,71,27 / DD 53,64,22), divided by the render's lift on turf.
def turf(n):
    yy,xx=np.mgrid[0:N,0:N];bs=((xx+N//8)//(N//4))%2==0;bt=((yy+N//8)//(N//4))%2==0
    a=np.zeros((N,N,3));a[bs&bt]=(65,78,24);a[bs&~bt]=(58,72,21);a[~bs&bt]=(49,60,15);a[~bs&~bt]=(43,54,12)
    a+=np.sin(yy*0.9)[...,None]*1.2;save(grain(a,3),n)
turf('turf')
def solid(n,c,g=2):save(grain(np.ones((N//4,N//4,3))*np.array(c,float),g),n)
solid('line',(236,238,234),1.5);solid('pad',(206,54,42),2)
def logo(n):  # p1 centre-ground painting: dark maroon field, white mark at the left, four slanted white strokes
    W,H=1024,256;im=Image.new('RGB',(W,H),(0,0,0));d=ImageDraw.Draw(im)
    d.rounded_rectangle([20,40,1004,216],radius=80,fill=(64,22,30))
    d.ellipse([140,70,300,190],fill=(232,232,236))
    for k in range(4):x=420+k*140;d.polygon([(x,190),(x+60,66),(x+110,66),(x+50,190)],fill=(232,232,236))
    a=np.array(im).astype(float);al=(a.sum(2)>0)
    rgba=np.dstack([np.clip(a,0,255),al*255]).astype(np.uint8);Image.fromarray(rgba,'RGBA').save(f'tex/{n}.png')
logo('logo')
solid('navy',(33,64,102),2);solid('deckg',(160,163,158),3);solid('soffit',(66,68,84),2)
def banners(n):  # p1 fence banners (SE, a 211-230): yellow and red panels ~2.5 m long, white and blue graphics
    W,H=1024,128;im=Image.new('RGB',(W,H));d=ImageDraw.Draw(im);pw=W//8
    for k in range(8):
        x=k*pw;c=(232,192,44) if k%2==0 else (212,52,46);d.rectangle([x,0,x+pw,H],fill=c)
        d.polygon([(x+pw*0.6,H),(x+pw*0.95,8),(x+pw,8),(x+pw,H)],fill=(236,238,240) if k%2 else (40,96,170))
        d.rectangle([x+10,30,x+pw*0.5,46],fill=(140,40,30) if k%2==0 else (250,230,200));d.rectangle([x,0,x+2,H],fill=(30,30,34))
    save(grain(np.array(im).astype(float),2),n)
banners('banners')
solid('recess',(118,130,150),2)   # p1 Players Stand: dark recess above the deck reads (60,66,76); render lift there ~0.5
