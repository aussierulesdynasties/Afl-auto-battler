# Hand-painted textures for the TIO Stadium model: no photo pixels. python tex.py -> tex/*.png + tex/tex.json (tile sizes in metres)
# Colours are read by eye from the 2025 Commons photos (refs/); every pattern is drawn here.
import numpy as np,json,os,math,random
from PIL import Image,ImageDraw,ImageFont,ImageFilter
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'tex');os.makedirs(OUT,exist_ok=True)
rng=np.random.default_rng(7);random.seed(7)
TILE={}
F='C:/Windows/Fonts/'
def noise(h,w,sc,oct=4):
    o=np.zeros((h,w))
    for i in range(oct):
        s=max(2,int(sc*2**i));a=rng.random((s,s))
        o+=np.asarray(Image.fromarray((a*255).astype(np.uint8)).resize((w,h),Image.BICUBIC),float)/255/2**i
    return (o-o.min())/(o.max()-o.min()+1e-9)
def base(h,w,col,var=0.18,sc=4):
    n=noise(h,w,sc);a=np.ones((h,w,3))*np.array(col,float)
    # painted blotching: relative shade plus an absolute grime/sun-fade term so dark paints carry detail too
    # low-frequency shade kept at half strength so tiles don't repeat as big blotches from afar; detail sits at high frequency
    n2=noise(h,w,sc*8,2);fine=rng.random((h,w));var*=0.5
    return a*(1-var/2+var*n)[...,None]+((n2-0.5)*36+(fine-0.5)*22)[...,None]
def streaks(a,amt=0.12,n=60):
    h,w=a.shape[:2]
    for _ in range(n):
        x=rng.integers(0,w);L=rng.integers(h//6,h);wd=rng.integers(2,8);y0=rng.integers(0,h-L+1)
        prof=np.linspace(1,0,L)[:,None]*amt*rng.random()
        a[y0:y0+L,x:x+wd]*=(1-prof[...,None])
    return a
def save(n,a,tile,alpha=None):
    a=np.clip(a,0,255).astype(np.uint8)
    im=Image.fromarray(a,'RGB')
    if alpha is not None:im.putalpha(Image.fromarray(np.clip(alpha,0,255).astype(np.uint8)))
    im.save(os.path.join(OUT,n+'.png'));TILE[n]=tile
# --- concrete: panel joints every 3 m, rain streaks, blotches (tile 6 x 6 m, 512 px)
def concrete(n,col,tile=(6,6),joints=3.0,var=0.22):
    S=512;a=base(S,S,col,var,3);a=streaks(a,0.15,50);px=S/tile[0]
    for k in range(int(tile[0]/joints)+1):
        x=int(k*joints*px)%S;a[:,max(0,x-1):x+2]*=0.72
        y=int(k*joints*px)%S;a[max(0,y-1):y+2,:]*=0.75
    sp=rng.random((S,S))<0.004;a[sp]*=0.7
    save(n,a,tile)
concrete('concrete',(176,172,164))
concrete('concrete_dark',(96,98,102),var=0.25)          # low landscape walls, rear stand base (photo 04, 05)
concrete('walkway',(170,160,150),tile=(4,4),joints=2.0)  # concrete path behind the boundary fence (10, 11)
# --- plaza pavers: pink-brown concrete pavers (02, 04, 06)
S=512;a=base(S,S,(176,140,122),0.2,4)
for y in range(0,S,16):
    a[y:y+1,:]*=0.8
    off=8 if (y//16)%2 else 0
    for x in range(off,S,32):a[y:y+16,x:x+1]*=0.82
for _ in range(400):
    x,y=rng.integers(0,S-32),rng.integers(0,S-16);a[y:y+15,x:x+31]*=0.9+0.2*rng.random()
save('paving',a,(8,8))
# --- grass outside the fence (cut grass, mower stripes faint, dry patches)
a=base(S,S,(78,112,52),0.35,6)
for x in range(0,S,64):a[:,x:x+32]*=1.05
d=noise(S,S,2)>0.72;a[d]=a[d]*0.6+np.array([150,130,80])*0.4
save('grass_out',a,(10,10))
# --- roof sheeting: rib every 0.3 m (ribbed deck), sheet laps every 6 m, grime toward the low edge
def roof(n,col,tile=(6,12),rib=0.3,grime=0.25):
    W,H=256,512;a=base(H,W,col,0.12,3);pu=W/tile[0]
    for k in range(int(tile[0]/rib)):
        x=int(k*rib*pu);a[:,x:x+2]*=0.82;a[:,x+2:x+3]*=1.06
    for k in range(2):
        y=int(k*H/2);a[y:y+3,:]*=0.8
    g=np.linspace(0,1,H)[:,None]**2*grime*noise(H,W,6)
    a*= (1-g)[...,None]
    a=streaks(a,0.1,30);save(n,a,tile)
roof('roof_grey',(158,166,172))       # centre roof, satellite grey (Maurice Rioli Stand)
roof('roof_white',(232,232,228),grime=0.18)  # wing roofs, satellite white
roof('roof_mlc',(226,226,222),grime=0.12)
# --- roof underside: dark steel deck with purlins every 1.2 m and rafters every 8 m (10, 11, 17)
W=512;a=base(W,W,(58,60,64),0.2,4);p=W/8
for k in range(int(8/1.2)+1):
    y=int(k*1.2*p);a[y:y+5,:]*=0.6;a[y+5:y+7,:]*=1.3
for k in range(int(8/0.3)):
    x=int(k*0.3*p);a[:,x:x+1]*=0.85
a[:,0:10]*=0.45
save('roof_under',a,(8,8))
# --- glass: dark blue-grey panes 1.5 m wide, white mullions, sky reflection gradient (14, 17, 18)
def glass(n,col,frame,tile=(3,3.5),pw=1.5,trans=None):
    H,W=448,384;a=base(H,W,col,0.15,2);a*= (0.85+0.3*np.linspace(1,0,H))[:,None,None]
    for k in range(H):a[k]*= 1+0.08*math.sin(k/9)
    pu=W/tile[0];pv=H/tile[1]
    for k in range(int(tile[0]/pw)+1):x=int(k*pw*pu)%W;a[:,max(0,x-3):x+4]=frame
    for y in (0,int(1.0*pv)):a[max(0,y-3):y+4,:]=frame
    a=a*(0.9+0.2*noise(H,W,3))[...,None];save(n,a,tile)
glass('glass',(70,86,100),(220,222,218))
glass('glass_mlc',(40,46,52),(30,30,32),pw=1.2)
glass('glass_box',(150,165,170),(60,62,66),pw=1.8)    # corporate boxes: pale glass, dark frames (17)
# --- cladding panels: light grey fibre-cement 1.2 x 2.4 m with joints (rear building, 04, 05, 14)
def clad(n,col,pw=1.2,ph=2.4,tile=(4.8,4.8),var=0.14):
    S=512;a=base(S,S,col,var,3);a=streaks(a,0.14,40);pu=S/tile[0]
    for k in range(int(tile[0]/pw)+1):x=int(k*pw*pu)%S;a[:,max(0,x-1):x+2]*=0.7
    for k in range(int(tile[1]/ph)+1):y=int(k*ph*pu)%S;a[max(0,y-1):y+2,:]*=0.7
    save(n,a,tile)
clad('clad_grey',(150,152,152))
clad('clad_cream',(214,208,190))
clad('clad_dark',(66,70,78),var=0.3)
# --- blockwork: navy painted block 0.4 x 0.2 m (gate houses, 03, 12)
S=512;a=base(S,S,(44,50,70),0.25,4);pu=S/4
for r in range(0,S,int(0.2*pu)):
    a[r:r+2,:]*=0.6;off=int(0.2*pu) if (r//int(0.2*pu))%2 else 0
    for x in range(off,S,int(0.4*pu)):a[r:r+int(0.2*pu),x:x+2]*=0.6
a=streaks(a,0.15,40);save('block_navy',a,(4,4))
# --- painted steel colours with wear toward the bottom
def paint(n,col,tile=(2,4),var=0.14,wear=0.2):
    H,W=512,256;a=base(H,W,col,var,4);g=np.linspace(0,1,H)[:,None]*wear*noise(H,W,5);a*=(1-g)[...,None]
    a=streaks(a,0.1,20)
    for k in range(4):y=int(k*H/4);a[y:y+3,:]=a[y:y+3,:]*0.55;a[y+3:y+5,:]+=30   # plate seams every 1 m, lit lip below
    sc=rng.random((H,W))<0.01;a[sc]+=45                                           # scuffs and chips
    save(n,a,tile)
paint('orange',(232,110,40))           # stair drums and rails (04, 05)
paint('steel_white',(226,228,226),var=0.12)   # light towers (07)
paint('steel_dark',(52,54,58))
paint('steel_galv',(160,164,166))
paint('screen_back',(40,42,46))
paint('timber',(150,104,66),var=0.3)
# timber battens on the Michael Long Centre (18)
H,W=512,512;a=base(H,W,(138,96,60),0.25,3)
for x in range(0,W,24):a[:,x:x+4]*=0.55;a[:,x+4:x+20]*=0.95+0.1*rng.random()
save('timber',a,(3,3))
# --- seats: empty tip-up seats in the 2025 mosaic (light blue, orange, purple, red, teal), row shadows, aisle (10, 11, 15, 16, 17)
# one tile = 12 m along the row x 16 rows; aisle stair at the tile edge; colour patches are irregular blocks as in the photos
SEATW=0.5;ROW=0.8;NR=16;L=12
W,H=1536,1024;a=np.zeros((H,W,3))
step=np.array([[150,148,144]])
pal=np.array([[96,184,222],[236,112,46],[158,84,150],[206,60,48],[48,150,160]],float)
wts=[0.4,0.3,0.22,0.04,0.04]
pu=W/L;pv=H/NR
# patch map: blocks of 3-8 seats x 2-5 rows, colours chosen by weight
cells=np.zeros((NR,int(L/SEATW)),int)
for r in range(NR):
    c=0
    while c<cells.shape[1]:
        k=rng.choice(5,p=wts);n=rng.integers(2,8);cells[r,c:c+n]=k;c+=n
for r in range(1,NR):
    m=rng.random(cells.shape[1])<0.55;cells[r,m]=cells[r-1,m]
a[:]=(120,118,114)
for r in range(NR):
    y0=int(r*pv);y1=int((r+1)*pv)
    a[y0:y1]=(150,147,140)
    a[y0:y0+int(pv*0.12)]=(80,78,76)       # riser shadow
    for c in range(cells.shape[1]):
        x0=int(c*SEATW*pu)+3;x1=int((c+1)*SEATW*pu)-3
        if x0<int(1.2*pu):continue            # aisle 1.2 m
        col=pal[cells[r,c]]*(0.9+0.2*rng.random())
        a[y0+int(pv*0.22):y0+int(pv*0.7),x0:x1]=col           # seat back
        a[y0+int(pv*0.7):y0+int(pv*0.82),x0:x1]=col*0.62      # seat pan in shadow
        a[y0+int(pv*0.22):y0+int(pv*0.27),x0:x1]=col*1.12
    # aisle steps: grey with yellow nosing
    a[y0:y1,0:int(1.2*pu)]=(160,156,148);a[y0:y0+5,0:int(1.2*pu)]=(210,190,70)
a=a*(0.92+0.16*noise(H,W,6))[...,None]
save('seats',a,(L,NR*ROW))
# --- chain-link boundary fence: 50 mm diamond mesh, galvanised; alpha (07, 10, 18)
S=512;tile=(2,1.2);A=np.zeros((S,S));pu=S/2
yy,xx=np.mgrid[0:S,0:S]/pu
m=(np.abs(((xx+yy)/0.05)%1-0.5)>0.42)|(np.abs(((xx-yy)/0.05)%1-0.5)>0.42)
A[m]=230
c=base(S,S,(170,172,170),0.2,4)
c[rng.random((S,S))<0.03]*=0.7                  # dull zinc spots on the wire
A[:,:6]=255;c[:,:6]=(150,150,150)          # post every 2 m
A[:10,:]=255;A[-8:,:]=255                 # top and bottom rails
save('chainlink',c,tile,A)
# --- black palisade fence: vertical pales every 0.13 m, rails, alpha (02, 12, 13)
S=512;A=np.zeros((S,S));c=base(S,S,(28,28,30),0.3,4);pu=S/2.5
for k in range(int(2.5/0.13)+1):x=int(k*0.13*pu);A[:,x:x+5]=255
for y in (int(0.15*pu),int(1.6*pu)):A[y:y+7,:]=255
A[:,:8]=255
for k in range(int(2.5/0.13)+1):x=int(k*0.13*pu);c[:,x+3:x+5]+=38                 # lit edge on each pale
c[rng.random((S,S))<0.02]+=50                                                      # dust and chips
save('palisade',c,(2.5,2.1),A)
# --- orange rail with mesh infill: alpha (04, 05, 06)
S=256;A=np.zeros((S,S));c=base(S,S,(228,104,40),0.15,3)
A[:10,:]=255;A[-8:,:]=255
for x in range(0,S,64):A[:,x:x+6]=255
for x in range(0,S,8):A[:,x:x+2]=200
c[:4,:]+=50;c[rng.random((S,S))<0.02]-=60                                          # lit top edge, chips
save('rail_orange',c,(2,1.1),A)
# --- big screen face (blank, dark, off): pixel grid hint and frame
S=512;a=base(S,S,(28,30,34),0.3,8)
for k in range(0,S,8):a[k:k+1,:]*=0.7;a[:,k:k+1]*=0.7
a[:12,:]=a[-12:,:]=a[:,:12]=a[:,-12:]=(70,72,76)
save('screen',a,(1,1))
# --- signs (ground's own names only), lettering redrawn by hand from photos 03, 12, 17, 07
def font(n,s):return ImageFont.truetype(F+n,s)
def tio_logo(d,x,y,h):
    # white box, blue T, red i, blue O with a white NT outline inside (03, 07)
    w=int(h*1.65);d.rounded_rectangle([x,y,x+w,y+h],radius=h//10,fill=(245,245,245),outline=(200,200,205),width=max(2,h//30))
    f=font('arialbd.ttf',int(h*0.92))
    d.text((x+int(h*0.08),y+int(h*0.02)),'T',font=f,fill=(30,80,180))
    d.rectangle([x+int(h*0.62),y+int(h*0.28),x+int(h*0.80),y+int(h*0.88)],fill=(220,30,40))
    d.rectangle([x+int(h*0.62),y+int(h*0.1),x+int(h*0.80),y+int(h*0.22)],fill=(220,30,40))
    d.ellipse([x+int(h*0.86),y+int(h*0.1),x+int(h*1.55),y+int(h*0.9)],fill=(30,80,180))
    d.polygon([(x+int(h*1.05),y+int(h*0.25)),(x+int(h*1.3),y+int(h*0.25)),(x+int(h*1.3),y+int(h*0.5)),(x+int(h*1.38),y+int(h*0.6)),(x+int(h*1.3),y+int(h*0.75)),(x+int(h*1.05),y+int(h*0.75))],fill=(245,245,245))
    return w
def sign_band(n,w_m,h_m,text_parts,ppm=80):
    W,H=int(w_m*ppm),int(h_m*ppm);im=Image.new('RGB',(W,H),(34,78,160));d=ImageDraw.Draw(im)
    d.rectangle([0,0,W,int(H*0.18)],fill=(20,44,110));d.rectangle([0,int(H*0.82),W,H],fill=(20,44,110))
    d.rectangle([0,int(H*0.32),W,int(H*0.68)],fill=(48,110,200))
    f=font('segoeui.ttf',int(H*0.5));x=int(W*0.08)
    l=d.textlength('Welcome to',font=f);lw=int(H*0.62*1.65);r=d.textlength('Stadium',font=f);tot=l+lw+r+2*H*0.15;x=(W-tot)/2
    d.text((x,int(H*0.18)),'Welcome to',font=f,fill=(250,250,250));x+=l+H*0.15
    tio_logo(d,int(x),int(H*0.19),int(H*0.62));x+=lw+H*0.15
    d.text((x,int(H*0.18)),'Stadium',font=f,fill=(250,250,250))
    a=np.asarray(im,float)*(0.92+0.16*noise(H,W,4))[...,None];save(n,a,(w_m,h_m))
sign_band('sign_welcome',13.0,1.6,None)
def sign_text(n,text,w_m,h_m,bg,fg,fnt='arialbd.ttf',ppm=80,size=0.5,blocks=None):
    W,H=int(w_m*ppm),int(h_m*ppm)
    a=np.ones((H,W,3))*np.array(bg,float)*(0.85+0.3*noise(H,W,4))[...,None]
    if blocks:
        pu=ppm
        for r in range(0,H,int(0.2*pu)):
            a[r:r+2,:]*=0.6;off=int(0.2*pu) if (r//int(0.2*pu))%2 else 0
            for x in range(off,W,int(0.4*pu)):a[r:r+int(0.2*pu),x:x+2]*=0.6
    im=Image.fromarray(np.clip(a,0,255).astype(np.uint8));d=ImageDraw.Draw(im);f=font(fnt,int(H*size))
    tw=d.textlength(text,font=f);d.text(((W-tw)/2,H*(1-size)/2-H*0.06),text,font=f,fill=fg)
    a=np.asarray(im,float);save(n,a,(w_m,h_m))
sign_text('sign_ahmat','THE AH MAT GATES',13.0,1.4,(44,50,70),(236,236,236),'bahnschrift.ttf',size=0.42,blocks=True)
sign_text('sign_bonson','THE BONSON GATES',11.0,1.4,(44,50,70),(236,236,236),'georgiab.ttf',size=0.42,blocks=True)
sign_text('sign_rioli','MAURICE RIOLI STAND',16.0,1.2,(60,62,68),(236,110,80),'times.ttf',size=0.8)
# tower panel: navy board, light-blue band, TIO logo, 'Stadium' (07)
W,H=400,500;im=Image.new('RGB',(W,H),(22,52,128));d=ImageDraw.Draw(im)   # photo 15: navy board, light-blue block band on top, logo, 'Stadium'
for i in range(0,W,40):d.rectangle([i,0,i+19,22],fill=(70,140,215))
lh=int(H*0.2);tio_logo(d,int((W-lh*1.65)/2),int(H*0.14),lh)
f=font('arialbd.ttf',int(H*0.13));tw=d.textlength('Stadium',font=f);d.text(((W-tw)/2,int(H*0.42)),'Stadium',font=f,fill=(250,250,250))
a=np.asarray(im,float)*(0.92+0.16*noise(H,W,3))[...,None];save('sign_tower',a,(6,7.5))
# report grey stddev of every texture (rule: none under 10)
res={}
for n in TILE:
    g=np.asarray(Image.open(os.path.join(OUT,n+'.png')).convert('L'),float);res[n]=round(float(g.std()),1)
json.dump({'TILE':TILE,'std':res},open(os.path.join(OUT,'tex.json'),'w'),indent=1)
bad={k:v for k,v in res.items() if v<10};print('textures',len(res),'under 10:',bad)
