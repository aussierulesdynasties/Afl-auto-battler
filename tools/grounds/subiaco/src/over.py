import sys,json,numpy as np
from PIL import Image,ImageDraw
from camlib import *
img,camf,out=sys.argv[1:4]
J=json.load(open(camf));p=np.array(J['p']);cam=p[:7];W,H=J['W'],J['H'];cx,cy=J.get('cx',W/2),J.get('cy',H/2)
im=Image.open(img).convert('RGB');d=ImageDraw.Draw(im)
for i,w in G['ways'].items():
    t=w['tags'];P=np.array(w['pts'])
    if len(P)<2:continue
    c=None
    if t.get('leisure')=='pitch':c=(255,255,0)
    elif 'highway' in t and 'name' in t:c=(0,255,255)
    elif 'Fremantle' in t.get('name',''):c=(255,0,0)
    elif 'building' in t:c=(80,120,255)
    if c is None:continue
    Q=proj(cam,np.c_[P,np.zeros(len(P))],cx,cy)
    if (np.abs(Q)>5000).any():continue
    d.line([tuple(q) for q in Q],fill=c,width=1 if 'building' in t else 2)
if 'tw' in J:
    for x,y in J['tw']:
        a=proj(cam,np.array([[x,y,0],[x,y,J['Ht']]]),cx,cy);d.line([tuple(a[0]),tuple(a[1])],fill=(255,0,255),width=2)
im.save(out)
