# python work/pano.py b0 b1 out : facade elevation stitched from the f-views (nearest view per bearing), z 0..45
import sys,os,json,numpy as np;sys.path.insert(0,'work');import tri
from PIL import Image,ImageDraw
exec(open('work/elev.py').read().split("v=sys.argv[1]")[0].split("D=json.load")[0])
D=json.load(open('model/mcg.json'));C=json.load(open('work/cams.json'))
exec("def polar"+open('work/elev.py').read().split("def polar")[1].split("v=sys.argv[1]")[0])
b0,b1=float(sys.argv[1]),float(sys.argv[2]);out=sys.argv[3]
PB,PZ=20,8;B=np.arange(b0,b1,1/PB);Z=np.arange(45,0,-1/PZ)
rf=np.nanmax([polar(D['osm'][k],B) for k in ('shane_warne','mcc','olympic','ponsford')],0)
fv=[k for k in C if k[0]=='f'];tb={k:np.degrees(np.arctan2(C[k][0],C[k][1]))%360 for k in fv}
S=np.zeros((len(Z),len(B),3),np.uint8);which=[]
for k in fv:
    sel=np.array([abs((b-tb[k]+180)%360-180)<=11.25 for b in B])
    if not sel.any():continue
    c=tri.camv(k);im=np.asarray(Image.open(f"{os.environ.get('IMG','ge')}/{k}.png").convert('RGB'))
    a=np.radians(B[sel])[None];r=rf[sel]
    X=np.stack([np.broadcast_to(r*np.sin(a),(len(Z),sel.sum())),np.broadcast_to(r*np.cos(a),(len(Z),sel.sum())),np.broadcast_to(Z[:,None],(len(Z),sel.sum()))],-1)
    P,_=projv(c,X);u=P[...,0].round().astype(int);w=P[...,1].round().astype(int);ok=(u>=0)&(u<1920)&(w>=85)&(w<1048)
    T=im[np.clip(w,0,1079),np.clip(u,0,1919)];T[~ok]=0;S[:,sel]=T
I=Image.fromarray(S);d=ImageDraw.Draw(I)
for bb in range(int(np.ceil(b0)),int(b1)+1):
    x=(bb-b0)*PB;d.line([x,I.height-(12 if bb%5==0 else 5),x,I.height],fill=(255,255,0))
    if bb%5==0:d.text((x+2,I.height-24),str(bb%360),fill=(255,255,0))
for zz in range(0,46):
    y=(45-zz)*PZ;d.line([0,y,10 if zz%5==0 else 4,y],fill=(255,0,255))
    if zz%5==0:d.text((12,y-5),str(zz),fill=(255,0,255))
    if zz%10==0:d.line([0,y,I.width,y],fill=(255,0,255))
I.save(out)
