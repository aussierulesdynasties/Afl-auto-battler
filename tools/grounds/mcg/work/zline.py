# python work/zline.py view out b:r[:z0:z1] ... : vertical rulers at plan (bearing,r) with z ticks every 1 m (labels every 5), gridded crop
import sys,numpy as np;sys.path.insert(0,'work');import tri,earthcam as E
from PIL import Image,ImageDraw
v,out=sys.argv[1],sys.argv[2];c=tri.camv(v);im=Image.open(f'ge/{v}.png').convert('RGB')
K=3;im=im.resize((im.width*K,im.height*K));d=ImageDraw.Draw(im);us=[];vs=[]
for spec in sys.argv[3:]:
    p=[float(t) for t in spec.split(':')];b,r=p[0],p[1];z0,z1=(p[2],p[3]) if len(p)>3 else (-6,45)
    x,y=r*np.sin(np.radians(b)),r*np.cos(np.radians(b))
    P=[K*E.proj(c,[x,y,z]) for z in np.arange(z0,z1+0.01,1)]
    d.line([tuple(q) for q in P],fill=(255,0,255),width=1)
    for z,q in zip(np.arange(z0,z1+0.01,1),P):
        L=8 if z%5==0 else 4;d.line([q[0]-L,q[1],q[0]+L,q[1]],fill=(255,0,255))
        if z%5==0:d.text((q[0]+10,q[1]-6),str(int(z)),fill=(255,255,0))
        us.append(q[0]);vs.append(q[1])
    d.text((P[-1][0]-10,P[-1][1]-16),f'r{r:g}',fill=(0,255,255))
im.crop((int(min(us))-120,int(min(vs))-40,int(max(us))+120,int(max(vs))+40)).save(out)
