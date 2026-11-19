# Heritage stands, hand-painted wall elevations (exec'd from texgen.py). Colours and layout read off the street photos
# (refs3/020-025: red brick, cream sandstone string courses, white sash windows, green verandah awnings) and the
# field photo (refs5/SCG-ladies-members-stands.jpg: two-tier open stands, maroon seats, slim columns, green verandah,
# white balustrade, yellow eave trim). No photo pixels: every element is drawn.
exec(open('blds.py').read())
PXM=140   # pixels per metre
BRICK=(132,76,58);   # street photos 020-025/053 brick median ~130,82,63 (024 sunlit 156,83,52; 053 overcast 105,64,47)
MORTAR=(196,186,172);SAND=(222,204,160);SANDD=(190,170,128);WHITE=(238,236,228)
GLASSC=(38,42,50);GREEN=(56,122,58);GREEND=(34,82,40);YEL=(226,196,96)
def _row(H,z):return int(round((H-z)*PXM))          # metres above ground -> image row (row 0 = top = v 1)
def _brick(img,tu,H):
    h,w=img.shape[:2];img[:]=np.array(MORTAR,float);bh=0.086;bl=0.24
    for r in range(int(H/bh)+1):
        y1=h-int(r*bh*PXM);y0=h-int((r+1)*bh*PXM)+2;off=bl/2 if r%2 else 0
        for c in range(-1,int(tu/bl)+2):
            x0=int((c*bl+off)*PXM);x1=int(((c+1)*bl+off)*PXM)-2
            if x1<=0 or x0>=w:continue
            img[max(0,y0):max(0,y1),max(0,x0):min(w,x1)]=np.array(BRICK)+rng.integers(-12,13)+rng.integers(-5,6,3)
def _band(img,H,z0,z1,col,x0=None,x1=None):
    r0,r1=_row(H,z1),_row(H,z0);img[r0:r1,(x0 or 0):(x1 if x1 is not None else img.shape[1])]=col
def _window(img,H,cx,z0,z1,wd,arch=False):
    x0=int((cx-wd/2)*PXM);x1=int((cx+wd/2)*PXM);r0,r1=_row(H,z1),_row(H,z0);f=int(0.09*PXM)
    _band(img,H,z0-0.16,z0,SAND,x0-int(0.12*PXM),x1+int(0.12*PXM))                  # sandstone sill
    if arch:_band(img,H,z1,z1+0.3,SAND,x0-int(0.08*PXM),x1+int(0.08*PXM))           # segmental head
    img[r0:r1,x0:x1]=WHITE                                                            # frame
    img[r0+f:r1-f,x0+f:x1-f]=GLASSC
    xm=(x0+x1)//2;rm=(r0+r1)//2
    img[rm-f//2:rm+f//2,x0:x1]=WHITE                                                  # meeting rail of the sash
    img[r0:r1,xm-f//3:xm+f//3]=WHITE                                                  # glazing bar
    img[r0+f:rm-f//2,x0+f:x1-f]+=np.linspace(26,0,rm-f//2-r0-f)[:,None,None]           # sky catching the top sash
def hwall(H):
    """street, side and back elevation: one 3.6 m bay of brick with sash windows on each floor."""
    tu=3.6;img=np.zeros((int(H*PXM),int(tu*PXM),3));_brick(img,tu,H);cx=tu/2
    _band(img,H,0,0.9,SANDD);_band(img,H,0.86,0.9,SAND)                               # sandstone plinth
    _window(img,H,cx,1.3,3.7,1.25,arch=True)
    _band(img,H,4.05,4.65,GREEN);_band(img,H,4.0,4.1,WHITE);_band(img,H,4.6,4.7,GREEND)  # verandah awning line
    for k in range(0,int(tu*PXM),int(0.15*PXM)):img[_row(H,4.6):_row(H,4.1),k:k+3]=GREEND  # awning corrugations
    _band(img,H,5.15,5.45,SAND)                                                       # string course
    _window(img,H,cx,6.0,8.4,1.15,arch=True)
    if H>=12.0:
        _band(img,H,9.0,9.25,SAND);_window(img,H,cx,9.7,H-1.4,1.0)
    _band(img,H,H-0.75,H,SAND);_band(img,H,H-0.8,H-0.75,SANDD)                        # cornice
    for k in range(0,int(tu*PXM),int(0.3*PXM)):img[_row(H,H-0.55):_row(H,H-0.75),k:k+int(0.15*PXM)]=SANDD   # dentils
    return img+grain(img.shape[0],img.shape[1],2.5),tu
def hstand(H,colc,zv=7.3):
    """field elevation: the two-tier open stand. Lower tier under the green verandah, white balustrade, upper tier of
    maroon seats rising to a dark roof space, slim columns every 4.7 m, yellow eave trim."""
    tu=4.7;img=np.zeros((int(H*PXM),int(tu*PXM),3));img[:]=(30,26,28)
    def seats(z0,z1):
        z=z0
        while z<z1-0.3:
            _band(img,H,z,z+0.42,(104,40,46));_band(img,H,z+0.36,z+0.42,(138,62,66));_band(img,H,z+0.42,z+0.5,(52,40,42));z+=0.5
    zl=zv-0.4;zb=zv+0.4;zt=zb+1.1   # verandah fascia height back-projected from the field photo (Ladies' 7.3, Members' 4.9)
    _band(img,H,0,0.9,(200,190,160));_band(img,H,0.85,0.9,WHITE)                      # front wall of the lower tier
    seats(0.9,zl-0.05)
    _band(img,H,zl,zb-0.1,GREEN);_band(img,H,zb-0.1,zb,YEL);_band(img,H,zl-0.05,zl+0.05,YEL)   # lower verandah fascia
    _band(img,H,zb,zt,(40,34,36))
    _band(img,H,zt-0.1,zt,WHITE);_band(img,H,zb+0.05,zb+0.15,WHITE)                   # balustrade rails
    for k in range(0,int(tu*PXM),int(0.16*PXM)):img[_row(H,zt-0.1):_row(H,zb+0.15),k:k+int(0.06*PXM)]=WHITE   # balusters
    seats(zt,H-2.4)
    _band(img,H,H-0.45,H,YEL);_band(img,H,H-0.55,H-0.45,GREEND)                       # eave trim
    ax0,ax1=int(2.75*PXM),int(3.35*PXM)                                                  # aisle stairs, both tiers
    for z0_,z1_ in ((0.9,zl-0.05),(zt,H-2.4)):
        img[_row(H,z1_):_row(H,z0_),ax0:ax1]=(150,146,138)
        z=z0_
        while z<z1_-0.25:img[_row(H,z+0.27):_row(H,z+0.25),ax0:ax1]=(214,186,70);z+=0.25
    x=int(0.24*PXM);img[_row(H,H-0.45):_row(H,0.9),0:x]=colc;img[_row(H,H-0.45):_row(H,0.9),0:4]=np.array(colc)*0.7   # column
    img[_row(H,H-0.45):_row(H,H-1.1),x:int(0.8*PXM)]=np.array(colc)*0.9                 # bracket under the eave
    return img+grain(img.shape[0],img.shape[1],2.5),tu
def hped():
    """Members' pediment under the clock tower: cream tympanum, arched fanlight, white raking trim (field photo)."""
    W,Hh=1024,512;img=base(Hh,W,SAND)+grain(Hh,W,2);yy,xx=np.mgrid[0:Hh,0:W]
    ax_,ay_=int(W*0.40),int((Hh-30)*0.80)
    cv2.ellipse(img,(W//2,Hh-30),(ax_,ay_),0,180,360,(176,140,64),-1)               # gilt fanlight filling the arch
    for a in range(180,361,12):
        t=math.radians(a);cv2.line(img,(W//2,Hh-30),(int(W/2+ax_*math.cos(t)),int(Hh-30+ay_*math.sin(t))),(120,96,44),5)
    cv2.ellipse(img,(W//2,Hh-30),(ax_,ay_),0,180,360,WHITE,14);cv2.ellipse(img,(W//2,Hh-30),(90,64),0,180,360,(120,96,44),-1)
    img[Hh-34:Hh]=WHITE
    save('hped',img,1.0,1.0)
def hgab():
    """gable faces (Members' wing, back ranges): cream-painted vertical boards with cover strips, weathering streaks."""
    tu,tv=1.2,1.2;W,H=256,256;img=base(H,W,(226,206,150))+mottle(H,W,4,8)+grain(H,W,4)
    for k in range(0,W,32):img[:,k:k+5]=(196,176,124);img[:,k+5:k+7]=(240,226,180)
    for _ in range(14):
        x=rng.integers(0,W);l=rng.integers(40,200);y=rng.integers(0,H-l);img[y:y+l,x:x+2]-=14
    save('hgab',img,tu,tv)
hgab()
import math
for z in sorted({b[6] for b in BLD}):
    im,tu=hwall(z);save('hw%d'%round(z*10),im,tu,z)
    im,tu=hstand(z,(226,206,120) if True else 0);save('hsL%d'%round(z*10),im,tu,z)
    im,tu=hstand(z,(150,196,120),4.9);save('hsM%d'%round(z*10),im,tu,z)
hped()
def ashlar():
    """cream sandstone in coursed blocks (the end pier beside the Ladies' Stand reads cream in the aerial photo)."""
    tu,tv=2.4,1.2;img=np.zeros((int(tv*PXM),int(tu*PXM),3));img[:]=SANDD;bh=0.3;bl=0.6
    for r in range(int(tv/bh)):
        y0=int(r*bh*PXM)+2;y1=int((r+1)*bh*PXM)-1;off=bl/2 if r%2 else 0
        for c in range(-1,int(tu/bl)+1):
            x0=int((c*bl+off)*PXM)+2;x1=int(((c+1)*bl+off)*PXM)-1
            if x1<=0 or x0>=img.shape[1]:continue
            img[y0:y1,max(0,x0):min(img.shape[1],x1)]=np.array(SAND)+rng.integers(-10,11)+rng.integers(-4,5,3)
    save('ashlar',img+grain(img.shape[0],img.shape[1],3),tu,tv)
ashlar()
panels('skyglass',(96,140,138),1.0,1.0,1.2,1.2,(70,110,108),N=64)   # glazing bars every 1.2 m
panels('trim',(232,214,140),1.0,1.0,4.0,4.0,(232,214,140),N=64)      # yellow-cream eave and barge trim (field photo)
panels('btrim',(238,236,228),1.0,1.0,4.0,4.0,(238,236,228),N=64)     # white barge boards

def hbal():
    """white cast-iron balustrade of the Members' upper tier: top and bottom rails, balusters every 0.12 m (field photo)."""
    tu,tv=0.96,0.9;W,H=384,360;img=base(H,W,(70,58,60))+grain(H,W,3)       # shadowed seats seen between the balusters
    for k in range(8):
        x=int(k*W/8);img[:,x+6:x+22]=WHITE;img[:,x+6:x+9]=(200,198,190)
        cv2.circle(img,(x+14,H//2),11,WHITE,-1)
    img[:22]=WHITE;img[18:22]=(196,194,186);img[H-26:]=WHITE;img[H-26:H-22]=(210,208,200)
    save('hbal',img+grain(H,W,3),tu,tv)
hbal()
def hgreen():
    """painted green timber fascia and stand front: vertical boards, joint shadows, paint wear."""
    tu,tv=2.4,1.2;W,H=512,256;img=base(H,W,GREEN)+mottle(H,W,4,9)+grain(H,W,4)
    for k in range(0,W,32):img[:,k:k+3]=GREEND;img[:,k+3:k+5]=(84,150,86)
    for _ in range(40):
        x,y=rng.integers(0,W),rng.integers(0,H);img[y:y+rng.integers(2,6),x:x+rng.integers(6,30)]=(96,140,96)
    save('hgreen',img,tu,tv)
hgreen()
def column(name,col):
    """painted cast-iron column: shaded round shaft, fluting, a band every 1.5 m."""
    tu,tv=0.8,1.5;W,H=128,240;img=base(H,W,col)
    sh=np.cos(np.linspace(-1.4,1.4,W))[None,:,None];img=img*(0.62+0.42*sh)
    for k in range(0,W,16):img[:,k:k+2]*=0.85
    img[0:10]*=0.7;save(name,img+grain(H,W,3),tu,tv)
column('colL',(226,206,120));column('colM',(206,220,184))

def hfriz():
    """Members' frieze under the cornice: red-brown painted band, cream paired brackets every 1.2 m, moulding lines."""
    tu,tv=2.4,0.65;W,H=480,130;img=base(H,W,(118,58,44))+mottle(H,W,4,8)+grain(H,W,4)
    for k in range(0,W,240):
        for dx in(0,36):img[:,k+20+dx:k+34+dx]=(222,204,160);img[:,k+20+dx:k+23+dx]=(170,150,110)
    save('hfriz',img,tu,tv)   # no horizontal lines: the band height is set by the geometry
hfriz()

def seath(name):
    """heritage stand seating under the roof: maroon tip-up seats in rows of 0.4 m rise, seat gaps, row shadows,
    concrete risers, an aisle stair every 13.2 m with pale nosings. 13.2 m x 1.6 m (4 rows)."""
    tu,tv=13.2,1.6;W,H=2112,256;img=base(H,W,(74,68,66))+mottle(H,W,6,6)+grain(H,W,4);rp=H//4
    for r in range(4):
        y0=r*rp
        img[y0:y0+int(rp*0.18)]=(44,38,40)                                  # shadow under the row in front
        for k in range(26):
            x0=int(k*0.5*W/tu)+2;x1=int((k+1)*0.5*W/tu)-2;c=np.array((100,34,40))+rng.integers(-8,9)+rng.integers(-3,4,3)
            img[y0+int(rp*0.2):y0+int(rp*0.72),x0:x1]=c                     # seat back
            img[y0+int(rp*0.2):y0+int(rp*0.27),x0:x1]=c+26                   # top edge in the light
            img[y0+int(rp*0.72):y0+int(rp*0.84),x0+3:x1-3]=c*0.6               # folded seat in shade
        ax0,ax1=int(12.1*W/tu),W
        img[y0:y0+rp,ax0:ax1]=(128,122,114)+rng.integers(-6,7)                # aisle stair
        img[y0+int(rp*0.45):y0+int(rp*0.5),ax0:ax1]=(214,204,170)              # step nosings
        img[y0:y0+int(rp*0.04),ax0:ax1]=(214,204,170)
    save(name,img+grain(H,W,3),tu,tv)
seath('seathL');seath('seathM')
