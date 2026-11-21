import json,sys,numpy as np
from PIL import Image,ImageDraw
from f2w import w2f
src,out,x0,y1,k=sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4]),float(sys.argv[5])
G=json.load(open('osm/geo.json'))['geo'];pp=np.array(G['242194673'])
F=w2f(pp);im=Image.open(src).convert('RGB');d=ImageDraw.Draw(im)
f=lambda p:((p[0]-x0)*k,(y1-p[1])*k)
d.line([f(q) for q in list(F)+[F[0]]],fill=(255,0,255),width=1)
P=json.load(open('prims.json'));ring=[p for p in P if p['name']=='fence_ring'][0]['pts'];d.line([f(q) for q in ring+[ring[0]]],fill=(0,255,255),width=1)
im.save(out);json.dump(F.tolist(),open('osm_pitch_field.json','w'))
