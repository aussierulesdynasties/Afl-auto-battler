# Texture pass (row 202 2b): repaint every big surface by hand so it reads as a real material up close - panel joints,
# per-panel tone, rain streaks, blotching, ribs, laps, grime, seams and wear. Colours keep the earlier photo-read means.
# No photo pixels. Exec'd by texgen.py after hertex.py; overrides the flat versions.
def _streaks(H,W,n,amp,lmin=0.2,lmax=0.9,wmin=2,wmax=10):
    """rain streaks hanging down from the top of a panel row: darker vertical runs fading downwards"""
    out=np.zeros((H,W,1))
    for _ in range(n):
        x=int(rng.integers(0,W));w=int(rng.integers(wmin,wmax+1));y0=int(rng.integers(0,H));L=int(H*rng.uniform(lmin,lmax))
        a=amp*rng.uniform(0.4,1.0);f=np.linspace(1,0,L)[:,None,None]**1.5
        ys=(np.arange(L)+y0)%H;out[ys,x:x+w]-=a*f
    return out
def _blotch(H,W,cells,amp):return mottle(H,W,cells,amp)+mottle(H,W,cells*3,amp*0.5)
def _panels(img,tu,tv,pw,ph,joint,var,jw=3,stag=0.0):
    H,W=img.shape[:2]
    for j in range(int(round(tv/ph))):
        y0=int(j*ph/tv*H);y1=int((j+1)*ph/tv*H);off=(stag*pw if j%2 else 0)
        for i in range(-1,int(round(tu/pw))+1):
            x0=max(0,M(i*pw+off,tu,W));x1=min(W,M((i+1)*pw+off,tu,W))
            if x1>x0:img[y0:y1,x0:x1]+=rng.uniform(-var,var)
            if 0<=x0<W:img[y0:y1,x0:x0+jw]=joint
        img[y0:y0+jw]=joint
        img[min(H-1,y0+jw):min(H,y0+jw+2)]+=10                     # lit lip under each horizontal joint
    return img
def _wear(H,W,n,amp,r0=3,r1=14):
    out=np.zeros((H,W,1))
    for _ in range(n):cv2.circle(out,(int(rng.integers(0,W)),int(rng.integers(0,H))),int(rng.integers(r0,r1)),float(amp*rng.uniform(-1,1)),-1)
    return cv2.GaussianBlur(out,(0,0),1.2)[...,None]

def concrete(name,col,tu,tv,pw,ph,joint,N=1024,var=7,streak=40,ties=True):
    W=N;H=int(N*tv/tu);img=base(H,W,col)+_blotch(H,W,5,9)+grain(H,W,3)
    img=_panels(img,tu,tv,pw,ph,joint,var)
    img+=_streaks(H,W,streak,22)
    if ties:                                                         # formwork tie holes on a 0.6 m grid
        for x in np.arange(0.3,tu,0.6):
            for y in np.arange(0.3,tv,0.6):cv2.circle(img,(M(x,tu,W),int(y/tv*H)),2,tuple(float(c)*0.6 for c in col),-1)
    save(name,img,tu,tv)

def metal(name,col,tu,tv,pw,ph,joint,N=1024,var=6,ribs=0,streak=30,wear=40):
    W=N;H=int(N*tv/tu);img=base(H,W,col)+_blotch(H,W,4,11)+grain(H,W,3)
    if ribs:
        x=np.arange(W)/W*tu/ribs*2*np.pi;img+=(np.sin(x)*14)[None,:,None]
    img=_panels(img,tu,tv,pw,ph,joint,var)
    img+=_streaks(H,W,streak,18)+_wear(H,W,wear,14)
    save(name,img,tu,tv)

def deck(name,col,tu,tv,rib,lap,N=1024,ramp=16,grime=24,blot=8):
    """corrugated or standing-seam deck: rib profile across, sheet end laps down the fall, grime streaks from the laps"""
    W=N;H=int(N*tv/tu);img=base(H,W,col)+_blotch(H,W,4,blot)+grain(H,W,2)
    x=np.arange(W)/W*tu/rib;ph=x%1.0
    prof=np.where(ph<0.18,1.0,np.where(ph<0.25,-1.6,0.0))*ramp+np.sin(ph*2*np.pi)*ramp*0.35   # lit rib face, shadowed back
    img+=prof[None,:,None]
    for k in range(int(round(tv/lap))):
        y=int(k*lap/tv*H);img[y:y+4]-=30;img[y+4:y+6]+=12
    img+=_streaks(H,W,int(tu*3),grime,0.3,1.0,3,int(W/tu*rib*0.6))
    save(name,img,tu,tv)

def boards(name,col,tu,tv,bl,N=512,var=12):
    """painted timber trim: boards with butt joints, a shadow lip on the bottom edge, flaking paint and grime"""
    W=N;H=max(32,int(N*tv/tu));img=base(H,W,col)+_blotch(H,W,3,6)+grain(H,W,3)
    for i in range(int(round(tu/bl))):
        x0=M(i*bl,tu,W);x1=M((i+1)*bl,tu,W);img[:,x0:x1]+=rng.uniform(-var,var);img[:,x0:x0+2]=np.array(col)*0.62
    img+=_wear(H,W,90,34,2,7)+_streaks(H,W,30,14,0.2,0.6,1,4)
    save(name,img,tu,tv)

def led(name,tu,tv,W,H,col=(30,32,36),cell=0.32):
    """switched-off LED panel: square modules with dark seams and a faint pixel lattice, slight sheen gradient"""
    img=base(H,W,col)+grain(H,W,2);yy,xx=np.mgrid[0:H,0:W]
    img+=((yy/H)*26)[...,None]
    px=max(2,int(cell/tu*W/8))
    img[(xx%px==0)|(yy%px==0)]+=10
    for i in range(int(round(tu/cell))+1):x=M(i*cell,tu,W);img[:,x:x+2]=(10,10,12)
    for j in range(int(round(tv/cell))+1):y=int(j*cell/tv*H);img[y:y+2]=(10,10,12)
    img+=_wear(H,W,30,16,4,10)
    save(name,img,tu,tv)

# --- concrete and render
concrete('conc',(196,192,184),4.8,4.8,2.4,1.2,(150,146,140))
concrete('wall',(212,208,198),8.0,6.0,4.0,3.0,(160,156,148),streak=60)
concrete('slab',(228,226,221),6.0,1.0,6.0,1.0,(176,174,170),N=1024,streak=30,ties=False)
concrete('tower',(168,160,146),2.0,4.0,0.5,1.2,(140,133,120),N=512,var=9,streak=36,ties=False)
concrete('dark',(48,50,54),6.0,6.0,3.0,3.0,(26,28,30),var=9,streak=40)
concrete('headback',(112,114,118),4.0,4.0,1.0,1.0,(84,86,90),N=512,var=8)
# --- sandstone ashlar base (stone): coursed blocks, each its own tone, darker weathering at the foot
def stone():
    tu,tv=4.8,6.0;W=1024;H=int(W*tv/tu);img=base(H,W,(214,210,200))+_blotch(H,W,5,8)+grain(H,W,4)
    img=_panels(img,tu,tv,1.2,0.6,(176,170,160),9,jw=4,stag=0.5)
    img+=(np.linspace(0,-24,H)**1)[:,None,None]*0+np.linspace(0,1,H)[:,None,None]**3*-22
    img+=_streaks(H,W,40,16)
    save('stone',img,tu,tv)
stone()
# --- metal cladding
metal('facade',(226,227,225),7.2,7.2,1.2,3.6,(186,188,188))
metal('facade2',(152,157,162),6.0,6.0,3.0,3.0,(116,120,124),ribs=0.3)
metal('cladl',(208,211,212),6.0,2.0,1.5,1.0,(160,162,164),var=9,streak=50)
metal('spand',(158,164,168),6.0,0.9,1.5,0.9,(122,126,130),N=1024,streak=20)
metal('steel',(204,206,209),2.0,2.0,1.0,2.0,(150,152,156),N=512,var=9,wear=80)
metal('rail',(150,152,154),2.0,2.0,1.0,2.0,(112,114,116),N=256,var=9,wear=60,streak=20)
# --- roofs
deck('roof',(232,234,236),12.0,12.0,0.5,6.0,N=1536,ramp=22,grime=10,blot=3)
deck('hroof',(60,124,58),8.0,8.0,0.2,2.4,N=1024,ramp=18,grime=20)
# --- soffit under the raked stands: dark concrete steps, a pale step line each 0.9 m row, water stains, a conduit run
def soffit():
    tu,tv=4.0,3.6;W,H=512,464;img=base(H,W,(52,58,64))+_blotch(H,W,4,8)+grain(H,W,3)
    for k in range(4):y=int(k*0.9/tv*H);img[y:y+6]=(92,98,104);img[y+6:y+16]=(40,44,48)
    img+=_streaks(H,W,24,14)+_wear(H,W,20,12,6,18)
    x=M(1.3,tu,W);img[:,x:x+5]=(110,112,114);img[:,x+5:x+7]=(30,32,34)
    save('soffit',img,tu,tv)
soffit()
# --- boundary fence: white boards, joint and post every 3 m, scuffs low down, dark cap shadow
def fence():
    tu,tv=12.0,1.2;W,H=2048,204;img=base(H,W,(238,238,234))+_blotch(H,W,4,5)+grain(H,W,2)
    for k in range(4):x=M(k*3.0,tu,W);img[:,x:x+4]=(150,150,148);img[:,x+4:x+6]=(255,255,252)
    img[:10]=(176,176,172);img[10:14]=(206,206,202)
    sc=_wear(H,W,90,40,2,7);sc[:int(H*0.55)]=0;img+=sc
    img+=_streaks(H,W,40,22,0.2,0.7,1,4)
    save('fence',img,tu,tv)
fence()
led('ribbon',48.0,1.0,4096,96)
led('sbad',1.0,1.0,256,512,cell=0.25)
boards('trim',(232,214,140),4.0,4.0,1.8)
boards('btrim',(238,236,228),4.0,4.0,1.8)
def skyglass():
    tu=tv=1.2;N=256;yy,xx=np.mgrid[0:N,0:N];img=base(N,N,(84,128,128))+((xx+yy)/(2*N)*44)[...,None]+grain(N,N,2)
    img[(((xx+yy*0.6)//24)%4==0)]+=12
    img[:,:10]=(52,84,82);img[:10]=(52,84,82);img[:,10:13]=(140,176,172)
    save('skyglass',img,tu,tv)
skyglass()
