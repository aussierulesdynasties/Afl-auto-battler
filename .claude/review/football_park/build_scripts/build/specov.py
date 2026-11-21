# python specov.py SPEC CAM PHOTO OUT x0 y0 x1 y1 scale
import sys,json,math,importlib.util,numpy as np
sys.path.insert(0,'../b')
from camlib import proj
from PIL import Image,ImageDraw
sp=importlib.util.spec_from_file_location('spec',sys.argv[1]);S=importlib.util.module_from_spec(sp);sp.loader.exec_module(S)
p=json.load(open(sys.argv[2]))['p'];x0,y0,x1,y1=[int(v) for v in sys.argv[5:9]];sc=float(sys.argv[9])
im=Image.open(sys.argv[3]).convert('RGB').crop((x0,y0,x1,y1));im=im.resize((int((x1-x0)*sc),int((y1-y0)*sc)),Image.LANCZOS);dr=ImageDraw.Draw(im)
def ring(t,d,z):r=math.radians(t);return ((72.5+d)*math.cos(r),(88.5+d)*math.sin(r),z)
def P(X):q=proj(p,[X])[0];return ((q[0]-x0)*sc,(q[1]-y0)*sc)
def interp(keys,t):
    ks=sorted(keys,key=lambda k:k[0]);t=t%360
    for i in range(len(ks)):
        t0,v0=ks[i];t1,v1=ks[(i+1)%len(ks)];span=(t1-t0)%360 or 360;dt=(t-t0)%360
        if dt<=span:w=dt/span;return [a+(b-a)*w for a,b in zip(v0,v1)]
def ts(t0,t1,st=1):span=(t1-t0)%360 or 360;n=int(span/st);return [t0+span*i/n for i in range(n+1)]
def line(pts,c,w=1):dr.line([P(x) for x in pts],fill=c,width=w)
cols=[(255,0,0),(255,128,0),(255,255,0),(0,255,0),(0,255,255),(255,0,255)]
for k in range(6):line([ring(t,*interp(S.BOWL,t)[2*k:2*k+2]) for t in ts(0,360)],cols[k])
for s in S.STRIPS:
    K=s['keys'];f=lambda t:interp(K,t) if len(K)>1 else K[0][1]
    line([ring(t,f(t)[0],f(t)[1]) for t in ts(s['t0'],s['t1'])],(255,255,255),2);line([ring(t,f(t)[2],f(t)[3]) for t in ts(s['t0'],s['t1'])],(0,0,255),2)
for s in S.WALLS:
    K=s['keys'];f=lambda t:interp(K,t) if len(K)>1 else K[0][1]
    line([ring(t,f(t)[0],f(t)[2]) for t in ts(s['t0'],s['t1'])],(255,0,255),1)
for k,(x,y) in S.TOWERS.items():line([(x,y,0),(x,y,S.TOWER['H'])],(0,255,0),1)
for b in getattr(S,'BOXES',[]):
    q=P(ring(b['t'],b['d'],b['z1']));dr.ellipse([q[0]-3,q[1]-3,q[0]+3,q[1]+3],outline=(255,255,255))
im.save(sys.argv[4])
