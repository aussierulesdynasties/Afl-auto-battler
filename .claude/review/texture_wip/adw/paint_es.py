# east/south outer facade, hand-drawn from eastgate_a_2026 / southgate_2026. 20 px per metre, tile 36 m x 27 m
import numpy as np
from PIL import Image, ImageDraw
P=20; W,H=36*P,27*P
im=Image.new('RGB',(W,H)); d=ImageDraw.Draw(im)
def y(z): return H-int(z*P)  # z metres -> row
def band(z0,z1,c): d.rectangle([0,y(z1),W,y(z0)],fill=c)
cream=(214,206,186); copper=(92,52,38); glass=(46,62,74); conc=(168,160,146); dark=(30,32,36)
band(0,5,dark)                      # entry glazing at ground
for x in range(0,36,9):             # concrete columns every 9 m
    d.rectangle([x*P,y(5),x*P+int(0.9*P),y(0)],fill=conc)
for x in np.arange(0,36,1.5):       # entry mullions
    d.line([int(x*P),y(5),int(x*P),y(0)],fill=(60,64,70),width=2)
band(5,7,copper)                    # copper band
band(7,13,glass)                    # curtain wall
for x in np.arange(0,36,1.5): d.line([int(x*P),y(13),int(x*P),y(7)],fill=(22,26,30),width=3)
for z in (9.5,11.5): d.line([0,y(z),W,y(z)],fill=(22,26,30),width=3)
d.rectangle([0,y(10.2),W,y(9.6)],fill=(70,92,104))  # sky reflection streak, even
band(13,15,copper)                  # soffit band
band(15,27,cream)                   # raked underside of upper tier
for z in np.arange(15.4,27,0.8): d.line([0,y(z),W,y(z)],fill=(178,170,152),width=4)  # tread undersides
d.rectangle([0,y(16),W,y(15)],fill=(232,228,216))   # balustrade band
for x0 in (0,18):                   # white raking struts, paired diagonals
    for s in (-1,1):
        xa=x0+9; d.line([int(xa*P),y(15),int((xa+s*6)*P),y(27)],fill=(245,245,242),width=int(0.6*P))
im.save('es_facade.png'); print(im.size)
