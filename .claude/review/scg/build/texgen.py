# Hand-made textures for the SCG model: every material drawn at real scale with crisp edges, colours read from daylight
# photos. No photo pixels. Writes out/tex/<mat>.png and out/tex/scale.json (metres covered by one tile, u x v).
import numpy as np,cv2,json,os
os.makedirs('out/tex',exist_ok=True);rng=np.random.default_rng(7);SCALE={}
def mottle(h,w,cells,amp):          # soft large-scale colour variation (weathering), not a blur of features
    n=rng.standard_normal((cells,cells));n=np.pad(n,1,mode='wrap')
    n=cv2.resize(n,(w+2*w//cells,h+2*h//cells),interpolation=cv2.INTER_CUBIC)[h//cells:h//cells+h,w//cells:w//cells+w]
    return n[...,None]*amp
def grain(h,w,amp):return rng.standard_normal((h,w,1))*amp
def save(name,img,tu,tv):
    cv2.imwrite('out/tex/%s.png'%name,np.clip(img,0,255).astype(np.uint8)[:,:,::-1]);SCALE[name]=[tu,tv]
def base(h,w,col):return np.ones((h,w,3))*np.array(col,float)
def M(x,tu,W):return int(round(x/tu*W))   # metres -> px along u

# --- seats: 24 seats of 0.5 m + a 1.1 m aisle stair = 13.1 m wide; 4 rows of 0.85 m
def seats():
    tu,tv=13.1,3.4;W,H=2048,532;img=base(H,W,(104,108,104))+grain(H,W,4)   # concrete terrace, in the seats' shade
    rp=H/4
    for r in range(4):
        y0=int(r*rp)
        img[y0:y0+int(rp*0.10)]=(80,82,80)                         # riser shadow line
        for s in range(24):
            x0=M(s*0.5+0.02,tu,W);x1=M(s*0.5+0.48,tu,W)
            c=np.array((32,128,122))+rng.integers(-5,6,3)            # SCG teal seats
            img[y0+int(rp*0.12):y0+int(rp*0.66),x0:x1]=c               # seat back
            img[y0+int(rp*0.12):y0+int(rp*0.16),x0:x1]=c+28            # top edge catching light
            img[y0+int(rp*0.66):y0+int(rp*0.86),x0+2:x1-2]=c*0.62      # seat pan in shade
        ax=M(12.0,tu,W)                                               # aisle stair
        img[y0:y0+int(rp),ax:ax+M(1.1,tu,W)]=(140,140,134)
        for k in range(3):img[y0+int(rp*k/3):y0+int(rp*k/3)+3,ax:ax+M(1.1,tu,W)]=(205,180,40)   # yellow step nosings
        img[y0:y0+int(rp),ax:ax+4]=(120,120,118);img[y0:y0+int(rp),ax+M(1.1,tu,W)-4:ax+M(1.1,tu,W)]=(120,120,118)
    save('seat',img,tu,tv)

def grass():
    tu=tv=40.0;N=2048;img=base(N,N,(92,142,58));x=np.arange(N)
    img[:,(x//(N//5))%2==1]=(108,158,66)                              # 8 m mowing stripes
    img+=grain(N,N,5)*np.array([0.5,1,0.4])+mottle(N,N,3,2)
    save('grass',img,tu,tv)

def roof():
    tu,tv=12.0,12.0;N=1536;img=base(N,N,(236,238,239))+mottle(N,N,5,3)+grain(N,N,1.5)
    for k in range(24):x=M(k*0.5,tu,N);img[:,x:x+2]=(214,216,218);img[:,x+2:x+3]=(248,249,250)   # standing seams
    img[:4]=(200,202,204)                                             # sheet end lap
    save('roof',img,tu,tv)

def roofu():
    tu,tv=6.0,6.0;N=1024;img=base(N,N,(196,199,201))+grain(N,N,2)
    for k in range(4):y=M(k*1.5,tv,N);img[y:y+10]=(150,153,156);img[y+10:y+13]=(222,224,225)   # purlins
    img[:,:16]=(130,133,136)                                          # rafter
    save('roofu',img,tu,tv)

def fascia():
    tu,tv=6.0,3.0;W,H=1024,512;img=base(H,W,(238,240,240))+grain(H,W,1.5)
    for k in range(2):x=M(k*3.0,tu,W);img[:,x:x+3]=(190,192,194)
    img[:10]=(250,250,250);img[-14:]=(120,122,124)                    # top capping, drip edge shadow
    save('fascia',img,tu,tv)

def panels(name,col,pw,ph,tu,tv,joint,N=1024,ribs=0):
    W=N;H=int(N*tv/tu);img=base(H,W,col)+mottle(H,W,4,4)+grain(H,W,2)
    for k in range(int(round(tu/pw))):x=M(k*pw,tu,W);img[:,x:x+3]=joint
    for k in range(int(round(tv/ph))):y=int(k*ph/tv*H);img[y:y+3]=joint
    if ribs:
        for k in range(int(tu/ribs)):x=M(k*ribs,tu,W);img[:,x:x+2]=np.array(col)*0.85;img[:,x+2:x+3]=np.minimum(255,np.array(col)*1.08)
    save(name,img,tu,tv)

def bricks(name,col,mortar,tu=2.4,tv=2.4,N=1024):
    img=base(N,N,mortar)+grain(N,N,3);bh=0.086;bl=0.24
    for r in range(int(round(tv/bh))):
        y0=int(r*bh/tv*N);y1=int((r+1)*bh/tv*N)-3;off=(bl/2 if r%2 else 0)
        for c in range(-1,int(tu/bl)+1):
            x0=M(c*bl+off,tu,N);x1=M((c+1)*bl+off,tu,N)-3
            cc=np.array(col)+rng.integers(-12,13)+rng.integers(-5,6,3)
            img[y0:y1,max(0,x0):max(0,min(N,x1))]=cc
    img+=grain(N,N,4)
    save(name,img,tu,tv)

def glass(name,tu=6.0,tv=3.6,N=1024,tint=(58,78,98),mull=1.5,mc=(184,188,192),transom=True):
    W=N;H=int(N*tv/tu);yy,xx=np.mgrid[0:H,0:W]
    img=np.array(tint,float)+((xx/W*0.6+yy/H*0.4)[...,None]*np.array([40,40,38]))   # sky reflection gradient
    img[(((xx+yy*0.7)//90)%5==0)]+=14                                                     # reflection streaks
    for k in range(int(round(tu/mull))):x=M(k*mull,tu,W);img[:,x:x+10]=mc                        # mullions
    if transom:img[:12]=mc;img[H//2-4:H//2+4]=mc                 # transom
    save(name,img,tu,tv)

def tower():
    tu,tv=2.0,4.0;W,H=256,512;img=base(H,W,(168,160,146))+mottle(H,W,3,6)+grain(H,W,3)
    for k in range(4):x=int(k*W/4);img[:,x:x+2]=(150,143,130)       # formwork lines
    img[::64]=(152,145,132)
    save('tower',img,tu,tv)

def lamp():
    tu=tv=2.0;N=512;img=base(N,N,(70,72,76));
    for i in range(4):
        for j in range(4):
            cv2.circle(img,(int((i+0.5)*N/4),int((j+0.5)*N/4)),int(N/10),(246,246,238),-1);cv2.circle(img,(int((i+0.5)*N/4),int((j+0.5)*N/4)),int(N/10),(150,150,150),3)
    save('lamp',img,tu,tv)

seats();grass();roof();roofu();fascia()
panels('wall',(212,208,198),4.0,3.0,8.0,6.0,(170,166,158))
panels('conc',(196,192,184),2.4,1.2,4.8,4.8,(160,156,150))
panels('slab',(228,226,221),6.0,10.0,6.0,1.0,(190,188,184),N=512)
panels('dark',(48,50,54),3.0,3.0,6.0,6.0,(36,38,40))
panels('facade',(226,227,225),1.2,3.6,7.2,7.2,(188,190,190))
panels('facade2',(152,157,162),3.0,3.0,6.0,6.0,(120,124,128),ribs=0.3)
panels('apron',(66,98,58),40.0,40.0,4.0,4.0,(66,98,58),N=512)
panels('ground',(84,84,86),40.0,40.0,8.0,8.0,(84,84,86),N=512)
panels('stone',(214,210,200),1.2,6.0,4.8,6.0,(184,180,172))
panels('steel',(204,206,209),2.0,2.0,2.0,2.0,(204,206,209),N=256)
panels('plant',(182,182,177),1.0,1.0,4.0,4.0,(150,150,146),ribs=0.1)
panels('headback',(112,114,118),1.0,1.0,4.0,4.0,(90,92,96),N=512)
panels('screen',(22,24,30),4.0,4.0,4.0,4.0,(22,24,30),N=256)
panels('hroof',(60,124,58),40.0,40.0,2.0,2.0,(60,124,58),N=512,ribs=0.2)
bricks('buff',(206,178,132),(222,214,198));bricks('brick',(160,78,58),(196,186,172))
# --- boundary fence (reference photo): white boards with red panels; pattern runs along the fence only
def fence():
    tu,tv=12.0,1.2;W,H=1024,128;img=base(H,W,(238,238,234))+grain(H,W,1.5)
    # director: no sponsor boards, bare fence
    for k in range(4):x=M(k*3.0,tu,W);img[:,x:x+2]=(150,150,148)
    save('fence',img,tu,tv)
# --- upper-deck LED ribbon (reference photo): mostly orange and red, short blue, green and purple runs
def ribbon():
    tu,tv=48.0,1.0;W,H=2048,64;img=base(H,W,(232,112,38))
    runs=[(0,7,(232,112,38)),(7,10,(214,52,40)),(10,13,(44,112,204)),(13,22,(236,128,44)),(22,24,(78,170,92)),(24,26,(132,72,162)),
          (26,34,(226,96,36)),(34,37,(214,52,40)),(37,40,(236,170,52)),(40,44,(44,112,204)),(44,48,(232,112,38))]
    img[:]=(30,32,36)   # director: no boards - the LED ribbon is blank
    img+=grain(H,W,3)
    save('ribbon',img,tu,tv)
fence();ribbon()
# --- raked underside of the stand (063 photo, Messenger east end): dark grey, a lighter step line every 0.9 m row
def soffit():
    tu,tv=4.0,3.6;W,H=256,232;img=base(H,W,(52,58,64))+grain(H,W,2)
    for k in range(4):y=int(k*0.9/tv*H);img[y:y+4]=(86,92,98)
    save('soffit',img,tu,tv)
soffit()
panels('rail',(150,152,154),2.0,2.0,2.0,2.0,(140,142,144),N=128)
glass('glass');glass('glassblk',tint=(22,22,26),mc=(58,58,62));glass('glassd',tint=(46,62,82));glass('glassm',tint=(34,40,48));glass('glassroof',tu=3.5,tv=3.5,tint=(118,136,160),mull=1.75)
# Trumper/O'Reilly backs (Gate 9 + Gate E photos): bright blue curtain glass, grey floor spandrels, pale grey band
glass('glasst',tu=6.0,tv=3.0,tint=(48,104,176),mull=1.5,mc=(196,200,204),transom=False)
panels('spand',(158,164,168),1.5,0.9,6.0,0.9,(128,132,136),N=512)
panels('cladl',(208,211,212),1.5,1.0,6.0,2.0,(178,180,182))
tower();lamp()

# --- scoreboard face (one picture over the whole board, 31.4 x 16.9 m): dark frame, white venue name on the header band,
# broadcast screen, blue score panel with white rows, green LED strip along the bottom (layout read off the reference photo)
def sbface():
    from PIL import Image as _I,ImageDraw as _D,ImageFont as _F
    W,H=2048,1104;img=base(H,W,(26,28,32))+grain(H,W,2)
    def box(x0,y0,x1,y1,c):img[int(y0*H):int(y1*H),int(x0*W):int(x1*W)]=c
    box(0.0,0.0,1.0,0.20,(18,18,20))
    g=np.linspace(0,1,int(0.44*H))[:,None,None]
    scr=(1-g)*np.array([34,52,96.])+g*np.array([46,118,62.]);img[int(0.22*H):int(0.22*H)+scr.shape[0],int(0.02*W):int(0.76*W)]=scr
    box(0.78,0.22,0.98,0.66,(38,86,168))
    # director: no lettering - the score panel's text rows are gone, the panel is blank
    box(0.02,0.68,0.98,0.96,(30,32,36))   # no boards: the advert strip is blank
    im=_I.fromarray(np.clip(img,0,255).astype(np.uint8));d=_D.Draw(im)
    # director: no lettering - the ground-name header is a blank panel
    save('sbface',np.asarray(im).astype(float),1.0,1.0)
def sbad():
    W,H=256,512;img=base(H,W,(30,32,36))+grain(H,W,2)   # no boards: the sponsor panel is blank
    img[:,:10]=(20,22,24);img[:,-10:]=(20,22,24);img[:10]=(20,22,24);img[-10:]=(20,22,24)
    save('sbad',img,1.0,1.0)
sbface();sbad()
exec(open('hertex.py').read())
json.dump(SCALE,open('out/tex/scale.json','w'),indent=0);print(sorted(SCALE))
