import math,urllib.request,io,json
from PIL import Image
z=19
# pitch centre in lat/lon: recompute from osm2geo offsets
d=json.load(open('osm/raw.json',encoding='utf-8'))
g=[e for e in d['elements'] if e['id']==355376900][0]['geometry']
lat=(min(p['lat'] for p in g)+max(p['lat'] for p in g))/2;lon=(min(p['lon'] for p in g)+max(p['lon'] for p in g))/2
print('centre',lat,lon)
def tile(lat,lon):
    n=2**z;x=(lon+180)/360*n;y=(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n;return x,y
cx,cy=tile(lat,lon);R=4
x0,y0=int(cx)-R,int(cy)-R
im=Image.new('RGB',(256*(2*R+1),256*(2*R+1)))
for i in range(2*R+1):
    for j in range(2*R+1):
        u=f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y0+j}/{x0+i}'
        im.paste(Image.open(io.BytesIO(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})).read())),(i*256,j*256))
mpp=156543.03392*math.cos(math.radians(lat))/2**z
px=(cx-x0)*256;py=(cy-y0)*256
json.dump({'mpp':mpp,'px':px,'py':py,'lat':lat,'lon':lon},open('sat.json','w'))
print(mpp,px,py,im.size);im.save('sat.png')
