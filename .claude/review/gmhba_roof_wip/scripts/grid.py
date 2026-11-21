import sys
from PIL import Image,ImageDraw
src,out,x0,y0,x1,y1,sc=sys.argv[1],sys.argv[2],*map(int,sys.argv[3:8])
im=Image.open(src).convert('RGB').crop((x0,y0,x1,y1)).resize(((x1-x0)*sc,(y1-y0)*sc),Image.LANCZOS);d=ImageDraw.Draw(im)
for x in range(x0-x0%10+10,x1,10):
  X=(x-x0)*sc;d.line([(X,0),(X,im.height)],fill=(255,0,0) if x%50==0 else (255,200,0),width=1)
  if x%50==0:d.text((X+2,2),str(x),fill=(255,0,0))
for y in range(y0-y0%10+10,y1,10):
  Y=(y-y0)*sc;d.line([(0,Y),(im.width,Y)],fill=(255,0,0) if y%50==0 else (255,200,0),width=1)
  if y%50==0:d.text((2,Y+2),str(y),fill=(255,0,0))
im.save(out)
