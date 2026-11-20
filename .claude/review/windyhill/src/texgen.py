# Hand-made textures (no photo pixels). Colours read from the 1992 aerial / period photos, in cols.json.
import numpy as np,json,sys
from PIL import Image
rng=np.random.default_rng(7);N=1024
C=json.load(open('cols.json'))
def save(n,a):Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save('tex/'+n+'.png')
def noise(s,oct=4,amp=1.0):
    out=np.zeros((N,N))
    for o in range(oct):
        k=2**(o+2);g=rng.standard_normal((k+1,k+1))
        im=np.array(Image.fromarray(g.astype(np.float32),'F').resize((N,N),Image.BICUBIC));out+=im/(2**o)
    return out/np.abs(out).max()*amp*0.4  # texture pass: low-frequency mottle cut to 0.4x
def tint(base,v):return np.array(base,float)[None,None,:]*(1+v[...,None])
yy,xx=np.mgrid[0:N,0:N]
# concrete (tile 4 m): fine aggregate + faint form joints every 2 m
def concrete(base):
    v=noise(0,5,0.06)+rng.standard_normal((N,N))*0.025
    a=tint(base,v);a[(xx%512)<2]*=0.82;return a
save('concrete',concrete(C['concrete']))
save('steps',concrete(C['terrace']))
# asphalt (tile 6 m)
v=noise(0,5,0.08)+rng.standard_normal((N,N))*0.06;save('asphalt',tint(C['asphalt'],v))
# brick (tile 2.4 m wide x 2.4 m high): 230x76 mm + 10 mm mortar, stretcher bond
ppm=N/2.4;bh=0.086*ppm;bw=0.24*ppm;a=np.zeros((N,N,3))
row=(yy//bh).astype(int);off=(row%2)*bw/2;col=((xx+off)//bw).astype(int)
bid=row*997+col;jit=np.random.default_rng(3).standard_normal(bid.max()+1)
a[:]=tint(C['brick'],0.05*jit[bid]+noise(0,3,0.04)+rng.standard_normal((N,N))*0.03)
mort=((yy%bh)<0.010*ppm)|(((xx+off)%bw)<0.010*ppm);a[mort]=C['mortar'];save('brick',a)
# corrugated steel roofs (tile 6 m): 76 mm ribs, painted colour per roof
def roof(base):
    ppm=N/6;ph=(xx/ppm)%0.0762/0.0762;sh=0.20*np.cos(ph*2*np.pi)+0.08*np.sign(np.sin(ph*2*np.pi))
    a=tint(base,sh+noise(0,3,0.03));a[(yy%(ppm*2.4))<2]*=0.85;return a
for k,v in C.items():
    if k.startswith('roof'):save(k,roof(v))
# painted white (fence, fascia, posts) tile 4 m: panel joints every 2.4 m
a=tint(C['white'],noise(0,3,0.02));a[(xx%(N/4*2.4))<2]*=0.8;save('white',a)
# render (cream painted render) tile 4 m
save('render',tint(C['render'],noise(0,4,0.035)+rng.standard_normal((N,N))*0.012))
# bowls / croquet greens: close-cut, faint 2 m mowing bands (tile 8 m)
band=np.where(((xx//(N/4))%2)==0,0.04,-0.04);save('green',tint(C['bowls'],band+noise(0,4,0.03)+rng.standard_normal((N,N))*0.02))
# oval grass (tile 4 m along a ring, rings via geometry): blades + light/dark ring band
g=noise(0,5,0.06)+rng.standard_normal((N,N))*0.05
save('grass',tint(C['grass'],g));save('grass2',tint(C['grass'],g-0.045))
save('bank',tint(C['bank'],noise(0,5,0.08)+rng.standard_normal((N,N))*0.06))
save('concourse',tint(C['concourse'],noise(0,5,0.05)+rng.standard_normal((N,N))*0.05))
pc=tint(C['clay'],noise(0,4,0.05)+rng.standard_normal((N,N))*0.03);pc[(np.abs(yy-N*0.06)<4)|(np.abs(yy-N*0.94)<4)]=C['white'];save('pitchclay',pc)
# seat tread (u along the row, 4 m; v 0..1 across one 0.8 m tread): concrete tread, bench plank at the back
def seat(base):
    a=concrete(C['terrace']);pv=yy/N
    plank=(pv>0.55)&(pv<0.88);a[plank]=tint(base,noise(0,3,0.04)+rng.standard_normal((N,N))*0.02)[plank]
    a[(pv>0.86)&(pv<0.88)]*=0.7;a[(pv>0.55)&(pv<0.565)]*=1.12;a[pv>0.97]*=0.8
    sup=(pv>0.88)&((xx%(N/4*1.2))<14);a[sup]=np.array(C['steel'])*0.6;return a
for k,v in C.items():
    if k.startswith('seat'):save(k,seat(v))
# scoreboard face (tile 4 m): black panels, white frame lines
a=np.zeros((N,N,3))+np.array(C['board']);a[((xx%256)<6)|((yy%256)<6)]=C['white'];save('board',a)
print('TEX OK')

# glass (tile 4 m): dark blue-grey panes 1.2 m wide in white mullions, sky reflection gradient
a=tint(C['glass'],0.10*(1-yy/N)+noise(0,3,0.03));a[((xx%(N/4*1.2))<10)|((yy%(N/4*1.0))<10)]=C['white'];save('glass',a)
# galvanised steel (tile 2 m)
save('steel',tint(C['steel'],noise(0,4,0.05)+rng.standard_normal((N,N))*0.02))

# scoreboard face (whole face, 1 UV): black board, white border, header strip, two team rows of score frames
a=np.zeros((N,N,3))+np.array(C['board'])+noise(0,3,4)[...,None]
def box(x0,y0,x1,y1,w=6):
    a[y0:y1,x0:x0+w]=C['white'];a[y0:y1,x1-w:x1]=C['white'];a[y0:y0+w,x0:x1]=C['white'];a[y1-w:y1,x0:x1]=C['white']
box(10,10,N-10,N-10,14)
a[70:180,60:N-60]=C['white']
for r in (300,620):
    box(60,r,430,r+220)
    for c in range(4): box(470+c*125,r,470+c*125+110,r+220)
save('sbface',a)

# boundary signs (24 m x 0.85 m strip): ten 2.4 m painted panels, plain colours with a lighter centre block, no wording
W_,H_=4096,256;a=np.zeros((H_,W_,3));pw=W_/10
pal=[(178,28,36),(250,250,246),(22,46,104),(240,196,30),(28,110,60),(20,20,22),(200,40,40),(30,80,160),(245,245,240),(230,120,20)]
cen=[(250,250,246),(178,28,36),(240,196,30),(22,46,104),(250,250,246),(240,196,30),(250,250,246),(250,250,246),(22,46,104),(250,250,246)]
for k in range(10):
    x0=int(k*pw);x1=int((k+1)*pw);a[:,x0:x1]=pal[k];a[70:186,x0+90:x1-90]=cen[k];a[:,x0:x0+6]=(235,235,230)
a=a*(1+np.random.default_rng(5).standard_normal((H_,W_,1))*0.01)
Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save('tex/signs.png')

# terrace tread (4 m along x, one tread depth along y, front edge at the image bottom = v 0):
# precast nosing strip with an arris shadow, 2 m expansion joints, grime toward the riser, weathering blotches
pv=1-yy/N
a=concrete(C['terrace'])*(1+noise(0,2,0.07)[...,None])
a[pv<0.07]*=1.13;a[(pv>=0.07)&(pv<0.085)]*=0.78;a[pv<0.012]*=0.85
a*= (1-0.16*np.clip((pv-0.82)/0.18,0,1))[...,None]
a[((xx%(N/2))<4)]*=0.72
save('tread',a)
# risers: same concrete with vertical rain streaks
st=np.array(Image.fromarray(rng.standard_normal((8,256)).astype(np.float32),'F').resize((N,N),Image.BICUBIC))
save('steps',concrete(C['terrace'])*(1-0.06*np.clip(st,0,None)[...,None]))
# apron paving: 1.5 m concrete slabs (tile 6 m), per-slab tone, sawn joints, weathering
sl=((yy//(N/4)).astype(int)*7+(xx//(N/4)).astype(int));j=np.random.default_rng(11).standard_normal(64)*0.012
a=tint(C['paving'],j[sl%64]+noise(0,4,0.05)+rng.standard_normal((N,N))*0.03);a[((xx%(N/4))<3)|((yy%(N/4))<3)]*=0.82
save('concourse',a)
# bench seats (1.2 m along x, seat depth along y): three painted timber slats with gaps
def bench(base):
    a=tint(base,noise(0,3,0.04)+rng.standard_normal((N,N))*0.02);g=(yy%(N/3))<26;a[g]*=0.35;a[(yy%(N/3)>=26)&(yy%(N/3)<40)]*=1.12
    a[(xx%(N/1))<0]*=1;return a
save('bench_grey',bench(C['seat_grey']));save('bench_red',bench(C['seat_red']))
