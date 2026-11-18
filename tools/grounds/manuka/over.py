import numpy as np,json,sys
from PIL import Image,ImageDraw
exec(open('fitcam.py').read().split("if __name__")[0])
p=np.array(json.load(open(sys.argv[1]))['p'])
im=Image.open('photo.png').convert('RGB');d=ImageDraw.Draw(im)
for k,v in G.items():
    if k=='masts':continue
    Y=proj(p,np.array([(x,y,0) for x,y in v]));d.line([tuple(q) for q in Y],fill=(255,255,0) if k=='pitch' else (0,255,255) if k=='stadium' else (255,0,255),width=2)
for i,(x,y) in enumerate(MA):
    a=proj(p,np.array([(x,y,0),(x,y,p[9])]));d.line([tuple(a[0]),tuple(a[1])],fill=(255,0,0),width=3);d.text(tuple(a[1]),'ABCDEF'[i],fill='red')
for k,(nk,lo) in OBS.items():
    for q in(nk,lo):d.ellipse([q[0]-4,q[1]-4,q[0]+4,q[1]+4],outline=(0,255,0),width=2)
for q in GR:d.ellipse([q[0]-4,q[1]-4,q[0]+4,q[1]+4],outline=(0,255,0),width=2)
im.save(sys.argv[2])
