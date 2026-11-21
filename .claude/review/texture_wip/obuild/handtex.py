# Hand-made (procedural) textures for the Optus model. No photo pixels are copied: o2 is used only for colour picks
# (k-means swatches written below as constants) and, for the two side-building roofs, as a layout mask (orange/grey/ribbed).
# Usage: python handtex.py   -> writes tex/*.png and tex/info.json
import numpy as np,json,math,os
from PIL import Image,ImageDraw,ImageFont,ImageFilter
T=os.path.join(os.path.dirname(os.path.abspath(__file__)),'tex');RNG=np.random.default_rng(7)
def save(n,a):Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(os.path.join(T,n+'.png'))
def pnoise(h,w,scale,rng=RNG):
    """periodic (tileable) noise, feature size ~scale px, unit std"""
    z=rng.standard_normal((h,w));F=np.fft.fft2(z);ky=np.fft.fftfreq(h)[:,None];kx=np.fft.fftfreq(w)[None,:]
    k=np.sqrt(kx**2+ky**2);F*=np.exp(-(k*scale)**2*4);r=np.real(np.fft.ifft2(F));return (r-r.mean())/(r.std()+1e-9)
def col(c,h,w):return np.ones((h,w,3))*np.array(c,float)
def shade(a,n,amt):return a*(1+amt*n[...,None])
def fill(a,x0,y0,x1,y1,c):a[max(0,y0):max(0,y1),max(0,x0):max(0,x1)]=c
info={}
# ---------------- bronze screen: 2 bays (29.04 m) x 20.65 m, 70 px/m. Horizontal anodised blades, 0.55 m pitch.
BAYD=755.1/52;PM=70;W=int(round(2*BAYD*PM));H=int(round(20.65*PM))
PAL=np.array([(74,56,48),(91,70,60),(57,41,35),(113,91,78),(143,118,98)],float)*1.18;PW=np.array([.26,.23,.19,.16,.11]);PW/=PW.sum()
RED=np.array([(118,64,48),(132,78,58)],float)   # rust-red blades seen through the middle of the screen in o2
a=col((34,25,22),H,W);pitch=int(0.55*PM);gap=int(0.07*PM);half=W//2
brush=pnoise(H,W,1.2)*0.025+pnoise(H,W,30)*0.03
for y0 in range(0,H,pitch):
    for xs,xe in ((0,W),):
        x=-int(RNG.integers(0,4*PM));start=x
        while x<start+W:
            L=int(RNG.uniform(3.0,14.0)*PM);c=PAL[RNG.choice(5,p=PW)] if RNG.random()>0.07 else RED[RNG.integers(2)]
            g=np.linspace(1.02,0.95,pitch-gap)[:,None,None];glint=RNG.random()<0.18
            for xa,xb in ((x,x+L-int(0.04*PM)),(x+W,x+W+L-int(0.04*PM)),(x-W,x-W+L-int(0.04*PM))):
                x0,x1=max(xa,0),min(xb,W)
                if x1>x0:
                    blk=a[y0:y0+pitch-gap,x0:x1];blk[:]=c*g[:blk.shape[0]]   # blade face catches more light at its top
                    if glint:a[y0:y0+2,x0:x1]=(163,158,146)                   # bright top-edge glint (o2's thin light lines)
            x+=L
a=shade(a,brush,1.0)
save('bronze',a);info['bronze_h_m']=20.65
# ---------------- glass band: 2 bays (27.94 m) x 15.62 m, 70 px/m. v=1 is the top (z=33).
BAYR=726.5/52;W=int(round(2*BAYR*PM));H=int(round(15.62*PM))
a=col((54,67,68),H,W)
rows=np.arange(H)/PM  # metres down from the top
for k,y in enumerate(range(0,H,int(2.0*PM))):
    ph=int(2.0*PM);n=pnoise(1,W,40)[0]
    rowc=np.array((129,138,135)) if k%2==0 else np.array((60,73,74))
    for x0 in range(0,W,int(BAYR/8*PM)):
        x1=min(W,x0+int(BAYR/8*PM));c=rowc*RNG.uniform(0.94,1.06)
        grad=np.linspace(1.08,0.9,ph)[:,None,None];blk=a[y:y+ph,x0:x1]
        blk[:]=c*grad[:blk.shape[0]]
a=shade(a,pnoise(H,W,60),0.015)
for y in range(0,H,int(2.0*PM)):a[y:y+int(0.32*PM)]=(192,195,191);a[y+int(0.32*PM):y+int(0.36*PM)]=(150,155,152)  # slab edge / transom
for i,x in enumerate(range(0,W,int(BAYR/8*PM))):
    wd=5 if i%4 else 9;a[:,x:x+wd]=(200,203,200)
a[0:int(0.45*PM)]=(232,232,230)                                  # top edge beam under the roof
save('glass',a);info['glass_h_m']=15.62
# ---------------- seats: one bay (14.8 m) wide, v by height through the bowl (matches build.py VZ knots)
SW,SH=1024,4096;PX=SW/14.8;a=col((150,145,138),SH,SW)
def vy(v):return int(round((1-v)*SH))             # image row for texture v (v=0 ground, 1 top)
KN=[(0,1.0),(1.6,0.95),(12,0.71),(15,0.667),(31.5,0.0)]
def VZ(z):
    for (z0,f0),(z1,f1) in zip(KN,KN[1:]):
        if z<=z1:return 1-(f0+(f1-f0)*(z-z0)/(z1-z0))
    return 1.0
# tier colours read from o2's far stand (lit rows): lower tier pale grey, middle tier tan, upper tier grey (under the roof)
TIER={'lo':np.array((216,208,203)),'mid':np.array((246,221,191)),'up':np.array((178,182,188))}   # lit render vs o2 cols 880-960: lo x1.08, mid x1.15
GAP=np.array((66,62,60));CON=np.array((176,170,162));AIS=np.array((214,208,198))
aisles=[0.0,7.4]
def rowband(z0,z1,n,tier_of,aoff=0.0):
    for r in range(n):
        za=z0+(z1-z0)*r/n;zb=z0+(z1-z0)*(r+1)/n;zm=za+0.6*(zb-za)
        yA,yM,yB=vy(VZ(za)),vy(VZ(zm)),vy(VZ(zb))   # yA bottom (larger row index), yB top
        SC=TIER[tier_of(r)]*(1.0 if r%2 else 0.96)
        a[yM:yA]=CON                                   # tread (walkway in front of the seats)
        a[yB:yM]=SC*0.88                               # riser zone: seat backs
        t=yA-yM;a[yM:yM+max(1,t//2)]=SC                # seat pans on the tread
        s=int(0.5*PX)
        for x in range(0,SW,s):a[yB:yM+max(1,t//2),x:x+2]=GAP     # gaps between seats
        a[yB:yB+max(1,(yM-yB)//5)]=GAP*1.2                        # shadow line under the row above
        for ax in aisles:                                         # stair aisles: pale concrete, step nosings
            x0=int((ax+aoff)*PX)-int(0.6*PX);x1=int((ax+aoff)*PX)+int(0.6*PX)
            for xa,xb in ((x0,x1),(x0+SW,x1+SW),(x0-SW,x1-SW)):
                xa_,xb_=max(0,xa),min(SW,xb)
                if xb_>xa_:a[yB:yA,xa_:xb_]=AIS;a[yM-1:yM+1,xa_:xb_]=(150,146,140);a[yA-2:yA,xa_:xb_]=(236,234,228)
ZT=6.4                                                    # teal fascia between lower and middle tier (o2: 0.45 up the rake)
rowband(1.6,12.0,24,lambda r:'lo' if 1.6+10.4*(r+1)/24<=ZT+0.01 else 'mid')
rowband(15.0,31.5,30,lambda r:'up',aoff=3.7)
yT1,yT0=vy(VZ(ZT+0.45)),vy(VZ(ZT));a[yT1:yT0]=(46,96,104);a[yT1:yT1+max(1,(yT0-yT1)//4)]=(226,228,226)   # teal fascia, white capping
# vomitories at the top of the middle tier, one per bay (o2: dark mouths with white frames)
vx0,vx1=int(3.2*PX),int(5.0*PX);vy0,vy1=vy(VZ(12.0)),vy(VZ(10.2));a[vy0:vy1,vx0:vx1]=(34,32,32)
a[vy0:vy1,vx0-4:vx0]=(220,220,216);a[vy0:vy1,vx1:vx1+4]=(220,220,216);a[vy0:vy0+4,vx0-4:vx1+4]=(220,220,216)
# front fence z 0..1.6: blank dark teal boards (director: "C: no lettering")
y1,y0=vy(VZ(1.6)),vy(VZ(0.0));a[y1:y0]=(42,58,62)
# suites band z 12..15 (o2: white rail over dark glazed boxes)
y1,y0=vy(VZ(15.0)),vy(VZ(12.0));h_=y0-y1;a[y1:y0]=(78,90,98)
a[y1+h_//2:y0]=(62,72,78)                                             # glass darker low down (interior)
a[y1:y1+max(2,h_//7)]=(232,232,230);a[y1+h_//3:y1+h_//3+max(2,h_//14)]=(206,208,206)   # white balustrade rail + glass rail
a[y0-max(2,h_//9):y0]=(186,182,176)                                    # slab edge
for x in range(0,SW,int(1.85*PX)):a[y1+h_//7:y0-h_//9,x:x+3]=(140,146,148)
a=shade(a,pnoise(SH,SW,3),0.025)
save('seats',a);info['stand_bay_m']=14.8
# ---------------- turf: 32 m tile, 64 px/m, tileable grass (no mowing stripes visible in o2)
S=2048;n=pnoise(S,S,0.8)*0.06+pnoise(S,S,6)*0.035+pnoise(S,S,120)*0.012
a=shade(col((124,136,67),S,S),n,1.0);a[...,0]+=pnoise(S,S,200)[...]*3
save('turf',a);info['turf_m']=32.0
# ---------------- roof membrane (top): 8 m tile, 128 px/m; white PTFE with radial seams every 1.6 m
S=1024;a=col((226,226,225),S,S);a=shade(a,pnoise(S,S,25)*0.012+pnoise(S,S,2)*0.006,1.0)
for x in range(0,S,int(1.6*128)):a[:,x:x+3]*=0.93
save('roof',a)
# roof underside: 10 m tile, 102 px/m; off-white with purlin shadows
S=1024;a=col((206,207,208),S,S);a=shade(a,pnoise(S,S,40),0.015)
for x in range(0,S,int(2.5*102.4)):a[:,x:x+10]=(178,180,182)
save('under',a)
# white painted steel (trusses, edge beams)
a=col((238,238,236),64,256);a=shade(a,pnoise(64,256,4),0.01);save('white',a)
# ---------------- recess under the screen: 4 m tile, 64 px/m; deep shadow with one white post (o2 posts ~3.8 m apart)
a=col((46,41,39),256,256);a=shade(a,pnoise(256,256,10),0.05);a[:,120:140]=(214,214,210);save('dark',a)
# ---------------- podium wall: precast sandstone panels 2.4 x 1.2 m (054), tile 4.8 x 2.4 m, 200 px/m
PP=200;W,H=int(4.8*PP),int(2.4*PP);a=col((206,184,165),H,W)
a=shade(a,pnoise(H,W,1.0)*0.03+pnoise(H,W,50)*0.02,1.0)
for r in range(2):
    y=r*int(1.2*PP);a[y:y+3]=(123,111,99);off=int(RNG.integers(-12,12))
    for x in (0,int(2.4*PP),W):
        xa,xb=max(0,x+off),min(W,x+off+3)
        if xb>xa:a[y:y+int(1.2*PP),xa:xb]=(123,111,99)
save('podwall',a);info['podwall_m']=[4.8,2.4]
# ---------------- paving: 2 m tile, 256 px/m, exposed-aggregate concrete with saw-cut joints every 1 m
def paving(n,base,spk):
    S=512;a=col(base,S,S);a=shade(a,pnoise(S,S,0.7)*0.05+pnoise(S,S,60)*0.02,1.0)
    m=RNG.random((S,S))<0.04;a[m]=np.array(spk)
    for x in (0,256):a[:,x:x+2]*=0.8;a[x:x+2,:]*=0.8
    save(n,a)
paving('plaza',(195,175,155),(150,138,122));paving('deck',(176,176,174),(130,130,128))
paving('concrete',(200,192,182),(150,144,138));info['plaza_m']=2.0
# ---------------- grand stair (o2): bench terraces between two concrete aisles. u = 2.4 m across, v = one tread
# (v=0 nosing at the front, v=1 back against the next riser). 512 x 256 px.
CONC=np.array((204,178,150));W2,H2=512,256;vv=np.arange(H2)[::-1][:,None]/H2   # vv: v of each image row
a=col(CONC,H2,W2);a=shade(a,pnoise(H2,W2,1.2)*0.03+pnoise(H2,W2,30)*0.02,1.0)
a[vv[:,0]<0.04]=(226,206,180)                                 # worn bright nosing
sl=(vv[:,0]>0.48)&(vv[:,0]<0.92)                               # bench zone at the back of the tread
a[sl]=(60,55,52)                                               # shadow under the slats
for k in range(3):                                             # three dark timber/composite slats
    m=(vv[:,0]>0.50+k*0.14)&(vv[:,0]<0.50+k*0.14+0.10);a[m]=(112,100,90)*np.array([1.0,1.0,1.0])*(1.04-0.03*k)
for x in (0,256):a[sl,x:x+12]=(214,214,210)                    # silver bench frames every 1.2 m
a[(vv[:,0]>0.92)]=CONC*0.9;save('bench',a)
a=col(CONC,H2,W2);a=shade(a,pnoise(H2,W2,1.2)*0.03+pnoise(H2,W2,30)*0.02,1.0)          # aisle tread: two half steps
a[vv[:,0]<0.04]=(226,206,180);m=(vv[:,0]>0.48)&(vv[:,0]<0.52);a[m]=(150,128,108);a[(vv[:,0]>0.52)&(vv[:,0]<0.56)]=(226,206,180)
save('aisle',a)
a=col((206,186,162),64,W2);a=shade(a,pnoise(64,W2,1.0)*0.03,1.0);a[:,0:4]=(140,124,108);a[0:3]=(150,132,114);save('riser',a)
# ---------------- terrace slabs (o2: large pale concrete slabs, tone varies slab to slab, dark saw cuts): 12 m tile, 64 px/m
S=768;a=col((192,186,178),S,S);a=shade(a,pnoise(S,S,0.8)*0.035+pnoise(S,S,40)*0.02,1.0)
sx,sy=int(3*64),int(6*64)
for i in range(0,S,sx):
    for j in range(0,S,sy):a[j:j+sy,i:i+sx]*=RNG.uniform(0.93,1.06)
for i in range(0,S,sx):a[:,i:i+3]=(126,120,114)
for j in range(0,S,sy):a[j:j+3,:]=(126,120,114)
save('terrace',a);info['terrace_m']=12.0
# ---------------- metal cladding of the side buildings: 4 m tile, 128 px/m, 0.3 m horizontal panels
a=col((168,166,164),512,512);a=shade(a,pnoise(512,512,30),0.008)
for y in range(0,512,int(0.3*128)):a[y:y+2]=(120,114,110)
save('clad',a)
# louvre (ribbed dark metal roof section): 4 m tile, ribs every 0.25 m
a=col((92,94,100),512,512)
for x in range(0,512,32):a[:,x:x+10]=(64,68,76);a[:,x+10:x+12]=(130,132,138)
save('louvre',a)
# grille (podium vehicle openings): 4 m tile, vertical bars 0.1 m apart over black
a=col((22,22,24),512,512)
for x in range(0,512,13):a[:,x:x+5]=(150,150,148)
save('grille',a)
# ---------------- side-building roofs: one texture each, 64 m span, 16 px/m. Layout (orange band / grey gravel /
# ribbed metal) is classified from o2 at each roof point; the fill is hand-made.
P=json.load(open(os.path.join(os.path.dirname(T),'cam7.json')))['p'];O=np.asarray(Image.open(os.path.join(os.path.dirname(T),'photo.jpg')).convert('RGB')).astype(float)
J=json.load(open(os.path.join(os.path.dirname(T),'geom.json')))
yw,pi,ro=P[3],P[4],P[5];f=np.array([math.cos(yw)*math.cos(pi),math.sin(yw)*math.cos(pi),math.sin(pi)]);r=np.array([math.sin(yw),-math.cos(yw),0]);u=np.cross(r,f)
R0=math.cos(ro)*r+math.sin(ro)*u;R1=-math.sin(ro)*r+math.cos(ro)*u
def proj(X):
    d=X-np.array(P[:3]);z=d@f;return P[7]+P[6]*(d@R0)/z,P[8]-P[6]*(d@R1)/z
for name,h in (('near',9.2),('far',9.0)):
    pts=np.array(J['bld'][name]);cc=pts.mean(0);S=1024;sp=64.0
    gy,gx=np.mgrid[0:S,0:S];X=cc[0]+(gx/S-0.5)*sp;Y=cc[1]+((S-1-gy)/S-0.5)*sp
    px,py=proj(np.stack([X,Y,np.full_like(X,h)],-1));ix=np.clip(px.astype(int),0,1919);iy=np.clip(py.astype(int),0,1078)
    c=O[iy,ix];orange=(c[...,0]-c[...,2]>45)&(c[...,0]>120);dark=(c.mean(-1)<110)&~orange
    def sm(b,k=15):return np.asarray(Image.fromarray((b*255).astype(np.uint8)).filter(ImageFilter.MedianFilter(k)).filter(ImageFilter.GaussianBlur(2)))>127
    m=sm(orange);dk=sm(dark,21)&~m
    a=col((141,136,130),S,S);a=shade(a,pnoise(S,S,0.6)*0.08,1.0)               # grey gravel
    og=shade(col((172,112,78),S,S),pnoise(S,S,0.6)*0.08,1.0);a[m]=og[m]           # orange gravel band
    rb=col((96,96,102),S,S)                                                        # ribbed dark metal deck, rib every 0.5 m
    for x in range(0,S,8):rb[:,x:x+3]=(66,70,78);rb[:,x+3:x+4]=(132,134,140)
    a[dk]=rb[dk]
    save('proof_'+name,a)
info['proof_span_m']=64.0
json.dump(info,open(os.path.join(T,'info.json'),'w',newline=''))
print('ok',info)
