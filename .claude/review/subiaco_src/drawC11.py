import sys,json,numpy as np
from PIL import Image,ImageDraw
sys.argv=[sys.argv[0]]+sys.argv[1:]
exec(open(sys.argv[3] if len(sys.argv)>3 else 'fitC11.py').read().split('out=[]')[0])
c11=json.load(open(sys.argv[1]));cam=c11['p'][:7]
im=Image.open('refs/c/03.jpg').convert('RGB');d=ImageDraw.Draw(im)
q=proj(cam,FE3,cx,cy);d.line([tuple(x) for x in q],fill=(255,140,0),width=2)
q=proj(cam,np.c_[RR,np.zeros(len(RR))],cx,cy);d.line([tuple(x) for x in q],fill=(0,255,255),width=2)
for s_ in (1,-1):
  for x in proj(cam,np.c_[posts(s_),np.zeros(4)],cx,cy):d.ellipse([x[0]-3,x[1]-3,x[0]+3,x[1]+3],fill=(255,0,0))
for t in TOW:
  l=proj(cam,np.array([[*t,0],[*t,60]]),cx,cy);d.line([tuple(l[0]),tuple(l[1])],fill=(255,0,255),width=3)
for x,y in GB:d.point((x,y),fill=(255,255,0))
for x,y in GR:d.point((x,y),fill=(0,255,0))
im.save(sys.argv[2])
