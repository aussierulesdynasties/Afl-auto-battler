# Hand-painted textures for People First Stadium. No photo pixels: colours are numbers read from the photo (k-means swatches).
# Each texture is tileable; its real size in metres is in TEX (used by build5.py to scale the UVs).
import numpy as np,json
from PIL import Image
from scipy.ndimage import zoom
rng=np.random.default_rng(7)
TEX={}
def noise(h,w,sc,amp,seed=0):
    r=np.random.default_rng(seed);n=np.zeros((h,w))
    for o in range(4):
        s=max(1,int(sc/(2**o)));g=r.standard_normal((h//s+2,w//s+2))
        g=zoom(g,s,order=3)[:h,:w];n+=g/(2**o)
    return n*amp
def img(h,w,c):a=np.zeros((h,w,3));a[:]=c;return a
def save(a,name,mw,mh):
    Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save('htex/'+name+'.png');TEX[name]=[mw,mh]
def rect(a,x0,y0,x1,y1,c):a[max(0,int(y0)):int(y1),max(0,int(x0)):int(x1)]=c
PPM=64
# seats: rows along v (v=0 front/low edge -> up the slope), seats along u. tile 4 m x 4 rows.
def seats(name,pitch,grey_frac,seed,pan=(0.16,0.60,0.90,0.94)):
    r=np.random.default_rng(seed);W=4*PPM;H=int(round(4*pitch*PPM));a=img(H,W,(196,186,180))   # tread concrete (photo 206,181,176 in shade mix)
    a+=noise(H,W,6,5,seed)[...,None]
    rp=H/4;sw=0.5*PPM
    for k in range(4):
        y0=k*rp
        rect(a,0,y0,W,y0+rp*0.08,(150,140,138))                    # riser shadow line at the row front
        for j in range(int(W/sw)):
            x0=j*sw;red=r.random()>grey_frac
            base=np.array((242,92,74)) if red else np.array((214,208,202))
            back=base*0.88
            rect(a,x0+2,y0+rp*pan[0],x0+sw-2,y0+rp*pan[1],base)              # seat pan
            rect(a,x0+2,y0+rp*pan[1],x0+sw-2,y0+rp*pan[2],back)              # seat back
            rect(a,x0+2,y0+rp*pan[2],x0+sw-2,y0+rp*pan[3],back*0.7)          # back top edge
    save(a,name,4.0,4*pitch)
seats('seat_low',0.70,0.0,1,(0.10,0.58,0.95,0.98));seats('seat_up',0.86,0.22,2)
# aisle steps: two steps per row, light concrete, yellow-free nosing, centre handrail
def aisle(name,pitch):
    W=int(1.1*PPM);H=int(round(4*pitch*PPM));a=img(H,W,(204,201,196))+noise(H,int(1.1*PPM),5,5,3)[...,None]
    st=H/8
    for k in range(8):rect(a,0,k*st,W,k*st+3,(160,156,152))
    rect(a,W//2-2,0,W//2+2,H,(120,124,130));save(a,name,1.1,4*pitch)
aisle('aisle_low',0.70);aisle('aisle_up',0.86)
# concrete (light, precast panels 3 m x 1.5 m)
def panels(name,col,pw,ph,joint,jc,nz,seed,mw=6.0,mh=3.0):
    W,H=int(mw*PPM),int(mh*PPM);a=img(H,W,col)+noise(H,W,8,nz,seed)[...,None]
    for x in np.arange(0,mw,pw):rect(a,x*PPM,0,x*PPM+joint,H,jc)
    for y in np.arange(0,mh,ph):rect(a,0,y*PPM,W,y*PPM+joint,jc)
    save(a,name,mw,mh)
panels('concrete',(190,188,182),3.0,1.5,2,(160,158,154),6,4)
panels('walk',(172,172,168),2.0,2.0,2,(150,150,147),5,5)
panels('apron',(168,168,163),2.0,2.0,2,(146,146,142),5,6)
panels('navy',(58,76,110),1.5,3.0,2,(38,50,74),3,7)  # blue lifted: render median 69,84,103 vs photo 66,82,114 (r16)
panels('dark',(56,58,66),1.2,1.2,2,(38,40,46),3,8)
panels('red',(205,44,40),3.0,3.0,2,(160,30,28),4,9)
panels('white',(236,236,234),3.0,1.5,2,(205,205,202),3,10)
panels('tower',(236,233,229),6.0,6.0,2,(205,202,198),3,11,6.0,6.0)
panels('yellow',(238,190,40),6.0,6.0,1,(210,165,30),4,12,6.0,6.0)
# glass: dark blue glazing, mullions 1.5 m, transoms at 1 m and 3 m
W,H=int(6*PPM),int(4*PPM);a=img(H,W,(48,58,76))+noise(H,W,16,6,13)[...,None]
for x in np.arange(0,6,1.5):rect(a,x*PPM,0,x*PPM+4,H,(150,156,166))
for y in (0,1.0,3.0):rect(a,0,y*PPM,W,y*PPM+4,(150,156,166))
save(a,'glass',6.0,4.0)
# roof membrane (PTFE white), seams every 1.5 m along u
W,H=int(30*PPM),int(30*PPM);a=img(H,W,(247,247,245))+noise(H,W,20,2.5,14)[...,None]   # 30 m tile: 5 m soiling on a 6 m tile repeated as a quilt
for x in np.arange(0,30,1.5):rect(a,x*PPM,0,x*PPM+2,H,(232,232,230))
save(a,'roof',30.0,30.0)
W,H=int(6*PPM),int(6*PPM);a=img(H,W,(212,212,208))+noise(H,W,20,3,15)[...,None]
for y in np.arange(0,6,2.0):rect(a,0,y*PPM,W,y*PPM+5,(170,170,166))
save(a,'roofunder',6.0,6.0)
panels('podroof',(234,231,227),6.0,6.0,2,(229,226,222),2.5,16,12.0,12.0)
# LED fascia (photo, far stand, x 975 / 1100): 2.9 m parapet face: white cap 0.15 m, pale blue LED 1.55 m (lettering left out), navy 1.2 m; panel seams 1 m
W,H=int(8*PPM),int(2.9*PPM);a=img(H,W,(32,42,63))+noise(H,W,6,2,21)[...,None]
c0,c1=int(0.15*PPM),int(1.70*PPM)
a[:c0]=(236,236,232);a[c0:c1]=(178,216,238);a[c0:c1]+=noise(c1-c0,W,4,2,22)[...,None];a[c1-3:c1]=(110,160,195)
for k in range(8):rect(a,k*PPM,c0,k*PPM+2,c1,(150,190,215));rect(a,k*PPM,c1,k*PPM+2,H,(24,32,50))
save(a,'led',8.0,2.9)
# field-side fence (photo: white board face; the LED ads on it are left out): white panels 2 m, navy capping rail, grime toward the bottom
W,H=int(8*PPM),int(1.0*PPM);a=img(H,W,(236,236,233))+noise(H,W,5,3,23)[...,None]
a[:4]=(40,48,70)
yy=np.linspace(0,1,H)[:,None,None];a-=12*yy**3
for k in range(4):rect(a,k*2*PPM,0,k*2*PPM+2,H,(196,196,192))
save(a,'fencelow',8.0,1.0)
# podium fins: vertical fins 0.6 m pitch on a white wall; each fin stacked colour blocks (blue, red, orange, yellow) 0.8-2.4 m tall
W,H=int(12*PPM),int(10.6*PPM);a=img(H,W,(224,222,219))+noise(H,W,6,3,17)[...,None]
pal=[(52,86,170),(208,58,48),(238,136,58),(244,196,88)]
r=np.random.default_rng(18)
for i in range(int(12/0.6)):
    x0=i*0.6*PPM+0.12*PPM;y=0.4*PPM;ci=r.integers(4)
    while y<H-0.3*PPM:
        h=r.uniform(0.8,2.4)*PPM;ci=(ci+1+r.integers(3))%4
        rect(a,x0,y,x0+0.36*PPM,min(y+h,H-0.3*PPM),pal[ci]);rect(a,x0+0.36*PPM,y,x0+0.42*PPM,min(y+h,H-0.3*PPM),np.array(pal[ci])*0.6);y+=h+0.06*PPM
save(a,'stripes',12.0,10.6)
# scoreboard screen: dark LED with a fine pixel grid
W,H=int(4*PPM),int(4*PPM);a=img(H,W,(22,26,38))
a[::4,:]=(14,16,24);a[:,::4]=(14,16,24);save(a,'screen',4.0,4.0)
# lamp face: grid of round lamps
W,H=int(1*PPM),int(1*PPM);a=img(H,W,(70,74,82));yy,xx=np.mgrid[0:H,0:W];m=(xx-W/2)**2+(yy-H/2)**2<(0.4*PPM)**2
a[m]=(236,238,240);save(a,'lamps',1.0,1.0)

# scoreboard face (photo-read colours; layout fractions measured on the photo's pixel grid)
import cv2
SBW,SBH=33.7,10.6;   # 29.7 m screen + 2 m over each end post
W,H=int(SBW*PPM),int(SBH*PPM);a=img(H,W,(28,32,42))
a+=noise(H,W,3,2,11)[...,None];a[::6,:]*=0.92;a[:,::6]*=0.92                  # LED pixel pitch
a[:int(0.015*H)]=(250,249,248)                                                  # white top edge
a[int(0.93*H):int(0.975*H)]=(17,114,182);a[int(0.975*H):]=(250,249,248)        # blue LED strip, white lip
b=np.ascontiguousarray(np.clip(a,0,255).astype(np.uint8))
# fs=H*0.15/22.0;cv2.putText(b,'metricon',(int((6.5+2)/SBW*W),int(0.25*H)),cv2.FONT_HERSHEY_DUPLEX|cv2.FONT_ITALIC,fs,(254,253,248),max(2,int(fs*2.2)),cv2.LINE_AA)   # removed: director 'C: no lettering' 2026-11-18
# cv2.ellipse(b,(int((15.7+2)/SBW*W),int(0.13*H)),(int(2.1/SBW*W),int(0.05*H)),0,200,340,(214,170,70),max(2,int(H*0.012)),cv2.LINE_AA)   # gold swoosh (arrays are RGB)   # removed: director 'C: no lettering' 2026-11-18
a=b.astype(float);save(a,'scorefront',SBW,SBH)
# side post: white with two blue right-pointing triangles
W,H=int(3.4*PPM),int(12.2*PPM);a=img(H,W,(250,249,248));b=np.ascontiguousarray(a.astype(np.uint8))
for t0,sp in ((0.21,0.23),(0.60,0.25)):   # two triangles per face, base at 0.28 W, apex at 0.96 W (photo grid x8)
    pts=np.array([[int(0.28*W),int(t0*H)],[int(0.96*W),int((t0+sp/2)*H)],[int(0.28*W),int((t0+sp)*H)]],np.int32);cv2.fillPoly(b,[pts],(3,112,205),cv2.LINE_AA)
save(b.astype(float),'scorepost',3.4,12.2)
# sign under the board: red with white frame
W,H=int(8.3*PPM),int(2.6*PPM);a=img(H,W,(243,56,59));a[:6]=a[-6:]=(250,249,248);a[:,:6]=a[:,-6:]=(250,249,248);a+=noise(H,W,4,3,12)[...,None];save(a,'redsign',8.3,2.6)
# grass (north-end strip behind the goals, satellite 2026): green, mown stripes 1 m, clumps
W,H=int(4*PPM),int(4*PPM);a=img(H,W,(98,132,62))+noise(H,W,6,9,21)[...,None]*np.array([0.8,1,0.6])
for k in range(4):
    if k%2:a[:,k*PPM:(k+1)*PPM]*=1.06
save(a,'grass',4.0,4.0)
# ground's own sign "People First Stadium" (south end, behind the stand, centred on the 250 deg rib).
# Copied by hand from a current photo (news.com.au rename story, drone shot): layout as fractions of the panel,
# panel edges in the photo tilt 8 px over its width (top 338-346, height 120 px): v measured from the local top edge.
# colours = photo medians x1.4 (the sign hangs in shade; x1.4 brings the white lettering to white). Font: Segoe UI Semibold.
from PIL import ImageDraw,ImageFont
SGW,SGH=40.5,5.5;W,H=int(SGW*PPM),int(SGH*PPM)
im=Image.new('RGB',(W,H),(10,8,66));d=ImageDraw.Draw(im)
def bx(u0,v0,u1,v1):return [int(u0*W),int(v0*H),int(u1*W),int(v1*H)]
P_,G_,B_=(83,80,179),(22,118,91),(11,123,210)
x0,y0,x1,y1=bx(0.270,0.090,0.2925,0.250);d.pieslice([2*x0-x1,2*y0-y1,x1,y1],0,90,fill=P_)                 # i dot: quarter disc, square corner top-left
x0,y0,x1,y1=bx(0.2714,0.348,0.2952,0.932);w_=x1-x0
d.rectangle([x0,y0,x1,y1-w_],fill=G_);d.rectangle([x0+w_//2,y1-w_,x1,y1],fill=G_);d.pieslice([x0,y1-2*w_,x0+2*w_,y1],90,180,fill=G_)   # stem, bottom-left rounded
x0,y0,x1,y1=bx(0.3138,0.093,0.3521,0.668);d.pieslice([2*x0-x1,y0,x1,y1],270,450,fill=B_)                  # blue half-disc, flat side left
FNT=ImageFont.truetype('C:/Windows/Fonts/seguisb.ttf',200)
def ink(t,sw):
    g=Image.new('L',(1400,400),0);ImageDraw.Draw(g).text((50,50),t,font=FNT,fill=255,stroke_width=sw,stroke_fill=255);return g
CAPH=np.where(np.asarray(ink('H',1)).max(1)>0)[0];CAPT,CAPB=CAPH.min(),CAPH.max()   # cap top / baseline rows
def word(t,u0,u1,vtop,vbase):
    # measured on the photo: left/right ink edges (u) and cap top / baseline (v) of each word
    g=ink(t,0);xs=np.where(np.asarray(g).max(0)>0)[0];g=g.crop((xs.min(),CAPT,xs.max()+1,400))
    sy=(vbase-vtop)*H/(CAPB-CAPT);sx=(u1-u0)*W/g.width
    g=g.resize((max(1,round(g.width*sx)),max(1,round(g.height*sy))),Image.LANCZOS)
    im.paste((236,238,244),(int(u0*W),int(vtop*H)),g)
word('People',0.381,0.5915,0.100,0.467);word('First',0.6034,0.7248,0.100,0.467);word('Stadium',0.381,0.6197,0.592,0.969)
a=np.asarray(im).astype(float)+noise(H,W,6,2.5,31)[...,None]
rect(a,W//2-1,0,W//2+1,H,(4,4,40))                                                                       # panel seam at the centre column
a[:3]=a[-3:]=(30,30,70);save(a,'pfsign',SGW,SGH)

# ---- weathering pass (hand-made, procedural): tileable blotches, rain streaks running down from each joint, grime
# under joints, fine grain. Each texture is matched by eye to its photo crop (z_texboard); clean surfaces stay clean.
def pnoise(h,w,sx,sy,seed):
    # periodic (tileable) noise: white noise filtered in the frequency domain, std 1; sx/sy = feature size in px
    r=np.random.default_rng(seed);F=np.fft.fft2(r.standard_normal((h,w)))
    fy=np.fft.fftfreq(h)[:,None];fx=np.fft.fftfreq(w)[None,:];F*=np.exp(-((fx*sx)**2+(fy*sy)**2)*6)
    n=np.real(np.fft.ifft2(F));return (n-n.mean())/(n.std()+1e-9)
def weather(name,blot,streak,grain,seed,joints_y=(),stain=0.0,stain_len=0.6):
    p='htex/'+name+'.png';a=np.asarray(Image.open(p).convert('RGB')).astype(float);h,w=a.shape[:2]
    d=blot*pnoise(h,w,PPM*1.2,PPM*1.2,seed)+streak*pnoise(h,w,6,PPM*1.5,seed+1)*(0.5+0.5*pnoise(h,w,PPM*0.8,PPM*3,seed+2).clip(0,None))
    d+=grain*np.random.default_rng(seed+3).standard_normal((h,w))
    yy=np.arange(h)[:,None]
    for yj in joints_y:                                   # dark run-off below each horizontal joint (image row 0 = top)
        t=(yy-yj*PPM)%h;d-=stain*np.exp(-t/(stain_len*PPM))*(0.6+0.4*pnoise(h,w,8,PPM,seed+4).clip(-1,1))
    a+=d[...,None];Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(p)
weather('concrete',4,3,2,40,joints_y=(0,1.5),stain=6)
weather('walk',8,2,4,41);weather('apron',8,2,4,42)
weather('navy',7,7,3,43,joints_y=(0,),stain=6);weather('dark',8,6,3,44,joints_y=(0,),stain=6)
weather('red',7,6,3,45,joints_y=(0,),stain=10);weather('white',2,2,1,46,joints_y=(0,1.5),stain=3)
weather('tower',2,2,1,47,joints_y=(0,),stain=3,stain_len=1.5);weather('yellow',7,7,3,48,stain=0)
# roof membrane: clean PTFE in the photo (clean patch at x 1000-1100, y 880-930: grey std 1.6), so only faint soft soiling
_p='htex/roof.png';_a=np.asarray(Image.open(_p).convert('RGB')).astype(float);_h,_w=_a.shape[:2]
_d=-abs(3*pnoise(_h,_w,PPM*5,PPM*5,49))+1*pnoise(_h,_w,6,PPM*2,50)+1*np.random.default_rng(51).standard_normal((_h,_w))
Image.fromarray(np.clip(_a+_d[...,None]+5,0,255).astype(np.uint8)).save(_p)
weather('roofunder',7,4,3,50);weather('podroof',2,1,1,51)
weather('grass',9,0,4,52);weather('screen',3,0,9,53)
json.dump(TEX,open('htex/tex.json','w',newline=''),indent=1);print(TEX)
