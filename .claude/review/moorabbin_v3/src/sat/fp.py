import json,math,sys,numpy as np
from PIL import Image,ImageDraw
O=json.load(open('C:/Users/DANTE/AppData/Local/Temp/claude/9f4017b9c485d8cb/fb8d066d-4ddf-4085-adc6-c6288b802d1c/scratchpad/moor/build.json'))
R=json.load(open('reg.json'));MPP=R['mpp'];pm=R['pmean'];cx,cy=833.577,922.026
src=sys.argv[1] if len(sys.argv)>1 else 'wb_3026_z19.png';scale=float(sys.argv[2]) if len(sys.argv)>2 else 1
_t=open(src.replace('.png','.txt')).read().split();org=(int(_t[1]),int(_t[2]))
DX,DY=(float(sys.argv[9]),float(sys.argv[10])) if len(sys.argv)>10 else (0,0)
def f(p):
    gx=473376*256+cx+(p[0]-pm[0])/MPP;gy=321937*256+cy-(p[1]-pm[1])/MPP
    return (gx/scale-org[0]*256+DX,gy/scale-org[1]*256+DY)
x0,y0,x1,y1=[float(v) for v in (sys.argv[3:7] if len(sys.argv)>6 else (-120,-40,10,125))]
a=f((x0,y1));b=f((x1,y0));K=int(sys.argv[7]) if len(sys.argv)>7 else 3
im=Image.open(src).convert('RGB').crop((int(a[0]),int(a[1]),int(b[0]),int(b[1])));im=im.resize((im.size[0]*K,im.size[1]*K),Image.LANCZOS)
g=lambda p:((f(p)[0]-int(a[0]))*K,(f(p)[1]-int(a[1]))*K)
d=ImageDraw.Draw(im)
for X in range(int(x0//10*10),int(x1)+1,10):d.line([g((X,y0)),g((X,y1))],fill=(255,255,255) if X%50==0 else (120,120,120),width=1);d.text(g((X+0.3,y1-2)),str(X),fill=(255,255,0))
for Y in range(int(y0//10*10),int(y1)+1,10):d.line([g((x0,Y)),g((x1,Y))],fill=(255,255,255) if Y%50==0 else (120,120,120),width=1);d.text(g((x0+0.5,Y+1.5)),str(Y),fill=(255,255,0))
cols={'greyroof':(255,0,0),'sawtooth':(255,140,0),'darkroof':(0,255,255),'whiteblock':(255,0,255),'redtower':(80,80,255)}
for bb in O['club']:
    P=[g(p) for p in bb['pts']];d.line(P+[P[0]],fill=cols[bb['n']],width=2);d.text(P[0],bb['n'],fill=cols[bb['n']])
P=[g(p) for p in O['blueseats']];d.line(P+[P[0]],fill=(0,120,255),width=2)
Pp=[g(p) for p in O['pitch']];d.line(Pp,fill=(255,0,255),width=1)
for k in ('front','rear'):d.line([g(p) for p in O['stand'][k]],fill=(0,255,0),width=2)
for k,(p,h) in O['poles'].items():q=g(p);d.ellipse((q[0]-5,q[1]-5,q[0]+5,q[1]+5),outline=(255,255,0),width=2);d.text((q[0]+6,q[1]),k,fill=(255,255,0))
im.save(sys.argv[8] if len(sys.argv)>8 else 'fp.png');print(im.size)
