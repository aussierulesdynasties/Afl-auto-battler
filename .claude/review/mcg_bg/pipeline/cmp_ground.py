"""side-by-side: aerial vs baked ground for a metre box. usage: cmp_ground.py x0 y0 x1 y1 out.png [baked file]"""
import sys,json,os
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
x0,y0,x1,y1=map(float,sys.argv[1:5]); out=sys.argv[5]; bk=sys.argv[6] if len(sys.argv)>6 else 'data/mcg/prep/ground_baked.png'
s=Image.open('data/mcg/sat.png').convert('RGB'); sm=0.5; sh=700
a=s.crop((int((x0+sh)/sm),int((sh-y1)/sm),int((x1+sh)/sm),int((sh-y0)/sm)))
b=Image.open(bk).convert('RGB'); N=b.size[0]; m=3000/N
c=b.crop((int((x0+1500)/m),int((1500-y1)/m),int((x1+1500)/m),int((1500-y0)/m)))
W=900; H=int(W*(y1-y0)/(x1-x0))
o=Image.new('RGB',(2*W+10,H),(255,255,255)); o.paste(a.resize((W,H)),(0,0)); o.paste(c.resize((W,H)),(W+10,0)); o.save(out); print(out,o.size)
