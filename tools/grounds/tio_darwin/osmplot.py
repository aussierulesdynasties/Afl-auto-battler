import json
from PIL import Image,ImageDraw
from geo import *
d=json.load(open('osm/area.json',encoding='utf-8'))
im=Image.open('sat/sat19.png').convert('RGB');dr=ImageDraw.Draw(im)
out={}
for e in d['elements']:
    t=e.get('tags',{});g=e.get('geometry')
    if not g or not t: continue
    pts=[ll2m(p['lat'],p['lon']) for p in g]
    col=None
    if e['id'] in (121389821,):col=(0,255,255);out['pitch']=pts
    elif e['id']==121389822:col=(255,0,255);out['stadium']=pts
    elif 'building' in t:col=(255,255,0);out.setdefault('buildings',{})[str(e['id'])]=pts
    elif t.get('barrier')=='fence':col=(255,128,0);out['fence_'+str(e['id'])]=pts
    if col:dr.line([m2px(*p) for p in pts],fill=col,width=3)
for r in range(-200,201,50):
    dr.line([m2px(r,-200),m2px(r,200)],fill=(255,0,0) if r==0 else (120,0,0));dr.line([m2px(-200,r),m2px(200,r)],fill=(255,0,0) if r==0 else (120,0,0))
json.dump(out,open('osm/osm_m.json','w'))
c=m2px(0,0);im.crop((int(c[0]-700),int(c[1]-700),int(c[0]+700),int(c[1]+700))).save('sat/osm_over.jpg')
import numpy as np;p=np.array(out['pitch']);print('pitch extent',p.min(0),p.max(0))
