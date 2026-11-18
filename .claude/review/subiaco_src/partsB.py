# per-part board: each named photo box cropped from the photo, the daylight render and the edge overlay, 3x, side by side
import sys
from PIL import Image,ImageDraw,ImageFont
ph,ren,ov,out=sys.argv[1:5]
P=Image.open(ph).convert('RGB');R=Image.open(ren).convert('RGBA').resize(P.size);bg=Image.new('RGBA',P.size,(40,44,52,255));bg.alpha_composite(R);R=bg.convert('RGB')
O=Image.open(ov).convert('RGB').resize(P.size)
parts=[('Near (south) roof with girders',(170,300,700,540)),('North stand: blue seats, white aisles, roof',(560,130,880,420)),
       ('East multi-storey block and NE corner',(660,380,960,580)),('West end: lit pad, bank, perimeter wall',(150,90,620,260)),
       ('West buildings and SW corner',(100,180,330,420)),('Light towers (4)',(100,0,920,330))]
try:F=ImageFont.truetype('arial.ttf',24)
except:F=ImageFont.load_default()
rows=[]
for name,(x0,y0,x1,y1) in parts:
    k=min(3.0,560/(y1-y0),640/(x1-x0));w,h=int((x1-x0)*k),int((y1-y0)*k)
    row=Image.new('RGB',(w*3+40,h+40),(24,26,30));d=ImageDraw.Draw(row);d.text((10,6),name,font=F,fill=(255,255,255))
    for i,im in enumerate((P,R,O)):row.paste(im.crop((x0,y0,x1,y1)).resize((w,h),Image.LANCZOS),(10+i*(w+10),36))
    rows.append(row)
W=max(r.width for r in rows);H=sum(r.height for r in rows)+50
B=Image.new('RGB',(W,H),(24,26,30));d=ImageDraw.Draw(B);d.text((10,10),'Subiaco 1997 (B) parts: photo | model | overlay',font=F,fill=(255,255,255));y=50
for r in rows:B.paste(r,(0,y));y+=r.height
B.save(out);print(B.size)
