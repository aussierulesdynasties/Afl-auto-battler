import math,json,urllib.request,io,sys
from PIL import Image
lat0,lon0=json.load(open('osm/geo.json'))['origin']
z=int(sys.argv[1]);X0,X1,Y0,Y1=map(float,sys.argv[2:6]);out=sys.argv[6]
k=111320.0
def ll(x,y):return lat0+y/110574.0,lon0+x/(k*math.cos(math.radians(lat0)))
def tile(lat,lon):
    n=2**z;return (lon+180)/360*n,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n
a=tile(*ll(X0,Y1));b=tile(*ll(X1,Y0))
tx0,ty0,tx1,ty1=int(a[0]),int(a[1]),int(b[0]),int(b[1])
im=Image.new('RGB',(256*(tx1-tx0+1),256*(ty1-ty0+1)))
for i in range(tx0,tx1+1):
    for j in range(ty0,ty1+1):
        u=f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{j}/{i}'
        t=Image.open(io.BytesIO(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read())).convert('RGB')
        im.paste(t,((i-tx0)*256,(j-ty0)*256))
im.save(out)
c=tile(lat0,lon0);mpp=156543.03392*math.cos(math.radians(lat0))/2**z
json.dump({'z':z,'tx0':tx0,'ty0':ty0,'cx':c[0],'cy':c[1],'mpp':mpp},open(out+'.json','w'));print(im.size,mpp)
