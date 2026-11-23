import sys
from PIL import Image, ImageDraw
im=Image.open(sys.argv[1]).convert('RGB'); d=ImageDraw.Draw(im); W,H=im.size
for x in range(0,W,50): d.line([(x,0),(x,H)],fill=(255,255,0) if x%200==0 else (90,90,0)); d.text((x+2,2),str(x),fill=(255,0,0))
for y in range(0,H,50): d.line([(0,y),(W,y)],fill=(255,255,0) if y%200==0 else (90,90,0)); d.text((2,y+2),str(y),fill=(255,0,0))
im.save(sys.argv[2])
