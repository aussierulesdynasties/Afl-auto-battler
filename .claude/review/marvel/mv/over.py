import sys,json,numpy as np
from PIL import Image,ImageDraw
from cam import *
p=json.load(open(sys.argv[1]))['p'];im=Image.open('m.png').convert('RGB');d=ImageDraw.Draw(im)
ways,nodes=load_map();G=json.load(open('osm/geo.json'))
def L(pts,z,col,w=2):
    X=np.array([(x,y,z) for x,y in pts]);C=np.array(p[:3]);M=R(*p[3:6]);dd=(X-C)@M.T
    if (dd[:,2]<1).any():return
    Y=proj(p,X);d.line([tuple(q) for q in Y],fill=col,width=w)
for t,pts in ways:
    if len(pts)<2:continue
    if 'building' in t:
        h=float(str(t.get('height','0')).split()[0] or 0)
        L(pts,0,(255,0,0),1)
        if h:L(pts,h,(255,80,80),2)
    elif t.get('highway')=='steps':L(pts,0,(255,150,0),3)
    elif t.get('highway') in('tertiary','trunk','primary'):L(pts,0,(200,200,200),1)
    elif 'railway' in t and t['railway']in('rail','tram'):L(pts,0,(120,120,255),1)
L(G['ways']['22971441'],0,(0,255,0),2);L(G['ways']['22971441'],40,(0,255,255),2);L(G['ways']['23272382'],4,(255,255,0),2)
for t,(x,y) in nodes:
    col=None
    if t.get('natural')=='tree':col=(0,255,0)
    if t.get('highway')=='street_lamp':col=(255,0,255)
    if t.get('man_made')=='flagpole':col=(255,0,0)
    if t.get('barrier')=='turnstile':col=(255,255,255)
    if col:
        q=proj(p,[(x,y,0)])[0];d.ellipse([q[0]-4,q[1]-4,q[0]+4,q[1]+4],outline=col,width=2)
im.save(sys.argv[2])
