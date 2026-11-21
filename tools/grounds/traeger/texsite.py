# Hand-made textures for everything outside the grandstand and clubrooms (replaces every old tex/ placeholder).
# Layouts read off c02/c03/c05 (2025 towers, pole signs, boundary fence, shed) and w01 (scoreboard). No photo pixels.
import numpy as np,json,os
from PIL import Image,ImageDraw,ImageFont
exec(open('texgen.py').read().split('TILE={};PANEL={}')[0])
J=json.load(open(os.path.join(OUT,'tex.json')));TILE={k:tuple(v) for k,v in J['TILE'].items()};PANEL={k:True for k in J['PANEL']}
PX=200
def u8(a):return Image.fromarray(np.clip(a,0,255).astype(np.uint8))
def font(n,s):return ImageFont.truetype(F+n,max(8,int(s)))
# ---- galvanised steel (poles, lattice, scoreboard legs): light grey with soft mottling and faint vertical streaks ----
w,h=int(2*PX),int(2*PX);img=base(h,w,'#a9adae',6,5,301)+noise(h,w,60,3,302)[...,None]
img+=noise(1,w,80,4,303)[0][None,:,None];save('steel',img);TILE['steel']=(2,2)
save('post',base(200,200,'#2b2d2f',3,4,304));TILE['post']=(2,2)          # w01: black scoreboard frame legs
# lamp-head frame (back and sides): one housing back per 1.3 m cell (6.5 m head / 5 columns), dark steel grid
fr=base(260,260,'#5d6164',4,4,305);fr[14:246,14:246]=rgb('#3c3f42')+noise(232,232,40,4,306)[...,None];fr[120:140,30:230]+=12
save('frame',fr);TILE['frame']=(1.3,1.3)
# ---- 2025 lamp head (c02): steel frame holding 5 columns x 6 rows of floodlights, dark housings, pale lenses ----
W,H=520,640;img=base(H,W,'#6b6f72',4,4,311);im=u8(img);d=ImageDraw.Draw(im)
cw,ch=W/5,H/6
for i in range(5):
    for j in range(6):
        x0,y0=int(i*cw+8),int(j*ch+8);x1,y1=int((i+1)*cw-8),int((j+1)*ch-8)
        d.rectangle([x0,y0,x1,y1],fill=(48,50,53));d.rectangle([x0+7,y0+7,x1-7,y1-7],fill=(214,218,220))
        d.line([(x0+9,y0+9),(x1-9,y0+9)],fill=(246,247,248),width=3)
im.save(os.path.join(OUT,'lamps.png'));PANEL['lamps']=True
# ---- pole sign (c02): royal blue panel, white TIO box at the top, "Traeger Park Oval" in white below ----
def pole_sign(name,bg,box,txtcol,lines):
    W,H=470,500;im=Image.new('RGB',(W,H),bg);d=ImageDraw.Draw(im)
    d.rectangle([0,0,W-1,H-1],outline=(236,238,240),width=6)
    if box:
        d.rounded_rectangle([int(W*0.25),int(H*0.08),int(W*0.75),int(H*0.40)],radius=14,fill=(248,248,248))
        d.text((W//2,int(H*0.24)),'TIO',font=font('segoeuib.ttf',H*0.22),fill=(30,86,170),anchor='mm')
    y=int(H*0.56) if box else int(H*0.40)
    for t in lines:d.text((W//2,y),t,font=font('segoeuib.ttf',H*0.13),fill=txtcol,anchor='mm');y+=int(H*0.17)
    a=np.asarray(im).astype(float)+noise(H,W,6,3,321)[...,None];save(name,a);PANEL[name]=True
pole_sign('sign_tio',(29,92,178),False,(250,250,250),[])  # no lettering (director 2026-11-18)
pole_sign('sign_white',(238,239,236),False,(40,62,120),[])
# ---- scoreboard (w01): blue header with the TIO box and "Traeger Park Oval", LED screen (switched off), name strip ----
W,H=940,770;im=Image.new('RGB',(W,H),(14,15,17));d=ImageDraw.Draw(im)
hh=int(H*0.17)
for y in range(hh):                                   # header: deep blue with lighter top and bottom stripes
    c=(52,72,170) if 0.12<y/hh<0.86 else (110,150,220);d.line([(0,y),(W,y)],fill=c)
# no lettering (director 2026-11-18): blank header
sy0,sy1=hh+int(H*0.012),int(H*0.955)
d.rectangle([int(W*0.02),sy0,int(W*0.98),sy1],fill=(20,22,26))
a=np.asarray(im).astype(float)
yy,xx=np.mgrid[0:H,0:W];led=((xx%6<3)&(yy%6<3))&(yy>sy0)&(yy<sy1)&(xx>W*0.02)&(xx<W*0.98)
a[led]+=8
im=u8(a);d=ImageDraw.Draw(im)
im.save(os.path.join(OUT,'screen.png'));PANEL['screen']=True
# ---- boundary fence (c04 close-up): pipe top and bottom rails, doubled posts at each 2.5 m joint, a single post
#      halfway, full-height 50 mm chain-link. The white backing sheet covers the stand side only (c05);
#      the north-east and far side are open mesh (c03, c07): rail.png = backed, rail_open.png = open ----
for name,backed in (('rail',True),('rail_open',False)):
    W,H=int(16*PX),int(1.0*PX);rgbA=np.zeros((H,W,4));yy,xx=np.mgrid[0:H,0:W]/PX;m=0.05
    sheet=(yy>0.09)&(yy<0.90)&backed;rgbA[...,:3]=rgb('#eef0ef');rgbA[...,3]=np.where(sheet,255,0)
    rgbA[sheet,:3]-=((yy[sheet]-0.09)*14)[:,None]                      # faint shading down the sheet
    # 3 mm galvanised wire on a 50 mm mesh: one 5 mm texel per wire at 60% cover, so from the stands the open mesh
    # reads as a faint grey haze with the wall showing through (w04: the arch shows through the chain-link)
    dia=(np.abs(((xx+yy)%m)-m/2)<0.0025)|(np.abs(((xx-yy)%m)-m/2)<0.0025)
    rgbA[dia,:3]=rgb('#8c8e8a');rgbA[dia,3]=np.maximum(rgbA[dia,3],150)
    xp=xx%2.5
    for x0,x1 in ((0.0,0.045),(0.075,0.11),(1.24,1.27)):                   # joint pair, then the mid post
        q=(xp>=x0)&(xp<x1);rgbA[q,:3]=rgb('#b9b4a8');rgbA[q,3]=255
    for y0,y1 in ((0.0,0.07),(0.93,1.0)):                                 # pipe rails with a highlight along the top
        q=(yy>=y0)&(yy<y1);rgbA[q,:3]=rgb('#c8c2b4')+(((yy[q]-y0)/(y1-y0)<0.35)*14)[:,None];rgbA[q,3]=255
    rgbA[...,:3]+=noise(H,W,30,4,331)[...,None]
    Image.fromarray(np.clip(rgbA,0,255).astype(np.uint8),'RGBA').save(os.path.join(OUT,name+'.png'));TILE[name]=(16,1)
# ---- east wall (c07): beige concrete blockwork, 390 x 190 mm blocks, stretcher bond, light mortar ----
w,h=int(1.6*PX),int(0.8*PX);img=base(h,w,'#c8b48e',4,5,351);yy,xx=np.mgrid[0:h,0:w]/PX
row=(yy//0.2).astype(int);xo=(xx+(row%2)*0.2)%0.4
mort=((yy%0.2)<0.012)|(xo<0.012);img[mort]=rgb('#ddd2bb');img+=np.where(mort,0,noise(h,w,40,3,353))[...,None]*0.6
save('block_tan',img);TILE['block_tan']=(1.6,0.8)
# ---- shed (c03): dark green Colorbond walls, vertical ribs ----
w,h=int(1.9*PX),int(1.9*PX);img=base(h,w,'#3f5a49',3,4,341);x=(np.arange(w)/PX)%0.19
img+=np.where(x<0.03,-16,np.where(x<0.045,10,0))[None,:,None];save('shed_wall',img);TILE['shed_wall']=(1.9,1.9)
# ---- east shelter roof: white ribbed deck (same as the grandstand roof) ----
img=base(int(1.9*PX),int(1.9*PX),'#e8e7e2',3,4,351);x=(np.arange(int(1.9*PX))/PX)%0.19
img+=np.where(x<0.035,-16,np.where(x<0.05,10,0))[None,:,None];save('roof_white',img);TILE['roof_white']=(1.9,1.9)
# ---- east boundary wall: red face brick ----
exec(open('texclub.py').read().split('# ---- face brick')[1].split("save('club_brick'")[0].split('\n',1)[1])
save('brick',brick('#9a4a32',361));TILE['brick']=(1.84,0.86)
# ---- trees (eucalypts): olive-grey leaf clumps with gaps, pale bark ----
w=h=400;img=base(h,w,'#6e7a45',10,6,371);r=np.random.default_rng(372);im=u8(img);d=ImageDraw.Draw(im)
for _ in range(900):
    x,y=r.integers(0,w),r.integers(0,h);s=r.integers(4,11);c=tuple(int(v) for v in rgb('#7d8a50')*r.uniform(0.7,1.25))
    d.ellipse([x-s,y-s//2,x+s,y+s//2],fill=c)
save('tree',np.asarray(im).astype(float));TILE['tree']=(4,4)
w,h=200,400;img=base(h,w,'#d9d2c3',8,3,381);img+=noise(h,1,40,10,382)[:,0][:,None,None]*0+noise(1,w,30,8,383)[0][None,:,None]
save('trunk',img);TILE['trunk']=(1,2)
# ---- ground: red Centralian dirt apron and the playing surface ----
save('dirt',base(600,600,'#b0623c',9,8,391)+noise(600,600,150,6,392)[...,None]);TILE['dirt']=(6,6)
# outer grass: the aerial (2020), w04 and c07 (2025) show dry olive grass outside the oval fence, up to the stand
w=h=600;img=base(h,w,'#6f7f3c',8,8,395)+noise(h,w,220,9,396)[...,None]*np.array([1.0,0.9,0.5]);save('grass_out',img);TILE['grass_out']=(6,6)
w=h=600;img=base(h,w,'#4f7d32',6,8,393)+noise(h,w,200,7,394)[...,None]*np.array([0.8,1,0.6]);save('grass',img);TILE['grass']=(6,6)
json.dump(dict(TILE=TILE,PANEL=list(PANEL)),open(os.path.join(OUT,'tex.json'),'w'))
print('site textures written')
