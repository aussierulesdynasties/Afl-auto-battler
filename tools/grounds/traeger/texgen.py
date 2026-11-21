# Hand-made textures for the grandstand (director 2026-11-18: no photo pixels on any model; photos are reference only).
# Every image is painted here from code: base colours picked by eye from w04/w17/c09, patterns measured off them.
# TILE[m] = metres covered by one image (u, v); PANEL[m] = the image covers one whole panel (UV 0..1).
import numpy as np,json,math,os
from PIL import Image,ImageDraw,ImageFont,ImageFilter
OUT='tex3';os.makedirs(OUT,exist_ok=True)
rng=np.random.default_rng(7)
F='C:/Windows/Fonts/'
def noise(h,w,cells,amp=1.0,seed=0):
    # periodic smooth noise: low-pass filtered white noise in the frequency domain (tiles seamlessly)
    r=np.random.default_rng(seed).standard_normal((h,w));m_=max(h,w);fy=np.fft.fftfreq(h)[:,None]*m_;fx=np.fft.fftfreq(w)[None,:]*m_
    k=np.exp(-(fx**2+fy**2)/(2*cells**2));n=np.real(np.fft.ifft2(np.fft.fft2(r)*k));n/=n.std()+1e-9;return n*amp
def rgb(c):return np.array([int(c[i:i+2],16) for i in(1,3,5)],float)
def base(h,w,col,var=6,cells=6,seed=0):
    img=np.zeros((h,w,3))+rgb(col);n=noise(h,w,cells,var*0.45,seed)+noise(h,w,cells*12,var*0.5,seed+1)
    return img+n[...,None]
def save(name,img):
    Image.fromarray(np.clip(img,0,255).astype(np.uint8)).save(os.path.join(OUT,name+'.png'))
TILE={};PANEL={}
PX=200  # pixels per metre for tiled materials
# ---- ribbed metal deck (roof top white, soffit beige): trapezoid ribs 0.19 m pitch along u ----
def ribbed(col,shade,tile=(1.9,1.9),seed=0,dirt=0):
    w,h=int(tile[0]*PX),int(tile[1]*PX);img=base(h,w,col,3,4,seed)
    x=(np.arange(w)/PX)%0.19;rib=np.where(x<0.035,-shade,np.where(x<0.05,shade*0.6,0))
    img+=rib[None,:,None]
    if dirt:img-=np.clip(noise(h,w,3,dirt,seed+5),0,None)[...,None]*np.array([0.8,0.9,1.1])
    return img
save('roof_top',ribbed('#e9e8e3',16,seed=1,dirt=5));TILE['roof_top']=(1.9,1.9)
save('canopy',ribbed('#e7e6e0',16,seed=2,dirt=5));TILE['canopy']=(1.9,1.9)
save('roof_soffit',ribbed('#d8d0bb',14,seed=3));TILE['roof_soffit']=(1.9,1.9)
save('canopy_under',ribbed('#d6cfbc',14,seed=4));TILE['canopy_under']=(1.9,1.9)
# ---- flat painted surfaces: render/paint with soft mottling, never one flat colour ----
def painted(col,tile=2.0,var=5,seed=0):return base(int(tile*PX),int(tile*PX),col,var,5,seed)
save('fascia',painted('#f1f0ec',seed=10));TILE['fascia']=(2,2)
save('steel_white',painted('#eeede8',var=4,seed=11));TILE['steel_white']=(2,2)
save('steel_grey',painted('#8d9196',var=5,seed=12));TILE['steel_grey']=(2,2)
img=painted('#dcd6c4',var=5,seed=13)
save('cream',img);TILE['cream']=(2,2)
save('rear_dark',painted('#3d3e40',var=4,seed=14));TILE['rear_dark']=(2,2)
# ---- concrete: deck, treads and risers with saw-cut joints every 3 m ----
def concrete(col,tile=3.0,seed=0,joint=True):
    w=h=int(tile*PX);img=base(h,w,col,6,8,seed)+noise(h,w,120,5,seed+3)[...,None]
    if joint:img[:,:3]-=28;img[:3,:]-=28
    return img
save('deck',concrete('#a7a39b',seed=20));TILE['deck']=(3,3)
save('riser',concrete('#b8b4ab',seed=21,joint=False));TILE['riser']=(3,3)
# ---- seats: moulded plastic, slate blue (rows 3+) and light grey (front two rows), w17 ----
save('seat_navy',base(100,100,'#4c566b',5,3,30));TILE['seat_navy']=(0.5,0.5)
save('seat_white',base(100,100,'#c9ccd0',5,3,31));TILE['seat_white']=(0.5,0.5)
# ---- plinth front (w04 back-projected at t 0.6): charcoal render panels, slab lip, arch, doors and recesses ----
def plinth_panel():
    P_=json.load(open('stand.json'))['P'];a0,a1,zt=P_['pl_s0'],P_['pl_s1'],P_['pl_z'];K=100
    w,h=int((a1-a0)*K),int(zt*K);img=base(h,w,'#3c3e40',4,int((a1-a0)*2),40)
    im=Image.fromarray(np.clip(img,0,255).astype(np.uint8));d=ImageDraw.Draw(im)
    X=lambda s_:int((s_-a0)*K);Y=lambda z_:int((zt-z_)*K)
    for s_ in(11.0,17.09,20.38,24.13):d.rectangle([X(s_)-2,0,X(s_)+2,h],fill=(32,33,35))          # panel recesses
    for s0_,s1_ in((13.15,13.96),(24.40,25.24),(27.23,28.40)):                                   # doors
        d.rectangle([X(s0_),Y(2.05-0.12),X(s1_),h],fill=(26,27,29));d.rectangle([X(s0_)+3,Y(1.9),X(s1_)-3,h],fill=(44,46,49))
        d.line([X(s0_)+3,Y(1.0),X(s1_)-3,Y(1.0)],fill=(36,37,40),width=2)
    c0,c1,zs=9.11,10.64,1.10;r_=(c1-c0)/2                                                             # arched opening
    d.rectangle([X(c0),Y(zs),X(c1),h],fill=(20,21,23));d.pieslice([X(c0),Y(zs+r_),X(c1),Y(zs-r_)],180,360,fill=(20,21,23))
    d.rectangle([0,0,w,int(0.12*K)],fill=(198,190,170))                                              # slab lip
    d.line([0,int(0.12*K),w,int(0.12*K)],fill=(120,116,104),width=2)
    return np.asarray(im).astype(float)
save('plinth',plinth_panel());PANEL['plinth']=True
# ---- dark horizontal cladding (c09): louvres 0.10 m pitch, lit top lip, deep shadow underneath ----
w,h=int(2*PX),int(1.0*PX);img=base(h,w,'#4a4c50',2,4,41);y=(np.arange(h)/PX)%0.10
prof=np.where(y<0.008,38,np.where(y<0.02,-34,np.where(y<0.06,-6+ (y-0.02)/0.04*12,6)))
img+=prof[:,None,None];save('cladding',img);TILE['cladding']=(2,1.0)
# ---- gabion wall (c09, close look): wire baskets 1.0 x 0.5 m of broken red-brown rock, fine wire mesh over it ----
def gabion(tile=(2.0,1.0),seed=50):
    from scipy.spatial import cKDTree
    w,h=int(tile[0]*PX),int(tile[1]*PX);r=np.random.default_rng(seed)
    n=int(tile[0]*tile[1]*110);pts=r.uniform(0,1,(n,2))*[w,h]
    big=np.concatenate([pts+[dx*w,dy*h] for dx in(-1,0,1) for dy in(-1,0,1)])   # wrapped: the tile repeats seamlessly
    yy,xx=np.mgrid[0:h,0:w];q=np.c_[xx.ravel(),yy.ravel()];d,i=cKDTree(big).query(q,k=2)
    lab=(i[:,0]%n).reshape(h,w);gap=(d[:,1]-d[:,0]).reshape(h,w)
    pal=np.array([rgb(c) for c in('#c89a7c','#b07a5e','#d4ae90','#9c6650','#bf8c6e','#a87262','#ccA086','#8e5c4a')])
    col=pal[r.integers(len(pal),size=n)]+r.normal(0,8,(n,1));img=col[lab]
    near=big[i[:,0]].reshape(h,w,2);sh=((xx-near[...,0])+(yy-near[...,1]))/12.0     # light from the top-left on each rock
    img-=np.clip(sh,-1.0,1.0)[...,None]*8
    img+=noise(h,w,40,6,seed+2)[...,None]
    img*=np.clip(0.35+gap/2.5,0.35,1.0)[...,None]                                          # dark voids between rocks
    m=int(0.075*PX)
    img[(yy%m)<2]=img[(yy%m)<2]*0.55+np.array([170,170,165])*0.45;img[:,(xx[0]%m)<2]=img[:,(xx[0]%m)<2]*0.55+np.array([170,170,165])*0.45
    for x0 in range(0,w,int(1.0*PX)):img[:,x0:x0+4]=img[:,x0:x0+4]*0.3+np.array([150,150,146])*0.7
    for y0 in range(0,h,int(0.5*PX)):img[y0:y0+4]=img[y0:y0+4]*0.3+np.array([150,150,146])*0.7
    return img
save('stone',gabion());TILE['stone']=(2.0,1.0)
# ---- box underside: beige with downlights every bay (w17) ----
P=json.load(open('stand.json'))['P']
bw=P['box_s1']-P['box_s0'];bd=P['box_t1']-P['box_t0']
w,h=int(bw*60),int(bd*60);img=base(h,w,'#d3ccb8',4,6,60);im=Image.fromarray(np.clip(img,0,255).astype(np.uint8));d=ImageDraw.Draw(im)
for k in range(8):
    x=int((k+0.5)/8*w)
    for yy in(0.3,0.7):d.ellipse([x-6,int(yy*h)-6,x+6,int(yy*h)+6],fill=(245,243,235),outline=(150,145,130))
im.save(os.path.join(OUT,'soffit_box.png'));PANEL['soffit_box']=True
# ======== box front: measured off w04 (cam_w04b back-projection, metres from the stand's south front corner) ========
s0,s1=P['box_s0'],P['box_s1']
POSTS=[8.03,10.22,12.45,14.53,16.71,18.88,21.15,23.35,25.51]          # heavy frames (w04 x 318..984)
MULL=[8.72,9.42,10.94,11.67,13.12,13.80,15.61,17.77,19.62,20.36,21.88,22.54,24.05,24.79]  # light mullions
PXB=120
def sx(s):return (s-s0)/(s1-s0)
# banner: navy, white lettering "Traeger Park Oval" s 15.8..19.0, TIO logo tile s 14.7..15.6 (w04)
bh=P['box_z1']-P['bn_z'];W_,H_=int((s1-s0)*PXB),int(bh*PXB)
img=np.zeros((H_,W_,3))+rgb('#22378f');img+=(np.linspace(-14,10,H_)[:,None,None]);img+=noise(H_,W_,8,3,70)[...,None]
im=Image.fromarray(np.clip(img,0,255).astype(np.uint8));d=ImageDraw.Draw(im)
d.rectangle([0,H_-5,W_,H_],fill=(18,30,80))
# no lettering (director 2026-11-18: "C: no lettering"): blank navy panel
im.save(os.path.join(OUT,'banner.png'));PANEL['banner']=True
# glass: dark tinted, sky-to-tree reflection gradient, white frames
gh=P['bn_z']-P['gl_z'];H_=int(gh*PXB)
img=np.zeros((H_,W_,3));tv=np.linspace(0,1,H_)[:,None]
img+=(rgb('#5d7487')*(1-tv)+rgb('#2c3a3a')*tv)[:,None,:].reshape(H_,1,3)
img+=noise(H_,W_,10,9,71)[...,None]*np.array([0.7,0.9,1.0])
img+=(np.clip(noise(H_,W_,4,1,72),0.3,None)-0.3)[...,None]*np.array([-14,-8,-14])  # soft tree reflections
im=Image.fromarray(np.clip(img,0,255).astype(np.uint8));d=ImageDraw.Draw(im);fc=(232,232,226)
for s in POSTS:x=int(sx(s)*W_);d.rectangle([x-7,0,x+7,H_],fill=fc)
for s in MULL:x=int(sx(s)*W_);d.rectangle([x-4,0,x+4,H_],fill=fc)
d.rectangle([0,0,W_,8],fill=fc);d.rectangle([0,H_-10,W_,H_],fill=fc);d.rectangle([0,0,10,H_],fill=fc);d.rectangle([W_-10,0,W_,H_],fill=fc)
im.save(os.path.join(OUT,'glass.png'));PANEL['glass']=True
# set-back window: two panes, same glass
W2,H2=int(1.3*PXB),int(1.72*PXB);g=np.asarray(im)[:,:W2].copy();g=np.asarray(Image.fromarray(g).resize((W2,H2)))
im2=Image.fromarray(g);d2=ImageDraw.Draw(im2);d2.rectangle([W2//2-4,0,W2//2+4,H2],fill=fc)
for r_ in([0,0,W2,8],[0,H2-9,W2,H2],[0,0,8,H2],[W2-8,0,W2,H2]):d2.rectangle(r_,fill=fc)
im2.save(os.path.join(OUT,'glass_sb.png'));PANEL['glass_sb']=True
# cream band: rendered panel, "Bowden McAdam Grandstand" in dark grey s 14.6..19.0 (w04)
ch_=P['gl_z']-P['box_z0'];H_=int(ch_*PXB)
img=np.zeros((H_,W_,3))+rgb('#e1dccb');img+=noise(H_,W_,10,4,73)[...,None];img[-6:]-=40
im=Image.fromarray(np.clip(img,0,255).astype(np.uint8));d=ImageDraw.Draw(im)
# no lettering (director 2026-11-18): blank cream panel
im.save(os.path.join(OUT,'cream_band.png'));PANEL['cream_band']=True
# ---- south wing and under-deck (w04, c06, c08, c09): light grey render, charcoal wall, door panels, white benches ----
img=base(int(2*PX),int(2*PX),'#a8a39a',5,6,401)+noise(int(2*PX),int(2*PX),90,3,402)[...,None]   # fine trowelled speckle
save('render_grey',img);TILE['render_grey']=(2,2)
save('under_wall',painted('#55575a',var=4,seed=403));TILE['under_wall']=(2,2)
save('bench_white',painted('#e4e4df',tile=1.0,var=3,seed=404));TILE['bench_white']=(1,1)
# black louvres on the wing's south face (c09): horizontal blades about 0.1 m apart, each lit on top, shadowed under
w,h=int(1*PX),int(1*PX);img=base(h,w,'#1f2022',3,4,406);y_=(np.arange(h)/PX)%0.1
img+=np.where(y_<0.012,26,np.where(y_>0.085,-10,0))[:,None,None];save('louvre_black',img);TILE['louvre_black']=(1,1)
w,h=260,350;img=base(h,w,'#8f9295',3,4,405);yy,xx=np.mgrid[0:h,0:w]
fr=(xx<9)|(xx>w-10)|(yy<9);img[fr]=rgb('#6c6f72')                       # steel frame round a flush door leaf
img[(np.abs(xx-w*0.82)<5)&(np.abs(yy-h*0.52)<14)]=rgb('#c9cbcc')          # pull handle
save('door_panel',img);PANEL['door_panel']=True
def bars_rgba(name,Wm,Hm,pitch,bw,col,rails=(),posts=(),post_w=0.06,bows=False,seed=0):
    # transparent background; vertical bars every `pitch` m (`bw` m wide), optional rails (z0,z1 in m from the bottom)
    # and posts (x positions in m); bows: a half-loop over every pair of bars (bow-top fence)
    Wp,Hp=int(Wm*PX),int(Hm*PX);A=np.zeros((Hp,Wp,4));yy,xx=np.mgrid[0:Hp,0:Wp]/PX;z=Hm-yy
    on=((xx%pitch)<bw)&(z<Hm-(0.25 if bows else 0.0))
    for z0,z1 in rails:on|=(z>=z0)&(z<z1)
    for x0 in posts:on|=(np.abs(xx-x0)<post_w/2)
    if bows:
        cx=np.floor(xx/(2*pitch))*2*pitch+pitch+bw/2;r=np.hypot((xx-cx)/pitch,(z-(Hm-0.25))/0.22)
        on|=(np.abs(r-1.0)<bw/pitch*0.9)&(z>=Hm-0.25)
    A[...,:3]=rgb(col)+noise(Hp,Wp,20,3,seed)[...,None];A[...,3]=np.where(on,255,0)
    Image.fromarray(np.clip(A,0,255).astype(np.uint8),'RGBA').save(os.path.join(OUT,name+'.png'));TILE[name]=(Wm,Hm)
bars_rgba('rail_bars',1.2,1.0,0.12,0.02,'#d9dbdc',rails=((0.0,0.04),),seed=410)                                    # stand balustrades: white bars
bars_rgba('rail_bow',2.4,1.2,0.12,0.018,'#1d1e20',rails=((0.08,0.12),(0.9,0.94)),posts=(0.03,),bows=True,seed=411)  # black bow-top
bars_rgba('rail_pal',2.4,1.8,0.13,0.025,'#8a8e92',rails=((0.12,0.17),(1.6,1.65)),posts=(0.04,),post_w=0.07,seed=412) # grey vertical-bar palisade
json.dump(dict(TILE=TILE,PANEL=list(PANEL)),open(os.path.join(OUT,'tex.json'),'w'))
print(sorted(os.listdir(OUT)))
