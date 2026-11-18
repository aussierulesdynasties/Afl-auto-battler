# projo.py box(x0 y0 x1 y1) scale out polys.json : draw 3D polylines (world m) on the photo crop with grid
import sys,json,numpy as np
from PIL import Image,ImageDraw
from gpaint_cam import R
p=json.load(open('cam.json'))['p'];C=np.array(p[:3]);M=R(*p[3:6]);f=p[6];W,H=2000,1333
def pr(X):
    d=M@(np.array(X,float)-C);return (W/2+f*d[0]/d[2],H/2-f*d[1]/d[2])
x0,y0,x1,y1=map(int,sys.argv[1:5]);s=float(sys.argv[5]);out=sys.argv[6];polys=json.load(open(sys.argv[7]))
im=Image.open('photo_clean.png').convert('RGB').crop((x0,y0,x1,y1));im=im.resize((int((x1-x0)*s),int((y1-y0)*s)),Image.BICUBIC)
dr=ImageDraw.Draw(im);step=10
for x in range((x0//step+1)*step,x1,step):dr.line([((x-x0)*s,0),((x-x0)*s,im.size[1])],fill=(255,255,0) if x%50==0 else (120,120,0))
for y in range((y0//step+1)*step,y1,step):dr.line([(0,(y-y0)*s),(im.size[0],(y-y0)*s)],fill=(255,0,255) if y%50==0 else (120,0,120))
for x in range((x0//50+1)*50,x1,50):dr.text(((x-x0)*s+2,2),str(x),fill=(255,255,0))
for y in range((y0//50+1)*50,y1,50):dr.text((2,(y-y0)*s+2),str(y),fill=(255,0,255))
cols=[(0,255,255),(0,255,0),(255,128,0),(255,0,0),(0,128,255)]
for i,pl in enumerate(polys):
    pts=[pr(X) for X in pl['p']];pts=[((u-x0)*s,(v-y0)*s) for u,v in pts]
    dr.line(pts+([pts[0]] if pl.get('closed',1) else []),fill=cols[i%5],width=2)
im.save(out)
