# radial brightness/colour profile strips from a view at height z: one row per bearing (2 deg), columns r 60..170 at 4 px/m
import sys,numpy as np;sys.path.insert(0,'work');import tri,earthcam as E
from PIL import Image,ImageDraw
v,z,out=sys.argv[1],float(sys.argv[2]),sys.argv[3]
c=tri.camv(v);im=np.asarray(Image.open(f'ge/{v}.png').convert('RGB')).astype(float)
R=np.arange(60,170,0.25);B=np.arange(0,360,1.0)
S=np.zeros((len(B)*3,len(R),3),np.uint8)
for i,b in enumerate(B):
    a=np.radians(b);X=np.stack([R*np.sin(a),R*np.cos(a),np.full_like(R,z)],1)
    P=np.array([E.proj(c,x) for x in X]);u=np.clip(P[:,0].round().astype(int),0,1919);w=np.clip(P[:,1].round().astype(int),0,1079)
    S[i*3:i*3+3]=im[w,u]
I=Image.fromarray(S).resize((len(R)*2,len(B)*3));d=ImageDraw.Draw(I)
for r in range(60,170,10):
    x=(r-60)*8;d.line([x,0,x,I.height],fill=(255,0,255));d.text((x+2,2),str(r),fill=(255,0,255))
for b in range(0,360,10):
    y=b*3;d.line([0,y,I.width,y],fill=(255,255,0));d.text((2,y+1),str(b),fill=(255,255,0))
I.save(out)
