import json,numpy as np,math
from PIL import Image,ImageDraw
exec(open('fitB.py').read().split('out=[]')[0])
J=json.load(open('camB.json'));cam=J['p'][:7];mg=J['mg']
im=Image.open('refs/c/17.jpg').convert('RGB');d=ImageDraw.Draw(im)
for i,w in G['ways'].items():
    t=w['tags'];Pp=np.array(w['pts'])
    if len(Pp)<2:continue
    col=(0,255,255) if ('highway' in t and 'name' in t) else (80,120,255) if 'building' in t else None
    if col is None:continue
    Q=proj(cam,np.c_[Pp,np.zeros(len(Pp))],cx,cy)
    if (np.abs(Q)>5000).any():continue
    d.line([tuple(q) for q in Q],fill=col,width=1)
for mm,col in((0,(255,255,0)),(mg,(255,128,0))):
    f=fence(mm);Q=proj(cam,np.c_[f,np.zeros(len(f))],cx,cy);d.line([tuple(q) for q in Q],fill=col,width=2)
for s in(1,-1):
    for X in posts(s):
        q=proj(cam,np.array([[*X,0],[*X,15]]),cx,cy);d.line([tuple(q[0]),tuple(q[1])],fill=(255,0,0),width=2)
for t,l in TW:
    X=at_z(cam,*l,cx,cy,0.0);q=proj(cam,np.array([X,X+[0,0,80]]),cx,cy);d.line([tuple(q[0]),tuple(q[1])],fill=(255,0,255),width=1)
im.save('overB.png')
