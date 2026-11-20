# Hand-made procedural textures (no photo pixels). Each texture's real-world size is in SIZES (metres, u x v).
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
rng=np.random.default_rng(7)
SIZES={}
def save(name,a,size):
    Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(f'tex/{name}.png');SIZES[name]=size
def noise(h,w,s,amp):
    n=rng.normal(0,1,(max(2,h//s),max(2,w//s)));n=np.array(Image.fromarray(n.astype(np.float32)).resize((w,h),Image.BICUBIC));return n*amp
# corrugated iron, ribs run along v (down the slope); 2.0 m across x 3.0 m along slope
def iron(name,col,W=1024,H=1536,mu=2.0,mv=3.0):
    x=np.arange(W)*mu/W;ph=np.sin(2*np.pi*x/0.0762)
    shade=1.0+0.13*ph[None,:]
    a=np.ones((H,W,3))*np.array(col)[None,None,:]*shade[...,None]
    a+=noise(H,W,64,5)[...,None]
    lap=(np.arange(H)%int(H*2.4/mv)<3)            # sheet lap every 2.4 m
    a[lap]*=0.85
    for k in range(0,W,int(W*0.0762*4/mu)):a[:,k:k+1]*=0.92   # screw lines on every 4th rib
    save(name,a,(mu,mv))
iron('roof_iron',(86,51,58))   # Ryde/Lewis roofs: roof_gor x (aerial Ryde roof / aerial Gorringe roof) = (0.83,0.78,0.82); was (158,52,46) bright red (gate 2026-11-19)
iron('roof_gor',(103,65,71))   # Gorringe roof: fitted so the render's median matches the photo crop's median, sky 1.1 (gate 2026-11-19)
# brick, stretcher bond 230x76 + 10 mm mortar, one bay 5.6 m wide x 3.0 m high
def brick(name,base,W=2048,H=1100,mu=5.6,mv=3.0):
    a=np.zeros((H,W,3));px=W/mu
    mort=np.array([196,186,168])
    a[:]=mort
    bh,bl,jt=0.076,0.230,0.010
    rows=int(mv/(bh+jt))+1
    for r in range(rows):
        y0=int(H-(r+1)*(bh+jt)*px);y1=int(y0+bh*px)
        off=(bl+jt)/2*(r%2)
        x=-off
        while x<mu:
            x0=int(x*px);x1=int((x+bl)*px)
            c=np.array(base)*(1+rng.normal(0,0.07))+rng.normal(0,6,3)
            a[max(0,y0):max(0,y1),max(0,x0):max(0,x1)]=c
            x+=bl+jt
    a+=noise(H,W,6,6)[...,None]
    save(name,a,(mu,mv))
brick('brick',(150,91,83))   # fitted so the render's median matches the photo crop's median (gate 2026-11-19), gorringe se_end (was 150,66,52)
def render(name,col,mu=4.0,mv=4.0,W=1024,H=1024,grime=True):
    a=np.ones((H,W,3))*np.array(col)+noise(H,W,32,4)[...,None]+noise(H,W,4,2.5)[...,None]
    if grime:a*=(0.93+0.07*np.linspace(0,1,H))[:,None,None][::-1]*0+1
    save(name,a,(mu,mv))
render('render_cream',(238,218,180))   # fitted so the render's median matches the photo crop's median (gate 2026-11-19), entrance pilaster (was 226,211,172)
render('ceiling',(214,204,178))
render('interior_dark',(46,42,40))
render('concrete',(176,172,164))
# painted steel/timber posts (maroon), 0.3 x 3 m
render('post_maroon',(122,38,48),0.6,3.0,256,1024)
render('fascia',(122,38,48),2.0,0.5,1024,256)
render('trim_white',(238,234,222),2.0,0.5,1024,256)
# gable pediment: cream boards with vertical battens every 0.45 m, 4 m x 3 m
def pediment():
    W,H=1024,768;mu,mv=4.0,3.0;a=np.ones((H,W,3))*np.array((226,211,172))+noise(H,W,16,3)[...,None]
    for k in range(0,W,int(W*0.45/mu)):a[:,k:k+6]=np.array((240,236,224))
    save('pediment',a,(mu,mv))
pediment()
# seat rows: one row 0.8 m tread x 0.3 m riser; texture covers 4 m wide x 1 row (u along row, v up the step profile)
def seats():
    # moulded plastic shells on real 3D seats (gate 3): plain light teal with faint moulding mottle
    W,H=256,256
    a=np.ones((H,W,3))*np.array((103,144,146))+noise(H,W,16,3)[...,None]   # seat back: fitted to the photo crop median (gate 2026-11-19) (was 52,104,84)
    save('seats',a,(0.5,0.5))
    a=np.ones((H,W,3))*np.array((86,122,122))+noise(H,W,16,3)[...,None]    # seat pan (was 40,84,68)
    save('seat_pan',a,(0.5,0.5))
seats()
# clock face
im=Image.new('RGB',(512,512),(226,211,172));d=ImageDraw.Draw(im);d.ellipse((40,40,472,472),fill=(30,30,30));d.ellipse((60,60,452,452),fill=(245,243,236))
import math
for k in range(12):
    t=k/12*2*math.pi;d.line((256+170*math.sin(t),256-170*math.cos(t),256+190*math.sin(t),256-190*math.cos(t)),fill=(20,20,20),width=10)
d.line((256,256,256+100*math.sin(1.2),256-100*math.cos(1.2)),fill=(20,20,20),width=12);d.line((256,256,256+150*math.sin(5.9),256-150*math.cos(5.9)),fill=(20,20,20),width=8)
im.save('tex/clock.png');SIZES['clock']=(1.6,1.6)
import json;json.dump(SIZES,open('tex/sizes.json','w'))
print(SIZES)
