# Hand-made tiling textures (no photo pixels): each map is drawn from measured module sizes, at real scale.
# TILE[name] = metres covered by one texture repeat (u,v). Colours read by eye from the 2019 aerial / 2024 photos.
import numpy as np,json
from PIL import Image
R=np.random.default_rng(7);N=1024
def base(c,var=0.012,n=N):
    a=np.ones((n,n,3))*np.array(c)
    # soft large-scale mottling (weathering), tiling: sum of whole-period sines
    y,x=np.mgrid[0:n,0:n]/n*2*np.pi
    m=sum(np.sin(k1*x+R.uniform(0,6))*np.sin(k2*y+R.uniform(0,6))/(k1+k2) for k1,k2 in((1,2),(2,1),(3,2),(2,3),(5,4)))
    return a*(1+var*4*m[...,None])+R.normal(0,var,(n,n,1))
def hline(a,y,w,c,alpha=1.0):a[int(y):int(y)+max(1,int(w))]=a[int(y):int(y)+max(1,int(w))]*(1-alpha)+np.array(c)*alpha
def vline(a,x,w,c,alpha=1.0):a[:,int(x):int(x)+max(1,int(w))]=a[:,int(x):int(x)+max(1,int(w))]*(1-alpha)+np.array(c)*alpha
TILE={};OUT={}
def save(name,a,tile):OUT[name]=np.clip(a,0,1);TILE[name]=tile
# roof deck: off-white standing-seam sheet; seams every 0.6 m along the slope, sheet end laps every 12 m
a=base((0.86,0.87,0.85),0.01);px=N/12
for i in range(20):x=i*0.6*px;vline(a,x,2,(0.70,0.71,0.70));vline(a,x+2,1,(0.95,0.95,0.94))
hline(a,0,3,(0.66,0.67,0.66));save('deck',a,(12,12))
# end roofs: dark ribbed sheet, ribs every 0.6 m with light crest
a=base((0.30,0.32,0.34),0.012);px=N/12
for i in range(20):x=i*0.6*px;vline(a,x,6,(0.40,0.42,0.44));vline(a,x+2,2,(0.52,0.54,0.56));vline(a,x+7,3,(0.22,0.23,0.25))
save('ribs',a,(12,12))
# gutter: yellow-brown, joints every 6 m
a=base((0.66,0.53,0.30),0.01);vline(a,0,3,(0.45,0.36,0.20));vline(a,N/2,3,(0.45,0.36,0.20));save('gutter',a,(12,2))
# white fascia: joints every 4 m
a=base((0.93,0.93,0.91),0.006)
for i in range(3):vline(a,i*N/3,2,(0.70,0.70,0.70))
hline(a,N-6,6,(0.80,0.80,0.79));save('fascia',a,(12,2))
# soffit: dark grey with purlin lines every 1.5 m
a=base((0.20,0.21,0.23),0.01)
for i in range(8):hline(a,i*N/8,4,(0.13,0.13,0.15))
save('soffit',a,(12,12))
# teal steel (roof trusses, brackets)
a=base((0.33,0.62,0.55),0.008);save('teal',a,(4,4))
# silver aluminium composite cladding: 3.0 x 1.2 m panels, 15 mm dark joints
a=base((0.74,0.76,0.79),0.008);px=N/6
for i in range(2):vline(a,i*3*px,3,(0.30,0.31,0.33))
for j in range(5):hline(a,j*1.2*px,3,(0.30,0.31,0.33))
save('silver',a,(6,6))
# dark glazing: 1.5 m mullions, 3.0 m transoms, sky gradient reflection per pane
a=np.zeros((N,N,3));px=N/6;yy=np.mgrid[0:N,0:N][0]
for j in range(2):
    s=slice(int(j*3*px),int((j+1)*3*px));t=(yy[s]-j*3*px)/(3*px)
    a[s]=(np.array((0.20,0.27,0.34))*(1-t[...,None])+np.array((0.10,0.13,0.17))*t[...,None])
a+=R.normal(0,0.006,(N,N,1))
for i in range(4):vline(a,i*1.5*px,8,(0.22,0.23,0.25))
for j in range(2):hline(a,j*3*px,10,(0.22,0.23,0.25))
save('glass',a,(6,6))
# south 2024 curtain wall: taller blue panes 1.8 x 3.6 m, bright silver mullions
a=np.zeros((N,N,3));px=N/7.2
for j in range(2):
    s=slice(int(j*3.6*px),int((j+1)*3.6*px));t=(yy[s]-j*3.6*px)/(3.6*px)
    a[s]=(np.array((0.42,0.55,0.70))*(1-t[...,None])+np.array((0.20,0.28,0.38))*t[...,None])
a+=R.normal(0,0.006,(N,N,1))
for i in range(4):vline(a,i*1.8*px,7,(0.80,0.82,0.84))
for j in range(2):hline(a,j*3.6*px,9,(0.80,0.82,0.84))
save('curtain',a,(7.2,7.2))
# navy stair-tower cladding: 1.5 x 3 m panels
a=base((0.14,0.18,0.33),0.01);px=N/6
for i in range(4):vline(a,i*1.5*px,3,(0.08,0.10,0.20))
for j in range(2):hline(a,j*3*px,3,(0.08,0.10,0.20))
save('navy',a,(6,6))
# stair mesh glazing: dark steel grid 0.3 m over darker void
a=base((0.08,0.09,0.11),0.01);px=N/6
for i in range(20):vline(a,i*0.3*px,3,(0.30,0.32,0.35));hline(a,i*0.3*px,3,(0.30,0.32,0.35))
save('mesh',a,(6,6))
# ground storey: silver piers every 8 m, dark glazed shopfront bays between
a=np.zeros((N,N,3))+np.array((0.11,0.13,0.16));px=N/8;yy2=yy/N
a=a+((1-yy2)*0.08)[...,None]
vline(a,0,int(0.9*px),(0.76,0.78,0.80))
for i in range(1,5):vline(a,0.9*px+i*1.42*px,4,(0.30,0.31,0.33))
hline(a,0,int(0.12*N),(0.70,0.72,0.74));hline(a,N-10,10,(0.5,0.5,0.5))
save('base',a,(8,6))
# pale concrete paving / podium deck: 1.2 m slabs with dark drainage strip every 6 m
a=base((0.74,0.72,0.68),0.012);px=N/6
for i in range(5):vline(a,i*1.2*px,2,(0.60,0.58,0.55));hline(a,i*1.2*px,2,(0.60,0.58,0.55))
hline(a,0,8,(0.35,0.35,0.36));save('paving',a,(6,6))
# light grey rendered concrete wall, formwork joints 2.4 x 1.2 m
a=base((0.80,0.80,0.78),0.01);px=N/4.8
for i in range(2):vline(a,i*2.4*px,2,(0.66,0.66,0.65))
for j in range(4):hline(a,j*1.2*px,2,(0.66,0.66,0.65))
save('concrete',a,(4.8,4.8))
# white painted steel (round columns, rails)
a=base((0.94,0.94,0.93),0.006);save('white',a,(4,4))
# silver tanks: brushed with horizontal seams every 1.5 m
a=base((0.78,0.80,0.82),0.006);xx=np.mgrid[0:N,0:N][1];a+=0.03*np.sin(xx/N*2*np.pi*40)[...,None]
for j in range(4):hline(a,j*N/4,3,(0.55,0.56,0.58))
save('tank',a,(6,6))
# seating: navy plastic seats in rows 0.8 m deep (riser shadow + seat backs)
a=base((0.16,0.20,0.34),0.01);px=N/8
for j in range(10):y=j*0.8*px;hline(a,y,int(0.18*px),(0.08,0.09,0.14));hline(a,y+0.18*px,int(0.08*px),(0.24,0.29,0.45))
for i in range(16):vline(a,i*0.5*px,2,(0.10,0.12,0.20))
save('seats',a,(8,8))
# shade canopy fabric
a=base((0.95,0.90,0.74),0.008);save('canvas',a,(4,4))
# planter (2024 south facade): low shrubs
a=base((0.20,0.36,0.16),0.03)
for k in range(400):
    cx,cy=R.integers(0,N,2);r=R.integers(10,30);y,x=np.ogrid[-cy:N-cy,-cx:N-cx];m=(x*x+y*y)<r*r
    a[m]=a[m]*0.6+np.array((0.26,0.48,0.20))*0.4*R.uniform(0.7,1.3)
save('plants',a,(4,4))
# sign box faces (no lettering): red panel / black panel
a=base((0.70,0.08,0.10),0.008);save('signred',a,(4,4))
a=base((0.06,0.06,0.07),0.008);save('signblack',a,(4,4))
for k,v in OUT.items():Image.fromarray((v*255).astype(np.uint8)).save('tex/%s.png'%k)
json.dump(TILE,open('tex/tiles.json','w'),indent=0)
print(sorted(TILE))
