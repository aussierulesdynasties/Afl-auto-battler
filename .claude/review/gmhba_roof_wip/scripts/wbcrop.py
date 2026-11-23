import math,io,sys,urllib.request,numpy as np
from PIL import Image,ImageDraw
lat0,lon0=-38.158219,144.354577;Z=19;REL=int(sys.argv[7]) if len(sys.argv)>7 else 3692
x0,x1,y0,y1,ppm,out=[float(a) for a in sys.argv[1:6]]+[sys.argv[6]]
def ll(x,y):return lat0+y/111320.0,lon0+x/(111320.0*math.cos(math.radians(lat0)))
def tp(lat,lon):
    n=2**Z;tx=(lon+180)/360*n;la=math.radians(lat);ty=(1-math.log(math.tan(la)+1/math.cos(la))/math.pi)/2*n;return tx*256,ty*256
cache={}
def tile(c,r):
    if (c,r) not in cache:
        u=f'https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/WMTS/1.0.0/default028mm/MapServer/tile/{REL}/{Z}/{r}/{c}'
        cache[(c,r)]=np.array(Image.open(io.BytesIO(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})).read())).convert('RGB'))
    return cache[(c,r)]
W,H=int((x1-x0)*ppm),int((y1-y0)*ppm);img=np.zeros((H,W,3),np.uint8)
for j in range(H):
    for i in range(W):
        px,py=tp(*ll(x0+(i+.5)/ppm,y1-(j+.5)/ppm));c,r=int(px//256),int(py//256)
        img[j,i]=tile(c,r)[int(py%256),int(px%256)]
im=Image.fromarray(img).resize((W*2,H*2),Image.NEAREST);d=ImageDraw.Draw(im)
for g in range(int(math.ceil(x0/5)*5),int(x1)+1,5):X=(g-x0)*ppm*2;d.line([(X,0),(X,H*2)],fill=(255,0,0) if g%10==0 else (255,255,0))
for g in range(int(math.ceil(y0/5)*5),int(y1)+1,5):Y=(y1-g)*ppm*2;d.line([(0,Y),(W*2,Y)],fill=(255,0,0) if g%10==0 else (255,255,0))
d.text((4,4),f'Esri Wayback 2026-11-18 z19; grid 5 m (red 10); X {x0}..{x1} Y {y1}..{y0}',fill=(255,255,255));im.save(out)
