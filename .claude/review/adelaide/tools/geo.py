import json,math
from PIL import Image,ImageDraw
d=json.load(open('raw.json',encoding='utf-8'))
P=[e for e in d['elements'] if e['type']=='way' and e['id']==4681536][0]
lat0=sum(g['lat'] for g in P['geometry'])/len(P['geometry']);lon0=sum(g['lon'] for g in P['geometry'])/len(P['geometry'])
k=111320.0
def xy(lat,lon):return ((lon-lon0)*k*math.cos(math.radians(lat0)),(lat-lat0)*110574.0)
keep=[4681536,111572163,191661675,271422946,271422949,621876938,621879217,621895966,268922032,1238356686,1238356692,621872719,1051207116]
G={};T=[]
for e in d['elements']:
    if e['type']=='way' and e['id'] in keep:G[str(e['id'])]=[xy(g['lat'],g['lon']) for g in e['geometry']]
    if e['type']=='node' and e.get('tags',{}).get('tower:type')=='lighting':T.append((e['id'],)+xy(e['lat'],e['lon']))
json.dump({'origin':[lat0,lon0],'ways':G,'towers':T},open('geo.json','w'))
S=3;W=1100;im=Image.new('RGB',(W,W),'white');dr=ImageDraw.Draw(im)
def px(p):return (W/2+p[0]*S,W/2-p[1]*S)
cols=['green','blue','purple','red','orange','cyan','magenta','brown','gray','olive','teal','navy','lime']
for i,(kk,pts) in enumerate(G.items()):
    dr.line([px(p) for p in pts],fill=cols[i%len(cols)],width=2);c=pts[0];dr.text(px(c),kk,fill=cols[i%len(cols)])
for t in T:
    q=px(t[1:]);dr.ellipse([q[0]-4,q[1]-4,q[0]+4,q[1]+4],fill='red');dr.text((q[0]+5,q[1]),str(t[0])[-2:],fill='black')
im.save('plan.png')
for kk,pts in G.items():
    xs=[p[0] for p in pts];ys=[p[1] for p in pts];print(kk,round(min(xs)),round(max(xs)),round(min(ys)),round(max(ys)))
for t in T:print(t[0],round(t[1],1),round(t[2],1),round(math.hypot(t[1],t[2]),1))
