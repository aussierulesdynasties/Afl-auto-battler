# Oval Hotel wings and East Gate glass, drawn from eastgate_a_2026. 20 px/m. hotel tile 12 x 21 m, gate tile 12 x 21 m
import numpy as np, random
from PIL import Image, ImageDraw
P=20; W,H=12*P,21*P; random.seed(3)
def Y(z): return H-int(z*P)
h=Image.new('RGB',(W,H),(40,30,26)); d=ImageDraw.Draw(h)
d.rectangle([0,Y(2.4),W,Y(0)],fill=(36,38,42))                       # ground floor shadowed glazing
for x in (0,6): d.rectangle([x*P,Y(2.4),x*P+12,Y(0)],fill=(150,144,132))
cop=[(104,58,40),(92,50,36),(116,66,44)]
for x in np.arange(0,12,0.6):                                        # vertical copper fins
    d.rectangle([int(x*P),Y(20),int(x*P)+9,Y(2.4)],fill=cop[int(x/0.6)%3])
for f in range(5):                                                   # 5 floors, windows two per 6 m bay
    z0=2.4+f*3.5
    d.rectangle([0,Y(z0+0.35),W,Y(z0)],fill=(26,26,30))              # slab edge
    for xw in (1.0,4.0,7.0,10.0):
        if (f+int(xw))%4==3: continue
        d.rectangle([int(xw*P),Y(z0+3.0),int((xw+1.4)*P),Y(z0+0.7)],fill=(120,150,170))
        d.rectangle([int(xw*P)+3,Y(z0+3.0)+3,int((xw+1.4)*P)-3,Y(z0+0.7)-3],fill=(90,118,138))
d.rectangle([0,Y(20),W,Y(19.4)],fill=(24,24,28))
h.save('hotel_facade.png')
g=Image.new('RGB',(W,H),(52,82,100)); d=ImageDraw.Draw(g)
d.rectangle([0,Y(5),W,Y(0)],fill=(30,32,36))
for x in (0,6): d.rectangle([x*P,Y(5),x*P+10,Y(0)],fill=(40,40,44))
d.rectangle([0,Y(6),W,Y(5)],fill=(26,28,32)); d.rectangle([0,Y(11.4),W,Y(10.4)],fill=(26,28,32))
d.rectangle([0,Y(7.5),W,Y(6)],fill=(84,116,132))                     # even sky reflection band
for x in np.arange(0,12,1.5): d.line([int(x*P),Y(20),int(x*P),Y(6)],fill=(28,34,40),width=3)
for z in (8,13.5,16,18.5): d.line([0,Y(z),W,Y(z)],fill=(28,34,40),width=3)
d.rectangle([0,Y(20),W,Y(19.3)],fill=(24,24,28))
g.save('gate_facade.png')
