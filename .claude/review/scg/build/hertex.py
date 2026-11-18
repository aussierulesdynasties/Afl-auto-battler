# Heritage stands, hand-painted wall elevations (exec'd from texgen.py). Colours and layout read off the street photos
# (refs3/020-025: red brick, cream sandstone string courses, white sash windows, green verandah awnings) and the
# field photo (refs5/SCG-ladies-members-stands.jpg: two-tier open stands, maroon seats, slim columns, green verandah,
# white balustrade, yellow eave trim). No photo pixels: every element is drawn.
exec(open('blds.py').read())
PXM=140   # pixels per metre
BRICK=(160,78,58);MORTAR=(196,186,172);SAND=(222,204,160);SANDD=(190,170,128);WHITE=(238,236,228)
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
def hstand(H,colc):
    """field elevation: the two-tier open stand. Lower tier under the green verandah, white balustrade, upper tier of
    maroon seats rising to a dark roof space, slim columns every 4.7 m, yellow eave trim."""
    tu=4.7;img=np.zeros((int(H*PXM),int(tu*PXM),3));img[:]=(30,26,28)
    def seats(z0,z1):
        z=z0
        while z<z1-0.3:
            _band(img,H,z,z+0.42,(104,40,46));_band(img,H,z+0.36,z+0.42,(138,62,66));_band(img,H,z+0.42,z+0.5,(52,40,42));z+=0.5
    _band(img,H,0,0.9,(200,190,160));_band(img,H,0.85,0.9,WHITE)                      # front wall of the lower tier
    seats(0.9,4.2)
    _band(img,H,4.25,4.95,GREEN);_band(img,H,4.95,5.05,YEL);_band(img,H,4.2,4.3,YEL)   # lower verandah fascia
    _band(img,H,5.05,6.15,(40,34,36))
    _band(img,H,6.05,6.15,WHITE);_band(img,H,5.1,5.2,WHITE)                           # balustrade rails
    for k in range(0,int(tu*PXM),int(0.16*PXM)):img[_row(H,6.05):_row(H,5.2),k:k+int(0.06*PXM)]=WHITE   # balusters
    seats(6.15,H-2.4)
    _band(img,H,H-0.45,H,YEL);_band(img,H,H-0.55,H-0.45,GREEND)                       # eave trim
    ax0,ax1=int(2.6*PXM),int(3.5*PXM)                                                  # aisle stairs, both tiers
    for z0_,z1_ in ((0.9,4.2),(6.15,H-2.4)):
        img[_row(H,z1_):_row(H,z0_),ax0:ax1]=(150,146,138)
        z=z0_
        while z<z1_-0.25:img[_row(H,z+0.27):_row(H,z+0.25),ax0:ax1]=(214,186,70);z+=0.25
    x=int(0.24*PXM);img[_row(H,H-0.45):_row(H,0.9),0:x]=colc;img[_row(H,H-0.45):_row(H,0.9),0:4]=np.array(colc)*0.7   # column
    img[_row(H,H-0.45):_row(H,H-1.1),x:int(0.8*PXM)]=np.array(colc)*0.9                 # bracket under the eave
    return img+grain(img.shape[0],img.shape[1],2.5),tu
def hped():
    """Members' pediment under the clock tower: cream tympanum, arched fanlight, white raking trim (field photo)."""
    W,Hh=1024,512;img=base(Hh,W,SAND)+grain(Hh,W,2);yy,xx=np.mgrid[0:Hh,0:W]
    cv2.ellipse(img,(W//2,Hh-30),(250,200),0,180,360,(176,140,64),-1)               # gilt fanlight
    for a in range(180,361,15):
        t=math.radians(a);cv2.line(img,(W//2,Hh-30),(int(W/2+250*math.cos(t)),int(Hh-30+200*math.sin(t))),(120,96,44),4)
    cv2.ellipse(img,(W//2,Hh-30),(250,200),0,180,360,WHITE,14);cv2.ellipse(img,(W//2,Hh-30),(70,56),0,180,360,(120,96,44),-1)
    img[Hh-34:Hh]=WHITE
    save('hped',img,1.0,1.0)
def hgab():
    """small field gables: cream face, white barge trim, louvred vent."""
    W,Hh=512,256;img=base(Hh,W,SAND)+grain(Hh,W,2)
    cv2.rectangle(img,(W//2-40,Hh-150),(W//2+40,Hh-60),(176,150,104),-1)
    for k in range(Hh-146,Hh-62,12):img[k:k+4,W//2-36:W//2+36]=(120,100,70)
    img[Hh-20:Hh]=WHITE
    save('hgab',img,1.0,1.0)
import math
for z in sorted({b[6] for b in BLD}):
    im,tu=hwall(z);save('hw%d'%round(z*10),im,tu,z)
    im,tu=hstand(z,(226,206,120) if True else 0);save('hsL%d'%round(z*10),im,tu,z)
    im,tu=hstand(z,(150,196,120));save('hsM%d'%round(z*10),im,tu,z)
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
