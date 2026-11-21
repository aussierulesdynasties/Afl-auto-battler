import json,sys,numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,'.');import rail_geo
D='data/mcg/prep/';j=lambda f:json.load(open(D+f))
spec=json.load(open('spec/mcg.json'));KE=spec.get('rail_cut',{}).get('keep_ellipse')
KF=np.array(j('footprint.json')) if spec.get('rail_cut',{}).get('keep_footprint') else None
P=rail_geo.plan(j('rails.json'),KF,KE,j('gantries.json'),j('rail_extra.json'),j('rail_shift.json'))
json.dump([t.tolist() for t in P['tracks']],open('out/mcg/rails/plan_tracks.json','w'))
json.dump(P['toes'],open('out/mcg/rails/toes.json','w'))
im=Image.open('data/mcg/sat19.png').convert('RGB')
x0,y0,x1,y1=[float(v) for v in sys.argv[1:5]];S=int(sys.argv[5]) if len(sys.argv)>5 else 1400
c=im.crop((int((x0+700)/0.25),int((700-y1)/0.25),int((x1+700)/0.25),int((700-y0)/0.25))).resize((S,S),Image.LANCZOS)
d=ImageDraw.Draw(c);f=lambda p:((p[0]-x0)/(x1-x0)*S,(y1-p[1])/(y1-y0)*S)
for t in P['tracks']:
  d.line([f(p) for p in t],fill=(0,255,255),width=1)
for i,p in enumerate(P['toes']):
  if x0<p[0]<x1 and y0<p[1]<y1:
    q=f(p);d.ellipse((q[0]-5,q[1]-5,q[0]+5,q[1]+5),outline=(255,0,0),width=2);d.text((q[0]+6,q[1]-6),str(i),fill=(255,255,0))
c.save(sys.argv[6])
