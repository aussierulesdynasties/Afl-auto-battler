# python work/epi.py A u v B out : draw ray from view A pixel into view B (z marks every 5 m), gridded crop
import sys,numpy as np;sys.path.insert(0,'work');import tri,earthcam as E
from PIL import Image,ImageDraw
A,u,v,B,out=sys.argv[1],float(sys.argv[2]),float(sys.argv[3]),sys.argv[4],sys.argv[5]
o,d=tri.ray(A,u,v);cb=tri.camv(B);im=Image.open(f'ge/{B}.png').convert('RGB');dr=ImageDraw.Draw(im)
pts=[]
for z in np.arange(-6,61,1.0):
    s=(z-o[2])/d[2];X=o+s*d;p=E.proj(cb,X)
    if p is None: continue
    pts.append((p[0],p[1],z))
for (a,b,z),(c,e,_) in zip(pts,pts[1:]):dr.line([a,b,c,e],fill=(255,0,0),width=1)
for a,b,z in pts:
    if z%5==0:dr.line([a-4,b,a+4,b],fill=(255,0,0));dr.text((a+5,b-5),str(int(z)),fill=(255,255,0))
us=[p[0] for p in pts];vs=[p[1] for p in pts]
x0,y0=int(max(0,min(us)-150)),int(max(0,min(vs)-80));x1,y1=int(min(1920,max(us)+150)),int(min(1080,max(vs)+80))
im.save('work/_epi.png')
import subprocess;subprocess.run(['python','work/ggrid.py','work/_epi.png',str(x0),str(y0),str(x1),str(y1),out,'2'])
