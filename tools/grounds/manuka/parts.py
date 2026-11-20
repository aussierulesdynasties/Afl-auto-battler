import sys;from PIL import Image,ImageDraw
ph=Image.open('photo.png').convert('RGB');rd=Image.open(sys.argv[1]).convert('RGBA')
bg=Image.new('RGBA',rd.size,(40,40,46,255));bg.alpha_composite(rd);rd=bg.convert('RGB')
P=[('North stand',(670,320,1630,580)),('West stand + sign building',(145,350,730,815)),('Media Centre (Bradman end)',(175,730,580,990)),
   ('South terraces + pavilion',(495,870,1630,1080)),('East: scoreboard, hill, forecourt',(1510,525,1890,960))]
H=360;rows=[]
for n,b in P:
    w=int((b[2]-b[0])*H/(b[3]-b[1]));w=min(w,900);a=ph.crop(b).resize((w,H),Image.LANCZOS);c=rd.crop(b).resize((w,H),Image.LANCZOS)
    r=Image.new('RGB',(2*w+10,H+30),(20,20,20));r.paste(a,(0,30));r.paste(c,(w+10,30))
    ImageDraw.Draw(r).text((6,8),n+'   photo | render',fill=(235,235,235));rows.append(r)
W=max(r.width for r in rows);B=Image.new('RGB',(W,sum(r.height+8 for r in rows)),(20,20,20));y=0
for r in rows:B.paste(r,(0,y));y+=r.height+8
B.save(sys.argv[2])
