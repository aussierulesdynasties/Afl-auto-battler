# Hand-made (procedural) textures for the Football Park models. No photo pixels: colours are the real materials'
# daylight colours read off the photos, drawn crisp. python tex.py OUTDIR [variant A|B]
import sys,os,numpy as np
from PIL import Image,ImageDraw,ImageFilter
out=sys.argv[1];VAR=sys.argv[2] if len(sys.argv)>2 else 'B';os.makedirs(out,exist_ok=True)
rng=np.random.default_rng(7)
def noise(h,w,scale,amp):
    # smooth value noise (tileable via wrap), amplitude amp (0-255 units)
    g=rng.standard_normal((max(2,h//scale),max(2,w//scale)))
    im=Image.fromarray(((g-g.min())/(np.ptp(g)+1e-9)*255).astype(np.uint8)).resize((w,h),Image.BICUBIC)
    return (np.asarray(im,float)/255-0.5)*2*amp*0.4  # texture pass: low-frequency mottle cut to 0.4x
def fine(h,w,amp):return rng.standard_normal((h,w))*amp
def base(h,w,c):a=np.zeros((h,w,3));a[:]=c;return a
def save(a,name):Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(os.path.join(out,name+'.png'))
def addn(a,n):return a+n[...,None]
# ---------- seat bay: one aisle-to-aisle bay (u) by one row (v). Aisle = concrete steps at u 0..aw.
def seat_row(name,seat,W=2048,H=128,aw=0.8/11.0,nseat=19):
    a=base(H,W,(188,190,186));a=addn(a,fine(H,W,4))          # concrete tread
    x0=int(aw*W);bw=(W-x0)/nseat
    for i in range(nseat):
        xa=int(x0+i*bw+bw*0.06);xb=int(x0+(i+1)*bw-bw*0.06)
        # seat pan (front 55% of row depth) and back (rear 30%), plastic with highlight
        a[int(H*0.06):int(H*0.62),xa:xb]=np.array(seat)*1.0
        a[int(H*0.06):int(H*0.13),xa:xb]=np.array(seat)*1.18                   # front lip highlight
        a[int(H*0.66):int(H*0.97),xa+2:xb-2]=np.array(seat)*0.80               # backrest (shaded side faces camera-away)
        a[int(H*0.62):int(H*0.66),xa:xb]=np.array(seat)*0.45                   # gap shadow
    # aisle: step nosing line and handrail post
    a[:,x0-3:x0]=(150,150,148);a[int(H*0.45):int(H*0.5),:x0]=(205,205,200)
    a=addn(a,fine(H,W,3));save(a,name)
def riser(name,seat,W=2048,H=64,aw=0.8/11.0,nseat=19):
    a=base(H,W,(150,152,148));a=addn(a,fine(H,W,4));x0=int(aw*W);bw=(W-x0)/nseat
    for i in range(nseat):
        xa=int(x0+i*bw+bw*0.06);xb=int(x0+(i+1)*bw-bw*0.06);a[int(H*0.12):int(H*0.85),xa:xb]=np.array(seat)*0.88
    a[:5,:]=(196,196,192);a[:,:x0]=(178,178,174);save(a,name)
# ---------- roof sheeting: one bay (u = between rafters) x full depth (v 0..1). Ribs run radially (along v).
def roof(name,c,W=1024,H=1024,ribs=24,rafter=True,rib_c=None,corr=0):
    a=base(H,W,c);a=addn(a,noise(H,W,64,4))
    if corr:
        for x in range(0,W,W//corr):a[:,x:x+2]=np.array(c)*0.93
    for i in range(ribs):
        x=int((i+0.5)*W/ribs)
        if rib_c is not None:a[:,x-6:x+6]=np.array(rib_c);a[:,x+6:x+9]=np.array(c)*0.8
        else:a[:,x-3:x+3]=np.array(c)*1.07;a[:,x+3:x+5]=np.array(c)*0.86
    if rafter:a[:,:10]=np.array(c)*0.78;a[:,W-4:]=np.array(c)*0.9
    for y in range(0,H,H//6):a[y:y+2,:]=np.array(c)*0.93                       # sheet end laps
    a[:14,:]=np.array(c)*0.72;a[H-10:,:]=np.array(c)*0.8                      # gutter / ridge flashing
    a=addn(a,fine(H,W,2.5));save(a,name)
def roof_under(name,c,W=512,H=512):
    a=base(H,W,c);a=addn(a,noise(H,W,64,3))
    for y in range(0,H,H//8):a[y:y+10,:]=np.array(c)*0.62                       # purlins
    a[:,:24]=np.array(c)*0.5;save(a,name)
# ---------- plain materials (tile sizes set in build TEX table)
def concrete(name,c,W=1024,H=1024,panel=(2,4)):
    a=base(H,W,c);a=addn(a,noise(H,W,128,5)+noise(H,W,16,3)+fine(H,W,3))
    for i in range(1,panel[0]):a[:,int(i*W/panel[0])-2:int(i*W/panel[0])+1]=np.array(c)*0.82
    for j in range(1,panel[1]):a[int(j*H/panel[1])-2:int(j*H/panel[1])+1,:]=np.array(c)*0.85
    a[:,:2]=np.array(c)*0.82;a[:2,:]=np.array(c)*0.85;save(a,name)
def pavers(name,c,W=1024,H=1024,n=10):
    a=base(H,W,c);bw=W//n;bh=W//(2*n)
    for j in range(H//bh):
        off=(bw//2)*(j%2)
        for i in range(-1,n+1):
            x0=i*bw+off;sh=rng.normal(0,2.5)  # texture pass: one even tone shift per paver (was 7 per channel: blotchy)
            a[j*bh:(j+1)*bh,max(0,x0):max(0,min(W,x0+bw))]=np.array(c)+sh
            a[j*bh:(j+1)*bh,max(0,x0):max(0,min(W,x0+3))]=np.array(c)*0.7
        a[j*bh:j*bh+3,:]=np.array(c)*0.7
    a=addn(a,fine(H,W,4));save(a,name)
def asphalt(name,c,W=1024,H=1024):
    a=base(H,W,c);a=addn(a,noise(H,W,128,4)+fine(H,W,9));save(a,name)
def grass(name,c,W=1024,H=1024,stripes=2):
    a=base(H,W,c);a=addn(a,noise(H,W,64,5)+fine(H,W,6))
    for i in range(stripes):
        if i%2:a[:,i*W//stripes:(i+1)*W//stripes]*=1.09
    save(a,name)
def glazing(name,W=512,H=1024,cols=1,rows=3,frame=(220,222,224)):
    # dark tinted glass with sky reflection gradient, mullions and transoms
    a=np.zeros((H,W,3));g=np.linspace(0,1,H)[:,None]
    a[...,0]=40+50*g;a[...,1]=55+55*g;a[...,2]=70+60*g
    for i in range(cols+1):x=int(i*W/cols);a[:,max(0,x-8):x+8]=frame
    for j in range(rows+1):y=int(j*H/rows);a[max(0,y-8):y+8,:]=frame
    save(a,name)
def facade(name,c,W=1024,H=2048,band=(0.70,0.93),blue=None):
    # rendered wall bay (u one column bay, v ground..top): render, window band, optional blue entry panel low
    a=base(H,W,c);a=addn(a,noise(H,W,128,3)+fine(H,W,2.5))
    y0,y1=int(H*(1-band[1])),int(H*(1-band[0]))
    a[y0:y1,int(W*0.06):int(W*0.94)]=0;g=np.linspace(0,1,y1-y0)[:,None]
    a[y0:y1,int(W*0.06):int(W*0.94),0]=45+40*g;a[y0:y1,int(W*0.06):int(W*0.94),1]=58+45*g;a[y0:y1,int(W*0.06):int(W*0.94),2]=72+50*g
    for k in range(1,4):x=int(W*0.06+k*(W*0.88)/4);a[y0:y1,x-5:x+5]=(210,212,214)
    if blue is not None:a[int(H*0.62):H-int(H*0.0),int(W*0.25):int(W*0.75)]=blue;a[int(H*0.62):int(H*0.63),int(W*0.25):int(W*0.75)]=np.array(blue)*0.7
    a[:,:int(W*0.05)]=np.array(c)*1.06;a[:,W-int(W*0.05):]=np.array(c)*0.9                                   # column faces
    a[H-30:,:]=np.array(c)*0.75;save(a,name)
def facade4(name,W=2048,H=1024,bays=4,blue_bay=2):
    a=base(H,W,(236,233,224));a=addn(a,noise(H,W,96,3)+fine(H,W,2.5));bw=W//bays
    a[int(H*0.05):int(H*0.20)]=(184,200,198)                   # rail / glass band under the roof
    a[int(H*0.20):int(H*0.30)]=(92,72,54)                      # dark brown band
    a[int(H*0.30):int(H*0.33)]=(206,200,186)
    for b in range(bays):
        x=b*bw;a[:,x:x+int(bw*0.07)]=(150,82,62);a[:,x+int(bw*0.07):x+int(bw*0.09)]=(110,60,46)   # rust post + shadow
        if b==blue_bay:a[int(H*0.62):H-20,x+int(bw*0.3):x+int(bw*0.75)]=(96,138,190);a[int(H*0.62):int(H*0.64),x+int(bw*0.3):x+int(bw*0.75)]=(70,100,140)
    a[H-20:]=(150,140,128);save(a,name)
def roof_truss(name,c,W=1024,H=1024):
    # white sheet roof, one 4-degree bay: sheet laps along v, light-grey truss chords and diagonals
    a=base(H,W,c);a=addn(a,noise(H,W,64,3)+fine(H,W,2))
    for x in range(0,W,W//12):a[:,x:x+3]=np.array(c)*0.93
    im=Image.fromarray(np.clip(a,0,255).astype(np.uint8));d=ImageDraw.Draw(im);g=(196,198,200)
    d.line((0,0,0,H),fill=g,width=14);d.line((W//2,0,W//2,H),fill=g,width=8)
    for k in range(6):y0=k*H/6;y1=(k+1)*H/6;d.line((0,y0,W//2,y1),fill=g,width=6);d.line((W//2,y1,W,y0),fill=g,width=6)
    d.rectangle((0,0,W,16),fill=(170,172,176));im.save(os.path.join(out,name+'.png'))
def lamps(name,W=512,H=1024,cols=6,rows=12):
    a=base(H,W,(70,72,76))
    im=Image.fromarray(a.astype(np.uint8));d=ImageDraw.Draw(im)
    cw=W/cols;rh=H/rows
    for i in range(cols):
        for j in range(rows):
            cx=(i+0.5)*cw;cy=(j+0.5)*rh;r=min(cw,rh)*0.38
            d.ellipse((cx-r-4,cy-r-4,cx+r+4,cy+r+4),fill=(40,40,44));d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(232,234,236))
            d.ellipse((cx-r*0.45,cy-r*0.6,cx+r*0.15,cy-r*0.1),fill=(255,255,255))
    for i in range(cols+1):d.line((i*cw,0,i*cw,H),fill=(150,152,156),width=6)
    im.save(os.path.join(out,name+'.png'))
def steel(name,c,W=256,H=256):
    a=base(H,W,c);a=addn(a,noise(H,W,32,3)+fine(H,W,2));save(a,name)
def screen(name,W=1024,H=512):
    a=base(H,W,(18,20,24));a=addn(a,fine(H,W,3))
    for x in range(0,W,16):a[:,x:x+2]=(30,32,36)
    for y in range(0,H,16):a[y:y+2,:]=(30,32,36)
    a[:12,:]=(70,72,76);a[-12:,:]=(70,72,76);a[:,:12]=(70,72,76);a[:,-12:]=(70,72,76);save(a,name)
def brick(name,c,W=1024,H=1024,n=8,wins=None):
    a=base(H,W,c);bw=W//n;bh=bw//3
    for j in range(H//bh):
        off=(bw//2)*(j%2);a[j*bh:j*bh+3,:]=np.array(c)*0.78
        for i in range(-1,n+1):
            x=i*bw+off
            if 0<=x<W:a[j*bh:(j+1)*bh,x:x+3]=np.array(c)*0.78
    a=addn(a,noise(H,W,64,4)+fine(H,W,3))
    if wins:  # window grid: wins=(cols,rows)
        cw=W/wins[0];rh=H/wins[1]
        for i in range(wins[0]):
            for j in range(wins[1]):
                x0=int(i*cw+cw*0.22);x1=int((i+1)*cw-cw*0.22);y0=int(j*rh+rh*0.25);y1=int((j+1)*rh-rh*0.2)
                a[y0-6:y1+6,x0-6:x1+6]=(225,225,222);g=np.linspace(0,1,y1-y0)[:,None]
                a[y0:y1,x0:x1,0]=40+40*g;a[y0:y1,x0:x1,1]=52+45*g;a[y0:y1,x0:x1,2]=66+50*g
    save(a,name)
def sign_band(name,W=2048,H=128):
    # bare fence (director 2026-11-18: "C: no boards"): plain white painted panels, grey joints every 2.5 m, no ads
    a=base(H,W,(236,236,234))
    for i in range(16):a[:,i*W//16:i*W//16+3]=(196,196,198)
    a[:8,:]=(250,250,250);a[-8:,:]=(60,60,62);save(a,name)

def field(name,c,A=72.5,B=88.5,ppm=20,inset=3.0):
    # whole oval, u=(x+A)/2A, v=(y+B)/2B (goals at y=+-B). AFL markings: boundary, centre square 50 m, circles 3/10 m,
    # 50 m arcs, goal squares 6.4 x 9 m, 15 cm white lines. Faint mowing bands 8 m across the ground.
    W,H=int(2*A*ppm),int(2*B*ppm);a=base(H,W,c);a=addn(a,noise(H,W,96,4)+fine(H,W,5))
    ys=(np.arange(H)/ppm-B)
    band=((np.floor((ys+B)/8)%2)==1);a[band]*=1.03
    im=Image.fromarray(np.clip(a,0,255).astype(np.uint8));d=ImageDraw.Draw(im);lw=max(2,int(0.15*ppm))
    P=lambda x,y:((x+A)*ppm,(y+B)*ppm);wht=(238,238,232)
    def ell(rx,ry):d.ellipse((*P(-rx,-ry),*P(rx,ry)),outline=wht,width=lw)
    ell(A-inset,B-inset)
    d.rectangle((*P(-25,-25),*P(25,25)),outline=wht,width=lw);ell(1.5,1.5);ell(5,5);d.line((*P(-2,0),*P(2,0)),fill=wht,width=lw)
    for sg in(-1,1):
        gy=sg*(B-inset);d.rectangle((*P(-3.2,min(gy,gy-sg*9)),*P(3.2,max(gy,gy-sg*9))),outline=wht,width=lw)
        # 50 m arc: circle radius 50 about the goal-line centre, clipped to inside the boundary
        for k in range(1200):
            th=np.pi*k/1200;x=50*np.cos(th);y=gy-sg*50*np.sin(th)
            if (x/(A-inset))**2+(y/(B-inset))**2<1:d.ellipse((*[v-lw/2 for v in P(x,y)],*[v+lw/2 for v in P(x,y)]),fill=wht)
    im.save(os.path.join(out,name+'.png'))
seat_c=(14,92,136) if VAR=='B' else (196,188,186)
seat_n=(30,58,110) if VAR=='B' else (196,188,186)
seat_row('seat_lb',seat_c);riser('riser',seat_c)
seat_row('seat_navy',seat_n);riser('riser_navy',seat_n)
roof('tan',(214,198,156) if VAR=='B' else (172,158,121));roof_truss('white',(240,241,242));(roof('west_roof',(218,214,206)) if VAR=='B' else roof('west_roof',(178,174,183),ribs=2,rib_c=(230,232,240),corr=64))
roof('box',(236,236,238) if VAR=='B' else (160,178,200),ribs=16)
roof('box_roof',(168,192,176) if VAR=='B' else (152,171,194),ribs=16)
roof_under('tan_under',(150,140,118))
concrete('deck',(178,176,170) if VAR=='B' else (92,90,98),panel=(2,2));concrete('west_back',(196,192,184),panel=(1,4))
concrete('embank',(186,188,180) if VAR=='B' else (86,84,94),panel=(3,3))
pavers('pink',(176,104,92));asphalt('apron',(150,150,140));field('turf',(40,75,25) if VAR=='A' else (68,92,30))
glazing('glass');facade4('facade');steel('col',(232,232,230));concrete('tower',(200,200,198),W=256,H=1024,panel=(1,8))
lamps('lamps');screen('screen');brick('admin',(214,200,178),wins=(4,4));roof('admin_roof',(188,200,190) if VAR=='B' else (78,86,104),ribs=20,rafter=False)
sign_band('signs');steel('posts',(244,244,240));steel('padding',(200,40,40))
if VAR=='A':
    grass('grass_n',(30,44,32),stripes=0);grass('grass_s',(82,93,58),stripes=0);grass('golf',(48,62,46),stripes=0)
    concrete('conc',(67,66,78),panel=(2,2));pavers('pink',(133,123,132));pavers('carpark',(110,88,98))
    asphalt('road',(70,66,76));asphalt('road_top',(49,50,55));asphalt('road_diag',(97,99,123));concrete('footpath',(104,105,117),panel=(2,2))
concrete('kerb',(196,196,198),W=256,H=256,panel=(1,1))
print('ok')
