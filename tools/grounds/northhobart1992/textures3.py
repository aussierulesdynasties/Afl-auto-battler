# Hand-painted detail pass (run after textures.py and textures2.py). No photo pixels: every mark is drawn here.
# Each surface gets the detail its real material has: concrete panel joints, rain streaks, blotching; steel seams and
# wear toward the bottom; board joints and nail lines on painted timber; ribs, laps and grime on iron; patches and
# cracks on asphalt. Texture sizes (metres) are unchanged, so every mark is at real spacing.
# Image row 0 is the top of a wall (high v), so streaks run down from row 0 and wear builds toward the last row.
import numpy as np,json
from PIL import Image,ImageDraw,ImageStat
rng=np.random.default_rng(1992)
SIZES=json.load(open('tex/sizes.json'))
def load(n):return np.asarray(Image.open(f'tex/{n}.png').convert('RGB')).astype(float)
def save(n,a):Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(f'tex/{n}.png')
def noise(h,w,s,amp):
    # tileable: random field low-passed in the Fourier domain wraps at the edges, so repeats show no seam
    F=np.fft.fft2(rng.normal(0,1,(h,w)));k=np.sqrt(np.fft.fftfreq(h)[:,None]**2+np.fft.fftfreq(w)[None,:]**2)
    n=np.real(np.fft.ifft2(F*np.exp(-(k*s*2.5)**2)));return n/(n.std()+1e-9)*amp
def grain(a,amp):H,W=a.shape[:2];a+=(rng.normal(0,amp,(H,W))+noise(H,W,2,amp*0.6))[...,None];return a
def px(n,a):H,W=a.shape[:2];mu,mv=SIZES[n];return W/mu,H/mv
def blotch(a,amp,s=96):H,W=a.shape[:2];a*=(1+noise(H,W,s,amp/220.0)+noise(H,W,s//4,amp/300.0))[...,None];return a
def streaks(a,n,dark,maxlen=0.7,width=(2,6)):
    H,W=a.shape[:2]
    for _ in range(n):
        x=rng.integers(0,W);w=rng.integers(*width);L=int(H*rng.uniform(0.15,maxlen));y0=rng.integers(0,max(1,H//6))
        prof=np.linspace(1,0,L)**1.5*dark*rng.uniform(0.5,1)
        a[y0:y0+L,x:x+w]*=(1-prof[:min(L,H-y0)])[:,None,None]
    return a
def wear_bottom(a,depth,dark):H=a.shape[0];r=np.clip((np.arange(H)-(H*(1-depth)))/(H*depth),0,1)**1.5;a*=(1-dark*r)[:,None,None];return a
def joints(a,n,du=None,dv=None,dark=0.72,w=3,hi=1.06):
    H,W=a.shape[:2];pu,pv=px(n,a)
    if du:
        for k in np.arange(du,SIZES[n][0]-1e-6,du) if SIZES[n][0]>du else [SIZES[n][0]]:
            x=int(k*pu)%W;a[:,max(0,x-w//2):x+w-w//2]*=dark;a[:,x+w-w//2:x+w-w//2+1]*=hi
        a[:,:w//2+1]*=dark
    if dv:
        for k in np.arange(dv,SIZES[n][1]-1e-6,dv) if SIZES[n][1]>dv else [SIZES[n][1]]:
            y=int(k*pv)%H;a[max(0,y-w//2):y+w-w//2]*=dark;a[y+w-w//2:y+w-w//2+1]*=hi
        a[:w//2+1]*=dark
    return a
def dots(a,step_u,step_v,col_mul=0.6,r=2,off=(0.05,0.05)):
    H,W=a.shape[:2]
    for u in np.arange(off[0],1,step_u):
        for v in np.arange(off[1],1,step_v):
            x,y=int(u*W),int(v*H);a[max(0,y-r):y+r,max(0,x-r):x+r]*=col_mul
    return a
def cracks(a,n,dark=0.6):
    H,W=a.shape[:2];im=Image.new('L',(W,H),0);d=ImageDraw.Draw(im)
    for _ in range(n):
        x,y=rng.uniform(0,W),rng.uniform(0,H);pts=[(x,y)];t=rng.uniform(0,6.28)
        for _ in range(rng.integers(6,16)):t+=rng.normal(0,0.6);x+=12*np.cos(t);y+=12*np.sin(t);pts.append((x,y))
        d.line(pts,fill=255,width=2)
    m=np.asarray(im)/255.0;a*=(1-(1-dark)*m)[...,None];return a
def patches(a,n,shift,size=(60,220)):
    H,W=a.shape[:2]
    for _ in range(n):
        w,h=rng.integers(*size),rng.integers(*size);x,y=rng.integers(0,W-w),rng.integers(0,H-h);a[y:y+h,x:x+w]*=shift*rng.uniform(0.97,1.03)
        a[y:y+2,x:x+w]*=0.8;a[y+h-2:y+h,x:x+w]*=0.8;a[y:y+h,x:x+2]*=0.8;a[y:y+h,x+w-2:x+w]*=0.8
    return a
P={}
# concrete (stand risers, side walls, terrace sides): 2.0 m pour joints, 1.0 m lift lines, blotching, rain streaks, splash at the foot
a=load('concrete');a=grain(a,7);a=blotch(a,9);a=joints(a,'concrete',du=2.0,dv=1.0,dark=0.8,w=3);a=streaks(a,40,0.16);a=wear_bottom(a,0.18,0.12);a=cracks(a,6,0.75);P['concrete']=a
# cream render (Gorringe and SE plinth): blotching, hairline cracks, rain streaks under every ledge, splash grime at the foot
a=load('render_cream');a=grain(a,6);a=blotch(a,7);a=streaks(a,55,0.14,0.5);a=cracks(a,10,0.8);a=wear_bottom(a,0.15,0.14);P['render_cream']=a
# grey wall cladding (stand backs): profiled sheets 0.76 m cover with laps, horizontal rail screw lines every 1.2 m, streaks, grime
a=load('cladding_grey');a=grain(a,4);a=joints(a,'cladding_grey',du=0.76,dark=0.7,w=4,hi=1.1);a=dots(a,0.05,0.3,0.6,2,(0.025,0.15));a=blotch(a,8);a=streaks(a,60,0.2,0.8);a=wear_bottom(a,0.2,0.15);P['cladding_grey']=a
# dark steel (columns, trusses, roof undersides): plate seams 1.0 m, bolt groups, rust-brown runs, wear toward the bottom
a=load('steel_dark');a=grain(a,5);a=joints(a,'steel_dark',du=1.0,dv=2.0,dark=0.6,w=3,hi=1.35);a=dots(a,0.0625,0.125,0.55,3,(0.03,0.06));a=blotch(a,14);a=streaks(a,45,-0.35,0.6);a=wear_bottom(a,0.25,-0.25);P['steel_dark']=a
# light poles: galvanised blotching (spangle), section joints every 3 m, drip streaks
a=load('pole_grey');a=grain(a,6);a=blotch(a,10,48);a=joints(a,'pole_grey',dv=3.0,dark=0.65,w=6);a=streaks(a,14,0.18,0.9,(3,8));a=wear_bottom(a,0.1,0.15);P['pole_grey']=a
# scoreboard black back panels: 1.2 m panel grid, bolt heads, weathering
a=load('sb_black');a=a+18;a=grain(a,7);a=joints(a,'sb_black',du=1.2,dv=1.2,dark=0.45,w=4,hi=1.6);a=dots(a,0.1,0.1,1.8,3,(0.15,0.15));a=blotch(a,25,64);a=streaks(a,30,-0.6,0.7);P['sb_black']=a
# painted timber: fascia boards (maroon), white trim, maroon posts: board joints every 2 m, nail lines, chipped paint, streaks
for n,du in(('fascia',2.0),('trim_white',2.0)):
    m=n=='fascia';a=load(n);a=grain(a,8 if m else 4);a=joints(a,n,du=du,dark=0.55 if m else 0.7,w=5 if m else 4,hi=1.25 if m else 1.06);a=dots(a,0.5,0.5,0.5 if m else 0.65,3,(0.06,0.3));a=blotch(a,16 if m else 9,48);a=streaks(a,30,0.3 if m else 0.2,0.9);a=patches(a,30 if m else 14,1.4 if m else 0.92,(3,9));a=wear_bottom(a,0.3,0.25 if m else 0.15);P[n]=a
a=load('post_maroon');a=grain(a,8);a=blotch(a,16,48);a=streaks(a,12,0.3,0.9,(3,8));a=patches(a,34,1.4,(3,9));a=joints(a,'post_maroon',dv=3.0,dark=0.55,w=5,hi=1.25);a=wear_bottom(a,0.2,0.3);P['post_maroon']=a
# Gorringe ceiling (boarded soffit) and the dark interior: 0.15 m boards, 2.4 m sheet ends, water stains
a=load('ceiling');a=joints(a,'ceiling',du=0.15,dv=2.4,dark=0.82,w=2,hi=1.04);a=grain(a,5);a=blotch(a,8);P['ceiling']=a
a=load('interior_dark');a=a+10;a=grain(a,6);a=joints(a,'interior_dark',du=1.2,dv=2.4,dark=0.55,w=3,hi=1.5);a=blotch(a,25);P['interior_dark']=a
# gable pediment: batten shadows, weathered boards
a=load('pediment');a=grain(a,5);a=joints(a,'pediment',du=0.45,dark=0.82,w=3);a=blotch(a,8);a=streaks(a,25,0.16,0.7);P['pediment']=a
# red corrugated iron: rust and grime blotches, runs down the ribs, lap lines darker at the eaves
a=load('roof_iron');a=grain(a,4);a=blotch(a,10,64);a=streaks(a,40,0.15,0.9,(2,5));P['roof_iron']=a
a=load('roof_gor');a=grain(a,4);a=blotch(a,10,64);a=streaks(a,40,0.15,0.9,(2,5));P['roof_gor']=a
# asphalt: patches, cracks, oil stains, aggregate speckle
a=load('asphalt');a=grain(a,8);a=patches(a,10,0.9,(80,260));a=cracks(a,18,0.55);a=blotch(a,9,128);P['asphalt']=a
# concrete terrace treads: 2.0 m expansion joints, worn centre line, stains
a=load('tread');a=grain(a,6);a=joints(a,'tread',du=2.0,dark=0.75,w=3);a=blotch(a,10);a=cracks(a,4,0.7);P['tread']=a
for n,a in P.items():
    save(n,a);print(f'{n:16s} sd={ImageStat.Stat(Image.open(f"tex/{n}.png").convert("L")).stddev[0]:5.1f}')
