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
# Seat rows (copied from GE f180 / n_w): one tile = 12 m along the tier x 3.2 m up the rake (4 rows of 0.8 m).
# A 1.0 m concrete aisle stair at u 0-1.0 (step nosing every 0.4 m), then 21 plastic seats at 0.524 m pitch.
# Each row from the front: narrow concrete tread, seat pan, backrest, dark riser shadow. v = 0 is the row front.
def seats(name,col,tread=(78,84,92)):
    # one 12 m tile of seat rows, no aisle: the aisles are their own radial strips in the model (mcg.json aisles)
    W,Hh=2048,1024;pu=W/12.0;pv=Hh/3.2;c0=np.array(col,float);sw=12.0/23
    a=np.ones((Hh,W,3))*np.array(tread,float)
    Y=lambda v:Hh-int(round(v*pv))  # image row of v metres (v up the rake; image row 0 = top of tile)
    for r in range(4):
        v0=r*0.8
        for k in range(23):
            u0=k*sw;c=c0*(1+R.normal(0,0.025));x0,x1=int((u0+0.03)*pu),int((u0+sw-0.03)*pu)
            a[Y(v0+0.42):Y(v0+0.14),x0:x1]=c            # seat pan
            a[Y(v0+0.74):Y(v0+0.42),x0:x1]=c*0.86       # backrest
            a[Y(v0+0.44):Y(v0+0.40),x0:x1]=c*0.7        # pan/back crease
        a[Y(v0+0.8):Y(v0+0.75),:]=np.array(tread)*0.6   # riser shadow under the next row
    a+=R.normal(0,2.0,(Hh,W,1));save(name,a,(12.0,3.2))
def seat3(name,col):save(name,flat(col,1,2),(1.0,1.0))
def steps(name,col=(150,152,152)):
    # aisle stair, 1.2 m wide: concrete treads, dark nosing every 0.4 m up the rake (the handrail is a 3D bar, build.py)
    W,Hh=256,1024;pu=W/1.2;pv=Hh/3.2;a=np.ones((Hh,W,3))*np.array(col,float)
    for k in range(8):
        y=Hh-int(round(k*0.4*pv));a[max(0,y-int(0.05*pv)):y]=np.array(col)*0.66;a[max(0,y-int(0.4*pv)):max(0,y-int(0.3*pv))]*=0.93
    a[:,:3]*=0.8;a[:,-3:]*=0.8
    a+=R.normal(0,2.5,(Hh,W,1));save(name,a,(1.2,3.2))
steps('aisle_dark',(84,90,98));steps('aisle_light',(176,178,174))
seat3('seat_navy',(18,80,124));seat3('seat_slate',(70,100,125));seat3('seat_steel',(112,124,134));seat3('seat_grey',(158,158,150))
# 3D seats (build.py seats3d) wear a plain moulded-plastic colour; the rows they sit on are concrete steps.
save('tread_dark',flat((92,96,102),2,4),(2.0,2.0));save('tread_dark_riser',flat((70,74,80),2,4),(2.0,2.0))
save('tread_light',flat((196,198,192),2,3),(2.0,2.0));save('tread_light_riser',flat((168,170,166),2,3),(2.0,2.0))
# MCC sector (290-8 deg): mossy teal-green seats (director 2026-11-19) on grey concrete rows: the gaps between seats read
# dark in photo s02 (69,110,102); only the aisle stairs and landings are white
seat3('seat_moss',(112,152,142))  # hue of the CC0 close photo (146,184,176), at model exposure
# backrests: 0.86 of each seat colour, as the painted seat tile had (build.py seats3d)
for _n,_c in (('seat_navy',(18,80,124)),('seat_slate',(70,100,125)),('seat_steel',(112,124,134)),('seat_grey',(158,158,150)),('seat_moss',(112,152,142))):seat3(_n+'_back',tuple(int(v*0.86) for v in _c));seat3(_n+'_under',tuple(int(v*0.6) for v in _c))
# Tier fronts: the walkway wall and the fascia below each tier lip read dark in every photo (shaded, black LED ribbon).
save('tier_wall',flat((86,90,96),2,4),(2.0,2.0));save('tier_fascia',flat((44,48,54),2,3),(2.0,2.0))
# MCC sector tier fronts (commons MCC 050425.jpg, CC0): white concrete band, black glass rail along its top, posts every 2 m; painted clean, not weathered (the photo's bands are clean white).
def fascia_mcc():
    a=flat((224,226,222),2,4);pv=N/3.0;pu=N/2.0;t=int(1.0*pv)
    a[:t]=flat((26,28,31),2,3)[:t];a[:int(0.06*pv)]=(60,62,66);a[t-int(0.04*pv):t]=(70,72,74)
    for x in (0,N-int(0.05*pu)):a[:t,x:x+int(0.05*pu)]=(14,15,17)
    a[t:t+int(0.05*pv)]*=0.8;save('fascia_mcc',a,(2.0,3.0))
fascia_mcc()
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
a=flat((44,54,66),2,6);p=N/3.0
v=np.linspace(0,1,N)[:,None,None];a=a*(0.85+0.3*v)
for k in range(2):a[:,int(k*1.5*p):int(k*1.5*p)+8]=(150,156,160)
for k in range(2):a[int(k*1.6*p):int(k*1.6*p)+8]=(150,156,160)
save('glass',a,(3.0,3.2))
# Steel: painted white towers, MCG blue roof trusses, galvanised grey, black screen.
for nm,col in (('steel_white',(234,236,234)),('steel_blue',(92,118,140)),('steel_galv',(156,160,164)),('steel_dark',(62,66,72)),('screen',(18,20,24)),('paint_white',(238,238,234))):
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
    a[int(1.4*pv):]=np.array((198,200,198))+fine(N,2)[int(1.4*pv):,:,None]  # pale concrete spandrel, 1.4 m dark glass per floor
    for k in range(4):a[:int(1.4*pv),int(k*1.5*pu):int(k*1.5*pu)+5]=(190,194,196)
def _grey(a,pu,pv):  # grey metal cladding with two teal-glass windows per tile
    for k in range(2):
        x0=int((k*3+0.6)*pu);x1=int((k*3+2.4)*pu);a[int(0.9*pv):int(2.6*pv),x0:x1]=(46,60,68);a[int(1.7*pv):int(1.7*pv)+4,x0:x1]=(160,166,168)
        a[int(0.9*pv):int(2.6*pv),x0:x0+4]=(170,174,176);a[int(0.9*pv):int(2.6*pv),x1-4:x1]=(170,174,176)
    for k in range(4):a[:,int(k*1.5*pu):int(k*1.5*pu)+2]*=0.85
def _white(a,pu,pv):  # white precast with a dark window strip per floor and panel joints every 1.5 m
    a[int(1.2*pv):int(2.2*pv)]=np.array((44,52,62))+fine(N,2)[int(1.2*pv):int(2.2*pv),:,None]
    for k in range(4):a[:,int(k*1.5*pu):int(k*1.5*pu)+3]*=0.8
def _blue(a,pu,pv):  # screen back (GE f045, f225): dark slate cladding, vertical seams every 1.5 m
    for k in range(4):a[:,int(k*1.5*pu):int(k*1.5*pu)+4]*=0.78
facade('fac_band',(44,54,66),_band);facade('fac_grey',(196,198,198),_grey);facade('fac_white',(214,216,212),_white);facade('fac_blue',(62,68,76),_blue)
json.dump(TILE,open(OUT+'tiles.json','w'),indent=0);print(sorted(TILE))
