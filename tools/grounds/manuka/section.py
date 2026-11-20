import sys;from polar import *
from PIL import Image,ImageDraw
def sect(deg,out,dmax=60,zmax=25,k=2.5):
    a=math.radians(deg)
    pts=np.array([[d,z] for d in range(-5,dmax+1,5) for z in range(0,zmax+1,5)])
    Y=proj([P_(a,d,z) for d,z in pts])
    x0,y0=Y.min(0)-40;x1,y1=Y.max(0)+40
    x0,y0=max(0,x0),max(0,y0);x1,y1=min(1920,x1),min(1280,y1)
    im=Image.open('photo.png').convert('RGB').crop((int(x0),int(y0),int(x1),int(y1)));im=im.resize((int((x1-x0)*k),int((y1-y0)*k)),Image.LANCZOS);dr=ImageDraw.Draw(im)
    T=lambda p:((p[0]-x0)*k,(p[1]-y0)*k)
    for d in range(-5,dmax+1,5):
        L=proj([P_(a,d,z) for z in range(0,zmax+1)]);dr.line([T(p) for p in L],fill=(255,255,0) if d%10==0 else (0,200,255),width=1)
        dr.text(T(L[0]),str(d),fill=(255,255,0))
    for z in range(0,zmax+1,5):
        L=proj([P_(a,d,z) for d in range(-5,dmax+1)]);dr.line([T(p) for p in L],fill=(255,0,255) if z%10==0 else (0,255,0),width=1)
        dr.text(T(L[-1]),f'z{z}',fill=(255,0,255))
    im.save(out)
for deg in sys.argv[1:]:sect(float(deg),f'z/sec{deg}.png')
