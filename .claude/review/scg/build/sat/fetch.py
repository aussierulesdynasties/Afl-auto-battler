# Esri World Imagery tiles around the SCG + the lat/lon <-> world-metre map, solved from OSM nodes in geo.json
import math,io,json,urllib.request,numpy as np
from PIL import Image
G=json.load(open('osm/geo.json'))['geo'];raw=json.load(open('osm/scg.json',encoding='utf-8'))
nodes={('T%d'%e['id']):(e['lat'],e['lon']) for e in raw['elements'] if e['type']=='node' and 'lat' in e}
ks=[k for k in G if k in nodes];A=[];B=[]
for k in ks:la,lo=nodes[k];A.append([lo,la,1]);B.append(G[k][0][:2])
A=np.array(A);B=np.array(B);X=np.linalg.lstsq(A,B,rcond=None)[0];res=np.abs(A@X-B).max()
print('nodes',len(ks),'fit residual m',res)
P=np.array(G['4000006'])[:-1].mean(0)
# invert: world (x,y) -> lon,lat
M=X[:2].T;t=X[2];Mi=np.linalg.inv(M)
lo,la=Mi@(P-t);print('pitch centre',la,lo)
z=19;n=2**z
def tile(la,lo):return (lo+180)/360*n,(1-math.asinh(math.tan(math.radians(la)))/math.pi)/2*n
cx,cy=tile(la,lo);Rt=4;x0,y0=int(cx)-Rt,int(cy)-Rt
im=Image.new('RGB',(256*(2*Rt+1),256*(2*Rt+1)))
for i in range(2*Rt+1):
    for j in range(2*Rt+1):
        u=f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y0+j}/{x0+i}'
        im.paste(Image.open(io.BytesIO(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'stadium-ref/1.0'})).read())).convert('RGB'),(i*256,j*256))
im.save('sat/sat.png')
json.dump({'z':z,'x0':x0,'y0':y0,'M':M.tolist(),'t':t.tolist()},open('sat/sat.json','w'));print(im.size)
