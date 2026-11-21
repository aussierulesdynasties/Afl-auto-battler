import json
from PIL import Image, ImageDraw
X0,X1,Y0,Y1=40,260,-140,-20
S=Image.open('data/optus/sat.png').convert('RGB')
a=S.crop(((X0+1500)/.5,(1500-Y1)/.5,(X1+1500)/.5,(1500-Y0)/.5)).resize((880,480),Image.LANCZOS)
G=Image.open('data/optus/prep/ground.png').convert('RGB')
g=G.crop(((X0+1500)/1.5,(1500-Y1)/1.5,(X1+1500)/1.5,(1500-Y0)/1.5)).resize((880,480),Image.BILINEAR)
B=json.load(open('data/optus/prep/forecourt.json'));F=Image.open('data/optus/prep/forecourt.png')
f=F.crop(((X0-B['x0'])/.1,(B['y1']-Y1)/.1,(X1-B['x0'])/.1,(B['y1']-Y0)/.1)).resize((880,480)); g.paste(f,(0,0),f)
o=Image.new('RGB',(880,960)); o.paste(a,(0,0)); o.paste(g,(0,480))
d=ImageDraw.Draw(o)
for k in range(0,880,80): d.line([(k,0),(k,960)],fill=(255,255,0)); d.text((k+2,2),str(X0+k//4),fill=(255,255,0))
for k in range(0,480,80): d.line([(0,k),(880,k)],fill=(255,255,0)); d.line([(0,k+480),(880,k+480)],fill=(255,255,0)); d.text((2,k+2),str(Y1-k//4),fill=(255,255,0))
o.save('_south.jpg',quality=88)
