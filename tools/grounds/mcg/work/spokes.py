# python work/spokes.py view z r0 r1 step_deg out [b0 b1] : radial rulers (ticks every 1 m, labels every 5 m) projected at height z
import sys,numpy as np;sys.path.insert(0,'work');import tri,earthcam as E
from PIL import Image,ImageDraw,ImageOps,ImageEnhance
v,z,r0,r1,st,out=sys.argv[1],float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4]),float(sys.argv[5]),sys.argv[6]
b0,b1=(float(sys.argv[7]),float(sys.argv[8])) if len(sys.argv)>8 else (0,360)
c=tri.camv(v);im=Image.open(f'ge/{v}.png').convert('RGB');im=ImageEnhance.Brightness(ImageOps.autocontrast(im,cutoff=2)).enhance(1.5)
K=int(__import__("os").environ.get("K","2"));im=im.resize((im.width*K,im.height*K));d=ImageDraw.Draw(im)
P=lambda b,r:K*E.proj(c,[r*np.sin(np.radians(b)),r*np.cos(np.radians(b)),z])
us=[];vs=[]
for b in np.arange(b0,b1+0.01,st):
    a=P(b,r0);e=P(b,r1);d.line([*a,*e],fill=(255,0,255),width=1);d.text((e[0]+3,e[1]),f'{b:g}',fill=(255,255,0))
    for r in np.arange(np.ceil(r0),r1+0.01,1):
        p=P(b,r);L=6 if r%5==0 else 3
        n=np.array([np.cos(np.radians(b)),np.sin(np.radians(b))])
        d.line([p[0]-L*n[0],p[1]-L*n[1],p[0]+L*n[0],p[1]+L*n[1]],fill=(255,0,255))
        if r%5==0:d.text((p[0]+7*n[0]+2,p[1]+7*n[1]-5),str(int(r)),fill=(255,255,255))
        us.append(p[0]);vs.append(p[1])
im.crop((int(min(us))-40,int(min(vs))-40,int(max(us))+40,int(max(vs))+40)).save(out)
