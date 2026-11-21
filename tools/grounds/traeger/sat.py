import math,json,urllib.request,io
from PIL import Image
lat0,lon0=json.load(open('osm/geo.json'))['origin'];z=18
def tile(lat,lon):
    n=2**z;x=(lon+180)/360*n;y=(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n;return x,y
cx,cy=tile(lat0,lon0);R=4
x0,y0=int(cx)-R,int(cy)-R;im=Image.new('RGB',(256*(2*R+1),256*(2*R+1)))
for i in range(2*R+1):
    for j in range(2*R+1):
        u=f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y0+j}/{x0+i}'
        req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
        im.paste(Image.open(io.BytesIO(urllib.request.urlopen(req,timeout=30).read())).convert('RGB'),(i*256,j*256))
im.save('sat/sat.png')
mpp=156543.03392*math.cos(math.radians(lat0))/2**z
json.dump({'x0':x0,'y0':y0,'cx':cx,'cy':cy,'z':z,'mpp':mpp},open('sat/sat.json','w'));print(im.size,mpp,(cx-x0)*256,(cy-y0)*256)
