# Texture pass (row 202 2b, director: painted detail on every big surface, "vibrant, real life textures, not
# fucking blurry photos"). Runs after gen_tex.py and repaints the big-surface maps by hand (texpaint.py): no photo
# pixels. Colours keep gen_tex.py's means (keep_mean), so only detail changes. Module sizes in metres.
import json,numpy as np
from texpaint import Canvas,save,gstd
T=json.load(open('tex/tiles.json'))
def out(name,c,tile=None):
    if tile:T[name]=list(tile)
    save(c.img(),'tex/%s.png'%name)
def panel_wall(col,tile,pw,ph,seed,joint=0.012,tone=0.045,streak=0.16,grime=0.10,ledges=None,mott=0.035):
    c=Canvas(*tile,col,seed);c.mottle(mott);c.panels(pw,ph,joint=joint,dark=0.5,tone=tone)
    c.streaks(ledges if ledges is not None else [k*ph for k in range(int(round(tile[1]/ph)))],per_m=1.0,amt=streak)
    c.grime_bottom(min(0.5,ph*0.4),grime,band=ph);c.speckle(0.6,(0.005,0.012),0.15);c.grain(0.012);c.keep_mean();return c
# ---- concrete: 2.4 x 1.2 m formwork panels, tie holes every 0.6 m, rain streaks under the ledge, blotching
c=Canvas(4.8,4.8,(0.80,0.80,0.78),11);c.mottle(0.05,(1.6,0.5,0.12));c.panels(2.4,1.2,joint=0.010,dark=0.62,tone=0.05,stagger=0.5)
for i in range(8):
    for j in range(8):c.a[int((j*0.6+0.3)*c.pv)-2:int((j*0.6+0.3)*c.pv)+3,int((i*0.6+0.3)*c.pu)-2:int((i*0.6+0.3)*c.pu)+3]*=0.72
c.streaks([0.0],per_m=2.2,length=(0.8,3.6),width=(0.03,0.22),amt=0.30)
c.streaks([1.2,2.4,3.6],per_m=0.8,length=(0.2,0.9),amt=0.14)
c.grime_bottom(0.5,0.14);c.speckle(2,(0.006,0.02),0.15);c.grain(0.018);c.keep_mean();out('concrete',c)
# ---- paving: 1.2 m slabs, slab-to-slab tone, dark drainage strip, gum/oil spots
c=Canvas(6,6,(0.62,0.54,0.40),12);c.mottle(0.05,(2.0,0.6,0.1));c.panels(1.2,1.2,joint=0.012,dark=0.62,tone=0.03,bevel=False)
c.hline(0.05,0.10,(0.33,0.33,0.34));c.speckle(1.2,(0.01,0.03),0.25);c.tint(0.25,0.8,(0.45,0.42,0.36))
c.grain(0.02);c.keep_mean();out('paving',c)
# ---- seats: 24 seats x 0.5 m then a 1.2 m aisle (13.2 m repeat), rows 0.8 m: riser shadow, seat back, gaps
W,H=13.2,8.0;c=Canvas(W,H,(0.16,0.20,0.34),13);y,x=np.mgrid[0:c.n,0:c.n];um=x/c.pu;vm=y/c.pv
r=vm%0.8;tread=(0.55,0.55,0.54)
A=np.zeros((c.n,c.n,3))+np.array((0.16,0.20,0.34))
A[r<0.10]=(0.07,0.08,0.11)                                  # riser shadow under the row in front
A[(r>=0.10)&(r<0.16)]=np.array(tread)*0.8                   # tread nosing
A[(r>=0.16)&(r<0.22)]=(0.26,0.32,0.50)                      # seat-back top edge catches the sky
A[(r>=0.22)&(r<0.60)]=(0.16,0.20,0.34)                      # seat backs
A[(r>=0.60)&(r<0.70)]=(0.11,0.14,0.24)                      # seat pan in shade
A[r>=0.70]=np.array(tread)*0.62                             # tread behind the seats
gap=(um%0.5)<0.035;sel=gap&(r>=0.16)&(r<0.70);A[sel]=(0.06,0.07,0.10)
ai=um>=12.0;A[ai]=np.array(tread)*np.where((vm[ai]%0.4)<0.04,0.55,1.0)[:,None]   # aisle stairs: two steps per row
A[(um>=12.0)&(um<12.04)|(um>=13.16)]=(0.30,0.30,0.30)
seat=np.floor(um/0.5).astype(int);row=np.floor(vm/0.8).astype(int);tone=1+0.05*c.R.normal(size=(30,12))
c.a=A*np.where(ai,1.0,tone[seat%30,row%12])[...,None]
c.mottle(0.04,(2.5,0.8));c.grain(0.01);out('seats',c,(W,H))
# ---- roof underside: profiled sheet ribs every 0.2 m, purlins every 1.5 m, sheet laps every 12 m, grime
c=Canvas(12,12,(0.20,0.21,0.23),14);c.mottle(0.06,(3,1,0.3))
for i in range(60):c.vline(i*0.2,0.03,(0.27,0.28,0.30),0.8);c.vline(i*0.2+0.04,0.03,(0.13,0.13,0.15),0.6)
for j in range(8):c.hline(j*1.5,0.12,(0.10,0.10,0.12));c.hline(j*1.5+0.08,0.03,(0.30,0.31,0.33),0.7)
c.hline(0.0,0.05,(0.08,0.08,0.09));c.streaks([k*1.5+0.08 for k in range(8)],per_m=0.6,length=(0.3,1.2),amt=0.2)
c.grain(0.015);c.keep_mean();out('soffit',c)
# ---- roof sheets: standing seams every 0.6 m (down the slope = v), end laps every 12 m, dirt along the ribs
def roof(col,seed,crest,shadow,name):
    c=Canvas(12,12,col,seed);c.mottle(0.05,(4,1.2,0.3))
    d=np.abs(((np.arange(c.n)/c.pu+0.3)%0.6)-0.3);dirt=np.exp(-(d/0.09)**2)            # dirt settles beside each seam
    c.mul(1-0.10*dirt[None,:]*np.clip(1+0.8*c.noise(0.05,1.5),0,2))
    for i in range(20):c.vline(i*0.6,0.035,crest);c.vline(i*0.6+0.035,0.03,shadow,0.8)
    c.hline(0.0,0.06,shadow);c.hline(0.07,0.03,crest,0.6)                                 # sheet end lap
    c.mul(1-0.05*np.clip(c.noise(0.4,3.0),0,3));c.grain(0.012);c.keep_mean();out(name,c)
roof((0.86,0.87,0.85),15,(0.97,0.97,0.96),(0.62,0.63,0.62),'deck')
roof((0.54,0.54,0.53),16,(0.80,0.80,0.79),(0.38,0.38,0.38),'endroof')
# ---- painted steel and fascias: seams, wear, grime toward the bottom edge
c=Canvas(4,4,(0.33,0.62,0.55),17);c.mottle(0.05,(1.5,0.4));c.vline(0,0.012,(0.18,0.33,0.29));c.hline(0,0.012,(0.18,0.33,0.29))
c.mul(1-0.06*np.clip(c.noise(0.3,1.2),0,3));c.speckle(1.5,(0.006,0.015),0.3);c.grain(0.012);c.keep_mean();out('teal',c)
c=Canvas(12,2,(0.93,0.93,0.91),18);c.mottle(0.03);c.panels(4,2,joint=0.015,dark=0.6,tone=0.03,bevel=False)
c.streaks([0.0],per_m=1.4,length=(0.3,1.6),amt=0.22);c.grime_bottom(0.45,0.22);c.hline(1.97,0.06,(0.70,0.70,0.69));c.grain(0.01);c.keep_mean();out('fascia',c)
c=Canvas(12,2,(0.66,0.53,0.30),19);c.mottle(0.05);c.panels(6,2,joint=0.02,dark=0.55,tone=0.04,bevel=False)
c.grime_bottom(0.7,0.28);c.streaks([0.0],per_m=1.0,length=(0.3,1.5),amt=0.2);c.grain(0.012);c.keep_mean();out('gutter',c)
c=Canvas(12,2,(0.17,0.18,0.19),20);c.mottle(0.06);c.panels(3,2,joint=0.02,dark=0.6,tone=0.06,bevel=False);c.hline(0.02,0.05,(0.09,0.09,0.10))
c.grime_bottom(0.6,0.2,col=(0.4,0.38,0.34));c.grain(0.015);c.keep_mean();out('riser',c)
c=Canvas(4,4,(0.94,0.94,0.93),21);c.mottle(0.03);c.hline(0,0.01,(0.75,0.75,0.75));c.mul(1-0.04*np.clip(c.noise(0.3,1.0),0,3));c.speckle(1,(0.005,0.012),0.2);c.grain(0.008);c.keep_mean();out('white',c)
c=Canvas(6,6,(0.78,0.80,0.82),22);c.mottle(0.04);xx=np.arange(c.n);c.mul(1+0.03*np.sin(xx/c.n*2*np.pi*40)[None,:])
for j in range(4):c.hline(j*1.5,0.02,(0.55,0.56,0.58))
c.streaks([j*1.5+0.02 for j in range(4)],per_m=1.2,length=(0.2,1.2),amt=0.18);c.grime_bottom(0.4,0.12,band=1.5);c.grain(0.01);c.keep_mean();out('tank',c)
for nm,col,seed in(('signred',(0.70,0.08,0.10),23),('signblack',(0.06,0.06,0.07),24)):
    c=Canvas(4,4,col,seed);c.mottle(0.05);c.panels(2,1,joint=0.012,dark=0.55 if nm=='signred' else 1.6,tone=0.05,bevel=False)
    c.grime_bottom(0.3,0.15,band=1.0,col=(0.5,0.48,0.45) if nm=='signblack' else (0.3,0.28,0.25));c.grain(0.01);c.keep_mean();out(nm,c)
c=Canvas(4,4,(0.95,0.90,0.74),25);c.mottle(0.04);xx=np.arange(c.n)
c.mul(1+0.012*c.noise(0.6,0.02));c.vline(0,0.03,(0.80,0.75,0.60));c.vline(2,0.03,(0.80,0.75,0.60))
c.grime_bottom(0.8,0.12);c.grain(0.01);c.keep_mean();out('canvas',c)
# ---- cladding panels: per-panel tone, joints, streaks under each panel's top joint, grime at the bottom
out('silver',panel_wall((0.74,0.76,0.79),(6,6),3.0,1.2,26,tone=0.05))
out('panel_lt',panel_wall((0.70,0.72,0.75),(6,6),3.0,1.2,27,tone=0.045))
out('navy',panel_wall((0.14,0.18,0.33),(6,6),1.5,3.0,28,tone=0.07,streak=0.10))
c=panel_wall((0.27,0.30,0.38),(6,6),1.5,3.0,29,tone=0.07);out('slate',c)
# louvre bay drawn on the slate cladding: 2.4 x 4 m, slats every 0.15 m with a shadow under each slat
a=c.a;px=c.pu;x0,x1,y0,y1=int(1.8*px),int(4.2*px),int(1.0*px),int(5.0*px)
a[y0:y1,x0:x1]=np.array((0.05,0.06,0.08))
for yv in np.arange(y0,y1,0.15*px):
    yi=int(yv);a[yi:yi+5,x0:x1]=np.array((0.42,0.44,0.50));a[yi+5:yi+14,x0:x1]=np.array((0.33,0.35,0.41));a[yi+14:yi+20,x0:x1]=np.array((0.12,0.13,0.16))
a[y0:y0+5,x0:x1]=a[y1-5:y1,x0:x1]=a[y0:y1,x0:x0+5]=a[y0:y1,x1-5:x1]=np.array((0.50,0.52,0.57))
c.a=a;c.grime_bottom(0.4,0.15,band=6.0);out('louvre',c)
# ---- dark glazing: each pane reflects a slightly different sky, dirt at the pane foot, lit mullion edge
c=Canvas(6,6,(0.15,0.20,0.26),30);y,x=np.mgrid[0:c.n,0:c.n];um=x/c.pu;vm=y/c.pv
t=(vm%3.0)/3.0;pane=(np.floor(um/1.5)+4*np.floor(vm/3.0)).astype(int);pt=1+0.10*c.R.normal(size=16)
c.a=(np.array((0.21,0.28,0.35))*(1-t[...,None])+np.array((0.10,0.13,0.17))*t[...,None])*pt[pane%16][...,None]
c.mul(1+0.05*c.noise(0.8,2.0));c.grime_bottom(0.3,0.10,band=3.0,col=(0.5,0.47,0.42))
for i in range(4):c.vline(i*1.5,0.05,(0.22,0.23,0.25));c.vline(i*1.5+0.03,0.01,(0.40,0.41,0.44))
for j in range(2):c.hline(j*3.0,0.06,(0.22,0.23,0.25));c.hline(j*3.0+0.035,0.01,(0.40,0.41,0.44))
c.grain(0.008);out('glass',c)
# ---- ground's own sign (director 2026-11-19: "Yes, ground's own signs"): white MARVEL on the red panel, white
# STADIUM on the black one, outward face only. Letters are drawn from a font (Bahnschrift Bold Condensed, the
# straight-sided condensed caps of the photos), sized to fill the panel like the 2019 aerial; a grey inset line
# copies the outlined channel letters of the close-up. Each map is one face: painted face-local, then rolled to the
# face's UV offset so it lands exactly on the panel. On this face u runs right-to-left seen from outside, so the
# face image is mirrored and U0 is the face's smallest u (its right-hand edge from outside); Ztop = top edge.
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import distance_transform_edt
def word(txt,W,H,cap,margin,P=200):
    f=ImageFont.truetype('C:/Windows/Fonts/bahnschrift.ttf',400);f.set_variation_by_name('Bold Condensed')
    im=Image.new('L',(4200,700),0);ImageDraw.Draw(im).text((40,40),txt,font=f,fill=255);m=im.crop(im.getbbox())
    FW,FH,tw,th=int(W*P),int(H*P),int((W-2*margin)*P),int(cap*P)
    F=Image.new('L',(FW,FH),0);F.paste(m.resize((tw,th),Image.LANCZOS),((FW-tw)//2,(FH-th)//2))
    return np.asarray(F,float)/255,P
def sign_face(name,col,seed,W,H,U0,Ztop,txt,stripes,gcol):
    c=Canvas(W,H,col,seed);c.mottle(0.04)
    if stripes:
        for i in range(int(round(W/0.3))):c.vline(i*0.3+0.15,0.025,np.array(col)*1.3,0.7)
    c.grime_bottom(0.3,0.12,col=gcol);c.grain(0.01);c.keep_mean()
    M,P=word(txt,W,H,3.4,0.45);D=distance_transform_edt(M>0.5)/P             # metres inside each letter
    def rs(a):return np.asarray(Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8)).resize((c.n,c.n),Image.LANCZOS),float)/255
    A=rs(M);ring=rs(((D>0.09)&(D<0.12)).astype(float));edge=rs(((D>0)&(D<0.03)).astype(float))
    L=np.ones((c.n,c.n,3))*np.array((0.90,0.90,0.88));L*=(1-0.25*ring)[...,None];L*=(1-0.15*edge)[...,None]
    L*=(1+0.02*c.noise(0.5))[...,None]
    c.a=c.a*(1-A[...,None])+L*A[...,None]
    c.a=c.a[:,::-1]
    du=int(round(((U0/W)%1)*c.n));dv=int(round((1-((Ztop/H)%1))*c.n))%c.n
    c.a=np.roll(np.roll(c.a,du,axis=1),dv,axis=0);out(name,c,(W,H))
sign_face('sign_marvel',(0.70,0.08,0.10),31,13.5,4.7,2.5,41.2,'MARVEL',True,(0.3,0.28,0.25))
sign_face('sign_stadium',(0.06,0.06,0.07),32,19.9,4.7,-17.4,41.2,'STADIUM',False,(0.5,0.48,0.45))
json.dump(T,open('tex/tiles.json','w'),indent=0)
