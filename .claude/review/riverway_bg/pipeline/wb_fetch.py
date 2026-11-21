import math,urllib.request,io,sys
from PIL import Image
R=3692;Z=19;LAT0,LON0=-19.317618,146.731873
def ll(x,y): return LAT0+y/110574, LON0+x/105054
def tile(lat,lon):
    n=2**Z; xt=(lon+180)/360*n; lr=math.radians(lat); yt=(1-math.log(math.tan(lr)+1/math.cos(lr))/math.pi)/2*n; return xt,yt
x0,x1,y0,y1=-800,-340,30,310
a=tile(*ll(x0,y1)); b=tile(*ll(x1,y0))
tx0,ty0,tx1,ty1=int(a[0]),int(a[1]),int(b[0]),int(b[1])
W=Image.new('RGB',((tx1-tx0+1)*256,(ty1-ty0+1)*256))
for tx in range(tx0,tx1+1):
  for ty in range(ty0,ty1+1):
    u=f'https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/WMTS/1.0.0/default028mm/MapServer/tile/{R}/{Z}/{ty}/{tx}'
    d=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read()
    W.paste(Image.open(io.BytesIO(d)).convert('RGB'),((tx-tx0)*256,(ty-ty0)*256))
W.save('data/riverway/wb/wb2026.png')
open('data/riverway/wb/wb2026.txt','w').write(f'{Z} {tx0} {ty0}\n')
print(W.size,tx0,ty0)
