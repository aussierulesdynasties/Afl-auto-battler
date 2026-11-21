# zoom crop of lplan_all_clean.png (M=0.25, s0=-200,t1=200) upscaled x3 with 2 m grid, labels every 10 m
import sys
from PIL import Image,ImageDraw
s,t,h=map(float,sys.argv[1:4]);out=sys.argv[4];K=3
im=Image.open('lplan_all_clean.png');M=0.25
x0=(200-(t+h))/M;y0=(s-h+200)/M;W=2*h/M
c=im.crop((int(x0),int(y0),int(x0+W),int(y0+W))).resize((int(W*K),int(W*K)),Image.LANCZOS);dr=ImageDraw.Draw(c)
import math
for k in range(math.ceil(s-h),int(s+h)+1):
    if k%2:continue
    y=(k-(s-h))/M*K;dr.line([(0,y),(c.width,y)],fill=(255,230,0) if k%10==0 else (120,110,0),width=1)
for k in range(math.ceil(t-h),int(t+h)+1):
    if k%2:continue
    x=((t+h)-k)/M*K;dr.line([(x,0),(x,c.height)],fill=(0,230,255) if k%10==0 else (0,110,130),width=1)
for a in range(math.ceil((s-h)/10)*10,int(s+h)+1,10):
    for b in range(math.ceil((t-h)/10)*10,int(t+h)+1,10):
        dr.text((((t+h)-b)/M*K+2,(a-(s-h))/M*K+1),'%d,%d'%(a,b),fill=(255,60,255))
c.save(out,quality=90)
