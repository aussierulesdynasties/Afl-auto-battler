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
roof('roof_grey',(196,200,202))       # centre roof, satellite light grey (Maurice Rioli Stand)
roof('roof_white',(232,232,228),grime=0.18)  # wing roofs, satellite white
roof('roof_mlc',(226,226,222),grime=0.12)
# --- roof underside: mid-grey steel deck with purlins every 1.2 m and rafters every 8 m (10, 11, 17)
W=512;a=base(W,W,(92,96,100),0.2,4);p=W/8
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
# MLC south facade (18), one 4.8 x 9.6 m tile, bottom up: dark plinth; ground-floor glass with dark mullions every 1.2 m
# and a transom at 2.6 m; charcoal slab edge; glass balustrade with a light top rail; upper glass; charcoal ribbed fascia
W,H=480,960;pm=100;a=np.zeros((H,W,3))
def zr(z0,z1):return slice(H-round(z1*pm),H-round(z0*pm))
a[zr(0,0.3)]=base(30,W,(52,54,56),0.2,3)
g=base(300,W,(46,54,62),0.15,2)*(0.8+0.45*np.linspace(1,0,300))[:,None,None];a[zr(0.3,3.3)]=g
a[zr(3.3,4.1)]=base(80,W,(54,56,60),0.2,3)
a[zr(4.1,5.1)]=base(100,W,(112,122,128),0.12,2)
a[zr(5.1,7.4)]=base(230,W,(50,58,66),0.15,2)*(0.85+0.35*np.linspace(1,0,230))[:,None,None]
r=base(220,W,(48,50,54),0.18,3)
for y in range(0,220,14):r[y:y+2]*=0.75
a[zr(7.4,9.6)]=r
for x in range(0,W,int(1.2*pm)):
    for z0,z1,c in ((0.3,3.3,(72,74,78)),(5.1,7.4,(64,66,70))):a[zr(z0,z1),max(0,x-3):x+4]=c
    a[zr(4.1,5.1),max(0,x-1):x+2]=(150,152,150)
for z,c in ((2.6,(72,74,78)),(6.6,(64,66,70))):a[zr(z-0.03,z+0.03)]=c
a[zr(5.02,5.1)]=(196,198,196)
a=a*(0.93+0.14*noise(H,W,4))[...,None];save('glass_mlc',a,(4.8,9.6))
glass('glass_box',(150,165,170),(60,62,66),pw=1.8)    # corporate boxes: pale glass, dark frames (17)
# --- cladding panels: light grey fibre-cement 1.2 x 2.4 m with joints (rear building, 04, 05, 14)
def clad(n,col,pw=1.2,ph=2.4,tile=(4.8,4.8),var=0.14):
    S=512;a=base(S,S,col,var,3);a=streaks(a,0.14,40);pu=S/tile[0]
    for k in range(int(tile[0]/pw)+1):x=int(k*pw*pu)%S;a[:,max(0,x-1):x+2]*=0.7
    for k in range(int(tile[1]/ph)+1):y=int(k*ph*pu)%S;a[max(0,y-1):y+2,:]*=0.7
    save(n,a,tile)
clad('clad_grey',(150,152,152))
clad('clad_cream',(214,208,190))
clad('clad_dark',(168,170,168),var=0.2)   # centre stand band under the boxes: light grey fascia (17)
# east building wall (07, 15, 19): cream render, dark window band 0.9-2.3 m, 4.8 x 4.2 m tile
S=512;a=base(S,S,(212,204,184),0.14,3);a=streaks(a,0.14,40);pv=S/4.2;y0,y1=S-int(2.3*pv),S-int(0.9*pv);a[y0:y1,:]=base(y1-y0,S,(38,44,50),0.2,2)
for k in range(0,S,int(S/4.8*1.6)):a[y0:y1,max(0,k-2):k+3]=(150,150,146)
save('wall_east',a,(4.8,4.2))
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
# seat plastics (10, 11, 15, 16, 17): light blue, orange, purple, red, teal; sun-faded, scuffs
for n_,c_ in (('seat_blue',(122,199,230)),('seat_orange',(239,118,75)),('seat_purple',(162,89,118)),('seat_red',(206,60,48)),('seat_teal',(48,150,160))):save(n_,(np.ones((128,128,3))*np.array(c_,float)+(rng.random((128,128))-0.5)[...,None]*8)*(0.97+0.06*noise(128,128,2))[...,None],(0.5,0.5))
paint('steel_rust',(128,72,52))   # scoreboard legs (07)
paint('screen_back',(122,120,88))   # olive cladding on the screen box sides (19)
paint('timber',(150,104,66),var=0.3)
# copper-brown cladding panels on the Michael Long Centre entry (18): smooth sheets 1.2 x 3 m, dark joints
H,W=512,512;a=base(H,W,(146,88,58),0.18,3);a=streaks(a,0.12,40)
for x in range(0,W,int(W/3*1.2)):a[:,x:x+3]*=0.5
a[H//2-1:H//2+2,:]*=0.55
save('timber',a,(3,3))
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
# --- big screen face (off): khaki-olive panel face as photo 19, pixel grid hint and frame
S=512;a=base(S,S,(112,104,78),0.2,8)
for k in range(0,S,8):a[k:k+1,:]*=0.7;a[:,k:k+1]*=0.7
a[:12,:]=a[-12:,:]=a[:,:12]=a[:,-12:]=(60,62,58)
save('screen',a,(1,1))
# --- signs (ground's own names only), lettering redrawn by hand from photos 03, 12, 17, 07
def font(n,s):return ImageFont.truetype(F+n,s)
def tio_logo(d,x,y,h,box=(245,245,245)):
    # white box, blue T, red i, blue O with a white NT outline inside (03, 07)
    w=int(h*1.65);d.rounded_rectangle([x,y,x+w,y+h],radius=h//10,fill=box,outline=(200,200,205),width=max(2,h//30))
    f=font('arialbd.ttf',int(h*0.92))
    d.text((x+int(h*0.08),y+int(h*0.02)),'T',font=f,fill=(30,80,180))
    d.rectangle([x+int(h*0.62),y+int(h*0.28),x+int(h*0.80),y+int(h*0.88)],fill=(220,30,40))
    d.rectangle([x+int(h*0.62),y+int(h*0.1),x+int(h*0.80),y+int(h*0.22)],fill=(220,30,40))
    d.ellipse([x+int(h*0.86),y+int(h*0.1),x+int(h*1.55),y+int(h*0.9)],fill=(30,80,180))
    d.polygon([(x+int(h*1.05),y+int(h*0.25)),(x+int(h*1.3),y+int(h*0.25)),(x+int(h*1.3),y+int(h*0.5)),(x+int(h*1.38),y+int(h*0.6)),(x+int(h*1.3),y+int(h*0.75)),(x+int(h*1.05),y+int(h*0.75))],fill=(245,245,245))
    return w
def sign_band(n,w_m,h_m,text_parts,ppm=80,box=(245,245,245)):
    W,H=int(w_m*ppm),int(h_m*ppm);im=Image.new('RGB',(W,H),(34,78,160));d=ImageDraw.Draw(im)
    d.rectangle([0,0,W,int(H*0.18)],fill=(20,44,110));d.rectangle([0,int(H*0.82),W,H],fill=(20,44,110))
    d.rectangle([0,int(H*0.32),W,int(H*0.68)],fill=(48,110,200))
    f=font('segoeui.ttf',int(H*0.5));x=int(W*0.08)
    l=d.textlength('Welcome to',font=f);lw=int(H*0.62*1.65);r=d.textlength('Stadium',font=f);tot=l+lw+r+2*H*0.15;x=(W-tot)/2
    d.text((x,int(H*0.18)),'Welcome to',font=f,fill=(250,250,250));x+=l+H*0.15
    tio_logo(d,int(x),int(H*0.19),int(H*0.62),box);x+=lw+H*0.15
    d.text((x,int(H*0.18)),'Stadium',font=f,fill=(250,250,250))
    a=np.asarray(im,float)*(0.92+0.16*noise(H,W,4))[...,None];save(n,a,(w_m,h_m))
sign_band('sign_welcome',13.0,1.6,None)
sign_band('sign_welcome_tan',13.0,1.6,None,box=(214,160,104))   # Bonson gate: the logo sits on a tan box (12)
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
# Bonson gate front (12), 14.3 x 4.5 m: navy block; cream raised letters on the block; two open passages with black gates;
# recessed ticket bay with three windows; ENTRY ONLY / EXIT ONLY, a dark ticket-price board and a grey display box.
# Positions are fractions of the wall width read off photo 12 (wall 150-1840 px, 100 px per metre of height).
def gate_front(name,GW,text,tc,box,entry,ticket,GH=4.5,gp=80):
    W,H=int(GW*gp),int(GH*gp)
    a=base(H,W,(44,50,70),0.25,4)
    for r in range(0,H,int(0.2*gp)):
        a[r:r+2,:]*=0.6;off=int(0.2*gp) if (r//int(0.2*gp))%2 else 0
        for x in range(off,W,int(0.4*gp)):a[r:r+int(0.2*gp),x:x+2]*=0.6
    def R(f0,f1,z0,z1):return slice(H-round(z1*gp),H-round(z0*gp)),slice(round(f0*W),round(f1*W))
    for f0,f1 in ((0.168,0.257),(0.713,0.802)):   # passages: dark depth, black palisade gate
        a[R(f0,f1,0,3.15)]=base(round(3.15*gp),round(f1*W)-round(f0*W),(70,72,70),0.2,3)
        ys,xs=R(f0,f1,0,2.3);sub=a[ys,xs]
        for x in range(0,sub.shape[1],9):sub[:,x:x+3]=(18,18,20)
        sub[:6]=(18,18,20)
    ys,xs=R(0.299,0.666,0,3.15);a[ys,xs]*=0.72;a[R(0.299,0.666,2.95,3.15)]=(22,22,28)   # recessed bay, soffit shadow
    for f0,f1 in ((0.364,0.402),(0.464,0.506),(0.569,0.611)):
        a[R(f0-0.004,f1+0.004,1.36,2.49)]=(214,214,210);a[R(f0,f1,1.4,2.45)]=base(84,round(f1*W)-round(f0*W),(52,62,58),0.2,2)
    if ticket:a[R(0.775,0.893,1.7,3.2)]=(16,16,18)      # ticket-price board
    a[R(*box,3.4,4.4)]=(150,154,156);a[R(box[0]+0.006,box[1]-0.006,3.48,4.32)]=(70,74,76)   # display box
    im=Image.fromarray(np.clip(a,0,255).astype(np.uint8));d=ImageDraw.Draw(im)
    for f0,f1,t in (((0.200,0.243,'ENTRY'),(0.882,0.918,'EXIT')) if entry else ()):
        d.rectangle([round(f0*W),H-round(4.3*gp),round(f1*W),H-round(3.35*gp)],fill=(238,232,222))
        fs=font('arialbd.ttf',int(0.26*gp))
        for k,w_ in enumerate((t,'ONLY')):
            tw=d.textlength(w_,font=fs);d.text(((f0+f1)/2*W-tw/2,H-round(4.2*gp)+k*int(0.38*gp)),w_,font=fs,fill=(196,40,48))
    fs=font('bahnschrift.ttf',int(0.5*gp));t=text;tw=d.textlength(t,font=fs)
    d.text((tc*W-tw/2+3,H-round(4.28*gp)+3),t,font=fs,fill=(20,20,26));d.text((tc*W-tw/2,H-round(4.28*gp)),t,font=fs,fill=(236,232,218))
    save(name,np.asarray(im,float),(GW,GH))
gate_front('gate_bonson_front',14.3,'THE BONSON GATES',0.4855,(0.672,0.758),True,True)
gate_front('gate_ahmat_front',14.8,'THE AH MAT GATES',0.48,(0.169,0.256),False,False)   # same family (03): no entry/exit signs or ticket board
sign_text('sign_rioli','MAURICE RIOLI STAND',16.0,1.2,(60,62,68),(236,110,80),'times.ttf',size=0.8)
# tower panel (07, 15): blue board, light-blue block band on top, TIO logo box, 'Stadium'; 6.2 x 5.8 m
W,H=520,480;im=Image.new('RGB',(W,H),(36,84,176));d=ImageDraw.Draw(im)
d.rectangle([0,int(H*0.06),W,int(H*0.40)],fill=(28,70,160))
for i in range(0,W,40):d.rectangle([i,int(H*0.13),i+22,int(H*0.33)],fill=(80,150,225))
lh=int(H*0.24);tio_logo(d,int((W-lh*1.65)/2),int(H*0.11),lh)
f=font('segoeuib.ttf',int(H*0.17));tw=d.textlength('Stadium',font=f);d.text(((W-tw)/2,int(H*0.50)),'Stadium',font=f,fill=(250,250,250))
a=np.asarray(im,float)*(0.92+0.16*noise(H,W,3))[...,None];save('sign_tower',a,(6.2,5.8))
# main scoreboard (07): blue 'TIO Stadium' banner on top, black 'Larrakia Country - Darwin' band under it; 9.3 m wide
W,H=860,130;im=Image.new('RGB',(W,H),(30,84,180));d=ImageDraw.Draw(im)
for y in range(H):d.line([(0,y),(W,y)],fill=(30+int(30*y/H),84+int(40*y/H),180+int(30*y/H)))
d.rectangle([0,0,W,5],fill=(20,40,100));d.rectangle([0,H-5,W,H],fill=(20,40,100))
lh=int(H*0.62);f=font('segoeuib.ttf',int(H*0.6));tw=d.textlength('Stadium',font=f);tot=lh*1.65+H*0.15+tw;x=(W-tot)/2
tio_logo(d,int(x),int(H*0.19),lh);d.text((x+lh*1.65+H*0.15,int(H*0.06)),'Stadium',font=f,fill=(250,250,250))
a=np.asarray(im,float)*(0.92+0.16*noise(H,W,3))[...,None];save('sign_sb_banner',a,(8.6,1.3))
sign_text('sign_sb_band','Larrakia Country - Darwin',8.6,0.9,(24,24,26),(240,240,240),'arialbd.ttf',size=0.62)
# report grey stddev of every texture (for the board; no floor since 2026-11-19)
res={}
for n in TILE:
    g=np.asarray(Image.open(os.path.join(OUT,n+'.png')).convert('L'),float);res[n]=round(float(g.std()),1)
json.dump({'TILE':TILE,'std':res},open(os.path.join(OUT,'tex.json'),'w'),indent=1)
bad={k:v for k,v in res.items() if v<10};print('textures',len(res),'under 10:',bad)
