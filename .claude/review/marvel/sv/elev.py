# Flat view of a pano with elevation-angle gridlines (every 1 deg, labelled every 5) for height reading.
import sys,os,json,numpy as np
from persp import render
from PIL import Image,ImageDraw
pid,vh,vp,fov,W,H,out=sys.argv[1],float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4]),int(sys.argv[5]),int(sys.argv[6]),sys.argv[7]
db=json.load(open('panos.json'));v=db[pid]
f=[x for x in ('loop/%s_z3.jpg'%pid,'n25/%s_z3.jpg'%pid,'%s.jpg'%pid) if os.path.exists(x)][0]
im=render(Image.open(f).convert('RGB'),v['h'],v['p'],v['r'],vh,vp,fov,W,H);dr=ImageDraw.Draw(im)
fl=W/2/np.tan(np.radians(fov)/2)
for e in range(-40,80):
    # row of elevation e at image centre column: angle from optical axis = e-vp
    a=np.radians(e-vp);y=H/2-fl*np.tan(a)
    if 0<=y<H:
        dr.line([(0,y),(30 if e%5 else 60,y)],fill=(255,255,0),width=1)
        if e%5==0:dr.text((62,y-6),'%d'%e,fill=(255,255,0))
for x in range(0,W,50):dr.line([(x,H-12),(x,H)],fill=(0,255,255));dr.text((x+2,H-24),str(x),fill=(0,255,255))
im.save(out);print(v['s'],v['t'],f)
