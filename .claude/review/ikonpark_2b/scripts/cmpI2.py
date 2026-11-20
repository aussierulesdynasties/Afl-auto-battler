import json,numpy as np,sys
from PIL import Image,ImageDraw
exec(open('w/cam.py').read())
c=json.load(open(sys.argv[1]));k=mk(np.array(c['q']))
TOP=np.array([(590,272),(640,268),(680,263),(700,261.7),(750,256.7),(800,249),(850,245.7),(900,243.3),(950,241.7),(1000,245),(1040,251)])
im=Image.open('refs/aus/ikon-park-2.jpg').convert('RGB');d=ImageDraw.Draw(im)
cols={'w/geomA7.json':(255,0,0),'w/geomA6.json':(255,255,0)}
for fn,col in cols.items():
    G=json.load(open(fn));F=np.array(G['pratt']['front']);B=np.array(G['pratt']['back'])
    for X in (F,B):
        p=k.proj(X);d.line([tuple(x) for x in p],fill=col,width=2)
    p=k.proj(F)
    # vertical miss at traced columns
    o=np.argsort(p[:,0]);m=[]
    for u,v in TOP:
        if p[o,0].min()<u<p[o,0].max(): m.append(round(np.interp(u,p[o,0],p[o,1])-v,1))
    print(fn,'front-edge v minus photo at traced cols:',m)
    # heights the photo implies: scale z so the edge hits the trace (per point)
for u,v in TOP: d.ellipse([u-3,v-3,u+3,v+3],outline=(0,255,255))
P=np.array(g['22779384']);d.line([tuple(x) for x in k.proj(np.c_[P,np.zeros(len(P))]) if -500<x[0]<1700],fill=(0,255,0))
im.save(sys.argv[2])
