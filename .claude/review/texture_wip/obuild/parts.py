# Crop board per part: PHOTO | RENDER | 50% overlay, each crop scaled 2x. Usage: python parts.py RENDER.png OUT.png
import sys
from PIL import Image,ImageDraw
ph=Image.open('photo.jpg').convert('RGBA');r=Image.open(sys.argv[1]).convert('RGBA')
ren=Image.alpha_composite(Image.new('RGBA',ph.size,(120,140,160,255)),r);ov=Image.blend(ph,Image.alpha_composite(ph,r),0.5)
P=[('roof',(560,290,1180,560)),('west terrace, glass, canopy',(1150,450,1700,880)),('stands',(560,330,1300,540)),('facade',(300,560,920,860)),('stair+lift towers',(1020,850,1220,1040)),('plaza east (pavilions removed)',(1220,560,1720,1000)),('gates+podium',(440,820,1060,950))]
rows=[]
for name,b in P:
    w,h=b[2]-b[0],b[3]-b[1];s=min(2.0,600/w)
    ims=[i.crop(b).resize((int(w*s),int(h*s)),Image.LANCZOS).convert('RGB') for i in (ph,ren,ov)]
    row=Image.new('RGB',(sum(i.width for i in ims)+20,ims[0].height+30),(0,0,0));x=0
    for i in ims:row.paste(i,(x,30));x+=i.width+10
    ImageDraw.Draw(row).text((8,8),name.upper()+'   photo | render | 50%',fill=(255,255,255));rows.append(row)
W=max(r.width for r in rows);out=Image.new('RGB',(W,sum(r.height for r in rows)),(0,0,0));y=0
for r_ in rows:out.paste(r_,(0,y));y+=r_.height
out.save(sys.argv[2])
