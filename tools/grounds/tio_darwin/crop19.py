# python crop19.py name x0 y0 x1 y1 [scale]  -> sat/c19_name.png, upscaled, 10 m grid (labels in field metres)
from PIL import Image,ImageDraw
import sys
from geo import *
n=sys.argv[1];x0,y0,x1,y1=map(float,sys.argv[2:6]);k=float(sys.argv[6]) if len(sys.argv)>6 else 3
im=Image.open('sat/sat19.png').convert('RGB')
a=m2px(x0,y1);b=m2px(x1,y0)
c=im.crop((int(a[0]),int(a[1]),int(b[0]),int(b[1])));c=c.resize((int(c.width*k),int(c.height*k)),Image.LANCZOS)
d=ImageDraw.Draw(c);m=J['mpp']/k
def P(x,y):return ((x-x0)/ (m)+0, (y1-y)/m)
import math
for r in range(-300,301,5):
    col=(255,0,0) if r%50==0 else ((255,200,0) if r%10==0 else (120,120,0))
    if x0<=r<=x1:d.line([P(r,y0),P(r,y1)],fill=col,width=1);d.text((P(r,y1)[0]+2,2),str(r),fill='yellow') if r%10==0 else 0
    if y0<=r<=y1:d.line([P(x0,r),P(x1,r)],fill=col,width=1);d.text((2,P(x0,r)[1]+2),str(r),fill='cyan') if r%10==0 else 0
c.save(f'sat/c19_{n}.png');print(c.size)
