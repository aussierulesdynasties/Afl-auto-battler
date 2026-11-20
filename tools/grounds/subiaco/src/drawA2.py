import numpy as np,json,math,sys
from PIL import Image,ImageDraw
exec(open('fitA14.py').read().split('p0=np.array')[0])
p=np.array(json.loads(sys.argv[1]));out=sys.argv[2]
im=Image.open('refs/c/01.jpg').convert('RGB');d=ImageDraw.Draw(im)
ov,sq,arcs,gs=mdl(p)
for X,c in [(ov,(255,255,0)),(sq,(0,255,255))]+[(a,(255,0,255)) for a in arcs]+[(np.vstack([g,g[:1]]),(255,128,0)) for g in gs]+[(RR,(0,255,0))]:
    q=P(p,X);d.line([tuple(x) for x in q],fill=c,width=1)
for x,y in RRI:d.ellipse([x-3,y-3,x+3,y+3],outline=(255,0,0))
cam=p[:7];bw=at_z(cam,924,554,cx,cy,2);q=P(p,np.array([bw,bw+[0,0,20]]));d.line([tuple(x) for x in q],fill=(255,0,0),width=2)
im.save(out)
