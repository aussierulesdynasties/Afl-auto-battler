# overlay model plan lines (fence ring, stand roof, clubrooms roofs, towers) on a field-frame satellite image
import json,sys
from PIL import Image,ImageDraw
src,out,x0,y1,k=sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4]),float(sys.argv[5])
im=Image.open(src).convert('RGB');d=ImageDraw.Draw(im)
f=lambda p:((p[0]-x0)*k,(y1-p[1])*k)
P=json.load(open('prims.json'))
ring=[p for p in P if p['name']=='fence_ring'][0]['pts'];d.line([f(q) for q in ring+[ring[0]]],fill=(0,255,255),width=1)
for J,c in(('stand.json',(255,0,0)),('club_uv.json',(255,255,0))):
    for g in json.load(open(J))['G']:
        if 'roof_top' in g['name'] or 'canopy_top' in g['name'] or (J=='club_uv.json' and 'roof' in g['name']):
            for fc in g['F']:d.polygon([f(g['V'][i]) for i in fc],outline=c)
for k_,v in json.load(open('towers.json')).items():b=f(v['base']);d.ellipse([b[0]-3,b[1]-3,b[0]+3,b[1]+3],outline=(255,0,255))
im.save(out)
