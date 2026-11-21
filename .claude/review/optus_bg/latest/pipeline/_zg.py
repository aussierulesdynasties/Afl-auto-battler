import sys
from PIL import Image, ImageDraw
P='D:/Temp/claude/14b1484a65bfbd74/76476bc6-b87c-4245-8ecb-61de5d49956b/scratchpad/proto/'
x0,x1,y0,y1=map(float,sys.argv[1:5]); out=sys.argv[5]
im=Image.open(P+'data/optus/sat_hi_south.png').convert('RGB')
c0,c1=(x0-90)/.125,(x1-90)/.125; r0,r1=(-15-y1)/.125,(-15-y0)/.125
cr=im.crop((int(c0),int(r0),int(c1),int(r1))); s=1100/cr.width; cr=cr.resize((1100,int(cr.height*s)),Image.LANCZOS)
d=ImageDraw.Draw(cr); pm=s/.125
for x in range(int(x0),int(x1)+1):
  X=(x-x0)*pm; d.line([(X,0),(X,cr.height)],fill=(255,0,255) if x%5==0 else (255,255,0),width=1)
  if x%5==0: d.text((X+2,2),str(x),fill=(255,0,255))
for y in range(int(y0),int(y1)+1):
  Y=(y1-y)*pm; d.line([(0,Y),(cr.width,Y)],fill=(255,0,255) if y%5==0 else (255,255,0),width=1)
  if y%5==0: d.text((2,Y+2),str(y),fill=(255,0,255))
cr.save(P+out,quality=92)
