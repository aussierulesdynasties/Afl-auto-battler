# Texture pass (row 202 2b, 2026-11-19). Director: "texture it by fucking hand to look the same but not like a fucking
# BLURRY PHOTO". Reads the gate-passed maps in ../tex_base (handtex.py output) and writes painted maps to ../tex.
# No photo pixels: every mark is drawn from module sizes in metres; colours keep each map's mean (keep_mean).
# The two OPTUS STADIUM signs are lettered from the reference photos (positions read off refs/o1, refs/o2).
# Usage: python paint_tex.py   (then build.py as before)
import json,os,math,numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy import ndimage as nd
from texpaint import Canvas
H_=os.path.dirname(os.path.abspath(__file__));B=os.path.join(H_,'..','tex_base');T=os.path.join(H_,'..','tex')
I=json.load(open(os.path.join(B,'info.json')));R=np.random.default_rng(202)
def load(n):return np.asarray(Image.open(os.path.join(B,n+'.png')).convert('RGB'),float)/255
def save(n,a):Image.fromarray((np.clip(a,0,1)*255+0.5).astype(np.uint8)).save(os.path.join(T,n+'.png'))
def pn(h,w,sy,sx=None):
    """tileable gaussian noise, unit std; feature size sy x sx pixels"""
    sx=sy if sx is None else sx;z=R.standard_normal((h,w));fy=np.fft.fftfreq(h)[:,None];fx=np.fft.fftfreq(w)[None,:]
    r=np.real(np.fft.ifft2(np.fft.fft2(z)*np.exp(-2*np.pi**2*((fx*sx)**2+(fy*sy)**2))));return (r-r.mean())/(r.std()+1e-9)
def keep(a,ref):return a*(ref.reshape(-1,3).mean(0)/a.reshape(-1,3).mean(0))
def canvas_from(n,tu,tv,seed):
    a=load(n);c=Canvas(tu,tv,a.reshape(-1,3).mean(0),seed,n=max(a.shape[:2]));return a,c
def fit(c,shape):  # square canvas -> map size
    return np.asarray(Image.fromarray((np.clip(c.a,0,1)*255).astype(np.uint8)).resize((shape[1],shape[0]),Image.LANCZOS),float)/255
# ---------------- roof membrane, 8 m tile (u round the roof, v inward). PTFE strips 1.6 m wide (welded seams),
# cross seams every 4 m, dirt settling along the seams, rain tracks running outward (down the image), soft sag tone.
a,c=canvas_from('roof',8,8,21);c.mottle(0.045,(3,1,0.3))
d=np.abs(((np.arange(c.n)/c.pu)%1.6)-0.8);seam=np.exp(-((0.8-d)/0.10)**2)
c.mul(1-0.12*seam[None,:]*np.clip(1+0.8*c.noise(0.05,1.2),0,2))
for k in range(5):c.vline(k*1.6,0.03,c.col*0.86,0.9);c.vline(k*1.6+0.035,0.015,np.minimum(c.col*1.03,1),0.7)
for k in range(2):c.hline(k*4.0,0.025,c.col*0.88,0.8)
sag=np.cos(np.pi*((np.arange(c.n)/c.pu)%1.6)/1.6*2)*0.5+0.5;c.mul(1-0.025*sag[None,:])   # each strip dips between seams
c.streaks([0.0,4.0],per_m=1.8,length=(0.6,3.5),width=(0.04,0.18),amt=0.22,col=(0.55,0.53,0.50))
c.speckle(0.5,(0.01,0.04),0.06);c.grain(0.006);c.keep_mean();save('roof',c.img())
# ---------------- roof underside, 10 m tile: fabric strips 1.6 m, purlin shadow bands every 2.5 m (kept), grime at purlins
a,c=canvas_from('under',10,10,22);c.a=a.copy();c.mottle(0.03,(4,1.2,0.3))
for k in range(7):c.vline(k*1.6,0.025,c.col*0.88,0.8)
for k in range(4):
    u=k*2.5+0.05;x=np.arange(c.n)/c.pu;dd=np.abs(((x-u+5)%10)-5);c.mul(1-0.10*np.exp(-(dd/0.35)**2)[None,:])
c.speckle(0.4,(0.02,0.06),0.08);c.grain(0.008);c.keep_mean();save('under',c.img())
# ---------------- seats: one 14.8 m bay. Row layout copied from handtex.py (same row heights, treads, aisles, teal
# fascia, vomitories, suites, front fence). Empty-seat photos (Commons 032, 005) show every row as a scatter of two
# seat colours; each seat here is the tier colour pushed toward pale grey-blue or toward tan at random, half each, so
# the tier's mean colour is unchanged. Seats 0.5 m wide, scuffed pans, dirty treads.
base=load('seats');SW,SH=1024,4096;PX=SW/14.8;a=np.ones((SH,SW,3))*np.array((150,145,138))/255
def vy(v):return int(round((1-v)*SH))
KN=[(0,1.0),(1.6,0.95),(12,0.71),(15,0.667),(31.5,0.0)]
def VZ(z):
    for (z0,f0),(z1,f1) in zip(KN,KN[1:]):
        if z<=z1:return 1-(f0+(f1-f0)*(z-z0)/(z1-z0))
    return 1.0
TIER={'lo':np.array((216,208,203))/255,'mid':np.array((246,221,191))/255,'up':np.array((178,182,188))/255}
AX=np.array((0.70,0.76,0.82))-np.array((0.86,0.79,0.66));AX/=np.linalg.norm(AX)     # grey-blue minus tan
GAP=np.array((66,62,60))/255;CON=np.array((176,170,162))/255;AIS=np.array((214,208,198))/255
s_px=int(0.5*PX);nseat=SW//s_px+1
tread_dirt=np.clip(pn(SH,SW,4,60)*0.5+0.5,0,1)
def rowband(z0,z1,n,tier_of,aoff=0.0):
    for r in range(n):
        za=z0+(z1-z0)*r/n;zb=z0+(z1-z0)*(r+1)/n;zm=za+0.6*(zb-za)
        yA,yM,yB=vy(VZ(za)),vy(VZ(zm)),vy(VZ(zb))
        SC=TIER[tier_of(r)]*(1.0 if r%2 else 0.96)
        a[yM:yA]=CON*(1-0.10*tread_dirt[yM:yA,:,None])
        k=np.where(R.random(nseat)<0.5,1.0,-1.0)*0.075*R.uniform(0.7,1.0,nseat)          # per-seat colour pick
        tone=1+0.03*R.standard_normal(nseat)
        sc=(SC[None,:]+k[:,None]*AX[None,:])*tone[:,None]
        cols=sc[np.minimum(np.arange(SW)//s_px,nseat-1)]                                   # (SW,3)
        t=yA-yM;yp=yM+max(1,t//2)
        a[yB:yM]=CON*0.84*(1-0.08*tread_dirt[yB:yM,:,None])                                 # bare riser: the seats are real 3D now (build.py)
        a[yM-1:yM+1]=np.array((236,234,228))/255                                            # tread nosing
        for ax in [0.0,7.4]:
            x0=int((ax+aoff)*PX)-int(0.6*PX);x1=int((ax+aoff)*PX)+int(0.6*PX)
            for xa,xb in ((x0,x1),(x0+SW,x1+SW),(x0-SW,x1-SW)):
                xa_,xb_=max(0,xa),min(SW,xb)
                if xb_>xa_:
                    a[yB:yA,xa_:xb_]=AIS*(1-0.06*tread_dirt[yB:yA,xa_:xb_,None]);a[yM-1:yM+1,xa_:xb_]=np.array((150,146,140))/255
                    a[yA-2:yA,xa_:xb_]=np.array((236,234,228))/255*(1-0.15*(R.random(xb_-xa_)<0.3))[None,:,None]   # worn nosings
ZT=6.4
rowband(1.6,12.0,24,lambda r:'lo' if 1.6+10.4*(r+1)/24<=ZT+0.01 else 'mid')
rowband(15.0,31.5,30,lambda r:'up',aoff=3.7)
yT1,yT0=vy(VZ(ZT+0.45)),vy(VZ(ZT));a[yT1:yT0]=np.array((46,96,104))/255;a[yT1:yT1+max(1,(yT0-yT1)//4)]=np.array((226,228,226))/255
a[yT0-max(1,(yT0-yT1)//5):yT0]*=0.85                                                       # grime on the fascia foot
vx0,vx1=int(3.2*PX),int(5.0*PX);vy0,vy1=vy(VZ(12.0)),vy(VZ(10.2));a[vy0:vy1,vx0:vx1]=np.array((34,32,32))/255
WF=np.array((220,220,216))/255;a[vy0:vy1,vx0-4:vx0]=WF;a[vy0:vy1,vx1:vx1+4]=WF;a[vy0:vy0+4,vx0-4:vx1+4]=WF
y1,y0=vy(VZ(1.6)),vy(VZ(0.0));a[y1:y0]=np.array((42,58,62))/255
for x in range(0,SW,int(2.4*PX)):a[y1:y0,x:x+2]*=0.7                                      # board joints in the front fence
y1,y0=vy(VZ(15.0)),vy(VZ(12.0));h_=y0-y1;a[y1:y0]=np.array((78,90,98))/255
a[y1+h_//2:y0]=np.array((62,72,78))/255
a[y1:y1+max(2,h_//7)]=np.array((232,232,230))/255;a[y1+h_//3:y1+h_//3+max(2,h_//14)]=np.array((206,208,206))/255
a[y0-max(2,h_//9):y0]=np.array((186,182,176))/255
for x in range(0,SW,int(1.85*PX)):a[y1+h_//7:y0-h_//9,x:x+3]=np.array((140,146,148))/255
a*=(1+0.02*pn(SH,SW,40)+0.012*R.standard_normal((SH,SW)))[...,None]
save('seats',a)
# ---------------- bronze screen (2 bays x 20.65 m): blades kept; add dust along each blade top, fine brushed grain,
# soft rain tracks down from the top edge, slightly darker toward the base.
a=load('bronze');Hb,Wb=a.shape[:2];PM=70;base=a.copy()
pitch=int(0.55*PM);y=np.arange(Hb)%pitch;top=np.exp(-(y/3.0)**2)[:,None]
a*=(1-0.08*top*np.clip(0.6+pn(Hb,Wb,4,120)*0.6,0,2))[...,None]+0*a
a*=(1+0.03*pn(Hb,Wb,0.6,25))[...,None]
st=np.clip(pn(Hb,Wb,300,6),0,None)*np.linspace(1,0.3,Hb)[:,None];a*=(1-0.05*st)[...,None]
a*=np.linspace(1.0,0.94,Hb)[:,None,None];save('bronze',keep(a,base))
# ---------------- glass band: kept layout; streaky sky reflections per pane, dust lines on transoms
a=load('glass');Hg,Wg=a.shape[:2];base=a.copy()
PW_=int(round(Wg/16));xx=(np.arange(Wg)%PW_)/PW_;yy=(np.arange(Hg)%140)/140
refl=0.05*(xx[None,:]*0.6+yy[:,None]*0.4-0.5);a*=(1+refl)[...,None]                      # each pane catches the sky a little brighter on one corner
y=np.arange(Hg);tr=((y%140)>=22)&((y%140)<30);a[tr]*=0.9
a*=(1+0.01*R.standard_normal((Hg,Wg)))[...,None];save('glass',keep(a,base))
# ---------------- podium wall: sandstone precast 2.4 x 1.2 m panels (joints kept), rain streaks under every joint,
# sandstone grain, blotching between panels
a=load('podwall');c=Canvas(4.8,2.4,a.reshape(-1,3).mean(0),23,n=1024)
c.mottle(0.05,(0.8,0.2,0.04),(0.6,0.8,1.0));c.panels(2.4,1.2,joint=0.02,dark=0.6,tone=0.015,bevel=True)   # low tone: 0.05 read as vertical stripes (4.8 m repeat)
c.streaks([0.0,1.2],per_m=3.0,length=(0.2,1.0),width=(0.02,0.10),amt=0.30,col=(0.45,0.40,0.34))
c.speckle(40,(0.002,0.005),0.18);c.speckle(20,(0.002,0.005),0.12,light=True);c.grain(0.03);c.keep_mean(a.reshape(-1,3).mean(0))
save('podwall',fit(c,a.shape))
# ---------------- terrace slabs (12 m tile): 3 x 6 m slabs (joints kept), tone per slab, dirt in the joints, scuffs
a,c=canvas_from('terrace',12,12,24);c.a=a.copy()
c.mottle(0.03,(3,0.8,0.15));x=np.arange(c.n)/c.pu
for k in range(4):dd=np.abs(((x-k*3+6)%12)-6);c.mul(1-0.08*np.exp(-(dd/0.12)**2)[None,:])
for k in range(2):dd=np.abs(((x-k*6+6)%12)-6);c.mul(1-0.08*np.exp(-(dd/0.12)**2)[:,None])
c.speckle(0.8,(0.01,0.05),0.12);c.speckle(0.3,(0.05,0.2),0.05);c.grain(0.015);c.keep_mean(a.reshape(-1,3).mean(0));save('terrace',c.img())
# ---------------- plaza / deck / concrete paving: tile widened 2 m -> 8 m (UV scale in info.json, no geometry change) so
# the blotching does not repeat every 2 m. Saw cuts every 1 m as before, exposed aggregate, gum and oil spots.
def paving(n,seed):
    base=load(n);c=Canvas(8,8,base.reshape(-1,3).mean(0),seed,n=2048);c.mottle(0.07,(3.0,0.8,0.2))
    c.panels(1.0,1.0,joint=0.008,dark=0.80,tone=0.025,bevel=False)
    c.mul(1+0.10*c.R.normal(size=(c.n,c.n))*(c.R.random((c.n,c.n))<0.35))           # aggregate
    c.speckle(40,(0.004,0.009),0.18);c.speckle(25,(0.004,0.008),0.12,light=True)       # dark and pale stones in the mix
    c.speckle(0.6,(0.01,0.03),0.12);c.speckle(0.08,(0.1,0.35),0.04);c.tint(0.15,1.2,(0.85,0.82,0.78));c.grain(0.012)
    c.keep_mean();save(n,c.img())
paving('plaza',25);paving('deck',26);paving('concrete',27);I['plaza_m']=8.0
# ---------------- metal cladding (side blocks, 4 m tile): 0.3 m panels kept; seams catch light, streaks, grime
a,c=canvas_from('clad',4,4,28);c.a=a.copy();c.mottle(0.02,(1.5,0.4))
for k in range(14):c.hline(k*0.3+0.02,0.012,np.minimum(c.col*1.12,1),0.6)
c.streaks([k*0.3 for k in range(14)],per_m=0.4,length=(0.1,0.6),amt=0.10);c.grime_bottom(0.8,0.10);c.grain(0.008);c.keep_mean();save('clad',c.img())
# ---------------- grand stair: bench treads, aisle treads, risers - worn nosings, dirt in the back corner, scuffs
for n,seed in (('bench',29),('aisle',30),('riser',31)):
    a=load(n);h,w=a.shape[:2];base=a.copy()
    a*=(1+0.03*pn(h,w,10,40)+0.02*pn(h,w,1.5))[...,None]
    sp=R.random((h,w))<0.01;a[sp]*=0.82
    if n!='riser':
        vv=np.arange(h)[::-1]/h;a*=(1-0.08*np.clip((vv-0.9)/0.1,0,1))[:,None,None]   # dirt where the tread meets the next riser
    save(n,keep(a,base))
# ---------------- white steel (tubes: u round the 4 faces, v along the member, 4 m repeat): face tones (the underside
# holds grime and shade), splice line every 4 m, dust runs along the member, paint chips
a=load('white');base=a.copy();h,w=a.shape[:2];H2,W2=128,512
a=np.ones((H2,W2,3))*base.reshape(-1,3).mean(0);fq=(np.arange(W2)*4//W2)
a*=np.array([1.0,0.95,0.84,0.93])[fq][None,:,None]
a*=(1+0.045*pn(H2,W2,30,4)+0.02*pn(H2,W2,3,3))[...,None]
a[0:2]*=0.80;a[2:3]*=1.02
chip=nd.binary_dilation(R.random((H2,W2))<0.0015,structure=np.ones((2,2)));a[chip]*=0.85
save('white',keep(a,base))
# ---------------- white columns (u round, v up the full column, image bottom = foot): grime and splash dirt rising from the
# foot, rain tracks from the head, paint mottle, a joint ring at mid height
a=load('column');base=a.copy();h,w=a.shape[:2];yy=np.arange(h)[:,None]/h
a=np.ones_like(a)*base.reshape(-1,3).mean(0)
a*=(1-0.20*np.clip((yy-0.82)/0.18,0,1)**1.5*(1+0.4*pn(h,w,4,10)))[...,None]
a*=(1-0.06*np.clip(pn(h,w,60,3),0,None)*(1-yy)**0.5)[...,None]
a*=(1+0.035*pn(h,w,12,12)+0.015*R.standard_normal((h,w)))[...,None]
a[int(h*0.5):int(h*0.5)+2]*=0.82;save('column',keep(a,base))
# ---------------- lamp posts (galvanised grey): spangle mottle, darker foot, vertical drips
a=load('lamp');base=a.copy();h=w=128;yy=np.arange(h)[:,None]/h
a=np.ones((h,w,3))*base.reshape(-1,3).mean(0)
a*=(1+0.07*pn(h,w,3,3)+0.05*pn(h,w,20,2))[...,None];a*=(1-0.18*np.clip((yy-0.8)/0.2,0,1))[...,None]
save('lamp',keep(a,base))
# ---------------- dark steel rails (4 m repeat, 16 px/m): hand-polished top lines, dust, scuffs, darker underside
a=load('rail');base=a.copy();h=w=256;yy=np.arange(h)[:,None]/h
a=np.ones((h,w,3))*base.reshape(-1,3).mean(0)
a*=(1+0.15*pn(h,w,2,40)+0.09*pn(h,w,4,4))[...,None]
for y0 in (0.02,0.27,0.52,0.77):a*=(1+0.45*np.exp(-((yy-y0)/0.012)**2)*(1+0.5*pn(h,w,2,30)))[...,None]
sc=nd.binary_dilation(R.random((h,w))<0.0015,structure=np.ones((2,3)));a[sc]*=1.3
save('rail',keep(a,base))
# ---------------- balustrade mesh (alpha = wires): wire tone mottle, oxidised crossings, gaps a shade darker
m=np.asarray(Image.open(os.path.join(B,'mesh.png')).convert('RGBA'),float)/255;rgb=m[...,:3];al=m[...,3];h,w=al.shape
wire=al>0.5;f=np.where(wire,1.12,0.80)*(1+0.06*pn(h,w,10,10)+0.03*R.standard_normal((h,w)))
cross=wire&nd.binary_erosion(wire,structure=np.ones((1,3)))&nd.binary_erosion(wire,structure=np.ones((3,1)));f[cross]*=0.85
rgb=keep(rgb*f[...,None],m[...,:3])
Image.fromarray((np.clip(np.dstack([rgb,al]),0,1)*255+0.5).astype(np.uint8),'RGBA').save(os.path.join(T,'mesh.png'))
# ---------------- louvres and recess: grain and dust on the ribs only
for n,seed in (('louvre',32),('dark',33),('plouvre',34),('pglass',35)):
    a=load(n);h,w=a.shape[:2];base=a.copy();a*=(1+0.03*pn(h,w,6,40)+0.012*R.standard_normal((h,w)))[...,None];save(n,keep(a,base))
# ---------------- ground signs: OPTUS STADIUM, white letters on the bronze screen, the yellow "yes" script after the
# first one (refs o1, o2; Commons 018). Sign A segments 268-286 (o2 left sign = o1 sign); sign B segments 10-23
# (o2 right sign, text only: its end is past the edge of the stadium in o2). Letter centre 9.5 m under the screen top,
# letter height from the text length (o1: length 7.25 x height). Each map is the bronze screen itself, resampled
# exactly as the screen's UVs read it, so the panel joins its neighbours without a seam.
J=json.load(open(os.path.join(H_,'geom.json')));D=np.array(J['drum']);HB=np.array(J['hb']);N=J['N'];NB=J['NB']
sD=np.concatenate([[0],np.cumsum(np.linalg.norm(np.roll(D,-1,0)-D,axis=1))]);BAY2=2*sD[N]/NB;BH=I['bronze_h_m']
BR=np.asarray(Image.open(os.path.join(T,'bronze.png')).convert('RGB'),float)/255
SZ0,SZ1=7.0,39.0;PPM=60
SIGNS={'sign_a':(268,287,281,True),'sign_b':(10,24,23,False)}   # first seg, end seg (exclusive), text end seg, yes logo
FB=ImageFont.truetype('C:/Windows/Fonts/bahnschrift.ttf',400);FB.set_variation_by_name('Bold')        # Commons 018: wide rounded capitals, not condensed
FY=ImageFont.truetype('C:/Windows/Fonts/Inkfree.ttf',400)
def mask(txt,font,sw=0):
    bb=font.getbbox(txt,stroke_width=sw);im=Image.new('L',(bb[2]-bb[0],bb[3]-bb[1]),0);ImageDraw.Draw(im).text((-bb[0],-bb[1]),txt,font=font,fill=255,stroke_width=sw,stroke_fill=255)
    return im
signinfo={}
for name,(i0,i1,it,yes) in SIGNS.items():
    s0,s1=sD[i0],sD[i1];W=int((s1-s0)*PPM);Hh=int((SZ1-SZ0)*PPM)
    ss=s0+(np.arange(W)+0.5)/PPM;zz=SZ1-(np.arange(Hh)+0.5)/PPM
    hbs=np.interp(ss,sD[:N+1],np.concatenate([HB,[HB[0]]]))
    u=(ss/BAY2)%1;v=1-(hbs[None,:]-zz[:,None])/BH
    px=(u*BR.shape[1]).astype(int)%BR.shape[1];py=((1-v)*BR.shape[0]).astype(int)%BR.shape[0]
    A=BR[py,px[None,:]].copy()
    # letters
    tw=sD[it]-s0-0.4;cap=tw/7.25;zc=float(np.mean(hbs))-9.5
    m=mask('OPTUS STADIUM',FB);m=m.resize((int(tw*PPM),int(cap*PPM)),Image.LANCZOS)
    M=np.zeros((Hh,W));x0=int(0.2*PPM);y0=int((SZ1-zc-cap/2)*PPM)
    mm=np.asarray(m,float)/255;M[y0:y0+mm.shape[0],x0:x0+mm.shape[1]]=mm[:Hh-y0,:W-x0]
    Y=np.zeros((Hh,W))
    if yes:
        ym=mask('yes',FY,9);lw=1.8*cap;lh=2.0*cap;ym=ym.resize((int(lw*PPM),int(lh*PPM)),Image.LANCZOS)   # 018: 1.8 x 2.0 capitals
        yx=x0+int((tw+0.5*cap)*PPM);yy=int((SZ1-(zc+cap/2+0.3*cap))*PPM)                    # 018: half a capital after the M, top 0.3 capital above
        ya=np.asarray(ym,float)/255;ya=ya[:Hh-yy,:W-yx];Y[yy:yy+ya.shape[0],yx:yx+ya.shape[1]]=ya
    for L,col in ((M,np.array((0.95,0.95,0.93))),(Y,np.array((0.93,0.74,0.16)))):
        sh=nd.shift(L,(int(0.10*PPM),int(0.06*PPM)),order=0)                       # letters stand off the screen: shadow below
        A*=(1-0.45*np.clip(sh-L,0,1))[...,None]
        edge=np.clip(L-nd.grey_erosion(L,size=(5,5)),0,1)                           # lit top-left edge, darker return
        lc=col*(1+0.008*pn(Hh,W,30))[...,None]*(1-0.10*edge)[...,None]
        A=A*(1-L[...,None])+lc*L[...,None]
    save(name,A);signinfo[name]=[int(i0),int(i1),SZ0,SZ1]
    print(name,'segs',i0,i1,'width %.1f m'%(s1-s0),'text %.1f m cap %.2f m centre z %.1f'%(tw,cap,zc))
I['signs']=signinfo
json.dump(I,open(os.path.join(T,'info.json'),'w',newline=''))
print('painted')
