import sys
from PIL import Image,ImageDraw
src,out,x0,y0,x1,y1,k=sys.argv[1],sys.argv[2],*map(int,sys.argv[3:7]),float(sys.argv[7])
im=Image.open(src).convert('RGB').crop((x0,y0,x1,y1));im=im.resize((int((x1-x0)*k),int((y1-y0)*k)),Image.LANCZOS);d=ImageDraw.Draw(im)
for x in range((x0//10+1)*10,x1,10):
    c=(255,0,0) if x%50==0 else (255,170,170);d.line([((x-x0)*k,0),((x-x0)*k,im.height)],fill=c,width=1)
    if x%50==0:d.text(((x-x0)*k+2,2),str(x),fill=(255,255,0))
for y in range((y0//10+1)*10,y1,10):
    c=(255,0,0) if y%50==0 else (255,170,170);d.line([(0,(y-y0)*k),(im.width,(y-y0)*k)],fill=c,width=1)
    if y%50==0:d.text((2,(y-y0)*k+2),str(y),fill=(255,255,0))
im.save(out)
