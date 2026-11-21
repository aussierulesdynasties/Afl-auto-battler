import numpy as np
import json as _j; _B=_j.load(open("data/optus/prep/forecourt.json")); X0=_B["x0"]; Y1=_B["y1"]
from PIL import Image
A=Image.open('data/optus/sat_hi_plaza.png').convert('RGB'); W,H=A.size
G=Image.open('data/optus/prep/ground.png').convert('RGB')
# ground.png: 2000 px over -1500..1500
gx0=(80+1500)/1.5; gy0=(1500-135)/1.5
g=G.crop((gx0,gy0,gx0+180/1.5,gy0+185/1.5)).resize((W,H),Image.BILINEAR)
F=Image.open('data/optus/prep/forecourt.png')
fx0=(80-X0)/0.1; fy0=(Y1-135)/0.1
f=F.crop((fx0,fy0,fx0+1800,fy0+1850)).resize((W,H),Image.BILINEAR)
g.paste(f,(0,0),f)
o=Image.new('RGB',(W*2,H)); o.paste(A,(0,0)); o.paste(g,(W,0)); o.resize((W,H//2)).save('_topchk.jpg',quality=85)
fa=np.asarray(F)[...,3].astype(float); hh,ww=fa.shape
yy,xx=np.mgrid[0:hh,0:ww]; x=X0+xx*0.1; y=Y1-yy*0.1
r=((x+16)/143)**2+(y/128)**2; ins=(r<=1)&(fa>0)
print('fence inside px',ins.sum(),'max r-depth m', (0 if not ins.any() else round(float(143*(1-np.sqrt(r[ins].min()))),2)))
