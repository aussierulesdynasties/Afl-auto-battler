import json,numpy as np
from PIL import Image,ImageDraw
im=Image.open('data/mcg/sat19.png').convert('RGB')
T=[np.array(t) for t in json.load(open('out/mcg/rails/plan_tracks.json'))]
toes=json.load(open('out/mcg/rails/toes.json'));H=15;S=300
tiles=[]
for i,p in enumerate(toes):
  x0,x1,y0,y1=p[0]-H,p[0]+H,p[1]-H,p[1]+H
  c=im.crop((int((x0+700)/.25),int((700-y1)/.25),int((x1+700)/.25),int((700-y0)/.25))).resize((S,S))
  d=ImageDraw.Draw(c);f=lambda q:((q[0]-x0)/(2*H)*S,(y1-q[1])/(2*H)*S)
  for t in T:
    m=(abs(t[:,0]-p[0])<H+2)&(abs(t[:,1]-p[1])<H+2)
    if m.sum()>1: d.line([f(q) for q in t[m]],fill=(0,255,255),width=1)
  q=f(p);d.ellipse((q[0]-4,q[1]-4,q[0]+4,q[1]+4),outline=(255,0,0),width=2)
  d.rectangle((0,0,120,14),fill=(0,0,0));d.text((2,1),'%d (%.0f,%.0f)'%(i,p[0],p[1]),fill=(255,255,0))
  tiles.append(c)
for s in range(0,len(tiles),16):
  B=Image.new('RGB',(4*S,4*S))
  for k,t in enumerate(tiles[s:s+16]): B.paste(t,((k%4)*S,(k//4)*S))
  B.save('out/mcg/rails/toes_%02d.png'%(s//16))
print(len(tiles))
