# Hand-made textures for the Norwood Oval exterior. No photo pixels: every image is painted here from numbers.
# Colours were read by eye from the date-checked photos (c32 2021+, main April 2024, Street View rear views).
# Each texture is drawn at real scale (px per metre); spec.json says how it maps onto faces:
#   mode 'wall': u = metres along the face's horizontal, v = metres up the face (tiles every tw x th)
#   mode 'fit' : the image covers the face's bounding box once (unique panels: signs, pediments)
import numpy as np, json, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ImageDraw.ImageDraw.text=lambda self,*a,**k: None   # director 2026-11-18 "C: no lettering": every sign is a blank panel (ground, club and stand names included)
OUT=os.path.join(os.path.dirname(__file__),'..','tex'); os.makedirs(OUT,exist_ok=True)
rng=np.random.default_rng(7)
SPEC={}
def save(name,a,tw,th,mode='wall',alpha=False):
    a=np.clip(a,0,255).astype(np.uint8)
    Image.fromarray(a,'RGBA' if alpha else 'RGB').save(os.path.join(OUT,name+'.png'))
    SPEC[name]=dict(img=name+'.png',tw=tw,th=th,mode=mode,alpha=alpha)
def canvas(w,h,c): return np.ones((h,w,3))*np.array(c,float)
def noise(h,w,s=1.0,blur=0):
    n=rng.normal(0,1,(h,w))
    if blur: n=np.array(Image.fromarray(((n*40)+128).clip(0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur)),float)/40-3.2
    return n*s
def font(sz,bold=True):
    for f in (['arialbd.ttf','Arial Bold.ttf'] if bold else ['arial.ttf']):
        try: return ImageFont.truetype(f,sz)
        except OSError: pass
    return ImageFont.load_default()
def seamless(a):  # wrap-blur noise so tiles meet cleanly
    return a
# ---------- corrugated steel: 76 mm pitch, ribs run along v (down the slope / up the wall) ----------
def corrugated(name,col,ppm=256,tw=1.0,th=1.0,pitch=0.076,amp=0.22):
    W,H=int(tw*ppm),int(th*ppm);x=np.arange(W)/ppm
    k=np.round(tw/pitch);ph=2*np.pi*x*k/tw
    shade=1+amp*np.sin(ph)                     # light from one side of each rib
    a=canvas(W,H,col)*shade[None,:,None]
    a+=noise(H,W,2.5)[...,None]
    # sheet laps every 0.762 m (10 ribs) as a slightly darker line
    lap=(np.abs(((x/0.762)%1)-0)<1.5/ppm/0.762)
    a[:,lap]*=0.85
    save(name,a,tw,th)
corrugated('corr_red',(150,52,47))          # Sir Edwin Smith Stand, huts: Colorbond red (c32)
corrugated('corr_slate',(96,102,108))       # bluestone clubrooms, hall: dark grey sheet (main photo)
corrugated('corr_zinc',(190,194,194))       # light zinc roofs (north block, Western Stand)
corrugated('corr_wsrear',(150,154,158))
corrugated('corr_green',(112,128,110))      # annex roof
corrugated('corr_maroon',(122,42,42),pitch=0.076,amp=0.18)   # Western Stand north wall, fence sheets (woods4)
corrugated('corr_cream',(205,200,186))      # SE hut
# ---------- brick: 230x76 mm, 10 mm joints, stretcher bond ----------
def brick(name,base=(150,62,48),mortar=(196,186,170),ppm=256,tw=1.2,th=0.86,var=9):
    W,H=int(tw*ppm),int(th*ppm);a=canvas(W,H,mortar)+noise(H,W,3)[...,None]
    bw,bh,j=0.24,0.086,0.01
    for r in range(int(round(th/bh))):
        off=(r%2)*bw/2
        for c in range(-1,int(tw/bw)+1):
            x0=c*bw+off;y0=r*bh
            col=np.array(base)+rng.normal(0,var)*np.array([1,0.8,0.7])+rng.normal(0,2.5,3)
            X0=int((x0+j/2)*ppm);X1=int((x0+bw-j/2)*ppm);Y0=int((y0+j/2)*ppm);Y1=int((y0+bh-j/2)*ppm)
            xs=[(X0+W)%W,(X1+W)%W]
            for xa,xb in ([(X0,X1)] if 0<=X0 and X1<=W else [(max(X0,0),min(X1,W)),((X0%W) if X0<0 else 0,(X1-W) if X1>W else 0)]):
                if xb>xa: a[Y0:Y1,xa:xb]=col+noise(Y1-Y0,xb-xa,4)[...,None]
    save(name,a,tw,th)
    return a
BR=brick('brick_red')
brick('brick_dark',base=(118,48,40),var=7)
# ---------- bluestone rubble (clubrooms walls), with no tiling seam inside a 2 m tile ----------
def bluestone(name,ppm=200,tw=2.0,th=1.2):
    W,H=int(tw*ppm),int(th*ppm);a=canvas(W,H,(150,140,124))+noise(H,W,4)[...,None]
    y=0
    while y<H:
        h=int(rng.uniform(0.16,0.3)*ppm);x=int(rng.uniform(0,0.2)*ppm)-int(0.2*ppm)
        while x<W:
            w=int(rng.uniform(0.25,0.55)*ppm);c=np.array([96,96,98])+rng.normal(0,11)+rng.normal(0,2.5,3)+(rng.random()<0.25)*np.array([14,8,0])
            im=Image.new('L',(W,H));d=ImageDraw.Draw(im)
            d.rounded_rectangle([x+3,y+3,x+w-3,y+h-3],radius=int(0.04*ppm),fill=255)
            m=np.array(im)>0
            if x+w>W:  # wrap
                im2=Image.new('L',(W,H));ImageDraw.Draw(im2).rounded_rectangle([x-W+3,y+3,x+w-W-3,y+h-3],radius=int(0.04*ppm),fill=255);m|=np.array(im2)>0
            a[m]=c+noise(H,W,6)[m][:,None]
            x+=w
        y+=h
    save(name,a,tw,th)
bluestone('bluestone')
# ---------- concrete / render / paint ----------
def flat(name,col,ppm=128,tw=2.0,th=2.0,n=3.0,grain=0,joints=None,jc=0.8):
    W,H=int(tw*ppm),int(th*ppm);a=canvas(W,H,col)+noise(H,W,n)[...,None]
    if grain: a+=noise(H,W,grain,blur=6)[...,None]
    if joints:
        for gx in np.arange(0,tw,joints[0]): a[:,int(gx*ppm):int(gx*ppm)+2]*=jc
        for gy in np.arange(0,th,joints[1]): a[int(gy*ppm):int(gy*ppm)+2,:]*=jc
    save(name,a,tw,th)
flat('concrete',(168,166,160),tw=3,th=3,grain=3,joints=(3,3))
flat('concrete_dark',(132,130,126),tw=2,th=2,grain=3)
flat('render_cream',(214,204,180),tw=2,th=2,grain=2)
flat('render_white',(226,226,220),tw=2,th=2,grain=2)
flat('paint_cream',(226,208,152),tw=1,th=1,n=2)            # grandstand columns and trims (c32)
flat('steel_white',(232,234,234),tw=1,th=1,n=1.5)          # light towers
flat('steel_galv',(160,164,166),tw=1,th=1,n=2)
flat('steel_dark',(52,54,57),tw=1,th=1,n=2)
flat('cladding_charcoal',(48,49,52),tw=2,th=2,n=2,joints=(1.2,3))
flat('cladding_khaki',(150,140,96),tw=2.75,th=1.15,n=2,joints=(2.75,1.15),jc=0.65)   # scoreboard back panels (main photo)
flat('cladding_grey',(118,122,126),tw=2,th=2,n=2,joints=(1.0,4),jc=0.85)
# ---------- timber boards ----------
def boards(name,col,ppm=200,tw=1.0,th=1.0,bw=0.15,vertical=True,gap=0.8):
    W,H=int(tw*ppm),int(th*ppm);a=canvas(W,H,col)+noise(H,W,3)[...,None]
    a+=noise(H,W,6,blur=2)[...,None]*np.array([1,1,1])
    n=int(round((tw if vertical else th)/bw))
    for i in range(n):
        p=int(i*bw*ppm)
        if vertical: a[:,p:p+2]*=gap
        else: a[p:p+2,:]*=gap
        c=rng.normal(0,5)
        if vertical: a[:,p+2:int((i+1)*bw*ppm)]+=c
        else: a[p+2:int((i+1)*bw*ppm),:]+=c
    save(name,a,tw,th)
boards('timber_darkgreen',(38,52,44))      # back wall of the old stand (deep shade in c32)
boards('timber_cream',(222,206,160),vertical=False)   # soffit boards
boards('deck_grey',(78,80,84),tw=1.0,th=1.0,bw=0.25,gap=0.7)  # Western Stand roof underside
# ---------- grandstand bench (one colour per texture; planks along u) ----------
def bench(name,col):
    ppm=200;tw,th=1.0,0.45;W,H=int(tw*ppm),int(th*ppm)
    a=canvas(W,H,col)+noise(H,W,3)[...,None]
    for y in (0.0,0.15,0.30):
        a[int(y*ppm):int(y*ppm)+3,:]*=0.55
    a[:,:]*=1-0.08*np.linspace(0,1,H)[:,None,None]
    save(name,a,tw,th)
# seat colours per section, bottom row -> top row (c32, 2021+: green, blue, red, red-orange, yellow, green from east to west)
SEC=[((112,186,96),(30,128,118)),((52,82,176),(30,52,138)),((222,122,62),(168,48,40)),((214,96,52),(170,44,34)),((222,196,64),(182,160,48)),((112,186,96),(30,128,118))]
BANDS=4
for s,(c0,c1) in enumerate(SEC):
    for b in range(BANDS):
        t=b/(BANDS-1);bench(f'bench_{s}_{b}',tuple(np.array(c0)*(1-t)+np.array(c1)*t))
bench('box_red',(196,40,44));bench('box_green',(44,120,80))
# ---------- tip-up seats (Western Stand: light blue/teal, d48 structure reference + c28) ----------
def tipup(name,col,ppm=200,tw=0.5,th=0.8):
    W,H=int(tw*ppm),int(th*ppm);a=canvas(W,H,(120,122,124))+noise(H,W,3)[...,None]   # concrete step
    a[:int(0.08*ppm)]*=0.7                                                           # riser shadow
    im=Image.new('RGB',(W,H));d=ImageDraw.Draw(im)
    x0,x1=int(0.04*ppm),int(0.46*ppm)
    d.rounded_rectangle([x0,int(0.12*ppm),x1,int(0.62*ppm)],radius=int(0.05*ppm),fill=tuple(int(c) for c in col))
    d.rectangle([x0+6,int(0.12*ppm)+6,x1-6,int(0.20*ppm)],fill=tuple(int(c*0.8) for c in col))
    m=np.array(im).sum(2)>0;a[m]=np.array(im)[m]+noise(H,W,3)[m][:,None]
    save(name,a,tw,th)
tipup('seat_teal',(58,168,190))
# ---------- concrete steps with yellow nosings (aisles) ----------
flat('stair',(170,168,162),tw=1,th=1,grain=2)
a=np.array(Image.open(os.path.join(OUT,'stair.png')),float);a[:12]=(214,186,58);save('stair_nosing',a,1,1)
# ---------- glass curtain wall (Wolf Blass centre): dark blue-grey glass, 1.5 m mullions, 3 m transoms ----------
def glass(name,ppm=128,tw=1.5,th=3.0,tint=(48,62,80)):
    W,H=int(tw*ppm),int(th*ppm)
    g=np.linspace(1.25,0.8,H)[:,None,None]
    a=canvas(W,H,tint)*g+noise(H,W,1.5)[...,None]
    a[:,:5]=(30,32,35);a[:5,:]=(30,32,35)
    save(name,a,tw,th)
glass('glass_dark')
glass('glass_ws',tint=(60,76,92),tw=2.0,th=2.4)
# ---------- Southern Stand rear (woods1_ses, woods1_wb): tall ground-floor windows, buff bands, small upper windows ----------
def rear_bay(name,tw=3.87,th=9.5,ppm=128):
    W,H=int(tw*ppm),int(th*ppm);b=np.array(Image.open(os.path.join(OUT,'brick_red.png')).resize((int(1.2*ppm),int(0.86*ppm))),float)
    a=np.tile(b,(H//b.shape[0]+1,W//b.shape[1]+1,1))[:H,:W].copy()
    Z=lambda z:H-int(z*ppm);X=lambda x:int(x*ppm)
    buff=(206,190,152)
    def band(z0,z1):a[Z(z1):Z(z0)]=np.array(buff)+noise(Z(z0)-Z(z1),W,3)[...,None]
    band(0,0.4);band(3.55,3.85);band(5.0,5.45);band(th-0.9,th-0.6)
    a[:,:X(0.35)]*=0.9                                                           # brick pilaster at the bay edge
    def win(cx,z0,w,h,split=2):
        x0,x1,y0,y1=X(cx-w/2),X(cx+w/2),Z(z0+h),Z(z0)
        a[y0-8:y0,x0-6:x1+6]=buff;a[y1:y1+8,x0-8:x1+8]=buff;a[y0:y1,x0:x1]=(236,236,230)
        fw=6;ys=np.linspace(y0+fw,y1-fw,split+1).astype(int)
        for j in range(split):
            for xa,xb in ((x0+fw,(x0+x1)//2-fw//2),((x0+x1)//2+fw//2,x1-fw)):
                ya,yb=ys[j]+(fw//2 if j else 0),ys[j+1]-(fw//2 if j<split-1 else 0)
                a[ya:yb,xa:xb]=np.array((40,50,62))*np.linspace(1.3,0.9,yb-ya)[:,None,None]
    for cx in (tw*0.3,tw*0.75):
        win(cx,1.0,0.95,2.2)                                                     # ground floor
        win(cx,6.3,0.9,1.2,split=1)                                              # upper floor
        a[Z(5.35):Z(5.1),X(cx-0.35):X(cx+0.35)]=(52,44,40)                       # vent in the buff band
    save(name,a,tw,th,mode='wall')
rear_bay('ses_rear_bay')
# ---------- grandstand front wall (c32): brick from the ground, small windows, pierced balustrade, buff cap; 2.33 m panels ----------
def podium(name,tw=2.33,th=2.2,ppm=200):
    W,H=int(tw*ppm),int(th*ppm);b=np.array(Image.open(os.path.join(OUT,'brick_red.png')).resize((int(1.2*ppm),int(0.86*ppm))),float)
    a=np.tile(b,(H//b.shape[0]+1,W//b.shape[1]+1,1))[:H,:W].copy()
    Z=lambda z:H-int(z*ppm);X=lambda x:int(x*ppm)
    a[Z(2.2):Z(2.08)]=(214,198,160)                                  # cap
    a[Z(1.32):Z(1.25)]=(196,176,140)                                 # buff band under the balustrade
    pw=X(0.36);a[:,:pw//2]*=0.9;a[:,W-pw//2:]*=0.9                   # pier faces
    for i in range(8):                                               # vertical slots in the balustrade
        x=pw//2+int((i+0.5)*(W-pw)/8);a[Z(1.95):Z(1.42),x-X(0.035):x+X(0.035)]=(46,22,20)
    x0,x1=X(tw/2-0.32),X(tw/2+0.32);a[Z(0.95):Z(0.45),x0:x1]=(236,232,224);a[Z(0.95)+6:Z(0.45)-6,x0+6:x1-6]=(44,52,60)   # small window
    a[Z(0.12):,:]=(196,176,140)                                      # plinth
    save(name,a,tw,th)
podium('ses_podium')
def board(name,txt,tw=5.0,th=0.5,ppm=200,bg=(230,216,170),fg=(40,36,30)):
    W,H=int(tw*ppm),int(th*ppm);im=Image.new('RGB',(W,H),bg);d=ImageDraw.Draw(im);d.rectangle([0,0,W-1,H-1],outline=(80,70,50),width=6)
    f=font(int(0.3*ppm));tb=d.textbbox((0,0),txt,font=f);d.text(((W-tb[2]+tb[0])//2,(H-tb[3]-tb[1])//2),txt,font=f,fill=fg)
    save(name,np.array(im,float),tw,th,mode='fit')
board('ses_sign','SIR EDWIN T. SMITH PAVILION')
# ---------- pediment (fit to the triangle's box): cream boards with vertical battens and a red-brown trim ----------
def pediment(name,tw=6.0,th=1.5,ppm=200):
    W,H=int(tw*ppm),int(th*ppm);a=canvas(W,H,(232,220,184))+noise(H,W,2)[...,None]
    for i in range(0,W,int(0.3*ppm)): a[:,i:i+8]=(206,190,150)
    im=Image.new('L',(W,H));d=ImageDraw.Draw(im)
    d.line([(0,H-1),(W//2,0),(W-1,H-1)],fill=255,width=int(0.12*ppm));d.line([(0,H-6),(W,H-6)],fill=255,width=int(0.1*ppm))
    a[np.array(im)>0]=(128,44,38)
    save(name,a,tw,th,mode='fit')
pediment('ses_pediment')
pediment('ses_gablet',tw=4.0,th=1.7)
# ---------- cupola: cream louvred sides ----------
def louvre(name,col=(226,212,170),tw=1.8,th=2.2,ppm=200):
    W,H=int(tw*ppm),int(th*ppm);a=canvas(W,H,col)+noise(H,W,2)[...,None]
    for y in range(int(0.4*ppm),int(1.8*ppm),int(0.1*ppm)): a[y:y+int(0.035*ppm),int(0.3*ppm):int(1.5*ppm)]=(70,64,52)
    save(name,a,tw,th,mode='fit')
louvre('cupola_louvre')
flat('lead_grey',(176,180,182),tw=1,th=1,n=2)
# ---------- Western Stand rear (woods2_ws): red/navy diagonal-striped mesh over beige precast, black columns, dark louvres ----------
def ws_rear(name,tw=6.0,th=7.0,ppm=100):
    W,H=int(tw*ppm),int(th*ppm);a=canvas(W,H,(196,186,164))+noise(H,W,3)[...,None]
    zt=3.4;Yt=H-int(zt*ppm)
    yy,xx=np.mgrid[0:Yt,0:W]/ppm
    stripe=((xx+yy)/1.2)%1<0.5
    a[:Yt][stripe]=(176,40,46);a[:Yt][~stripe]=(30,40,86)
    mesh=((np.mgrid[0:Yt,0:W][0]+np.mgrid[0:Yt,0:W][1])%6==0)|((np.mgrid[0:Yt,0:W][0]-np.mgrid[0:Yt,0:W][1])%6==0)
    a[:Yt][mesh]*=1.35
    a[Yt:Yt+int(0.3*ppm)]=(150,146,138)                         # soffit lip
    a[:,W//2:W//2+2]*=0.9
    for x in (int(0.3*ppm),):                                   # black column
        a[Yt:,x:x+int(0.3*ppm)]=(28,28,30)
    a[H-int(2.6*ppm):,int(2.2*ppm):int(5.6*ppm)]=(40,38,36)    # louvres
    for y in range(H-int(2.6*ppm),H,int(0.12*ppm)): a[y:y+3,int(2.2*ppm):int(5.6*ppm)]=(70,66,60)
    save(name,a,tw,th)
ws_rear('ws_rear_bay')
# ---------- Western Stand back wall under the roof: glass corporate boxes over dark panels (d48 structure, c28) ----------
def ws_back(name,tw=4.0,th=3.0,ppm=128):
    W,H=int(tw*ppm),int(th*ppm);a=canvas(W,H,(58,60,64))+noise(H,W,2)[...,None]
    a[int(0.3*ppm):int(2.4*ppm),int(0.1*ppm):int(3.9*ppm)]=np.array((70,88,104))*np.linspace(1.2,0.85,int(2.4*ppm)-int(0.3*ppm))[:,None,None]
    for x in np.arange(0.1,3.95,0.95): a[int(0.3*ppm):int(2.4*ppm),int(x*ppm):int(x*ppm)+4]=(40,40,42)
    save(name,a,tw,th)
ws_back('ws_backwall')
# ---------- floodlight head (c32): white frame, 7 rows of lamps ----------
def lamp(name,tw=4.4,th=3.4,ppm=128):
    W,H=int(tw*ppm),int(th*ppm);a=canvas(W,H,(236,238,238))+noise(H,W,1)[...,None]
    rows,cols=7,6
    for r in range(rows):
        for c in range(cols):
            x0=int((0.2+c*(tw-0.4)/cols+0.04)*ppm);x1=int((0.2+(c+1)*(tw-0.4)/cols-0.04)*ppm)
            y0=int((0.15+r*(th-0.3)/rows+0.05)*ppm);y1=int((0.15+(r+1)*(th-0.3)/rows-0.05)*ppm)
            a[y0:y1,x0:x1]=(150,156,162);a[y0+4:y1-4,x0+4:x1-4]=(60,66,76)
            a[y0+4:y0+8,x0+4:x1-4]=(200,206,214)
    save(name,a,tw,th,mode='fit')
lamp('lamp_face')
flat('lamp_back',(214,216,218),tw=1,th=1,n=1.5,joints=(0.5,0.5),jc=0.85)
# ---------- boundary fence: low charcoal hoarding with a white rail (main photo), white picket south (c32) ----------
def hoarding(name,tw=2.0,th=1.0,ppm=200):
    W,H=int(tw*ppm),int(th*ppm);a=canvas(W,H,(36,38,40))+noise(H,W,2)[...,None]
    a[:int(0.08*ppm)]=(236,236,232);a[:,:4]=(24,24,26)
    save(name,a,tw,th)
hoarding('fence_hoarding')
def picket(name,tw=1.0,th=1.0,ppm=200):
    W,H=int(tw*ppm),int(th*ppm);a=np.zeros((H,W,4))
    pw,ps=int(0.07*ppm),int(0.12*ppm)
    for x in range(0,W,ps):
        a[int(0.06*ppm):,x:x+pw,:3]=(240,240,236);a[int(0.06*ppm):,x:x+pw,3]=255
        a[:int(0.06*ppm),x+pw//4:x+pw-pw//4,:3]=(240,240,236);a[:int(0.06*ppm),x+pw//4:x+pw-pw//4,3]=255
    for y in (0.2,0.75): a[int(y*ppm):int(y*ppm)+int(0.06*ppm),:,:3]=(228,228,224);a[int(y*ppm):int(y*ppm)+int(0.06*ppm),:,3]=255
    a[...,:3]+=noise(H,W,2)[...,None]
    save(name,a,tw,th,alpha=True)
picket('fence_picket')
# ---------- terraces ----------
flat('terrace_tread',(158,156,150),tw=2,th=0.9,grain=3,joints=(2,0.9),jc=0.75)
flat('terrace_riser',(128,126,122),tw=2,th=0.28,n=2)
# ---------- scoreboard front (LED screen, dark with a fine pixel grid) ----------
def led(name,tw=11.0,th=2.3,ppm=100):
    W,H=int(tw*ppm),int(th*ppm);a=canvas(W,H,(18,18,22))
    a[::3,:]*=0.6;a[:,::3]*=0.6
    a[:6]=a[-6:]=(50,50,54);a[:,:6]=a[:,-6:]=(50,50,54)
    save(name,a,tw,th,mode='fit')
led('board_front')
# ---------- Wolf Blass Community Centre street front (c32): glass upper with the name in white letters, mural band ----------
def wbcc_upper(name,tw,th,ppm=64):
    W,H=int(tw*ppm),int(th*ppm)
    g=np.array(Image.open(os.path.join(OUT,'glass_dark.png')).resize((int(1.5*ppm),int(3*ppm))),float)
    a=np.tile(g,(H//g.shape[0]+1,W//g.shape[1]+1,1))[:H,:W].copy()
    a[:int(0.5*ppm)]=(40,40,44)
    im=Image.fromarray(a.clip(0,255).astype(np.uint8));d=ImageDraw.Draw(im)
    f=font(int(0.42*ppm));txt='WOLF BLASS COMMUNITY CENTRE'
    tb=d.textbbox((0,0),txt,font=f);d.text(((W-(tb[2]-tb[0]))//2,int(0.04*ppm)),txt,font=f,fill=(240,240,236))
    save(name,np.array(im,float),tw,th,mode='fit')
def wbcc_mural(name,tw,th,ppm=64):
    W,H=int(tw*ppm),int(th*ppm);a=canvas(W,H,(40,52,140))
    yy,xx=np.mgrid[0:H,0:W];a[((xx//int(0.6*ppm))+(yy//int(0.6*ppm)))%2==0]*=1.12   # halftone-like crowd panel
    im=Image.fromarray(a.clip(0,255).astype(np.uint8));d=ImageDraw.Draw(im)
    d.rectangle([0,0,W,int(0.45*ppm)],fill=(206,30,48))
    f=font(int(0.34*ppm));d.text((int(0.2*ppm),int(0.04*ppm)),'NORWOOD FOOTBALL CLUB  Est.1878',font=f,fill=(255,255,255))
    f2=font(int(1.1*ppm));d.text((int(tw*0.45*ppm),int(1.0*ppm)),'REDLEGS',font=f2,fill=(220,34,52),stroke_width=6,stroke_fill=(255,255,255))
    d.rectangle([int(tw*0.82*ppm),int(0.6*ppm),int(tw*0.97*ppm),int(2.4*ppm)],fill=(206,30,48))
    f3=font(int(0.32*ppm));d.text((int(tw*0.83*ppm),int(0.9*ppm)),'FORTIS',font=f3,fill=(255,255,255));d.text((int(tw*0.83*ppm),int(1.3*ppm)),'IN PROCELLA',font=font(int(0.18*ppm)),fill=(255,255,255))
    save(name,np.array(im,float),tw,th,mode='fit')
WB_FRONT=float(np.hypot(-47.5+55.4,-68+44.6))
wbcc_upper('wbcc_upper',WB_FRONT,6.0)
wbcc_mural('wbcc_mural',WB_FRONT,3.0)
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'tex2.py')).read())
json.dump(SPEC,open(os.path.join(OUT,'spec.json'),'w'),indent=1)
print(len(SPEC),'textures ->',os.path.abspath(OUT))
