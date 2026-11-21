# python proofboard.py BUILD PROOFDIR -> out/final/{triptych_aerial,triptych_w04,parts}.png
# Triptych = photo | render | 50% overlay at the photo's full resolution. Parts = per-part photo beside the model still.
import sys,os
from PIL import Image,ImageDraw,ImageFont
H=os.path.dirname(os.path.abspath(__file__));BUILD,PROOF=sys.argv[1],sys.argv[2]
O=os.path.join(H,'out','final');os.makedirs(O,exist_ok=True)
F=lambda s:ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',s)
def trip(photo,render,name,ground=None):
    ph=Image.open(photo).convert('RGBA');m=Image.open(render).convert('RGBA').resize(ph.size)
    rn=Image.new('RGBA',ph.size,(30,30,30,255))
    if ground:rn.alpha_composite(Image.open(ground).convert('RGBA').resize(ph.size))
    rn.alpha_composite(m)
    ov=Image.blend(ph,rn,0.5) if ground else ph.copy()
    if not ground:m2=m.copy();m2.putalpha(m.split()[3].point(lambda v:v//2));ov.alpha_composite(m2)
    w,h=ph.size;out=Image.new('RGB',(3*w+40,h+60),(24,24,26));d=ImageDraw.Draw(out)
    for i,(im,t) in enumerate(((ph,'Photo'),(rn,'Model render, same camera'),(ov,'50% overlay'))):
        out.paste(im.convert('RGB'),(10+i*(w+10),50));d.text((10+i*(w+10),8),t,font=F(30),fill=(240,240,240))
    out.save(os.path.join(O,name));print(name,out.size)
trip(os.path.join(H,'refs','ref.jpg'),os.path.join(BUILD,'render_model.png'),'triptych_aerial.png',os.path.join(BUILD,'render_ground.png'))
w4=os.path.join(BUILD,'render_w04.png')
if os.path.exists(w4):trip(os.path.join(H,'refs','web','w04.jpg'),w4,'triptych_w04.png')
C=lambda f,box=None:(lambda im:im.crop(box) if box else im)(Image.open(os.path.join(H,f)).convert('RGB'))
P=[('Stand',C('refs/web/w04.jpg'),'stand'),
   ('Facade',C('out/crop_w04_box.png'),'stand_facade_close'),
   ('Roof',C('refs/web/w04.jpg',(0,0,1280,330)),'roof'),
   ('Clubrooms',C('refs/web/w04.jpg',(960,280,1280,600)),'clubrooms'),
   ('Towers',C('refs/commons/c00.jpg',(2300,0,2900,960)),'tower_full'),
   ('Tower head',C('refs/commons/c00.jpg',(2520,0,2870,110)),'tower_head'),
   ('Scoreboard and boards',C('out/c07_rail.png'),'scoreboard'),
   ('Fence, stand side',C('refs/commons/c05.jpg'),'fence'),
   ('Fence and wall, east',C('out/c07_wall.png'),'fence_east')]
RH=420;rows=[]
for t,ph,st in P:
    r=Image.open(os.path.join(PROOF,st+'.png')).convert('RGB');a=ph.resize((int(ph.width*RH/ph.height),RH),Image.LANCZOS);b=r.resize((int(r.width*RH/r.height),RH),Image.LANCZOS)
    if a.width>1100:a=a.resize((1100,int(RH*1100/a.width)),Image.LANCZOS)
    rows.append((t,a,b))
W=max(a.width+b.width for _,a,b in rows)+30;out=Image.new('RGB',(W,sum(RH+60 for _ in rows)+10),(24,24,26));d=ImageDraw.Draw(out);y=0
for t,a,b in rows:
    d.text((10,y+12),t+'   (photo left, model right)',font=F(28),fill=(255,255,255));y+=50
    out.paste(a,(10,y));out.paste(b,(20+a.width,y));y+=RH+10
out.save(os.path.join(O,'parts.png'));print('parts',out.size)
