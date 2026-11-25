import numpy as np,json,math,sys
from PIL import Image,ImageDraw
exec(open('cam.py').read())
c=json.load(open('cam.json'));p=np.array(c['p'])
T=json.load(open('osm/geo.json'))['tags']
im=Image.open('refs/scg.jpg').convert('RGB');d=ImageDraw.Draw(im)
for k,pts in G.items():
    if k[0]=='T':
        a=proj(p,[(*pts[0],0),(*pts[0],p[9])]);d.line([tuple(a[0]),tuple(a[1])],fill=(255,0,0),width=2);d.text(tuple(a[1]),k[-3:],fill=(255,255,0));continue
    t=T[k];col=(255,255,0) if 'leisure' in t and 'building' not in t else ((0,255,255) if t.get('building') in('roof','grandstand') else (255,0,255))
    Y=proj(p,np.c_[np.array(pts),np.zeros(len(pts))]);
    if (Y[:,0]>-500).all():d.line([tuple(q) for q in Y],fill=col,width=1)
for q in np.load('grass.npy'):d.ellipse([q[0]-2,q[1]-2,q[0]+2,q[1]+2],outline=(255,128,0))
im.save(sys.argv[1] if len(sys.argv)>1 else 'g/over.png')
