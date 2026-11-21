# crop board per part: satellite | model straight down | outline overlay, one row per part of the ground (same crop, same scale)
from PIL import Image,ImageDraw
parts=[('N','North end roof and arch'),('S','South end roof and arch'),('W','West side: facade, podium, seating'),('E','East side: blocks B, C, D, boxes A, E'),
       ('NW','North-west corner'),('NE','North-east corner block'),('SW','South-west corner'),('SE','South-east corner')]
for i in range(0,8,4):
    rows=parts[i:i+4];T=420;bd=Image.new('RGB',(3*T+40,len(rows)*(T+30)+10),(24,24,24));d=ImageDraw.Draw(bd)
    for r,(k,lab) in enumerate(rows):
        y=r*(T+30)+30;d.text((10,y-22),lab+'  (satellite | model straight down, same lean | outlines on satellite)',fill=(255,255,255))
        for c,tag in enumerate(('sat','model','on')):bd.paste(Image.open('t_%s_%s.jpg'%(tag,k)).resize((T,T)),(10+c*(T+10),y))
    bd.save('board_parts_%d.jpg'%(i//4+1),quality=90)
print('ok')
