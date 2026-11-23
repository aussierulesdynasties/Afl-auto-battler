# Orthophoto of a model-frame box at height z from the six straight-down Google Earth shots (gtrace.shots), with a grid:
# python3 ortho.py x0 x1 y0 y1 z res out.png [grid_m]. Working images only: never commit the output (docs/MCG_STANDARD.md).
import sys,json,numpy as np,math
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import gtrace as G
from PIL import Image,ImageDraw
from scipy.ndimage import map_coordinates
x0,x1,y0,y1,z,res=[float(a) for a in sys.argv[1:7]];out=sys.argv[7]
S=[s for s in G.shots()]
xs=np.arange(x0,x1,res);ys=np.arange(y1,y0,-res);X,Y=np.meshgrid(xs,ys)
best=np.full(X.shape,1e9);img=np.zeros(X.shape+(3,))
for s in S:
    u,v=G.proj(s,X,Y,z);d=np.hypot(u-640,v-360)
    ok=(u>3)&(u<1276)&(v>35)&(v<716)&(d<best)
    for c in range(3):
        ch=map_coordinates(s['im'][:,:,c],[v,u],order=1,mode='nearest');img[...,c]=np.where(ok,ch,img[...,c])
    best=np.where(ok,d,best)
im=Image.fromarray(img.clip(0,255).astype(np.uint8));dr=ImageDraw.Draw(im)
GS=int(sys.argv[8]) if len(sys.argv)>8 else 10
for gx in range(int(math.ceil(x0/GS))*GS,int(x1)+1,GS):
    c=int((gx-x0)/res);dr.line([(c,0),(c,im.height)],fill=(255,0,255) if gx%50==0 else (0,255,255),width=1);dr.text((c+2,2),str(gx),fill=(255,255,0))
for gy in range(int(math.ceil(y0/GS))*GS,int(y1)+1,GS):
    r=int((y1-gy)/res);dr.line([(0,r),(im.width,r)],fill=(255,0,255) if gy%50==0 else (0,255,255),width=1);dr.text((2,r+2),str(gy),fill=(255,255,0))
im.save(out);print(im.size)
