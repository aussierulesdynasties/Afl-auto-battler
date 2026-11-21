# marks satellite edge (red) and model roof edge (cyan) per angle on the satellite; crops around angle clusters
import json,math,numpy as np,sys
from PIL import Image,ImageDraw
X0,Y1,RES=-260,230,0.25;oc=json.load(open('geom.json'))['oc'];rows=json.load(open('r2/roofsat.json'))
im=Image.open('sat/sat_025.png').convert('RGB');d=ImageDraw.Draw(im)
P=lambda x,y:((x-X0)/RES,(Y1-y)/RES)
for a,l,m,dd in rows:
  c,s=math.cos(math.radians(a)),math.sin(math.radians(a))
  d.line([P(oc[0]+c*95,oc[1]+s*95),P(oc[0]+c*165,oc[1]+s*165)],fill=(255,255,0) if dd is not None and abs(dd)>2 else (90,90,0))
  for r,col in ((l,(255,0,0)),(m,(0,255,255))):
    if r is None:continue
    u,v=P(oc[0]+c*r,oc[1]+s*r);d.ellipse([u-3,v-3,u+3,v+3],outline=col,width=2)
  u,v=P(oc[0]+c*168,oc[1]+s*168);d.text((u-8,v-6),str(a),fill=(255,255,255))
im.save('r2/roofmark.png')
for n,a0,a1 in (('E',0,14),('N',84,134),('W',190,236),('S',282,340)):
  am=math.radians((a0+a1)/2);cx,cy=oc[0]+math.cos(am)*135,oc[1]+math.sin(am)*135
  span=max(40,(a1-a0)*math.pi/180*140+20)
  u0,v0=P(cx-span/2,cy+span/2);u1,v1=P(cx+span/2,cy-span/2)
  c=im.crop((int(u0),int(v0),int(u1),int(v1)));k=max(1,int(900/c.size[0]));c.resize((c.size[0]*k,c.size[1]*k),Image.NEAREST).save('r2/roofmark_%s.png'%n)
