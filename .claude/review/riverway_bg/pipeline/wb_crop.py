import math,sys
from PIL import Image,ImageDraw
Z,TX0,TY0=map(int,open('data/riverway/wb/wb2026.txt').read().split())
W=Image.open('data/riverway/wb/wb2026.png');LAT0,LON0=-19.317618,146.731873;n=2**Z
def px(x,y):
    lat,lon=LAT0+y/110574,LON0+x/105054;lr=math.radians(lat)
    return ((lon+180)/360*n-TX0)*256,((1-math.log(math.tan(lr)+1/math.cos(lr))/math.pi)/2*n-TY0)*256
nm,x0,x1,y0,y1=sys.argv[1],*map(float,sys.argv[2:6]);S=8
a=px(x0,y1);b=px(x1,y0);c=W.crop((int(a[0]),int(a[1]),int(b[0]),int(b[1])))
c=c.resize((int((x1-x0)*S),int((y1-y0)*S)),Image.LANCZOS);d=ImageDraw.Draw(c)
for x in range(int(x0),int(x1)+1,5):
  col=(255,255,0) if x%10==0 else (0,200,200);d.line([((x-x0)*S,0),((x-x0)*S,c.height)],fill=col)
  if x%10==0:d.text(((x-x0)*S+2,2),str(x),fill=col)
for y in range(int(y0),int(y1)+1,5):
  col=(255,255,0) if y%10==0 else (0,200,200);d.line([(0,(y1-y)*S),(c.width,(y1-y)*S)],fill=col)
  if y%10==0:d.text((2,(y1-y)*S+2),str(y),fill=col)
d.text((4,c.height-14),'Esri Wayback, captured 2026-02-02',fill=(255,255,255))
c.save(f'out/riverway/chk/wb_{nm}.png');print(c.size)
