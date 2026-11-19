# Hand-drawn Gorringe gable pieces copied from the photo (run after textures3.py): the clock in its square dark frame,
# and the stand's own name board "HORRIE GORRINGE STAND" (grey board, white capitals) under it. No photo pixels.
import json,math,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageStat
S=json.load(open('tex/sizes.json'))
im=Image.new('RGB',(512,512),(196,176,146));d=ImageDraw.Draw(im)
d.rectangle((22,22,490,490),fill=(74,56,46))                          # dark frame box
d.ellipse((58,58,454,454),fill=(40,36,34));d.ellipse((70,70,442,442),fill=(242,240,232))
for k in range(60):
    t=k/60*2*math.pi;r0=150 if k%5 else 132
    d.line((256+r0*math.sin(t),256-r0*math.cos(t),256+164*math.sin(t),256-164*math.cos(t)),fill=(25,25,25),width=8 if k%5==0 else 3)
d.line((256,256,256+95*math.sin(1.2),256-95*math.cos(1.2)),fill=(20,20,20),width=12);d.line((256,256,256+140*math.sin(5.9),256-140*math.cos(5.9)),fill=(20,20,20),width=8)
a=np.asarray(im).astype(float);a+=np.random.default_rng(7).normal(0,4,a.shape[:2])[...,None];Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save('tex/clock.png');S['clock']=(1.0,1.0)
W,H=2048,166;im=Image.new('RGB',(W,H),(128,128,132));d=ImageDraw.Draw(im);d.rectangle((0,0,W-1,H-1),outline=(70,70,74),width=10)
try:fn=ImageFont.truetype('arialbd.ttf',120)
except Exception:fn=ImageFont.load_default()
t='HORRIE GORRINGE STAND';bb=d.textbbox((0,0),t,font=fn);d.text(((W-(bb[2]-bb[0]))/2-bb[0],(H-(bb[3]-bb[1]))/2-bb[1]),t,fill=(236,236,232),font=fn)
a=np.asarray(im).astype(float);a+=np.random.default_rng(8).normal(0,4,a.shape[:2])[...,None];Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save('tex/gor_name.png');S['gor_name']=(3.2,0.26)
json.dump(S,open('tex/sizes.json','w'))
for n in('clock','gor_name'):print(n,'sd',round(ImageStat.Stat(Image.open(f'tex/{n}.png').convert('L')).stddev[0],1))
