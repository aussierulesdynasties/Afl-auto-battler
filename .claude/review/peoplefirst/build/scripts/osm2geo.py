import json,math
from PIL import Image,ImageDraw
d=json.load(open('osm/raw.json',encoding='utf-8'))
lat0,lon0=-28.0064,153.3666
def xy(g):return (round((g['lon']-lon0)*111320*math.cos(math.radians(lat0)),2),round((g['lat']-lat0)*110574,2))
G={}
for e in d['elements']:
    if 'geometry' in e:G[str(e['id'])]=[xy(g) for g in e['geometry']]
pp=G['355376900'];ox=(min(p[0] for p in pp)+max(p[0] for p in pp))/2;oy=(min(p[1] for p in pp)+max(p[1] for p in pp))/2
G={k:[(round(x-ox,2),round(y-oy,2)) for x,y in v] for k,v in G.items()}
json.dump(G,open('osm/geo.json','w'))
im=Image.new('RGB',(1000,1000),'white');dr=ImageDraw.Draw(im)
s=3.2;P=lambda p:(500+p[0]*s,500-p[1]*s)
for x in range(-150,151,25):
    dr.line([P((x,-150)),P((x,150))],fill=(230,230,230));dr.line([P((-150,x)),P((150,x))],fill=(230,230,230))
    dr.text(P((x,-148)),str(x),fill=(150,150,150));dr.text(P((-148,x)),str(x),fill=(150,150,150))
for k,pts in G.items():
    dr.line([P(p) for p in pts],fill=(0,0,0),width=1);c=pts[0];dr.text(P(c),k[-4:],fill=(255,0,0))
im.save('plan.png')
for k in ('355376900','355376898','1228620773','355377361','1228620775','1228620776'):
    xs=[p[0] for p in G[k]];ys=[p[1] for p in G[k]];print(k,min(xs),max(xs),min(ys),max(ys))
