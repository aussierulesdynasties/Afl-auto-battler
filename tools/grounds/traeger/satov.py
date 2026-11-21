import json,sys,numpy as np
from PIL import Image,ImageDraw
from f2w import *
J=json.load(open('sat/sat.json'));im=Image.open('sat/sat.png')
ox=(J['cx']-J['x0'])*256;oy=(J['cy']-J['y0'])*256;m=J['mpp'];k=3
im=im.resize((im.width*k,im.height*k),Image.LANCZOS);ox*=k;oy*=k;m/=k;d=ImageDraw.Draw(im)
f=lambda p:(ox+p[0]/m,oy-p[1]/m)
def L(pts,c,w=2):
    W=f2w(pts);d.line([f(q) for q in W],fill=c,width=w)
L([(-25,-25),(25,-25),(25,25),(-25,25),(-25,-25)],(255,255,0))
for e in(-1,1):
    L([(-9.6,e*84),(9.6,e*84)],(255,0,255));L([(-3.2,e*84),(-3.2,e*75),(3.2,e*75),(3.2,e*84)],(255,0,255))
B=json.load(open('bnd_m.json'));L(B+[B[0]],(0,255,255))
G=json.load(open('osm/geo.json'))['geo']
for kk in('242194673','242194648','242194649'):d.line([f(q) for q in G[kk]],fill=(255,128,0),width=1)
x0,y0,x1,y1=map(float,sys.argv[2:6])
im.crop((int(ox+x0/m),int(oy-y1/m),int(ox+x1/m),int(oy-y0/m))).save(sys.argv[1])
