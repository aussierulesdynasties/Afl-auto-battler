# python work/elev.py view b0 b1 out [dr] : unrolled facade elevation at r=footprint(b)+dr, z 0..45; x=bearing (20 px/deg), y=z (8 px/m)
import sys,json,numpy as np;sys.path.insert(0,'work');import tri
from PIL import Image,ImageDraw
def projv(c,X):
    d=X-c['C'];z=d@c['fwd'];return np.stack([c['W']/2+c['f']*(d@c['right'])/z,c['H']/2-c['f']*(d@c['up'])/z],-1),z
D=json.load(open('model/mcg.json'))
def polar(P,bs):
    P=np.array(P,float);Q=np.roll(P,-1,0);out=np.full(len(bs),np.nan)
    for i,b in enumerate(bs):
        d=np.array([np.sin(np.radians(b)),np.cos(np.radians(b))])
        for a,c in zip(P,Q):
            e=c-a;M=np.array([[d[0],-e[0]],[d[1],-e[1]]])
            if abs(np.linalg.det(M))<1e-9:continue
            t,s=np.linalg.solve(M,a)
            if t>0 and 0<=s<=1:out[i]=t if np.isnan(out[i]) else max(out[i],t)
    return out
v=sys.argv[1];b0,b1=float(sys.argv[2]),float(sys.argv[3]);out=sys.argv[4];dr=float(sys.argv[5]) if len(sys.argv)>5 else 0
PB,PZ=20,8;B=np.arange(b0,b1,1/PB);Z=np.arange(45,0,-1/PZ)
rf=np.nanmax([polar(D['osm'][k],B) for k in ('shane_warne','mcc','olympic','ponsford')],0)+dr
c=tri.camv(v);im=np.asarray(Image.open(f'ge/{v}.png').convert('RGB'))
a=np.radians(B)[None];X=np.stack([np.broadcast_to(rf*np.sin(a),(len(Z),len(B))),np.broadcast_to(rf*np.cos(a),(len(Z),len(B))),np.broadcast_to(Z[:,None],(len(Z),len(B)))],-1)
P,_=projv(c,X);u=P[...,0].round().astype(int);w=P[...,1].round().astype(int);ok=(u>=0)&(u<1920)&(w>=85)&(w<1048)
S=im[np.clip(w,0,1079),np.clip(u,0,1919)];S[~ok]=0
I=Image.fromarray(S);d=ImageDraw.Draw(I)
for bb in range(int(np.ceil(b0)),int(b1)+1):
    x=(bb-b0)*PB;d.line([x,I.height-(12 if bb%5==0 else 5),x,I.height],fill=(255,255,0))
    if bb%5==0:d.text((x+2,I.height-24),str(bb%360),fill=(255,255,0))
for zz in range(0,46):
    y=(45-zz)*PZ;d.line([0,y,10 if zz%5==0 else 4,y],fill=(255,0,255))
    if zz%5==0:d.text((12,y-5),str(zz),fill=(255,0,255));d.line([0,y,I.width,y],fill=(255,0,255) if zz%10==0 else (150,0,150)) if zz%10==0 else None
I.save(out);print(I.size,'r',np.nanmin(rf).round(1),np.nanmax(rf).round(1))
