# top-down proof: Esri satellite (straight down, 0.25 m/px, north up) | model straight down (build2.py top) | overlay
import json,sys,numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as nd
SAT=sys.argv[1]
S=Image.open(SAT).convert('RGBA');T=Image.open('out/top.png').convert('RGBA')
a=np.asarray(T).copy();al=a[...,3].astype(float)
ov=S.copy();h=a.copy();h[...,3]=(al*0.5).astype(np.uint8);ov.alpha_composite(Image.fromarray(h))
m=al>128;e=m^nd.binary_erosion(m,iterations=2);o=np.asarray(ov).copy();o[e]=(255,230,0,255);ov=Image.fromarray(o)
base=S.copy();base.alpha_composite(T)
box=(300,300,1700,1700);W=800
labs=['Esri World Imagery, today, straight down, north up','model straight down, same scale and north','model 50% over satellite, yellow = model outline']
B=Image.new('RGB',(W*3,W+36),(20,20,20));d=ImageDraw.Draw(B)
for k,(im,lab) in enumerate(zip([S,base,ov],labs)):B.paste(im.convert('RGB').crop(box).resize((W,W)),(k*W,36));d.text((k*W+10,12),lab,fill=(255,255,255))
d.line((20,W+20,20+W*100/350,W+20),fill=(255,255,255),width=3);d.text((24,W+2),'100 m',fill=(255,255,255))
B.save('out/topdown_board.jpg',quality=88);ov.convert('RGB').crop(box).save('out/topdown_overlay_full.jpg',quality=90)
