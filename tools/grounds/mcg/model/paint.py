# Hand-made textures for the MCG, painted in code (no photo pixels). TILE[name] = metres covered by one tile (u, v).
# Colours read off the 2026 Google Earth views and daylight photos; patterns are drawn, not sampled.
import numpy as np,json,math,os
from PIL import Image
R=np.random.default_rng(11);N=1024;OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'tex')+'/';TILE={}
def save(name,a,tile):
    Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(OUT+name+'.png');TILE[name]=tile
def noise(n,sc,amp):
    g=R.normal(0,1,(sc,sc));g=np.tile(g,(2,2));im=Image.fromarray(((g-g.min())/np.ptp(g)*255).astype(np.uint8)).resize((2*n,2*n),Image.BICUBIC)
    a=np.asarray(im,float)[n//2:n//2+n,n//2:n//2+n]/255-0.5;return a*amp
def fine(n,amp):return R.normal(0,amp,(n,n))
def flat(col,f=3,s=5):return np.ones((N,N,3))*np.array(col,float)+fine(N,f)[:,:,None]+noise(N,24,s)[:,:,None]
# Seat rows: one tile = 4 m along the row x 3.2 m up the rake (4 rows of 0.8 m). Plastic seats 0.5 m wide,
# backrest band, concrete riser and walkway between rows. v runs up the rake.
def seats(name,col,riser=(150,150,146)):
    a=np.ones((N,N,3))*np.array(riser,float);pu=N/4.0;pv=N/3.2
    for r in range(4):
        v0=r*0.8
        for k in range(8):
            u0=k*0.5;c=np.array(col,float)*(1+R.normal(0,0.03))
            x0,x1=int((u0+0.02)*pu),int((u0+0.48)*pu)
            # seat pan (lower) and backrest (upper, slightly darker)
            a[int((v0+0.08)*pv):int((v0+0.40)*pv),x0:x1]=c
            a[int((v0+0.40)*pv):int((v0+0.70)*pv),x0:x1]=c*0.85
        a[int((v0+0.70)*pv):int((v0+0.74)*pv)]=np.array(riser)*0.7  # shadow line at the riser
    a+=fine(N,2.5)[:,:,None];save(name,a,(4.0,3.2))
seats('seat_teal',(96,170,176));seats('seat_navy',(22,74,118),riser=(64,68,74));seats('seat_blue',(58,98,150));seats('seat_grey',(128,138,150))
# Roof sheeting: light metal deck, ribs every 0.3 m along v (radial), long panels.
def deck(name,col,pitch=0.3,tile=3.0):
    x=np.arange(N)/N*(tile/pitch);rib=np.where((x%1)<0.14,0.82,1.0)+0.03*np.cos(2*math.pi*x)
    a=np.ones((N,N,3))*np.array(col,float)*rib[None,:,None]+noise(N,10,6)[:,:,None]+fine(N,1.5)[:,:,None];save(name,a,(tile,tile))
deck('roof_white',(206,204,198));deck('roof_grey',(164,171,171));deck('roof_soffit',(196,200,204))
# Translucent roof panel band (polycarbonate): pale with darker purlin lines every 1.5 m.
a=flat((206,214,216),2,5);p=N/3.0
for k in range(2):a[int(k*1.5*p):int(k*1.5*p+10)]*=0.75
save('roof_clear',a,(3.0,3.0))
# Precast concrete facade panels 3 m x 1.5 m with joints; two tones.
def panels(name,col,pu=3.0,pv=1.5):
    a=flat(col,3,8);xu=N/6.0;
    for k in range(3):a[:,int(k*pu*xu):int(k*pu*xu)+3]*=0.72
    for k in range(5):a[int(k*pv*xu):int(k*pv*xu)+3]*=0.72
    save(name,a,(6.0,6.0))
panels('conc_light',(204,200,190));panels('conc_beige',(196,184,160));panels('conc_grey',(150,152,152))
# Glazing band: dark blue-grey glass, mullions every 1.5 m, transom every 1.6 m.
a=flat((52,66,82),2,6);p=N/3.0
v=np.linspace(0,1,N)[:,None,None];a=a*(0.85+0.3*v)
for k in range(2):a[:,int(k*1.5*p):int(k*1.5*p)+8]=(150,156,160)
for k in range(2):a[int(k*1.6*p):int(k*1.6*p)+8]=(150,156,160)
save('glass',a,(3.0,3.2))
# Steel: painted white towers, MCG blue roof trusses, galvanised grey, black screen.
for nm,col in (('steel_white',(234,236,234)),('steel_blue',(54,104,170)),('steel_galv',(156,160,164)),('steel_dark',(62,66,72)),('screen',(18,20,24)),('paint_white',(238,238,234))):
    save(nm,flat(col,2,4),(2.0,2.0))
# Light tower head: frame of 4 x 8 lamps, white frame, grey lamp faces with a bright rim.
a=np.ones((N,N,3))*np.array((236,236,232),float);cu,cv=N/8,N/4
for i in range(8):
    for j in range(4):
        x0,y0=int(i*cu+8),int(j*cv+10);x1,y1=int((i+1)*cu-8),int((j+1)*cv-10)
        a[y0:y1,x0:x1]=(176,182,186);a[y0+6:y1-6,x0+6:x1-6]=(92,98,104)
save('lamps',a,(1,1))
# Paving: light concourse concrete, 1.2 m saw joints; asphalt; grass.
a=flat((196,192,184),5,10);p=N/2.4
for k in range(2):a[int(k*1.2*p):int(k*1.2*p)+2]*=0.78;a[:,int(k*1.2*p):int(k*1.2*p)+2]*=0.78
save('paving',a,(2.4,2.4))
save('asphalt',flat((76,78,80),8,8),(3,3))
g=np.ones((N,N,3))*np.array((96,132,62),float)+noise(N,40,22)[:,:,None]*np.array((0.8,1,0.5))+R.normal(0,10,(N,N,1))*np.array((0.7,1,0.4));save('grass',g,(4,4))
# Arena fence: white pickets on a green-capped rail (MCG boundary), drawn with alpha in RGB only (solid fence panels).
a=np.ones((N,N,3))*np.array((236,236,232),float);a[:int(N*0.08)]=(40,90,60);a[int(N*0.93):]=(120,124,120);save('fence',a,(2.0,1.2))
# Tier fascias and roof edge fascias: white metal cladding, panel joints every 2 m.
for nm,col in (('fascia',(232,234,232)),('roof_fascia',(226,230,232))):
    a=flat(col,2,4);xu=N/4.0
    for k in range(2):a[:,int(k*2*xu):int(k*2*xu)+3]*=0.8
    save(nm,a,(4.0,4.0))
# Northern Stand inner roof band: teal-tinted translucent sheeting with purlins every 1.5 m and ribs.
x=np.arange(N)/N*10;rib=np.where((x%1)<0.12,0.9,1.0)
a=np.ones((N,N,3))*np.array((167,197,192),float)*rib[None,:,None]+noise(N,10,5)[:,:,None]+fine(N,1.5)[:,:,None];p3=N/3.0
for k in range(2):a[int(k*1.5*p3):int(k*1.5*p3+8)]*=0.8
save('roof_teal',a,(3.0,3.0))
# Facade cladding, one tile = 6 m along x 3.6 m (one floor). v runs up the wall.
def facade(name,base,f):
    a=flat(base,2,6);pu=N/6.0;pv=N/3.6;f(a,pu,pv);save(name,a,(6.0,3.6))
def _band(a,pu,pv):  # dark glass with a grey spandrel band per floor, mullions every 1.5 m
    a[int(2.4*pv):]=np.array((126,132,138))+fine(N,2)[int(2.4*pv):,:,None]
    for k in range(4):a[:int(2.4*pv),int(k*1.5*pu):int(k*1.5*pu)+5]=(140,146,150)
def _grey(a,pu,pv):  # grey metal cladding with two teal-glass windows per tile
    for k in range(2):
        x0=int((k*3+0.6)*pu);x1=int((k*3+2.4)*pu);a[int(0.9*pv):int(2.6*pv),x0:x1]=(70,112,118);a[int(1.7*pv):int(1.7*pv)+4,x0:x1]=(160,166,168)
        a[int(0.9*pv):int(2.6*pv),x0:x0+4]=(170,174,176);a[int(0.9*pv):int(2.6*pv),x1-4:x1]=(170,174,176)
    for k in range(4):a[:,int(k*1.5*pu):int(k*1.5*pu)+2]*=0.85
def _white(a,pu,pv):  # white precast with a dark window strip per floor and panel joints every 1.5 m
    a[int(1.2*pv):int(2.2*pv)]=np.array((44,52,62))+fine(N,2)[int(1.2*pv):int(2.2*pv),:,None]
    for k in range(4):a[:,int(k*1.5*pu):int(k*1.5*pu)+3]*=0.8
def _blue(a,pu,pv):  # blue-grey curtain wall, mullions 1.5 m, transom per floor
    for k in range(4):a[:,int(k*1.5*pu):int(k*1.5*pu)+5]=(150,160,168)
    a[:6]=(150,160,168);a[int(1.1*pv):int(1.1*pv)+4]=(130,140,150)
facade('fac_band',(48,60,74),_band);facade('fac_grey',(116,122,128),_grey);facade('fac_white',(214,216,212),_white);facade('fac_blue',(76,100,124),_blue)
json.dump(TILE,open(OUT+'tiles.json','w'),indent=0);print(sorted(TILE))
