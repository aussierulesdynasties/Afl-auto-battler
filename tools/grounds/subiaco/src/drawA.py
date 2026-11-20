import numpy as np,json,math,sys
from PIL import Image,ImageDraw
exec(open('fitA11.py').read().split('best=None\nfor f0')[0])
p=np.array(json.loads(sys.argv[1]));out=sys.argv[2]
im=Image.open('refs/c/01.jpg').convert('RGB');d=ImageDraw.Draw(im)
ov,sq,arcs=model(p);cam=p[:7]
for P,c in [(ov,(255,255,0)),(sq,(0,255,255))]+[(a,(255,0,255)) for a in arcs]:
    q=pd(cam,P);d.line([tuple(x) for x in q],fill=c,width=1)
q=pd(cam,RR);d.line([tuple(x) for x in q],fill=(0,255,0),width=1)
for x,y in RRI:d.ellipse([x-3,y-3,x+3,y+3],outline=(255,0,0))
im.save(out)
