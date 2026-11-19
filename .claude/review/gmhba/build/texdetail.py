# Hand-painted detail for every big surface (director 2026-11-19: "a lot of solid colour blocks with zero texture",
# texture plan approved "Yes, all grounds"). Procedural only: no photo pixels. Runs after mktex.py and overwrites the
# flat textures. Sizes in metres; a tile is 8 m (128 px/m) unless noted (build.py TILEM / tilew).
#  concrete : precast panel joints 2.0 x 1.6 m, rain streaks under each horizontal joint, blotching between panels
#  cladding : white folded panels 0.4 m wide (p11: ~29 panels across the 12 m Gate 1 glass box; p13 close-up),
#             staggered horizontal joints, grime toward each panel's bottom edge
#  roofs    : ribbed sheeting, ribs 0.25 m (p13 underside), sheet end laps, dirt along the ribs
#  seats    : 12 m tile, seats 0.5 m, rows 0.75 m (16 per tile so the p12 diagonal repeats cleanly) with each row's shadow, gaps between seats, a 1.2 m aisle per tile,
#             blue and white from p12
#  steel    : painted panels with seams, wear and grime toward the bottom edge
import numpy as np
from PIL import Image,ImageDraw
N=1024;PX=N/8.0
R=np.random.default_rng(11)
def save(a,n):Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(f'tex/{n}.png')
def tnoise(n,sig,seed):
    # tileable smooth noise, std 1: white noise low-passed in the Fourier domain (periodic by construction)
    r=np.random.default_rng(seed).normal(size=(n,n));f=np.fft.fftfreq(n)
    G=np.exp(-2*(np.pi*sig)**2*(f[:,None]**2+f[None,:]**2));o=np.real(np.fft.ifft2(np.fft.fft2(r)*G));return o/o.std()
def fbm(n,seed,sigs=(64,24,8)):return sum(tnoise(n,s,seed+i)/(i+1) for i,s in enumerate(sigs))
def streaks(n,rows_y,seed,amp=22,length=(0.25,1.1),count=60):
    # dark rain streaks hanging under each ledge/joint row, fading downward, wrapping across the tile
    rg=np.random.default_rng(seed);s=np.zeros((n,n))
    for y0 in rows_y:
        for _ in range(count):
            x=rg.integers(0,n);w=rg.integers(2,14);L=int(rg.uniform(*length)*PX);k=rg.uniform(0.35,1.0)
            yy=np.arange(L);fall=k*np.exp(-yy/(L*0.45))
            for dx in range(-w,w+1):
                c=(x+dx)%n;s[(y0+yy)%n,c]+=fall*np.exp(-(dx/(w*0.6+0.5))**2)
    return -amp*np.clip(s,0,1.6)
def finish(a,grain=2.0):return a+R.normal(0,grain,a.shape[:2])[...,None]
def col(c):return np.array(c,float)[None,None,:]

# ---- concrete: precast panels 2.0 x 1.6 m (8 m tile: 4 x 5)
def concrete(n,base,pw=2.0,ph=1.6,seed=1,streak=22,blot=7):
    a=np.ones((N,N,3))*col(base);pwp,php=int(pw*PX),int(ph*PX)
    rg=np.random.default_rng(seed)
    for j in range(0,N,php):
        for i in range(0,N,pwp):a[j:j+php,i:i+pwp]+=rg.normal(0,5)             # each panel cast a touch different
    a+=(fbm(N,seed)*blot)[...,None]                                              # blotching
    a+=(tnoise(N,2.5,seed+9)*2.5)[...,None]                                      # fine aggregate
    a+=streaks(N,list(range(0,N,php)),seed+3,streak)[...,None]                   # rain streaks under each joint
    for i in range(0,N,pwp):a[:,i:i+3]*=0.62;a[:,(i+3)%N]*=1.04                 # vertical joint, lit lip
    for j in range(0,N,php):a[j:j+3,:]*=0.6;a[(j+3)%N,:]*=1.05                  # horizontal joint (ledge)
    return finish(a)
save(concrete('wall',(196,198,192)),'wall')
save(concrete('cream',(222,219,212),2.0,1.6,5,16,6),'cream')                       # rooftop precast parapet
rc=concrete('recess',(118,130,150),4.0,8.0,7,18,4)
for i in range(0,N,int(4.0*PX)):rc[:,i:i+int(0.45*PX)]*=0.78;rc[:,i+int(0.45*PX):i+int(0.5*PX)]*=0.9   # rake beams every 4 m, 0.45 m deep
save(rc,'recess')                     # rake underside: beams every 4 m

# ---- white folded cladding (fascia): 0.4 m panels, two facets each, staggered joints, grime at each panel foot
def cladding(n,base,pw=0.4,seed=2,dark=False,grime=26):
    a=np.ones((N,N,3))*col(base);pwp=int(round(pw*PX));ncol=N//pwp
    rg=np.random.default_rng(seed);x=np.arange(N)
    facet=np.where((x%pwp)<pwp*0.5,6.0,-6.0);a+=facet[None,:,None]              # folded panel: lit and shaded facet
    a+=(fbm(N,seed,(80,30))*3)[...,None]
    for c in range(ncol):
        x0=c*pwp;off=int(rg.uniform(0,1.6)*PX);hgt=int(rg.choice([1.6,2.0])*PX)
        for y in range(off-hgt*4,N,hgt):
            y1=y+hgt
            for yy in range(max(y,y1-int(0.5*PX)),y1):                          # grime building toward the foot
                if 0<=yy<N:a[yy,x0:x0+pwp]-=grime*((yy-(y1-0.5*PX))/(0.5*PX))**2
            if 0<=y1<N:a[y1:y1+2,x0:x0+pwp]*=0.72                                 # horizontal joint
        a[:,x0:x0+2]*=0.7                                                         # vertical seam
    a+=streaks(N,[0],seed+4,10,(1.0,3.0),40)[...,None]
    return finish(a,1.5)
save(cladding('fascia',(236,238,240)),'fascia')
save(cladding('teal',(40,108,130),1.0,6,grime=34),'teal')

# ---- painted steel: panel seams, wear, grime toward the bottom edge
def steel(n,base,pw=2.0,ph=2.0,seed=3,grime=24,wear=6):
    a=np.ones((N,N,3))*col(base);pwp,php=int(pw*PX),int(ph*PX)
    a+=(fbm(N,seed,(48,12))*wear)[...,None]
    yy=np.arange(N)%php;a-=(grime*(yy/php)**3)[:,None,None]                    # each panel dirtier toward its foot
    a+=streaks(N,list(range(0,N,php)),seed+5,14,(0.2,0.8),30)[...,None]
    for j in range(0,N,php):a[j:j+3,:]*=0.66;a[(j+3)%N,:]*=1.04
    for i in range(0,N,pwp):a[:,i:i+2]*=0.72
    rg=np.random.default_rng(seed)
    for _ in range(140):                                                          # chips and scuffs in the paint
        x,y=rg.integers(0,N,2);r=rg.integers(1,4);a[max(0,y-r):y+r,max(0,x-r):x+r]-=rg.uniform(10,30)
    return finish(a,1.5)
save(steel('tower',(240,242,244),8.0,2.0,3,20,4),'tower')                          # light tower: flange rings every 2 m
save(steel('navy',(33,64,102),2.0,2.0,8,26,9),'navy')
save(steel('soffit',(66,68,84),1.2,2.4,9,22,8),'soffit')

# ---- roof sheeting: ribs 0.25 m, end laps, dirt along the ribs
def sheeting(n,base,rib=0.25,seed=4,dirt=14,lap=4.0,ra=1.0):
    a=np.ones((N,N,3))*col(base);rp=rib*PX;x=np.arange(N);ph=(x%rp)/rp
    prof=ra*np.where(ph<0.10,20.0,np.where(ph<0.17,-24.0,0.0))                      # rib crest lit, far flank shaded
    a+=prof[None,:,None]
    d=np.exp(-((ph-0.21)/0.07)**2)                                                # dirt lodged beside each rib
    a-=(dirt*d[None,:]*(0.6+0.4*np.clip(fbm(N,seed,(40,10)),-1,2)))[...,None]
    a+=(fbm(N,seed+1,(120,40))*5)[...,None]
    for y0 in np.arange(0,N,lap*PX).astype(int):                                 # sheet end lap: a step and a shadow
        a[y0:y0+3,:]*=0.7;a[y0+3:y0+int(0.15*PX),:]*=1.03
    return finish(a,1.5)
save(sheeting('roof',(204,207,211),dirt=22),'roof')
save(sheeting('roofdark',(78,82,88),seed=5,dirt=14),'roofdark')
save(sheeting('roofgrey',(182,191,199),seed=6,dirt=20),'roofgrey')
save(sheeting('under',(170,172,176),seed=7,dirt=12,ra=1.9),'under')   # p13: underside ribs cast strong shadows

# ---- flat roofs and decks: membrane sheets with seams and ponding stains; paving with varied pavers
def deck(n,base,seed,blot=7):
    a=np.ones((N,N,3))*col(base);a+=(fbm(N,seed,(90,30,6))*blot)[...,None]
    st=np.clip(tnoise(N,40,seed+3),0.8,3)-0.8;a-=(st*14)[...,None]              # dried ponding stains
    for i in range(0,N,int(1.0*PX)):a[:,i:i+2]*=0.85                              # membrane laps every 1 m
    for j in range(0,N,int(4.0*PX)):a[j:j+2,:]*=0.85
    return finish(a,2)
save(deck('deck',(168,159,148),12),'deck');save(deck('deckg',(160,163,158),13,10),'deckg')
def pave(n):
    a=np.ones((N,N,3))*col((184,169,145));pw=int(N*0.6/8);ph=int(N*0.3/8);rg=np.random.default_rng(14)
    for j in range(0,N,ph):
        off=(j//ph%2)*pw//2
        for i in range(-pw,N,pw):
            x0=max(0,i+off);a[j:j+ph,x0:min(N,i+off+pw)]+=rg.normal(0,8)
        a[j:j+1,:]-=34
        for i in range(off,N,pw):a[j:j+ph,i:i+1]-=34
    a+=(fbm(N,15,(70,20))*6)[...,None];return finish(a,2)
save(pave('pave'),'pave')

# ---- glass curtain wall (annex): pane-to-pane tone, interior blinds and lights, frames every 1.6 m
def aglass(n):
    a=np.ones((N,N,3))*col((34,38,44));pw=int(1.6*PX);rg=np.random.default_rng(16);fh=N//2
    for i in range(0,N,pw):
        for j in range(0,N,fh):
            t=rg.uniform(-8,14);a[j:j+fh,i:i+pw]+=t
            if rg.random()<0.4:a[j:j+int(rg.uniform(0.2,0.45)*fh),i:i+pw]+=26        # blind half down
            if rg.random()<0.3:a[j+fh//3:j+fh//3+6,i+10:i+pw-10]+=60                 # ceiling light strip
    xx=np.arange(N)[None,:];yy=np.arange(N)[:,None]
    for k in range(4):
        x0=rg.integers(0,N);w=rg.integers(30,70);m=np.abs((xx-x0)-(yy*0.35))%N<w;a[m]+=14  # sky reflections
    for i in range(0,N,pw):a[:,i:i+8]=(58,62,68)
    for j in(0,fh):a[j:j+10,:]=(62,66,72)
    return finish(a,2)
save(aglass('aglass'),'aglass')

# ---- GMHBA wedge front: dark cladding panels 1.25 m with facets, seams and grime
WJ=__import__('json').load(open('wedge.json'));W=int(WJ['L']*20);H=int(16.5*20)
def wedgef():
    a=np.ones((H,W,3))*col((54,54,60));pp=25;x=np.arange(W)
    a+=np.where((x%pp)<pp/2,7.0,-7.0)[None,:,None]
    nz=tnoise(1024,30,17)[:H,:W]*7;a+=nz[...,None]
    for i in range(0,W,pp):a[:,i:i+2]*=0.7
    for z in(6.0,9.5,13.0):y=int((16.5-z)*20);a[y:y+2,:]*=0.7;a[y+2:y+14,:]-=np.linspace(10,0,12)[:,None,None]
    a+=R.normal(0,2,a.shape[:2])[...,None];return a
_wf=Image.fromarray(np.clip(wedgef(),0,255).astype(np.uint8)).convert('RGBA')
# GMHBA STADIUM letters on the wedge cladding (p1), in the sign quad measured on p1 (wedge.json)
import sys,math;sys.path.insert(0,'.');from signs import gmhba
sg=WJ['sign'];s0=min(q[0] for q in sg);s1=max(q[0] for q in sg);z1=max(q[1] for q in sg)
ang=math.degrees(math.atan2(sg[1][1]-sg[0][1],sg[1][0]-sg[0][0]))
lg=gmhba(int((s1-s0)*20),int((sg[0][1]-sg[3][1]+sg[1][1]-sg[2][1])/2*20)).rotate(ang,expand=True,resample=Image.BICUBIC)
_wf.alpha_composite(lg,(int(s0*20),int((16.5-z1)*20)));_wf.convert('RGB').save('tex/wedgef.png')

# ---- pocket grass: mowing bands, clover and worn patches
def turf(n):
    yy,xx=np.mgrid[0:N,0:N];bs=((xx+N//8)//(N//4))%2==0
    a=np.where(bs[...,None],col((58,72,21)),col((47,58,15)))
    a=a+(fbm(N,18,(60,16,3))*7)[...,None]*np.array([0.8,1.0,0.5])
    w=np.clip(tnoise(N,50,19)-1.3,0,2);a+=(w*22)[...,None]*np.array([1.2,0.9,0.9])  # worn, sandy patches
    return finish(a,3)
save(turf('turf'),'turf')

# ---- seats: 12 m tile, 24 seats x 15 rows, row shadow, gaps, one 1.2 m aisle of concrete steps per tile
def seats(n,dark,seed,pb=0.55):   # empty seats only: no crowd in any ground model (director 2026-11-19)
    rows=16;sw=0.5;rh=N/rows;aisle=1.2;cw=sw/12.0*N;ax=int((12.0-aisle)/12.0*N)
    BLUE=(20,88,150);WHITE=(226,228,230)                          # p12: blue (3,79,125) in shade
    im=Image.new('RGB',(N,N),(150,152,156));d=ImageDraw.Draw(im);rg=np.random.default_rng(seed)
    for r in range(rows):
        y=r*rh
        d.rectangle([0,y,N,y+rh*0.20],fill=(112,114,118))                        # riser face
        d.rectangle([0,y+rh*0.20,N,y+rh*0.25],fill=(178,180,183))                 # tread nosing
        d.rectangle([0,y+rh*0.80,N,y+rh],fill=(96,98,102))                         # the row's shadow on the tread
        c=0
        while (c+1)*cw<=ax:
            x=c*cw;colr=BLUE if ((c+r)//2)%2==0 else WHITE   # p12: pairs of one colour, shifted a seat each row
            # p12: seats sit tight side by side; the backs fill the row, the next row's backs hide the tread
            d.rounded_rectangle([x,y+rh*0.06,x+cw,y+rh*0.78],radius=5,fill=colr)
            sh=tuple(int(v*0.80) for v in colr);d.rectangle([x,y+rh*0.06,x+cw,y+rh*0.14],fill=sh)    # back's top lip
            d.line([x,y+rh*0.10,x,y+rh*0.78],fill=tuple(int(v*0.62) for v in colr),width=2)          # the join between seats
            sh=tuple(int(v*0.72) for v in colr);d.rectangle([x,y+rh*0.78,x+cw,y+rh*0.92],fill=sh)     # seat pan in the back's shade
            c+=1
        d.rectangle([ax,y,N,y+rh],fill=(168,170,172))                              # aisle step
        d.rectangle([ax,y,N,y+rh*0.08],fill=(206,186,60))                          # yellow step nosing
        d.rectangle([ax+4,y+rh*0.85,N-4,y+rh],fill=(140,142,145))
    a=np.asarray(im).astype(float);a=finish(a,2.5)
    if dark is True:a=a*0.55
    elif dark:a=a*(np.array(dark)/a.reshape(-1,3).mean(0))
    return a
save(seats('seats',False,21),'seats');save(seats('seats_dark',True,22),'seats_dark')
save(seats('crowd_shade',True,23),'crowd_shade')   # empty seats in deep roof shade (name kept for the build)
save(seats('seats_empty',False,24),'seats_empty')
