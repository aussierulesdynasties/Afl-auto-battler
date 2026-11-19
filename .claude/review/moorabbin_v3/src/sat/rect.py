# rectified view of the Huggins complex: t along the stand from R0 (east end) to R1, s along 'no' (+ toward the field)
import json,math,sys,numpy as np
from PIL import Image,ImageDraw
O=json.load(open('C:/Users/DANTE/AppData/Local/Temp/claude/9f4017b9c485d8cb/fb8d066d-4ddf-4085-adc6-c6288b802d1c/scratchpad/moor/build.json'))
R=json.load(open('reg.json'));MPP=R['mpp'];pm=R['pmean'];cx,cy=833.577,922.026
src=sys.argv[1];DX,DY=float(sys.argv[2]),float(sys.argv[3]);out=sys.argv[4]
_t=open(src.replace('.png','.txt')).read().split();org=(int(_t[1]),int(_t[2]))
def f(p):return (473376*256+cx+(p[0]-pm[0])/MPP-org[0]*256+DX,321937*256+cy-(p[1]-pm[1])/MPP-org[1]*256+DY)
R0=np.array([-19.0,93.1]);R1=np.array([-67.1,67.6]);LH=np.linalg.norm(R1-R0);tv=(R1-R0)/LH;no=np.array([-tv[1],tv[0]])
T0,T1,S0,S1,K=int(sys.argv[5]),int(sys.argv[6]),int(sys.argv[7]) if len(sys.argv)>7 else -40,int(sys.argv[8]) if len(sys.argv)>8 else 25,int(sys.argv[9]) if len(sys.argv)>9 else 10
im=Image.open(src).convert('RGB');a=np.asarray(im,float)
W,H=(T1-T0)*K,(S1-S0)*K;tt=T0+(np.arange(W)+0.5)/K;ss=S0+(np.arange(H)+0.5)/K
TT,SS=np.meshgrid(tt,ss);X=R0[0]+tv[0]*TT+no[0]*SS;Y=R0[1]+tv[1]*TT+no[1]*SS
px,py=f((X,Y));xi=np.clip(px.astype(int),0,a.shape[1]-2);yi=np.clip(py.astype(int),0,a.shape[0]-2);fx=(px-xi)[...,None];fy=(py-yi)[...,None]
r=a[yi,xi]*(1-fx)*(1-fy)+a[yi,xi+1]*fx*(1-fy)+a[yi+1,xi]*(1-fx)*fy+a[yi+1,xi+1]*fx*fy
out_im=Image.fromarray(r.astype(np.uint8)).transpose(Image.FLIP_TOP_BOTTOM)   # s up = behind the stand at top
d=ImageDraw.Draw(out_im)
g=lambda p:(((p-R0)@tv-T0)*K,H-((p-R0)@no-S0)*K)
for v in range(T0,T1+1,5):d.line([(v-T0)*K,0,(v-T0)*K,H],fill=(90,90,90) if v%10 else (200,200,200));d.text(((v-T0)*K+2,2),'t%d'%v,fill=(255,255,0))
for v in range(S0,S1+1,5):y=H-(v-S0)*K;d.line([0,y,W,y],fill=(90,90,90) if v%10 else (200,200,200));d.text((2,y+1),'s%d'%v,fill=(255,255,0))
cols={'greyroof':(255,0,0),'sawtooth':(255,140,0),'darkroof':(0,255,255),'whiteblock':(255,0,255),'redtower':(80,80,255),'brickblock':(0,255,0),'rearroof':(255,255,255)}
for bb in ([] if len(sys.argv)>10 else O['club']):P=[g(np.array(p)) for p in bb['pts']];d.line(P+[P[0]],fill=cols[bb['n']],width=2)
P=[g(np.array(p)) for p in O['blueseats']];d.line(P+[P[0]],fill=(0,120,255),width=2)
Pp=[g(np.array(p)) for p in O['pitch']];d.line(Pp,fill=(255,0,255),width=1)
out_im.save(out);print(out_im.size)
