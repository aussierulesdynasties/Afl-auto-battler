"""aerial crop with metre grid. usage: grid_sat.py x0 y0 x1 y1 step out.png"""
import sys
from PIL import Image, ImageDraw
x0,y0,x1,y1,st=map(float,sys.argv[1:6]); out=sys.argv[6]
s=Image.open('data/mcg/sat.png').convert('RGB'); sm=0.5; sh=700
a=s.crop((int((x0+sh)/sm),int((sh-y1)/sm),int((x1+sh)/sm),int((sh-y0)/sm)))
W=1400; k=W/(x1-x0); a=a.resize((W,int((y1-y0)*k))); d=ImageDraw.Draw(a)
import math
x=math.ceil(x0/st)*st
while x<x1:
    px=(x-x0)*k; d.line([(px,0),(px,a.size[1])],fill=(255,255,0),width=1); d.text((px+2,2),str(int(x)),fill=(255,255,0)); x+=st
y=math.ceil(y0/st)*st
while y<y1:
    py=(y1-y)*k; d.line([(0,py),(W,py)],fill=(0,255,255),width=1); d.text((2,py+2),str(int(y)),fill=(0,255,255)); y+=st
a.save(out); print(out,a.size)
