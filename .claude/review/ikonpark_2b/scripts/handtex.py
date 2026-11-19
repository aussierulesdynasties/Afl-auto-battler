# Ikon Park hand-painted textures (row 202 2b texture pass). No photo pixels: every mark is drawn from module sizes in
# metres with texpaint.Canvas (copied from the Optus pass). Repeat sizes match build2.py UVs:
#   default 4 x 4 m; brick/timber/wood 2 m; glass 3 m; seats 4 m along the row x 4 rows of 0.8 m; roofs 4 m x 4 m.
# Usage: python handtex.py OUTDIR   -> OUTDIR/*.png and OUTDIR/stddev.txt (every texture must be >= 10)
import sys,os,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from texpaint import Canvas,save,gstd
out=sys.argv[1];os.makedirs(out,exist_ok=True)
def C(c):return np.array(c,float)/255
def put(name,cv):save(cv.img(),os.path.join(out,name+'.png'))

# ---- face brick, stretcher bond: 230 x 76 mm bricks, 10 mm joints; 2 m repeat
def brick(name,c,mortar,seed):
    cv=Canvas(2,2,C(mortar),seed);n=cv.n;pu=cv.pu;bw,bh=0.24,0.086
    rows=int(round(2/bh));bh=2/rows
    for r in range(rows):
        off=0 if r%2==0 else bw/2;y0=int(r*bh*pu)+1;y1=int((r+1)*bh*pu)-1;x=-off
        while x<2:
            col=C(c)*(1+cv.R.normal(0,0.07))*(1+cv.R.normal(0,0.03,3))
            for xa in (x,x+2,x-2):
                x0,x1=int(max(0,(xa)*pu+1)),int(min(n,(xa+bw)*pu-1))
                if x1>x0:cv.a[y0:y1,x0:x1]=col
            x+=bw
    cv.mottle(0.06,(1.0,0.3,0.05));cv.grain(0.03);cv.grime_bottom(0.5,0.12);cv.speckle(6,(0.01,0.03),0.25)
    put(name,cv)
brick('brick',(184,104,62),(190,180,164),1);brick('brickdark',(150,70,46),(184,174,160),2)

# ---- empty plastic seats on concrete treads: 4 m x 4 rows (0.8 m). Row: tread, seat pan, seat back, riser shadow.
def seats(name,seat,seed,tread=(176,174,168)):
    cv=Canvas(4,3.2,C(tread),seed);n=cv.n;pu,pv=cv.pu,cv.pv;S=C(seat)
    cv.mottle(0.05,(1.0,0.3,0.05))
    for r in range(4):
        y=r*0.8
        def band(a,b,col):cv.a[int((y+a)*pv):int((y+b)*pv)]=col
        band(0.66,0.80,C((112,110,106)))                              # riser face in shadow
        for s in range(8):                                            # 0.5 m seat pitch, each seat its own tone
            x0,x1=int((s*0.5+0.04)*pu),int((s*0.5+0.46)*pu);k=1+cv.R.normal(0,0.04)
            cv.a[int((y+0.10)*pv):int((y+0.30)*pv),x0:x1]=S*0.80*k   # seat back
            cv.a[int((y+0.30)*pv):int((y+0.50)*pv),x0:x1]=S*k        # seat pan (empty)
            cv.a[int((y+0.50)*pv):int((y+0.54)*pv),x0:x1]=S*0.55     # lip shadow
            cv.a[int((y+0.10)*pv):int((y+0.12)*pv),x0:x1]=S*1.25     # top rim catches light
        band(0.54,0.58,C((92,90,86)))                                 # shadow cast by the seats on the tread
    cv.a[:, :int(0.06*pu)]=C((150,148,142))                           # handrail post line at the repeat edge
    cv.grain(0.03);cv.speckle(3,(0.01,0.04),0.2);cv.streaks([0.66,1.46,2.26,3.06],0.6,(0.05,0.12),(0.02,0.08),0.15)
    put(name,cv)
seats('seats',(34,62,120),3);seats('seatslegends',(40,70,132),4)

# ---- concrete terrace steps: 4 m x 4 steps of 0.8 m, with crush rail line every 4 m
cv=Canvas(4,3.2,C((168,166,160)),5);pv,pu=cv.pv,cv.pu
cv.mottle(0.08)
for r in range(4):
    y=r*0.8;cv.hline(y+0.66,0.03,C((200,198,190)),0.9);cv.a[int((y+0.68)*pv):int((y+0.8)*pv)]*=0.72
cv.vline(0.05,0.06,C((110,112,112)));cv.streaks([0.68,1.48,2.28,3.08],1.0,(0.05,0.15),(0.02,0.1),0.25);cv.speckle(8,(0.01,0.05),0.25)
cv.grain(0.03);put('terrace',cv)

# ---- corrugated roof sheet: 4 x 4 m, ribs every 0.2 m (shading across the rib), sheet laps every 1 m along the slope,
#      sheet ends staggered, rust/grime toward the low (front) edge = v 0.
def roof(name,c,seed,rib=0.2):
    cv=Canvas(4,4,C(c),seed);n=cv.n;x=np.arange(n)/cv.pu;ph=(x%rib)/rib
    cv.mul((0.88+0.12*np.cos(ph*2*np.pi))[None,:]*np.ones((n,1)))
    cv.panels(0.76,1.0,joint=0.012,dark=0.82,tone=0.04,stagger=0.5,lip=0.4,bevel=True)
    cv.mottle(0.05,(2.0,0.5,0.1));cv.streaks([0.0,1.0,2.0,3.0],0.8,(0.3,1.5),(0.02,0.06),0.12)
    cv.grime_bottom(1.2,0.10);cv.speckle(2,(0.01,0.03),0.2);cv.grain(0.02)
    put(name,cv)
roof('roof',(232,234,230),6);roof('greyroof',(150,156,158),7);roof('sawtooth',(196,200,200),8);roof('roofgrey',(166,175,188),9)

# ---- off-form concrete: 4 m, formwork panels 1.2 x 2.4 m, tie holes, rain streaks, blotching
cv=Canvas(4,4,C((206,204,196)),10)
cv.panels(1.2,2.4,joint=0.01,dark=0.8,tone=0.05,stagger=0.0)
y,x=np.mgrid[0:cv.n,0:cv.n]
for u in np.arange(0.3,4,0.6):
    for v in np.arange(0.3,4,0.6):
        cv.a[int(v*cv.pv)-3:int(v*cv.pv)+3,int(u*cv.pu)-3:int(u*cv.pu)+3]*=0.7
cv.mottle(0.07);cv.streaks([0.0,2.4],1.5,(0.4,2.2),(0.03,0.2),0.22);cv.grime_bottom(0.8,0.15);cv.speckle(5,(0.01,0.04),0.25)
cv.grain(0.025);put('concrete',cv)

# ---- painted steel: light grey, seams every 1 m, wear toward the bottom
def steel(name,c,seed):
    cv=Canvas(4,4,C(c),seed);cv.panels(1.0,4.0,joint=0.008,dark=0.75,tone=0.03,bevel=False)
    cv.mottle(0.05);cv.streaks([0.0],2.0,(0.5,3.0),(0.02,0.1),0.18);cv.grime_bottom(1.0,0.14);cv.speckle(4,(0.005,0.02),0.3)
    cv.grain(0.02);put(name,cv)
steel('steel',(206,210,212),11);steel('white',(236,238,234),13)
# dark steel: same sheet, but seams and rust edges drawn lighter so the dark paint still reads as metal
cv=Canvas(4,4,C((78,84,90)),12);cv.panels(1.0,4.0,joint=0.02,dark=0.55,tone=0.08,bevel=True);cv.mottle(0.14,(1.0,0.3,0.05))
for u in np.arange(0.5,4,1.0):cv.vline(u,0.03,C((128,134,140)),0.8)
cv.streaks([0.0],2.0,(0.5,3.0),(0.02,0.1),0.3);cv.speckle(10,(0.01,0.03),0.4,light=True);cv.grain(0.04);put('steeldark',cv)

# ---- roof underside: purlins every 1.2 m in shadow, sheet ribs faint
cv=Canvas(4,4,C((92,96,98)),14);x=np.arange(cv.n)/cv.pu;cv.mul((0.9+0.1*np.cos((x%0.2)/0.2*2*np.pi))[None,:]*np.ones((cv.n,1)))
for v in np.arange(0,4,1.2):cv.hline(v,0.10,C((44,46,48)));cv.hline(v+0.10,0.03,C((140,144,146)))
cv.mottle(0.12);cv.grain(0.03);put('under',cv)

# ---- glass bays: 3 x 3 m, two lights wide, transom at 0.7, brick spandrel band at the bottom
def glass(name,frame,seed,tint=(46,64,80)):
    cv=Canvas(3,3,C(frame),seed);n=cv.n;m=int(n*0.04)
    for (x0,x1) in ((m,n//2-m//2),(n//2+m//2,n-m)):
        for (y0,y1) in ((m,int(n*0.7)-m//2),(int(n*0.7)+m//2,n-int(n*0.18))):
            g=np.linspace(1.18,0.8,y1-y0)[:,None,None];cv.a[y0:y1,x0:x1]=C(tint)*g
            cv.a[y0:y0+int((y1-y0)*0.35),x0:x0+int((x1-x0)*0.3)]+=0.06
    cv.a[n-int(n*0.18):]=C((176,98,60));cv.hline(3*0.82,0.03,C((210,206,198)))
    cv.mottle(0.05);cv.streaks([0.0,0.12*3],1.0,(0.2,1.0),(0.01,0.05),0.15);cv.grain(0.02);put(name,cv)
glass('glass',(232,232,226),15);glass('glassdark',(70,72,74),16)

# ---- timber boards: 2 m, vertical boards 0.15 m, each its own tone, grain along v, weathering at the bottom
def timber(name,seed,base=(176,104,56),joint=(110,62,34)):
    cv=Canvas(2,2,C(base),seed);n=cv.n;w=0.15
    for i in range(int(2/w)+1):
        x0=int(i*w*cv.pu);x1=min(n,int((i+1)*w*cv.pu));cv.a[:,x0:x1]*=1+cv.R.normal(0,0.07)
        cv.a[:,x0:x0+4]=C(joint)
    cv.mul(1+0.08*cv.noise(0.01,0.4));cv.grime_bottom(0.6,0.15);cv.speckle(5,(0.005,0.02),0.25);cv.grain(0.03)
    put(name,cv)
timber('timber',17)
timber('wood',18,(132,110,88),(84,68,54))   # weathered grey-brown paling, as the west fence in the 1994 photo

# ---- small flat colours (score board panels, trims): still painted, not flat
for name,c,seed in (('yellow',(230,190,40),19),('red',(175,45,50),20),('orange',(200,110,45),21),
                   ('pool',(70,170,205),24)):
    cv=Canvas(4,4,C(c),seed);cv.panels(1.2,1.2,joint=0.02,dark=0.55,tone=0.08,bevel=True);cv.mottle(0.14)
    cv.streaks([0.0],1.0,(0.3,1.5),(0.02,0.1),0.3);cv.grime_bottom(0.6,0.18);cv.speckle(8,(0.01,0.03),0.35,light=True);cv.grain(0.04);put(name,cv)
# turf/park/asphalt are not on the model (stadium only), kept as painted fills for any stray reference
for name,c,seed in (('grass',(58,126,60),25),('park',(80,128,70),26),('asphalt',(122,126,128),27)):
    cv=Canvas(4,4,C(c),seed);cv.mottle(0.12);cv.grain(0.08);put(name,cv)
with open(os.path.join(out,'stddev.txt'),'w',encoding='utf-8',newline='') as f:
    for fn in sorted(os.listdir(out)):
        if fn.endswith('.png'):
            s=gstd(os.path.join(out,fn));f.write(f'{fn[:-4]} {s:.1f}{"  LOW" if s<10 else ""}\n')
print(open(os.path.join(out,'stddev.txt')).read())
