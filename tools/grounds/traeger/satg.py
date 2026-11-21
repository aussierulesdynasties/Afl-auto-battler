# satellite (any sat/*.png + .json) resampled into the FIELD frame with a 1 m / 5 m grid: python satg.py SAT OUT x0 y0 x1 y1 ppm [nogrid]
import json,sys,numpy as np
from PIL import Image,ImageDraw
from f2w import f2w
src=sys.argv[1];J=json.load(open(src+'.json' if not src.endswith('sat.png') else 'sat/sat.json'));S=np.asarray(Image.open(src).convert('RGB')).astype(float)
tx0=J.get('tx0',J.get('x0'));ty0=J.get('ty0',J.get('y0'))
ox=(J['cx']-tx0)*256;oy=(J['cy']-ty0)*256;m=J['mpp']
x0,y0,x1,y1=map(float,sys.argv[3:7]);k=float(sys.argv[7])
xs=np.arange(x0,x1,1/k);ys=np.arange(y1,y0,-1/k)
X,Y=np.meshgrid(xs,ys);W=f2w(np.stack([X.ravel(),Y.ravel()],1))
u=ox+W[:,0]/m;v=oy-W[:,1]/m
u0=np.clip(np.floor(u).astype(int),0,S.shape[1]-2);v0=np.clip(np.floor(v).astype(int),0,S.shape[0]-2);fu=(u-u0)[:,None];fv=(v-v0)[:,None]
c=S[v0,u0]*(1-fu)*(1-fv)+S[v0,u0+1]*fu*(1-fv)+S[v0+1,u0]*(1-fu)*fv+S[v0+1,u0+1]*fu*fv
im=Image.fromarray(c.reshape(len(ys),len(xs),3).astype(np.uint8))
if len(sys.argv)<9:
    d=ImageDraw.Draw(im)
    for r in range(-400,401,1):
        if r%5:continue
        col=(255,0,0) if r%25==0 else (255,200,0)
        if x0<=r<=x1:
            px=(r-x0)*k;d.line([(px,0),(px,im.height)],fill=col,width=1);d.text((px+2,2),str(r),fill=(255,255,0))
        if y0<=r<=y1:
            py=(y1-r)*k;d.line([(0,py),(im.width,py)],fill=col,width=1);d.text((2,py+2),str(r),fill=(0,255,255))
im.save(sys.argv[2]);print(im.size)
