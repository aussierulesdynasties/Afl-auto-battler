import json,math
from PIL import Image,ImageDraw
d=json.load(open('osm/raw.json',encoding='utf-8'))
N={e['id']:(e['lat'],e['lon']) for e in d['elements'] if e['type']=='node'}
W={e['id']:e for e in d['elements'] if e['type']=='way'}
pitch=W[4941717]['nodes'];la=sum(N[n][0] for n in pitch)/len(pitch);lo=sum(N[n][1] for n in pitch)/len(pitch)
def xy(n):lat,lon=N[n];return ((lon-lo)*111320*math.cos(math.radians(la)),(lat-la)*110574)
st=[xy(n) for n in W[457102567]['nodes']]
def inside(p,poly):
    x,y=p;c=False
    for i in range(len(poly)):
        x1,y1=poly[i];x2,y2=poly[i-1]
        if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:c=not c
    return c
G={'pitch':[xy(n) for n in pitch],'stadium':st}
info={}
for wid,e in W.items():
    t=e.get('tags',{})
    if 'building' in t:
        pts=[xy(n) for n in e['nodes']];c=(sum(p[0] for p in pts)/len(pts),sum(p[1] for p in pts)/len(pts))
        if inside(c,st) or math.hypot(*c)<140:G[str(wid)]=pts;info[wid]=(t.get('name',''),t.get('building'),t.get('building:levels'),[round(v) for v in c])
masts=[xy(e['id']) for e in d['elements'] if e['type']=='node' and e.get('tags',{}).get('tower:type')=='lighting']
G['masts']=masts
json.dump(G,open('osm/geo.json','w'),indent=0)
for k,v in info.items():print(k,v)
print('masts',[(round(x,1),round(y,1)) for x,y in masts])
xs=[p[0] for p in G['pitch']];ys=[p[1] for p in G['pitch']];print('pitch extent',min(xs),max(xs),min(ys),max(ys))
S=4;im=Image.new('RGB',(1200,1200),'white');dr=ImageDraw.Draw(im)
f=lambda p:(600+p[0]*S,600-p[1]*S)
for k,v in G.items():
    if k=='masts':continue
    dr.line([f(p) for p in v],fill=(0,140,0) if k=='pitch' else (0,0,0) if k=='stadium' else (200,0,0),width=2)
    if k not in('pitch','stadium'):dr.text(f((sum(p[0] for p in v)/len(v),sum(p[1] for p in v)/len(v))),k[-4:],fill=(0,0,255))
for m in masts:dr.ellipse([f(m)[0]-5,f(m)[1]-5,f(m)[0]+5,f(m)[1]+5],fill=(255,0,0))
for x in range(-140,141,20):dr.line([f((x,-140)),f((x,140))],fill=(220,220,220))
im.save('plan.png')
