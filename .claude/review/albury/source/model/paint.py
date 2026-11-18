# Hand-made textures for Albury Sports Ground, painted in code (no photo pixels).
# Each texture tiles; TILE[name] = metres covered by one tile (u, v), used by the build for UVs.
import numpy as np,json,math
from PIL import Image,ImageDraw,ImageFont,ImageFilter
R=np.random.default_rng(7);N=1024;OUT='model/tex/';TILE={}
def save(name,a,tile):
    Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(OUT+name+'.png');TILE[name]=tile
def noise(n,sc,amp):  # smooth value noise, tileable
    g=R.normal(0,1,(sc,sc));im=Image.fromarray(((g-g.min())/(np.ptp(g))*255).astype(np.uint8)).resize((n,n),Image.BICUBIC)
    a=np.asarray(im,float)/255-0.5;return a*amp
def fine(n,amp):return R.normal(0,amp,(n,n))
# Brick: Albury red face brick, stretcher bond, 230x76 + 10 mm cream-grey mortar. Tile 2.4 m x 1.032 m (12 courses).
def brick(name,base,var,mortar,tile_u=2.4,courses=12):
    H=N//2;a=np.zeros((H,N,3));ch=86/1000;tile_v=courses*ch;px_u=N/tile_u;px_v=H/tile_v
    a[:]=mortar
    for c in range(courses):
        off=0 if c%2==0 else 0.12
        y0=int(c*ch*px_v);y1=int((c*ch+0.076)*px_v)
        x=-off
        while x<tile_u:
            x0=int(round(x*px_u));x1=int(round((x+0.230)*px_u))
            col=np.array(base)*(1+R.normal(0,var))+R.normal(0,6,3)
            for xa,xb in ((x0,x1),):
                xs=np.arange(xa,xb)%N;a[y0:y1][:,xs]=col
            x+=0.240
    a+=fine(N,4)[:H,:,None]*np.array([1,1,1]);a+=noise(N,48,10)[:H,:,None]
    save(name,a,(tile_u,tile_v))
brick('brick_red',(168,72,48),0.07,(196,184,166))
brick('brick_dark',(132,58,42),0.06,(176,166,152))
# Corrugated iron, ~76 mm pitch, ridges along v. Tile 1.52 m (20 ridges) x 1.52 m.
def corr(name,col,tile=1.52,rid=20,streak=6):
    x=np.arange(N)/N*rid*2*math.pi;sh=0.90+0.10*np.cos(x)+0.04*np.cos(2*x);a=np.ones((N,N,3))*np.array(col)*sh[None,:,None]
    a+=noise(N,16,streak)[:,:,None];a+=fine(N,1.5)[:,:,None];save(name,a,(tile,tile))
corr('roof_grey',(150,160,170));corr('roof_tan',(196,170,128));corr('roof_white',(214,218,220));corr('roof_dkgrey',(108,116,124));corr('roof_blue',(92,128,170));corr('gutter_brown',(92,62,46));corr('roof_bluegrey',(122,146,168))
# Flat membrane / steel deck roof (club): broad trapezoidal ribs every 0.35 m.
x=np.arange(N)/N*8;rib=np.where((x%1)<0.12,0.86,1.0);a=np.ones((N,N,3))*np.array((206,210,212))*rib[None,:,None]+noise(N,12,8)[:,:,None]
save('roof_deck',a,(2.8,2.8))
# Painted render / cream trim (Victorian cream), fine sand texture.
for nm,col in (('render_cream',(226,214,184)),('paint_white',(236,236,232)),('render_grey',(186,184,178)),('render_pale',(240,235,220))):
    a=np.ones((N,N,3))*np.array(col)+fine(N,3)[:,:,None]+noise(N,24,5)[:,:,None];save(nm,a,(2.0,2.0))
# Concrete: light grey, fine aggregate, saw joints every 1.5 m.
a=np.ones((N,N,3))*np.array((178,176,170))+fine(N,6)[:,:,None]+noise(N,20,10)[:,:,None]
a[:3]=a[:3]*0.75;a[:,:3]=a[:,:3]*0.75;save('concrete',a,(1.5,1.5))
# Asphalt and grass for the apron (outside the oval fence).
a=np.ones((N,N,3))*np.array((70,72,74))+fine(N,9)[:,:,None]+noise(N,30,8)[:,:,None];save('asphalt',a,(3,3))
g=np.ones((N,N,3))*np.array((92,128,58))+noise(N,40,22)[:,:,None]*np.array((0.8,1,0.5))+R.normal(0,10,(N,N,1))*np.array((0.7,1,0.4))
save('grass',g,(4,4))
# Netball court: green acrylic, red surround.
for nm,col in (('court_green',(70,128,98)),('court_red',(176,62,52))):
    a=np.ones((N,N,3))*np.array(col)+fine(N,3)[:,:,None]+noise(N,16,4)[:,:,None];save(nm,a,(3,3))
# Glass: dark blue-grey with sky gradient; frames painted by geometry.
a=np.zeros((N,N,3));v=np.linspace(0,1,N)[:,None];a[:]=(np.array((96,112,128))*(1-v)+np.array((40,48,58))*v)[:,None,:].reshape(N,1,3) if False else 0
a=np.dstack([np.repeat((96*(1-v)+40*v),N,1),np.repeat((112*(1-v)+48*v),N,1),np.repeat((128*(1-v)+58*v),N,1)]);save('glass',a,(2,2))
# Bench seats (grandstand tiers): grey-blue painted timber slats 90 mm with 15 mm gaps, along u.
H=N;a=np.ones((H,N,3))*np.array((60,62,60));p=H/0.42
for k in range(4):
    y0=int(k*0.105*p);y1=int((k*0.105+0.09)*p);a[y0:y1]=np.array((150,162,170))+fine(N,3)[y0:y1,:,None]
save('seat_slats',a,(2.0,0.42))
# Steel: painted white posts/brackets, galvanised grey rails.
for nm,col in (('steel_white',(232,232,226)),('steel_galv',(160,164,166)),('steel_green',(46,74,58)),('steel_black',(36,38,40))):
    a=np.ones((64,64,3))*np.array(col)+fine(64,2)[:,:,None];Image.fromarray(np.clip(a,0,255).astype(np.uint8)).resize((256,256)).save(OUT+nm+'.png');TILE[nm]=(1,1)
# Timber picket fence with alpha: white pickets 70 mm wide, 45 mm gaps, pointed tops, two rails. Tile 1.15 m x 1.2 m.
W,H=1024,1068;img=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(img);px=W/1.15
for k in range(10):
    x0=k*0.115*px;x1=x0+0.07*px;top=0.05*px;bot=H
    d.polygon([(x0,top+0.035*px),((x0+x1)/2,top),(x1,top+0.035*px),(x1,bot),(x0,bot)],fill=(238,238,232,255))
    d.line([(x1,top+0.035*px),(x1,bot)],fill=(200,200,194,255),width=3)
for yy in (0.25,0.95):
    d.rectangle([0,yy*px,W,(yy+0.075)*px],fill=(226,226,220,255))
img.save(OUT+'pickets.png');TILE['pickets']=(1.15,1.2)
# Chain-mesh (black PVC) security fence with alpha, 50 mm diamonds.
W=512;img=Image.new('RGBA',(W,W),(0,0,0,0));d=ImageDraw.Draw(img);s=W/10
for i in range(-10,21):
    d.line([(i*s,0),(i*s+W,W)],fill=(28,30,30,255),width=4);d.line([(i*s,W),(i*s+W,0)],fill=(28,30,30,255),width=4)
img.save(OUT+'mesh.png');TILE['mesh']=(0.5,0.5)
# Signs: lettering painted with a system font.
def font(sz,bold=True):
    for f in (r'C:\Windows\Fonts\arialbd.ttf',r'C:\Windows\Fonts\arial.ttf'):
        try:return ImageFont.truetype(f,sz)
        except:pass
def sign(name,size,bg,lines,fg,border=None):
    img=Image.new('RGB',size,bg);d=ImageDraw.Draw(img);W,H=size;n=len(lines);y=0
    tot=sum(sz for _,sz in lines)+ (n-1)*H*0.04;y=(H-tot)/2
    for t,sz in lines[:0]:  # no lettering (director 2026-11-18): blank panel
        f=font(sz);w=d.textlength(t,font=f);d.text(((W-w)/2,y),t,font=f,fill=fg);y+=sz+H*0.04
    if border:d.rectangle([4,4,W-5,H-5],outline=border,width=8)
    img.save(OUT+name+'.png')
sign('sign_tigers_club',(1024,640),(250,212,30),[('ALBURY',150),('TIGERS CLUB',150),('LICENSED CLUB',90)],(20,20,20),(20,20,20))
sign('sign_tigers_ltd',(1024,128),(168,72,48),[('ALBURY TIGERS CLUB LTD',84)],(250,206,40))
# Club field roof: light-grey corrugated with bands of brown-rusted ribs (Earth view g_e2_090). Tile 4.2 m along u.
W=1024;H=512;x=np.arange(W)/W*4.2;rib=np.arange(H)/H*1.52*2*math.pi/0.076
a=np.ones((H,W,3))*np.array((198,204,208))*(0.92+0.08*np.cos(rib))[:,None,None]
band=(x>2.2)&(((x*1000)%200)<60)
a[:,band]=a[:,band]*0.55+np.array((120,74,52))*0.45
a+=noise(W,16,6)[:H,:,None];save('roof_ribbed',a,(4.2,1.52))
def tiger(d,cx,cy,r):  # stylised gold tiger head, hand-drawn
    d.ellipse([cx-r,cy-r*0.95,cx+r,cy+r*0.95],fill=(232,168,40))
    for sx in (-1,1):
        d.ellipse([cx+sx*r*0.75-r*0.25,cy-r*1.05,cx+sx*r*0.75+r*0.25,cy-r*0.55],fill=(232,168,40),outline=(30,24,20),width=max(2,int(r*0.05)))
        d.polygon([(cx+sx*r*0.95,cy-r*0.2),(cx+sx*r*0.45,cy-r*0.1),(cx+sx*r*0.9,cy+r*0.05)],fill=(30,24,20))
        d.polygon([(cx+sx*r*0.9,cy+r*0.3),(cx+sx*r*0.5,cy+r*0.3),(cx+sx*r*0.85,cy+r*0.48)],fill=(30,24,20))
        d.ellipse([cx+sx*r*0.38-r*0.12,cy-r*0.2,cx+sx*r*0.38+r*0.12,cy-r*0.02],fill=(250,240,210),outline=(30,24,20),width=3)
    for k in (-1,0,1):d.polygon([(cx+k*r*0.18-r*0.05,cy-r*0.92),(cx+k*r*0.18+r*0.05,cy-r*0.92),(cx+k*r*0.1,cy-r*0.45)],fill=(30,24,20))
    d.ellipse([cx-r*0.38,cy+r*0.15,cx+r*0.38,cy+r*0.8],fill=(250,240,210))
    d.polygon([(cx-r*0.14,cy+r*0.15),(cx+r*0.14,cy+r*0.15),(cx,cy+r*0.32)],fill=(30,24,20))
# Field-side banner under the club roof: black, white/yellow lettering, a tiger head at each end.
img=Image.new('RGB',(2048,256),(22,22,24));d=ImageDraw.Draw(img)
# no lettering or logos (director 2026-11-18): blank black panel
for t,y,sz,c in ():
    f=font(sz);w=d.textlength(t,font=f);d.text(((2048-w)/2,y),t,font=f,fill=c)
img.save(OUT+'sign_tradition.png')
# Street mural: gold tiger on the brick wall (painted over the brick texture tile).
b=np.asarray(Image.open(OUT+'brick_red.png').convert('RGB'));img=Image.fromarray(np.vstack([b[:,:512]]*2)).resize((512,640))
d=ImageDraw.Draw(img);tiger(d,256,330,250);img.save(OUT+'mural_tiger.png')
# Back of the east stand (482327982, Earth view g_e_270): black board, gold frame, TRADITION / ALBURY [tiger] TIGERS / LIVES HERE.
img=Image.new('RGB',(2048,512),(20,20,22));d=ImageDraw.Draw(img);d.rectangle([6,6,2041,505],outline=(214,170,60),width=12)
# no lettering or logos (director 2026-11-18): blank black board in its gold frame
for t,cx,y,sz,c in ():
    f=font(sz);w=d.textlength(t,font=f);d.text((cx-w/2,y),t,font=f,fill=c)
img.save(OUT+'sign_east_stand.png')
# Sponsor boards beside it: plain painted panels in the colours seen (lettering too small to read in any source).
img=Image.new('RGB',(1024,256),(240,240,236));d=ImageDraw.Draw(img)
for k,c in enumerate([(236,236,232),(28,70,140),(236,236,232),(200,40,40),(236,236,232),(30,110,60),(236,236,232),(28,70,140),(250,206,40),(236,236,232)]):
    d.rectangle([k*102+4,8,k*102+98,248],fill=c,outline=(120,120,120),width=3)
img.save(OUT+'sponsor_boards.png')
# Clear PVC blinds on the SE stand (961): dark interior seen through clear sheet, white frame posts at the tile edge,
# white bottom rail and a thin mid rail. Tile 3.0 m x 4.6 m (one bay). Painted, no photo pixels.
a=np.ones((N,N,3))*np.array((70,80,88));a*=np.linspace(1.18,0.9,N)[::-1][:,None,None]
a+=noise(N,10,10)[:,:,None]+fine(N,2)[:,:,None]
W=(232,234,232);b=int(N*0.11);a[:b]=W;a[:b]+=fine(N,3)[:b,:,None]          # bottom skirt (v=0 at row 0 -> bottom)
pw=int(N*0.035);a[:,:pw]=W;a[:,-pw:]=W                                       # frame posts at both tile edges
m=int(N*0.52);a[m:m+int(N*0.012)]=(214,218,220)                              # mid rail
a[-int(N*0.02):]=W                                                           # head rail
save('blind_clear',a[::-1],(3.0,4.6))  # image row 0 is the top (v=1)
json.dump(TILE,open('model/tex/tiles.json','w'),indent=1);print(len(TILE),'textures')
