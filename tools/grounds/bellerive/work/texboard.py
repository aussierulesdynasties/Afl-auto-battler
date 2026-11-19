# python work/texboard.py out.jpg stddev.txt : per surface, texture swatch | GE photo crop | model render crop (same pixels), + grey stddev of every texture
import sys,os,json,math,glob
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageStat
sys.path.insert(0,'work');import earthcam
C=json.load(open('work/cams.json'));DZ=float(open('work/dz.txt').read())
def P(b,r,z):return (r*math.sin(math.radians(b)),r*math.cos(math.radians(b)),z)
S=[('roof_white','f180',P(180,100,16.0)),('fac_boon','f180',P(180,108,7)),('fac_ponting','f270',P(262,101,8)),
 ('fac_members','f315',P(322,101,7)),('glass_members','f135',P(322,90,6)),('seats_blue','f090',P(250,76,4)),
 ('seats_dark','f135',P(330,88,1.4)),('terrace','f270',P(80,69,0.2)),('grass_hill','f090',P(80,85,1.2)),
 ('roof_tan','f225',P(36,80,6.6)),('screen','f270',(93.8,-21.5,7.0)),('tower','f000',(-55.3,-88.87,30)),
 ('skylight','f180',P(232.5,93,22)),('sign_ninja_w','f000',(-55,98,12))]
f=ImageFont.truetype('arialbd.ttf',22);T=240;rows=[]
for m,v,X in S:
    x0,y0,a,d,h,t=C[v];c=earthcam.cam(h,t,d,tz=a-DZ,tx=x0,ty=y0);u,w=earthcam.proj(c,X)
    g=Image.open(f'ge/{v}.png').convert('RGB');r=Image.open(f'rr/{v}.png').convert('RGBA')
    bg=g.copy();bg.paste(r,(0,0),r)
    hb=60;box=(int(u)-hb,int(w)-hb,int(u)+hb,int(w)+hb)
    tx=Image.open(f'model/tex/{m}.png').convert('RGB');W,H=tx.size;s=min(W,H,512)
    sw=tx.crop((0,0,s,s)).resize((T,T))
    row=Image.new('RGB',(T*3+260,T),(30,30,30));dr=ImageDraw.Draw(row)
    row.paste(sw,(260,0));row.paste(g.crop(box).resize((T,T),Image.LANCZOS),(260+T,0));row.paste(bg.crop(box).resize((T,T),Image.LANCZOS),(260+2*T,0))
    sd=ImageStat.Stat(tx.convert('L')).stddev[0]
    dr.text((10,80),m,font=f,fill=(255,255,255));dr.text((10,115),f'stddev {sd:.1f}',font=f,fill=(255,220,120));dr.text((10,150),f'view {v}',font=f,fill=(170,170,170))
    rows.append(row)
hd=Image.new('RGB',(T*3+260,34),(15,15,15));d=ImageDraw.Draw(hd)
for i,s_ in enumerate(('hand-made texture','GE photo crop','model, same pixels')):d.text((260+i*T+8,6),s_,font=f,fill=(255,255,255))
B=Image.new('RGB',(T*3+260,34+T*len(rows)));B.paste(hd,(0,0))
for i,r in enumerate(rows):B.paste(r,(0,34+i*T))
B.save(sys.argv[1],quality=90)
with open(sys.argv[2],'w',newline='') as o:
    for p in sorted(glob.glob('model/tex/*.png')):
        o.write(f'{os.path.basename(p)[:-4]:18s} {ImageStat.Stat(Image.open(p).convert("L")).stddev[0]:6.1f}\n')
