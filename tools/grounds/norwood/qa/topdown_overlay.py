"""Top-down QA: every upward face of the model's modules drawn where Google Earth's top-down mosaic shows it
(each point leaned out from its tile's centre for its height), over the mosaic, so a roof or a court that is
off shows as a gap between the outline and the picture.

    python3 qa/topdown_overlay.py <mosaic.png> <modules, e.g. town,west> <out.png> <e0,n0,e1,n1> [scale]

The mosaic is Google Earth's nine top-down tiles (the td_* views, ge_shoot.js) at 0.2 m a pixel, 300 m a
side round the centre circle; it stays on the machine (raw imagery is never committed)."""
import os, sys, math, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "model"))
from PIL import Image, ImageDraw
import nwlib
MOSAIC=sys.argv[1]
mods=sys.argv[2].split(','); out=sys.argv[3]; box=[float(v) for v in sys.argv[4].split(',')]  # e0,n0,e1,n1
S=int(sys.argv[5]) if len(sys.argv)>5 else 3
# the nine tiles' centres (model metres) and Google Earth's camera height over the turf
T=[(-75.8,-84.8),(4.2,-84.8),(84.2,-84.8),(-75.8,-4.8),(84.2,-4.8),(-75.8,75.2),(4.2,75.2),(84.2,75.2),(4.2,-4.8)]
def tile(e,n): return np.array(min(T,key=lambda t: math.hypot(e-t[0],(n-t[1])*1.6)))
H=260.0
def app(p):
    t=tile(p[0],p[1]); return t+(np.array(p[:2])-t)/(1-min(p[2],200)/H)
nwlib.PARTS.clear()
for m in mods: __import__(m).build()
im=Image.open(MOSAIC).convert('RGB')
e0,n0,e1,n1=box
def px(e,n): return ((e/0.2+750)-(e0/0.2+750))*S, ((750-n/0.2)-(750-n1/0.2))*S
c=im.crop((int(e0/0.2+750),int(750-n1/0.2),int(e1/0.2+750),int(750-n0/0.2))); c=c.resize((c.width*S,c.height*S),Image.LANCZOS)
d=ImageDraw.Draw(c)
for name,faces in nwlib.PARTS.items():
    for pts,mat,uv in faces:
        P=np.array(pts,float)
        if len(P)<3: continue
        nrm=np.cross(P[1]-P[0],P[2]-P[0])
        if np.linalg.norm(nrm)<1e-9 or abs(nrm[2])/np.linalg.norm(nrm)<0.5: continue
        Q=[px(*app(p)) for p in P]
        d.line(Q+[Q[0]],fill=(255,0,255),width=1)
c.save(out); print('saved',out,c.size)
