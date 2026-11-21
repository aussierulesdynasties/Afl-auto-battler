import math,sys
from PIL import Image,ImageDraw
A0,A1=129.0,179.0
POLY=[(-69.2,85.5),(-86.6,92.4),(-116.0,106.5),(-116.0,-8.0)]
def rear(an):
    dx,dy=math.cos(math.radians(an)),math.sin(math.radians(an));best=None
    for k in range(3):
        (px,py),(qx,qy)=POLY[k],POLY[k+1];ex,ey=qx-px,qy-py;den=dx*ey-dy*ex
        if abs(den)<1e-9:continue
        t=(px*ey-py*ex)/den;u=(px*dy-py*dx)/den
        if t>0 and -1e-6<=u<=1+1e-6 and (best is None or t<best):best=t
    return best
P=lambda an,r:(r*math.cos(math.radians(an)),r*math.sin(math.radians(an)))
OX,OY,M=1175.087,1233.696,0.2347774
im=Image.open('sat/g19.png').convert('RGB');d=ImageDraw.Draw(im)
px=lambda x,y:(OX+x/M,OY-y/M)
for k in range(3):d.line(px(*POLY[k])+px(*POLY[k+1]),fill=(255,255,0),width=1)
n=int(sys.argv[1]) if len(sys.argv)>1 else 15
S=[A0+(A1-A0)*k/3000 for k in range(3001)];L=[0]
for k in range(1,3001):
    a=P(S[k-1],rear(S[k-1]));b=P(S[k],rear(S[k]));L.append(L[-1]+math.dist(a,b))
E=[S[min(range(3001),key=lambda m:abs(L[m]-L[-1]*k/n))] for k in range(n+1)]
for i in range(n):
    bm=(E[i]+E[i+1])/2;x,y=px(*P(bm,rear(bm)));d.ellipse((x-4,y-4,x+4,y+4),outline=(255,0,0),width=2)
for a in(A0,A1):d.line(px(0,0)+px(*P(a,140)),fill=(0,255,255))
im.crop((560,560,1180,1300)).resize((930,1110)).save('w/ov19_%d.png'%n);print(L[-1])
