# python swire.py camjson photo x0 y0 x1 y1 scale out  -- draws stand.json edges through a camera
import sys,json,numpy as np
from PIL import Image,ImageDraw
from cam import proj
cj,ph=sys.argv[1],sys.argv[2];x0,y0,x1,y1,sc=map(int,sys.argv[3:8]);out=sys.argv[8]
p=np.array(json.load(open(cj))['p']);G=json.load(open('stand.json'))['G']
im=Image.open(ph).convert('RGB').crop((x0,y0,x1,y1));im=im.resize((im.width*sc,im.height*sc),Image.LANCZOS);d=ImageDraw.Draw(im)
COL={'roof_top':(255,0,0),'roof_soffit':(255,120,0),'canopy':(255,0,255),'box_front':(0,255,255),'seats':(0,255,0),'plinth':(255,255,0),'lift':(0,120,255)}
for m in G:
    c=COL.get(m['mat'],(255,255,255))
    for f in m['F']:
        X=np.array([m['V'][i] for i in f]);Q=proj(p,X)
        pts=[((u-x0)*sc,(v-y0)*sc) for u,v in Q];d.line(pts+[pts[0]],fill=c,width=1)
im.save(out)
