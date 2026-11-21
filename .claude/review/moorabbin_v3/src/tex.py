# Hand-made procedural textures: no photo pixels. Each tile covers a stated real size (metres); 256 px per metre max.
import numpy as np,json
from PIL import Image,ImageDraw,ImageFilter,ImageFont
rng=np.random.default_rng(7);OUT='hand/';TILES={}
def save(n,a,wm,hm):
    Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(OUT+n+'.png');TILES[n]=(wm,hm)
def noise(h,w,scale,amp):
    # smooth value noise, tileable via wrap
    g=rng.standard_normal((max(2,h//scale),max(2,w//scale)))
    im=Image.fromarray(((g-g.min())/(np.ptp(g)+1e-9)*255).astype(np.uint8)).resize((w,h),Image.BICUBIC)
    return (np.array(im,float)/255-0.5)*2*amp
def base(h,w,c,amp_fine=6,amp_soft=8):
    a=np.zeros((h,w,3))+np.array(c,float)
    n=noise(h,w,max(4,w//24),amp_soft)[...,None]+rng.normal(0,amp_fine,(h,w,1))
    return a+n
# concrete (clean, light, faint form joints every 1.4 m): tile 1.4 x 1.4 m
h=w=358;a=base(h,w,(180,176,165),4,6);a[:,:2]-=18;save('concrete',a,1.4,1.4)
# painted white render / fascia: tile 2 x 2 m
a=base(512,512,(226,228,226),2,3);save('white',a,2,2)
# rear wall dark render: tile 2 x 2 m
a=base(512,512,(52,56,62),3,4);save('darkwall',a,2,2)
# roof top: profiled steel deck, ribs every 0.19 m (5 ribs per 0.95 m sheet), grey-green from the aerial
w=243;h=256;a=base(h,w,(118,125,114),2,3)
for k in range(5):
    x=int(k*w/5);a[:,x:x+5]+=26;a[:,x+5:x+8]-=22
save('roof_deck',a,0.95,1.0)
# roof underside: dark painted steel deck, same rib pitch
a=base(h,w,(32,31,35),2,2)
for k in range(5):
    x=int(k*w/5);a[:,x:x+5]+=10;a[:,x+5:x+8]-=8
save('roof_under',a,0.95,1.0)
# benches: three painted green timber slats along the bench, 6 mm gaps, tile 1 m x 0.4 m
w=256;h=103;a=base(h,w,(66,104,92),3,4)
for k in range(1,3):y=int(k*h/3);a[y-1:y+1]=(24,38,36)
a[:2]=a[:2]*0.75;a[-2:]=a[-2:]*0.75
save('bench',a,1.0,0.4)
# glazed rear rooms: dark glass with white door panels every 5.6 m bay (door 1.2 m wide), mullions every 1.4 m; tile 5.6 x 3.1 m
w=1434;h=794;a=base(h,w,(38,44,56),2,3)
gl=np.linspace(0,1,h)[:,None,None];a=a+gl*18
for k in range(4):x=int(k*w/4);a[:,x:x+8]=(28,30,34)
x0=int(w*0.5-1.2*256/2);a[int(h*0.25):,x0:x0+307]=(222,224,222);a[int(h*0.25):int(h*0.25)+6,x0:x0+307]=(150,150,150)
a[:10]=(28,30,34);save('rear_rooms',a,5.6,3.1)
# grass, mowing stripes are geometry-scale: tile 10 x 10 m, crisp blade noise
w=h=512;a=base(h,w,(110,150,78),9,10)
a+=rng.normal(0,7,(h,w,1))*np.array([0.6,1,0.4]);save('grass',a,10,10)
# terrace: concrete step tread with grass strip along its back (0.375 m riser, 0.6 m tread), tile 1 x 0.6 m
w=256;h=154;a=base(h,w,(180,176,165),4,5);g=base(h,w,(112,140,80),8,8);a[int(h*0.72):]=g[int(h*0.72):];a[:3]-=25;save('terrace',a,1.0,0.6)
# brick (Heritage Museum), stretcher bond 230x76 mm + 10 mm joints; tile 0.96 x 0.688 m (4 x 8 courses)
w=246;h=176;a=np.zeros((h,w,3))+(205,200,192)
bw=w/4;bh=h/8
for r in range(8):
    off=(r%2)*bw/2
    for c in range(-1,5):
        x0=int(c*bw+off)+1;y0=int(r*bh)+1;col=np.array((150,92,72))*(0.9+0.2*rng.random())
        a[y0:int(y0+bh)-2,max(0,x0):min(w,int(x0+bw)-2)]=col
a+=rng.normal(0,4,(h,w,1));save('brick',a,0.96,0.688)
# Huggins blue plastic seats: one seat 0.5 m wide per row, tile 0.5 x 0.8 m
w=128;h=205;a=base(h,w,(80,96,128),3,3);a[:,:6]=(40,46,58);a[:,-6:]=(40,46,58);a[int(h*.55):]=base(h,w,(180,176,165),4,4)[int(h*.55):];save('blue_seat',a,0.5,0.8)
a=base(h,w,(70,108,92),3,3);a[:,:6]=(30,46,40);a[:,-6:]=(30,46,40);a[int(h*.55):]=base(h,w,(180,176,165),4,4)[int(h*.55):];save('green_seat',a,0.5,0.8)
# dark brown roof sheeting (Huggins), ribs 0.19 m
w=243;h=256;a=base(h,w,(70,62,54),2,3)
for k in range(5):x=int(k*w/5);a[:,x:x+5]+=18;a[:,x+5:x+8]-=16
save('brown_roof',a,0.95,1.0)
# galvanised steel (light towers, posts)
a=base(256,256,(196,198,200),3,5);save('steel',a,1,1)
json.dump(TILES,open(OUT+'tiles.json','w'),indent=0)
print(sorted(TILES))
