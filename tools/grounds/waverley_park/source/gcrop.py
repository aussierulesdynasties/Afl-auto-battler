import sys
from PIL import Image,ImageDraw
src,name,x0,y0,x1,y1,sc=sys.argv[1],sys.argv[2],*map(int,sys.argv[3:8])
P=Image.open(src).convert('RGB')
f=P.size[0]/1023
a=P.crop((int(x0*f),int(y0*f),int(x1*f),int(y1*f))).resize(((x1-x0)*sc,(y1-y0)*sc),Image.LANCZOS);d=ImageDraw.Draw(a)
for x in range((x0//10+1)*10,x1,10):
    X=(x-x0)*sc;d.line([(X,0),(X,4 if x%50 else 12)],fill=(255,255,0))
    if x%50==0:d.text((X+2,12),str(x),fill=(255,255,0))
for y in range((y0//10+1)*10,y1,10):
    Y=(y-y0)*sc;d.line([(0,Y),(4 if y%50 else 12,Y)],fill=(255,255,0))
    if y%50==0:d.text((14,Y),str(y),fill=(255,255,0))
a.save('out/'+name+'.png')
