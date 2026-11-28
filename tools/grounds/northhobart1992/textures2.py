# More hand-made procedural textures (no photo pixels) for the rest of the ground. Adds to tex/sizes.json.
import numpy as np,json,math
from PIL import Image,ImageDraw
rng=np.random.default_rng(11)
SIZES=json.load(open('tex/sizes.json'))
def save(name,a,size):
    Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(f'tex/{name}.png');SIZES[name]=list(size)
def noise(h,w,s,amp):
    n=rng.normal(0,1,(max(2,h//s),max(2,w//s)));n=np.array(Image.fromarray(n.astype(np.float32)).resize((w,h),Image.BICUBIC));return n*amp
def iron(name,col,W=1024,H=1536,mu=2.0,mv=3.0):
    x=np.arange(W)*mu/W;ph=np.sin(2*np.pi*x/0.0762)
    a=np.ones((H,W,3))*np.array(col)[None,None,:]*(1.0+0.10*ph[None,:])[...,None]
    a+=noise(H,W,64,4)[...,None]
    a[(np.arange(H)%int(H*2.4/mv)<3)]*=0.88
    save(name,a,(mu,mv))
iron('roof_white',(232,232,224))
# translucent skylight sheeting (pale green-white), same corrugation
iron('roof_clear',(206,222,196))
def flat(name,col,mu=4.0,mv=4.0,W=1024,H=1024,f=4,a1=3.0,a2=2.0):
    a=np.ones((H,W,3))*np.array(col)+noise(H,W,32,a1)[...,None]+noise(H,W,f,a2)[...,None];save(name,a,(mu,mv))
flat('steel_dark',(70,72,76))
flat('pole_grey',(150,152,154),0.6,3.0,256,1024)
flat('sb_black',(22,22,24))
flat('sb_red',(178,34,36),2.0,2.0,512,512)
# grey steel cladding, vertical ribs every 0.2 m
def cladding():
    W,H=1024,1024;mu,mv=4.0,4.0;x=np.arange(W)*mu/W
    a=np.ones((H,W,3))*np.array((112,114,116))*(1+0.06*np.sign(np.sin(2*np.pi*x/0.2)))[None,:,None]+noise(H,W,16,3)[...,None];save('cladding_grey',a,(mu,mv))
cladding()
# turf: mown stripes 2.5 m wide (5 m period, measured off the aerial), fine blade noise. u across the stripes.
def grass():
    W,H=1000,1000;mu,mv=10.0,10.0;x=np.arange(W)*mu/W
    st=np.where((x%5.0)<2.5,1.05,0.95)
    base=np.array((70,122,46))
    a=np.ones((H,W,3))*base*st[None,:,None]
    a+=noise(H,W,2,7)[...,None]*np.array((0.6,1.0,0.5))+noise(H,W,50,5)[...,None]
    save('grass',a,(mu,mv))
grass()
def asphalt():
    W,H=1024,1024;a=np.ones((H,W,3))*np.array((84,84,82))+noise(H,W,2,9)[...,None]+noise(H,W,64,5)[...,None]
    spk=rng.random((H,W))>0.985;a[spk]+=35;save('asphalt',a,(6.0,6.0))
asphalt()
# terrace tread: concrete with a darker worn front edge strip
def tread():
    W,H=1024,256;mu,mv=4.0,1.0;a=np.ones((H,W,3))*np.array((168,164,156))+noise(H,W,8,5)[...,None]+noise(H,W,2,3)[...,None]
    a[:int(H*0.06)]*=0.78;save('tread',a,(mu,mv))
tread()
# painted timber bench planks (grey-white), planks 0.1 m with dark gaps, 4 m long x 0.45 m (seat + front)
def bench():
    W,H=1024,128;mu,mv=4.0,0.45;a=np.ones((H,W,3))*np.array((214,214,206))+noise(H,W,8,4)[...,None]
    for k in range(0,H,int(H*0.1/mv)):a[k:k+3]=np.array((90,90,88))
    save('bench',a,(mu,mv))
bench()
# white timber picket/paling fence boards 0.15 m, 1 m high
def fence():
    W,H=1024,256;mu,mv=4.0,1.0;a=np.ones((H,W,3))*np.array((236,236,230))+noise(H,W,8,3)[...,None]
    for k in range(0,W,int(W*0.15/mu)):a[:,k:k+3]=np.array((180,180,176))
    a[int(H*0.12):int(H*0.16)]*=0.85;a[int(H*0.8):int(H*0.84)]*=0.85;save('fence_white',a,(mu,mv))
fence()
# eucalypt / street-tree foliage: clumped leaf masses, dark and mid greens; bark
def foliage():
    W,H=1024,1024;a=np.zeros((H,W,3))+np.array((40,70,36))
    im=Image.fromarray(a.astype(np.uint8));d=ImageDraw.Draw(im)
    for _ in range(5000):
        x,y=rng.integers(0,W),rng.integers(0,H);r=rng.integers(4,14);g=rng.uniform(0.7,1.35)
        c=tuple(int(v*g) for v in (58,96,46));d.ellipse((x-r,y-r//2,x+r,y+r//2),fill=c)
    a=np.asarray(im).astype(float)+noise(H,W,64,8)[...,None];save('foliage',a,(3.0,3.0))
foliage()
def bark():
    W,H=256,1024;a=np.ones((H,W,3))*np.array((96,82,66))+noise(H,W,6,10)[...,None]*np.array((1,0.9,0.8));save('bark',a,(1.0,3.0))
bark()
# scoreboard face, layout read from the 1990 photo of this board (w_northhobart1990*.jpg); hand-drawn, no lettering.
# Whole face 3.4..12.8 m high, 9.54 m wide (front edge from the aerial), UV-fitted to one quad.
def sbface():
    mu,mv=9.54,9.4;px=110;W,H=int(mu*px),int(mv*px);a=np.ones((H,W,3))*np.array((58,60,62))+noise(H,W,16,3)[...,None]
    Y=lambda z:int((12.8-z)*px);X=lambda f:int(f*W)
    def box(f0,f1,z0,z1,c):a[Y(z1):Y(z0),X(f0):X(f1)]=np.array(c)
    box(0,1,9.8,12.8,(250,250,246));box(0.015,0.985,9.85,12.75,(184,30,34))        # red top board, white frame
    box(0.80,0.975,10.0,12.6,(248,248,244))                                          # clock panel (right)
    cy,cx,r=(Y(11.3)),X(0.8875),int(1.05*px);yy,xx=np.mgrid[:H,:W];d=np.hypot(yy-cy,xx-cx)
    a[d<r]=(30,30,34);a[d<r*0.86]=(236,236,230);a[d<r*0.08]=(20,20,20)
    for k in range(12):
        t=k*np.pi/6;m=(np.abs(d-r*0.76)<r*0.06)&(np.abs(np.arctan2(yy-cy,xx-cx)-t+np.pi)%(2*np.pi)-np.pi<0.06*np.pi/1)
        a[m&(np.abs(((np.arctan2(yy-cy,xx-cx)-t)+np.pi)%(2*np.pi)-np.pi)<0.07)]=(20,20,20)
    for ang,ln in((-1.2,0.45),(0.4,0.68)):
        for t_ in np.linspace(0,ln*r,200):a[int(cy-np.cos(ang)*t_)-3:int(cy-np.cos(ang)*t_)+3,int(cx+np.sin(ang)*t_)-3:int(cx+np.sin(ang)*t_)+3]=(20,20,20)
    box(0,1,6.2,9.8,(22,26,30))                                                      # dark score board
    for z0 in(8.85,7.9):                                                             # two team rows
        box(0.04,0.22,z0,z0+0.8,(34,40,48));box(0.045,0.215,z0+0.03,z0+0.77,(28,32,38))   # team-name block (blank)
        x=0.27
        for g in(2,2,3):
            box(x-0.012,x+g*0.075+0.004,z0-0.03,z0+0.83,(40,44,50))
            for k in range(g):
                f0=x+k*0.075;box(f0,f0+0.062,z0+0.04,z0+0.76,(46,46,46))
                for (u0,u1,v0,v1) in((0.15,0.85,0.88,0.94),(0.15,0.85,0.47,0.53),(0.15,0.85,0.06,0.12),(0.1,0.18,0.5,0.9),(0.82,0.9,0.5,0.9),(0.1,0.18,0.1,0.5),(0.82,0.9,0.1,0.5)):
                    box(f0+u0*0.062,f0+u1*0.062,z0+0.04+v0*0.72,z0+0.04+v1*0.72,(62,60,56))   # unlit 7-segment digit
            x+=g*0.075+0.05
    box(0.18,0.82,7.12,7.75,(236,200,58))                                            # yellow league strip (blank)
    for f0 in(0.05,0.12,0.40,0.47,0.62,0.69,0.76):box(f0,f0+0.055,6.32,6.98,(46,46,46)) # small third row
    for f0 in(0.56,0.76):box(f0,f0+0.16,4.4,5.2,(26,28,30));box(f0+0.005,f0+0.155,4.42,4.55,(90,92,94))   # lower windows
    box(0,1,6.14,6.2,(120,122,124))
    save('sb_face',a,(mu,mv))
sbface()
json.dump(SIZES,open('tex/sizes.json','w'));print(sorted(SIZES))

# Ryde St field slope with the bank's name, hand-painted: word positions read off aerial 1182_185 (fractions of the
# straight part of the slope between the hips, u left->right, v eave->ridge). Option C for the director only.
def roof_nab():
    from PIL import ImageFont
    W,H=4096,660;x=np.arange(W)*26.1/W;a=np.ones((H,W,3))*np.array((232,232,224))
    a*= (1.0+0.06*np.sin(2*np.pi*x/0.0762))[None,:,None];a+=noise(H,W,64,3)[...,None]
    im=Image.fromarray(np.clip(a,0,255).astype(np.uint8));d=ImageDraw.Draw(im)
    fn=ImageFont.truetype('arialbd.ttf',400);navy=(38,42,84)
    V=lambda v:int(H*(1-v))
    for word,u0,u1 in(('National',0.0,0.314),('Australia',0.353,0.673),('Bank',0.827,0.995)):
        bb=d.textbbox((0,0),word,font=fn);tw,th=bb[2]-bb[0],bb[3]-bb[1]
        g=Image.new('L',(tw,th),0);ImageDraw.Draw(g).text((-bb[0],-bb[1]),word,font=fn,fill=255)
        bw,bh=int((u1-u0)*W),V(0.435)-V(0.72);g=g.resize((bw,bh),Image.LANCZOS)
        im.paste(Image.new('RGB',(bw,bh),navy),(int(u0*W),V(0.72)),g)
    cx,cy,R=int(0.75*W),(V(0.435)+V(0.72))//2,int(0.55*(V(0.435)-V(0.72)))
    pts=[(cx+(R if k%2==0 else R*0.42)*math.sin(k*math.pi/5),cy-(R if k%2==0 else R*0.42)*math.cos(k*math.pi/5)) for k in range(10)]
    d.polygon(pts,fill=(204,36,44))
    save('roof_nab',np.asarray(im).astype(float),(26.1,4.2))
roof_nab()
json.dump(SIZES,open('tex/sizes.json','w'))

# glazed end screen of the Cazaly stand (1965 and 2009 photos): pale grey-blue panes, dark mullions every 1.5 m
def glass_screen():
    W=H=768;a=np.ones((H,W,3))*np.array((62,70,80))   # dark like the Gorringe deck glass in the photo (gate 2026-11-19; was 150,166,178);a+=np.linspace(14,-14,H)[:,None,None];a+=noise(H,W,48,3)[...,None]
    m=int(0.08*W/3.0)
    for k in range(2):s=k*W//2;a[:,s:s+m]=(60,64,68);a[s:s+m,:]=(60,64,68)
    save('glass_screen',a,(3.0,3.0))
glass_screen()
json.dump(SIZES,open('tex/sizes.json','w'))

# boundary hoardings, colours read from the 1990 photo (web/w_northhobart1990.jpg); plain until the lettering decision
HOARD={'hoard_white':(236,234,228),'hoard_red':(190,30,38),'hoard_blue':(40,70,150),'hoard_navy':(28,36,70),'hoard_redwhite':(200,40,50)}
def hoard(name,col):
    W,H=600,100;a=np.ones((H,W,3))*np.array(col,float)+noise(H,W,24,2)[...,None]
    if name=='hoard_redwhite':
        for k in range(3):s=int(W*(0.08+k*0.32));a[18:82,s:s+int(W*0.2)]=(244,242,238)
    a[:4]=a[-4:]=(120,120,120);a[:,:3]=a[:,-3:]=(120,120,120)
    save(name,a,(6.0,1.0))
for n,c in HOARD.items():hoard(n,c)
# club sign over the Gorringe entrance (hr_gor): red board, cream rim. Lettering and badge removed:
# director 2026-11-18 "C: no lettering" (every sign a blank panel)
def club_sign():
    W,H=2300,275;im=Image.new('RGB',(W,H),(176,30,36));d=ImageDraw.Draw(im)
    d.rectangle((0,0,W-1,H-1),outline=(236,226,196),width=14)
    save('club_sign',np.array(im,float),(4.6,0.55))
club_sign()
json.dump(SIZES,open('tex/sizes.json','w'))
