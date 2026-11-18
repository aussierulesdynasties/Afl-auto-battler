# python sbs.py u0 v0 u1 v1 out.png [scale]: photo above render above 50% overlay
import sys
from PIL import Image
u0,v0,u1,v1=map(int,sys.argv[1:5]);o=sys.argv[5];k=float(sys.argv[6]) if len(sys.argv)>6 else 1
a=Image.open('p92.png').convert('RGB');b=Image.open('out/r92t.png').convert('RGBA').resize(a.size)
bg=Image.new('RGBA',a.size,(255,0,255,255));bg.alpha_composite(b);b=bg.convert('RGB')
A,B=a.crop((u0,v0,u1,v1)),b.crop((u0,v0,u1,v1));O=Image.blend(A,B,0.5)
w,h=A.size;S=Image.new('RGB',(w,h*3));S.paste(A,(0,0));S.paste(B,(0,h));S.paste(O,(0,2*h))
S.resize((int(w*k),int(3*h*k)),Image.LANCZOS).save(o)
