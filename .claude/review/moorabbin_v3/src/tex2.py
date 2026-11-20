# Texture pass 2 (2026-11-19): hand-made, procedural, no photo pixels. Every tile is periodic (noise built in the
# Fourier domain), so repeats have no seams. Real sizes in metres are written to hand/tiles.json for the UV scale.
# Rule: every big surface gets painted detail (joints, rain streaks, blotching, ribs at real spacing, sheet laps, grime,
# seat gaps, steel seams, wear toward the bottom) and grey stddev >= 10 (PIL L, 0-255).
import numpy as np,json,os,shutil
from PIL import Image,ImageDraw,ImageFont
D=os.path.dirname(os.path.abspath(__file__));OUT=os.path.join(D,'hand')
TL=json.load(open(os.path.join(OUT,'tiles.json')))
os.makedirs(os.path.join(D,'hand_v1'),exist_ok=True)
rng=np.random.default_rng(20261119)
def pnoise(h,w,cyc):
    """periodic smooth noise in -1..1, feature size ~ 1/cyc of the tile"""
    f=np.fft.fft2(rng.standard_normal((h,w)))
    ky=np.fft.fftfreq(h)[:,None]*h;kx=np.fft.fftfreq(w)[None,:]*w
    k=np.sqrt((kx/max(cyc[1],1e-3))**2+(ky/max(cyc[0],1e-3))**2)
    n=np.real(np.fft.ifft2(f*np.exp(-k**2)));n-=n.mean();return n/(np.abs(n).max()+1e-9)
def fine(h,w,a):return rng.normal(0,a,(h,w))
def col(h,w,c):return np.zeros((h,w,3))+np.array(c,float)
def lum(a,m):return a+m[...,None]
def streaks(h,w,n,amp,lmin=0.3,lmax=1.0,width=(1,4)):
    """vertical rain streaks hanging from the top of the tile (row 0 = top), fading downward"""
    s=np.zeros((h,w))
    for _ in range(n):
        x=rng.integers(0,w);ww=rng.integers(*width);L=int(h*rng.uniform(lmin,lmax));y0=rng.integers(0,max(1,h//6))
        prof=np.linspace(1,0,L)**1.5*rng.uniform(0.5,1)
        for dx in range(ww):s[y0:y0+L,(x+dx)%w]+=prof[:min(L,h-y0)]
    return -s*amp
def save(n,a,wm,hm):
    p=os.path.join(OUT,n+'.png')
    if os.path.exists(p) and not os.path.exists(os.path.join(D,'hand_v1',n+'.png')):shutil.copy(p,os.path.join(D,'hand_v1',n+'.png'))
    Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(p);TL[n]=[wm,hm]
    g=np.asarray(Image.open(p).convert('L'),float);print(n,'%dx%d'%(a.shape[1],a.shape[0]),'std %.1f'%g.std(),flush=True)
PX=180   # px per metre for walls/concrete (tile 2 m = 360 px)
# ---- concrete (terraces, apron, treads): 2 x 2 m tile. Form joint on two edges, aggregate speckle, blotches,
#      water stains, a few dark spots (chewing gum / oil)
h=w=360;a=col(h,w,(176,172,162))
a=lum(a,pnoise(h,w,(3,3))*26+pnoise(h,w,(10,10))*10+fine(h,w,6))
a[:,:3]-=30;a[:3,:]-=24
for _ in range(14):
    y,x=rng.integers(0,h),rng.integers(0,w);r=rng.integers(2,6);yy,xx=np.ogrid[:h,:w]
    a[((yy-y)%h)**2+((xx-x)%w)**2<r*r]-=rng.uniform(25,50)
save('concrete',a,2.0,2.0)
# ---- white painted render (walls, fascias, fence boards): 2 x 2 m tile; panel joint on the edges, rain streaks from
#      the top, grime rising from the bottom, blotchy repaint
a=col(h,w,(228,229,226))
a=lum(a,pnoise(h,w,(2,2))*17+fine(h,w,3)+streaks(h,w,26,24,0.2,0.9))
g_=np.linspace(0,1,h)[:,None]**3*26;a-=g_[...,None]*np.array([1,1,1.15])
a[:,:2]-=40;a[:2,:]-=34
save('white',a,2.0,2.0)
# ---- dark render (stand back wall, scoreboard back): 2 x 2 m
a=col(h,w,(60,63,68))
a=lum(a,pnoise(h,w,(2,2))*22+fine(h,w,5)+streaks(h,w,30,-22,0.3,1.0));a[:,:2]+=18;a[:2,:]+=14
a-=np.linspace(0,1,h)[:,None,None]**2*10
save('darkwall',a,2.0,2.0)
# ---- profiled steel roof deck: ribs every 0.19 m (5 per 0.95 m sheet), sheet lap across every 6 m (tile 0.95 x 6 m),
#      pans carry dirt lines that run down the fall, rust spots near the lap
def deck(c,ribhi,riblo,dirt,name,W=0.95,Hm=6.0,lap=True):
    w=int(W*256);h=int(Hm*64);a=col(h,w,c)
    a=lum(a,pnoise(h,w,(6,1.5))*9+fine(h,w,2.5))
    for k in range(5):
        x=int(k*w/5);a[:,x:x+6]+=ribhi;a[:,x+6:x+10]-=riblo
    for k in range(5):                                   # dirt line in each pan, running down the fall
        x=int((k+0.5)*w/5)+rng.integers(-6,6);t=np.abs(np.arange(w)-x)
        a-=(np.exp(-(t/7.0)**2)[None,:]*dirt*(0.5+0.5*pnoise(h,1,(4,1))))[...,None]
    if lap:a[:5]-=34;a[5:8]+=16
    for _ in range(10):
        y,x=rng.integers(0,h//8),rng.integers(0,w);a[y:y+rng.integers(3,14),x:x+3]+=np.array([16,-6,-14])
    save(name,a,W,Hm)
deck((150,158,148),24,26,18,'roof_deck')
deck((48,47,52),16,18,8,'roof_under',lap=False)
# purlin shadow lines on the underside every 1.2 m
a=np.asarray(Image.open(os.path.join(OUT,'roof_under.png')),float)
for k in range(5):y=int(k*a.shape[0]/5);a[y:y+6]-=24
a=lum(a,pnoise(a.shape[0],a.shape[1],(3,2))*12);save('roof_under',a,0.95,6.0)
deck((74,66,58),18,18,12,'brown_roof')
# ---- steel (posts, gates, legs, poles): 1 x 1 m, rolled seam, scratches, wear and rust toward the bottom
h=w=256;a=col(h,w,(150,153,156))
a=lum(a,pnoise(h,w,(3,3))*28+fine(h,w,5)+streaks(h,w,16,20,0.3,1.0,(1,2)))
a[:,126:129]-=28;a[:,129:131]+=14
for _ in range(30):
    y,x=rng.integers(0,h),rng.integers(0,w);L=rng.integers(6,30);a[y,x:x+L]+=18
g_=np.linspace(0,1,h)[:,None]**4;a+=g_[...,None]*np.array([-6,-20,-30])
save('steel',a,1.0,1.0)
# ---- glazing (Huggins and sawtooth windows): 1.5 x 1 m pane with frame, sky-to-ground gradient, smears
h,w=256,384;a=col(h,w,(46,52,62))
a+=np.linspace(30,-6,h)[:,None,None]
a=lum(a,pnoise(h,w,(2,3))*14+fine(h,w,2))
for _ in range(5):                                       # diagonal reflection bands
    x0=rng.integers(0,w);ww=rng.integers(12,40);yy,xx=np.ogrid[:h,:w];a[((xx-x0-yy*0.6)%w)<ww]+=14
a[:,:8]=(200,202,200);a[:,-8:]=(200,202,200);a[:8]=(200,202,200);a[-10:]=(190,190,188)
save('glass',a,1.5,1.0)
# ---- bench seating (long stand): three green timber slats per 1 m, 8 mm gaps, a gap every bench (2 m tile),
#      worn paint on the seat front edge, bird droppings
h,w=103,512;a=col(h,w,(66,104,92))
a=lum(a,pnoise(h,w,(2,8))*14+fine(h,w,4))
for k in range(1,3):y=int(k*h/3);a[y-2:y+1]=(22,34,32)
a[:3]*=0.7;a[-4:]=a[-4:]*0.6+60
a[:,:4]=(28,32,30)                                       # gap between benches every 2 m
for _ in range(16):
    y,x=rng.integers(0,h),rng.integers(0,w);a[y:y+2,x:x+2]=(210,210,200)
save('bench',a,2.0,0.4)
# ---- Huggins tier seats (blue, green): 0.5 m seat with plastic tip-up seat shape, gap and shadow between seats,
#      concrete tread below with the shadow of the seat row on it
def seat(c,name):
    h,w=205,128;a=col(h,w,c);cut=int(h*.55)
    a=lum(a,pnoise(h,w,(2,1))*12+fine(h,w,3))
    a[:,:8]=np.array(c)*0.35;a[:,-8:]=np.array(c)*0.35   # gap between seats
    a[:10,8:-8]+=22;a[cut-12:cut]*=0.55                  # seat-back top highlight, shadow under the seat
    t=col(h,w,(170,166,156));t=lum(t,pnoise(h,w,(2,2))*14+fine(h,w,4));t[cut:cut+30]*=np.linspace(0.55,1,30)[:,None,None]
    a[cut:]=t[cut:];a[-3:]-=30
    save(name,a,0.5,0.8)
seat((80,96,128),'blue_seat');seat((70,108,92),'green_seat')
# ---- bank grass: 10 x 10 m, worn patches and mower passes
h=w=512;a=col(h,w,(104,140,74))
a=lum(a,pnoise(h,w,(4,4))*24+pnoise(h,w,(30,30))*9+fine(h,w,8))
yy,xx=np.ogrid[:h,:w];a+=(((xx//64)%2)*6-3)[...,None]*np.array([0.5,1,0.4])
wear=np.clip(pnoise(h,w,(3,3))-0.55,0,1)*120;a+=wear[...,None]*np.array([0.55,0.15,0.2])
save('park_grass',a,10,10)
# ---- the ground's own signs: hand-lettered, read off the 1993 last-game panorama (and the 2000s G.G. Huggins photo
#      for the letter style). Huggins fascia: white band, "G.G. HUGGINS STAND" in black at 0.366-0.515 of the band
#      (panorama x 590-735 of the band's 235-1205), the rest of the band plain white (its other boards were ads: out).
FB='C:/Windows/Fonts/arialbd.ttf'
def band_text(img,text,x0,x1,y0,y1,fill):
    d=ImageDraw.Draw(img);H=y1-y0;fs=int(H*0.95)
    while fs>4:
        f=ImageFont.truetype(FB,fs);bb=d.textbbox((0,0),text,font=f)
        if bb[2]-bb[0]<=x1-x0 and bb[3]-bb[1]<=H:break
        fs-=1
    bb=d.textbbox((0,0),text,font=f);tw=bb[2]-bb[0]
    # stretch to the measured length like the real board (letters spaced across it)
    tmp=Image.new('L',(tw+4,bb[3]+4),0);ImageDraw.Draw(tmp).text((-bb[0]+2,2),text,font=f,fill=255)
    tmp=tmp.crop((0,bb[1],tw+4,bb[3]+4)).resize((x1-x0,y1-y0));img.paste(Image.new('RGB',tmp.size,fill),(x0,y0),tmp)
h,w=166,4096;a=col(h,w,(236,236,232));a=lum(a,pnoise(h,w,(1,40))*6+fine(h,w,2)+streaks(h,w,120,10,0.3,1.0,(1,3)))
a[:6]=(70,74,80);a[-6:]=(70,74,80)
end=int(w*0.932);a[:,end:]=(52,56,64)
im=Image.fromarray(np.clip(a,0,255).astype(np.uint8))
sx0,sx1=int(w*0.366),int(w*0.515)
band_text(im,'G.G. HUGGINS STAND',sx0,sx1,int(h*0.30),int(h*0.70),(18,18,22))
a=np.asarray(im,float);save('huggins_band',a,TL['huggins_band'][0],TL['huggins_band'][1])
# Ian Drake pavilion fascia: "IAN DRAKE JUNIOR DEVELOPMENT PAVILION", dark letters on white, 0.17-0.92 of the board
h,w=114,3072;a=col(h,w,(236,236,232));a=lum(a,pnoise(h,w,(1,30))*6+fine(h,w,2)+streaks(h,w,90,10,0.3,1.0,(1,3)))
a[:5]=(70,74,80);a[-5:]=(70,74,80)
im=Image.fromarray(np.clip(a,0,255).astype(np.uint8))
band_text(im,'IAN DRAKE JUNIOR DEVELOPMENT PAVILION',int(w*0.17),int(w*0.92),int(h*0.22),int(h*0.78),(20,22,30))
a=np.asarray(im,float);save('pav_sign',a,TL['pav_sign'][0],TL['pav_sign'][1])
json.dump(TL,open(os.path.join(OUT,'tiles.json'),'w'))
