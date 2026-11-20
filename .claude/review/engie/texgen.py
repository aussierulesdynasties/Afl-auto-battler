# Hand-made textures for the ENGIE model (no photo pixels). 100 px per metre unless noted.
# Colours are read off the 2026 photos by eye and set by hand.
import numpy as np,os
from PIL import Image,ImageDraw,ImageFilter
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'tex');os.makedirs(OUT,exist_ok=True)
rng=np.random.default_rng(7)
def noise(h,w,amp,blur=1.2):
    n=rng.normal(0,1,(h,w)).astype(np.float32)
    im=Image.fromarray(((n*40)+128).clip(0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
    return (np.asarray(im,np.float32)-128)/40*amp
def save(a,name):Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(os.path.join(OUT,name))
def fill(h,w,rgb,amp=4,blur=1.2):
    a=np.zeros((h,w,3),np.float32)+np.array(rgb,np.float32);return a+noise(h,w,amp,blur)[...,None]

# seats: one tile = 16 seats (0.5 m) x 4 rows (0.8 m), viewed from above the rake, pitch at the bottom
def seats():
    W,H=800,320;a=fill(H,W,(84,80,76),3)            # concrete tread, in the seats' shadow
    d=ImageDraw.Draw(im:=Image.fromarray(a.astype(np.uint8)))
    red=(206,38,34);redd=(150,24,24);redl=(232,72,60)
    for r in range(4):
        y0=r*80
        d.rectangle([0,y0,W,y0+3],fill=(92,88,84))          # riser edge shadow line
        for s in range(16):
            x0=s*50+4
            d.rounded_rectangle([x0-1,y0+5,x0+44,y0+32],5,fill=redd)   # seat back (top edge, darker)
            d.rounded_rectangle([x0,y0+9,x0+43,y0+30],4,fill=red)
            d.rectangle([x0+3,y0+13,x0+39,y0+15],fill=redl)          # back highlight
            d.rounded_rectangle([x0+1,y0+30,x0+42,y0+60],4,fill=red) # seat pan
            d.rectangle([x0+1,y0+58,x0+42,y0+62],fill=redd)
            d.rectangle([x0+19,y0+62,x0+23,y0+68],fill=(60,60,62))   # stanchion
    save(np.asarray(im,np.float32)+noise(H,W,2,0.8)[...,None],'seats.png')
# aisle stairs: 1.2 m wide x 3.2 m (4 rows, 2 steps per row), concrete with yellow nosings
def aisle():
    W,H=120,320;a=fill(H,W,(150,146,140),4);im=Image.fromarray(a.astype(np.uint8));d=ImageDraw.Draw(im)
    for k in range(8):
        y=k*40;d.rectangle([0,y,W,y+3],fill=(100,96,92));d.rectangle([0,y+4,W,y+8],fill=(214,186,60))
    d.rectangle([0,0,4,H],fill=(170,170,172));d.rectangle([W-5,0,W,H],fill=(170,170,172))
    save(np.asarray(im,np.float32),'aisle.png')
# off-white roof sheeting: 4 m x 4 m, ribs every 0.2 m (Kliplok-style) running down the slope
def roof():
    W=H=400;a=fill(H,W,(236,237,236),2.5,2)
    for x in range(0,W,20):a[:,x:x+3]-=22;a[:,x+3:x+5]+=8
    a[::200,:]-=6
    save(a,'roof.png')
# clean concrete: 4 m x 4 m, formwork joints every 2 m, tie holes
def concrete(name,rgb):
    W=H=400;a=fill(H,W,rgb,5,1.5)+noise(400,400,6,25)[...,None]
    a[::200,:]-=18;a[:,::200]-=18
    for y in range(50,400,100):
        for x in range(50,400,100):a[y-2:y+2,x-2:x+2]-=30
    save(a,name)
# metal cladding panels: 4 m wide x 4 m, vertical panels 0.6 m with joints
def cladding(name,rgb,pw=60):
    W=H=400;a=fill(H,W,rgb,2,1.5)
    for x in range(0,W,pw):a[:,x:x+2]-=35;a[:,x+2:x+3]+=10
    a[198:201,:]-=25
    save(a,name)
# blue glazing: 4 m x 2.4 m, mullions every 1.2 m, transom at 2.1 m
def glazing():
    W,H=400,240;a=np.zeros((H,W,3),np.float32)
    g=np.linspace(0,1,H)[:,None];a[...]=np.array((70,96,130))*(1-g[...,None]*0.3)+np.array((150,175,200))*g[...,None]*0.3
    a+=noise(H,W,2,3)[...,None]
    for x in range(0,W,120):a[:,x:x+5]=(58,60,64)
    a[0:5,:]=(58,60,64);a[30:34,:]=(58,60,64)
    save(a,'glazing.png')
# grass: mown in stripes both ways (photo rectified to plan, square-wave fit): stripes along x every 22.0 m, light centre
# at world x 40.15; stripes along y every 23.2 m, light centre at world y 59.05. Light x light, mixed, dark x dark = 3 tones.
# One tile = one period each way, 22.0 m x 23.2 m at 25 px/m; flat UVs are world x, y, so the phase is set in pixels here.
def grass():
    W,H=550,580;a=fill(H,W,(118,129,71),5,0.7)+noise(H,W,4,10)[...,None]
    xs=np.arange(W)/25.0;ys=(H-1-np.arange(H))/25.0              # image row 0 = top = v 1
    # no mowing pattern: the game's turf draws it (secretary 2026-11-18, stadium-only ruling)
    save(a,'grass.png')
# grey ribbed metal deck (south roof, photo mean 158,162,167): 4 m tile, ribs every 0.3 m running down the slope
def metal_deck():
    W=H=400;a=fill(H,W,(176,180,186),2.5,2)
    for x in range(0,W,30):a[:,x:x+3]-=26;a[:,x+3:x+5]+=10
    a[::200,:]-=8
    save(a,'metal_deck.png')
# red painted steel: 1 m x 1 m
def steel():
    a=fill(100,100,(196,30,28),3,1.0);a[:, :6]*=0.8;save(a,'red_steel.png')
def louvre():
    W,H=200,100;a=fill(H,W,(160,163,166),2);
    for y in range(0,H,10):a[y:y+3,:]-=40
    save(a,'louvre.png')
# floodlight head: 2 m x 1 m tile = 4 lamps x 2 rows, dark housings, pale lenses, grey frame
def lamps():
    W,H=200,100;a=fill(H,W,(92,94,98),2);im=Image.fromarray(a.astype(np.uint8));d=ImageDraw.Draw(im)
    for r in range(2):
        for c in range(4):
            x0=c*50+5;y0=r*50+5;d.rectangle([x0,y0,x0+40,y0+40],fill=(40,42,46))
            d.ellipse([x0+5,y0+5,x0+35,y0+35],fill=(214,218,214));d.ellipse([x0+12,y0+10,x0+24,y0+20],fill=(246,248,246))
    save(np.asarray(im,np.float32),'lamps.png')
# lamp backs (photo, heads seen from behind): 2 m x 1.6 m tile = 4 dark grey lamp housings with silver rims, a white
# catwalk rail along the bottom of each row
def lamp_backs():
    W,H=200,160;a=fill(H,W,(52,54,58),2);im=Image.fromarray(np.clip(a,0,255).astype(np.uint8));d=ImageDraw.Draw(im)
    for c in range(4):
        x0=c*50+5;d.rectangle([x0,12,x0+40,128],fill=(74,77,82));d.rectangle([x0+4,16,x0+36,124],fill=(46,48,52))
        d.rectangle([x0,12,x0+40,16],fill=(170,172,174))
    d.rectangle([0,138,W,146],fill=(226,228,226));d.rectangle([0,150,W,153],fill=(200,202,200))
    save(np.asarray(im,np.float32),'lamp_backs.png')
# pale grey mesh panel below the lamps: 1 m tile, fine perforated grid
def mesh_panel():
    W=H=100;a=fill(H,W,(196,200,200),3,1)
    a[::5,:]-=14;a[:,::5]-=14
    al=np.full((H,W),20,np.float32);al[::5,:]=120;al[:,::5]=120   # perforated: fine see-through mesh, ~78% of the ground shows through (photo, towers 25 and 27)
    Image.fromarray(np.dstack([np.clip(a,0,255),al]).astype(np.uint8),'RGBA').save(os.path.join(OUT,'mesh_panel.png'))
# tower paint of towers 25-30 (photo: sunlit tan 218,188,144, shade 108,78,54): 1 m tile, faint weathering
def tan_steel():
    a=fill(100,100,(190,150,112),4,2);a[:, :6]*=0.85;save(a,'tan_steel.png')
# field side of the head below the lamps (photo, far towers): dark brown perforated panel
def mesh_dark():
    W=H=100;a=fill(H,W,(104,82,66),3,1);a[::5,:]-=12;a[:,::5]-=12
    al=np.full((H,W),20,np.float32);al[::5,:]=120;al[:,::5]=120
    Image.fromarray(np.dstack([np.clip(a,0,255),al]).astype(np.uint8),'RGBA').save(os.path.join(OUT,'mesh_dark.png'))
# video screen (switched off): 1 m x 1 m, black LED tiles 0.5 m with fine pixel lines
def screen():
    a=fill(100,100,(18,19,22),1.5)
    a[::4,:]-=6;a[:,::4]-=6;a[::50,:]=(44,46,50);a[:,::50]=(44,46,50)
    save(a,'screen.png')
# clear polycarbonate roof: 4 m x 4 m, pale blue-grey, ribs every 0.6 m, purlin shadow every 2 m
def clear_roof():
    W=H=400;a=fill(H,W,(196,206,214),2,2)
    for x in range(0,W,60):a[:,x:x+4]-=30
    a[::200,:]-=20
    save(a,'clear_roof.png')
# copper-coloured metal cladding: 4 m x 4 m, 0.5 m panels with weathering
def copper():
    W=H=400;a=fill(H,W,(166,108,64),4,1.5)+noise(400,400,8,30)[...,None]
    for x in range(0,W,50):a[:,x:x+2]-=40
    a[::100,:]-=15
    save(a,'copper.png')
seats();aisle();lamps();screen();clear_roof();copper();roof();concrete('concrete.png',(176,174,168));concrete('deck.png',(150,148,144))
cladding('cladding.png',(150,152,154));cladding('cladding_tan.png',(176,156,128),80);glazing();grass();metal_deck();lamp_backs();mesh_panel();tan_steel();mesh_dark();steel();louvre()
print(sorted(os.listdir(OUT)))
# --- v15 additions: near facade and north-west block (colours read off photo.jpg by eye) ---
# dark tinted glazing: 4 m x 3 m, mullions every 1.5 m, transom at 2.4 m, faint sky reflection at the top
def dark_glass():
    W,H=400,300;a=np.zeros((H,W,3),np.float32);g=np.linspace(0,1,H)[:,None,None]
    a[...]=np.array((52,58,66))*(1-g)+np.array((30,34,40))*g;a+=noise(H,W,1.5,3)[...,None]
    for x in range(0,W,150):a[:,x:x+5]=(96,98,100)
    a[0:5,:]=(96,98,100);a[60:64,:]=(96,98,100)
    save(a,'dark_glass.png')
# white painted concrete render: 4 m x 4 m, panel joints every 2 m
def render(name,rgb):
    W=H=400;a=fill(H,W,rgb,2.5,1.5)+noise(400,400,3,30)[...,None];a[::200,:]-=14;a[:,::200]-=14;save(a,name)
# face brick: 1 m x 1 m, 230 x 76 mm bricks, stretcher bond, pale mortar
def brick():
    W=H=100;a=fill(H,W,(214,206,194),2);im=Image.fromarray(a.astype(np.uint8));d=ImageDraw.Draw(im)
    cols=[(150,78,58),(138,70,52),(162,88,64),(128,66,50)]
    for r in range(13):
        y=r*7.7;off=0 if r%2 else 11.5
        for c in range(-1,6):
            x=c*23+off;d.rectangle([x+1,y+1,x+22,y+6.7],fill=cols[(r*3+c)%4])
    save(np.asarray(im,np.float32)+noise(H,W,3,0.6)[...,None],'brick.png')
# coloured feature panels on the upper concourse wall: 2 m x 1.5 m, flat painted sheet, panel edges
def panel(name,rgb):
    W,H=200,150;a=fill(H,W,rgb,2,1.5);a[:,0:3]-=40;a[0:3,:]-=30;a[-3:,:]-=30;save(a,name)
# charcoal vertical cladding (service tower, lower block): 4 m x 4 m, 0.3 m ribs
def dark_clad():
    W=H=400;a=fill(H,W,(78,80,84),2,1.5)
    for x in range(0,W,30):a[:,x:x+3]-=22;a[:,x+3:x+5]+=12
    save(a,'dark_clad.png')
# ribbed blue-grey wall cladding of the north-west block: 4 m x 4 m, 0.25 m ribs
def blue_clad():
    W=H=400;a=fill(H,W,(112,138,168),2,1.5)
    for x in range(0,W,25):a[:,x:x+3]-=30;a[:,x+3:x+5]+=14
    save(a,'blue_clad.png')
# timber pergola roof: 2 m x 2 m, battens 0.15 m on 0.25 m spacing
def timber():
    W=H=200;a=fill(H,W,(66,44,34),2)
    for y in range(0,H,25):a[y:y+15,:]=np.array((136,86,62),np.float32)+noise(15,W,4,1)[...,None]
    save(a,'timber.png')
# Members sign: 4 m x 3.5 m, blank navy panel (crest and MEMBERS removed): director's ruling C "no lettering" (secretary 2026-11-18)
def members():
    W,H=400,350;a=fill(H,W,(34,40,78),1.5)
    im=Image.fromarray(np.clip(a,0,255).astype(np.uint8))
    save(np.asarray(im,np.float32),'members.png')
dark_glass();render('white_render.png',(232,232,228));brick();panel('panel_orange.png',(226,132,36));panel('panel_green.png',(132,186,52))
dark_clad();blue_clad();timber();members()
# PTFE membrane roof fabric: 6 m x 6 m, bright white with welded seams every 1.5 m and a faint tension sheen
def membrane():
    W=H=300;a=fill(H,W,(240,240,236),1.5,2)+noise(300,300,3,40)[...,None]
    for x in range(0,W,75):a[:,x:x+2]-=16
    save(a,'membrane.png')
membrane()

# dirt track between the grass and the fence (photo: dry tan clay, darker wheel ruts running round): 4 m x 4 m
def dirt():
    W=H=400;a=fill(H,W,(150,118,84),6,0.8)+noise(H,W,7,18)[...,None]
    for y in (60,140,260,330):a[y:y+14,:]-=10
    save(a,'dirt.png')
# fence boards round the boundary (photo: red boards and blue boards, white lettering not painted), 8 m x 1 m tile
def boards():
    W,H=800,100;a=fill(H,W,(200,30,36),2,1.0)
    a[:, 400:800]=np.array((30,52,120),np.float32)+noise(H,400,2,1.0)[...,None]
    a[:, 398:402]=(230,230,230);a[:4,:]=(235,235,235);a[-6:,:]=(60,60,60)
    save(a,'boards.png')
dirt();boards()
# sponsor band along the far stand's upper-tier front: 7 m repeat, dark olive field, a lime logo panel 1.9 m and a
# mid-olive message panel (photo row 474-484); lettering left off until the sponsor-board question is answered
def band():
    W,H=700,150;a=fill(H,W,(52,60,28),2);im=Image.fromarray(a.astype(np.uint8));d=ImageDraw.Draw(im)
    d.rounded_rectangle([20,22,210,128],28,fill=(150,178,72));d.ellipse([85,45,145,105],fill=(70,98,40))
    d.rounded_rectangle([235,30,680,120],14,fill=(96,110,46))
    d.rectangle([0,0,W,8],fill=(40,44,24));d.rectangle([0,H-8,W,H],fill=(40,44,24))
    save(np.asarray(im,np.float32),'band.png')
band()
# NE concourse roof band (photo columns 150-430): charcoal ribbed metal, a pale skylight strip 3 m x 0.8 m every 7 m along
# the middle of the band; tile 7 m round the roof x the band's width
def ne_roof():
    W,H=700,100;a=fill(H,W,(66,68,72),3);im=Image.fromarray(a.astype(np.uint8));d=ImageDraw.Draw(im)
    for x in range(0,W,20):d.line([x,0,x,H],fill=(56,58,62),width=2)
    d.rectangle([200,42,500,58],fill=(198,202,206));d.rectangle([200,42,500,44],fill=(150,154,158))
    save(np.asarray(im,np.float32),'ne_roof.png')
ne_roof()
# near stand roof (t 141-175): light ribbed metal deck in full sun (photo 225-236), 4 m x 4 m tile, a rib every 0.3 m
def metal_light():
    W=H=400;a=fill(H,W,(222,226,222),2.0,2)
    for x in range(0,W,30):a[:,x:x+3]-=18;a[:,x+3:x+5]+=6
    save(a,'metal_light.png')
metal_light()
# awning sheet: blue-grey steel, 2 m x 1 m tile, a standing seam every 0.5 m
def awning():
    W,H=200,100;a=fill(H,W,(118,128,146),2.0,2)
    for x in range(0,W,50):a[:,x:x+2]+=16;a[:,x+2:x+4]-=10
    save(a,'awning.png')
awning()
render('red_render.png',(150,58,50))
# NE roof inner strip (photo 2030-2130 x 575-615): pale sunlit sheeting, ribs every 0.3 m
def clear_strip():
    W=H=400;a=fill(H,W,(222,226,212),2,2)
    for x in range(0,W,30):a[:,x:x+3]-=18
    save(a,'clear_strip.png')
clear_strip()
# light tower shaft column (photo tower 25: rust-red lattice ~1 m wide): 1 m tile, edge chords, a rung and a diagonal, dark gaps
def rust_lattice():
    W=H=100;a=fill(H,W,(98,60,48),3);im=Image.fromarray(a.astype(np.uint8));d=ImageDraw.Draw(im);c=(156,74,52)
    d.rectangle([0,0,9,99],fill=c);d.rectangle([90,0,99,99],fill=c);d.rectangle([0,0,99,7],fill=c);d.line([(5,4),(95,96)],fill=c,width=7)
    save(np.asarray(im,np.float32)+noise(H,W,3,0.8)[...,None],'rust_lattice.png')
rust_lattice()
