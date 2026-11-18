# python pxgrid.py x0 y0 x1 y1 K OUT : photo crop with a pixel grid every 10 px (labels every 20)
import sys;from PIL import Image,ImageDraw
x0,y0,x1,y1,K=map(int,sys.argv[1:6]);im=Image.open('e86_l.jpg').convert('RGB').crop((x0,y0,x1,y1)).resize(((x1-x0)*K,(y1-y0)*K),Image.LANCZOS);d=ImageDraw.Draw(im)
for x in range((x0//10)*10,x1+1,10):
    X=(x-x0)*K;d.line([(X,0),(X,im.height)],fill=(255,255,0) if x%50==0 else (200,200,200),width=1)
    if x%20==0:d.text((X+2,2),str(x),fill=(255,40,40))
for y in range((y0//10)*10,y1+1,10):
    Y=(y-y0)*K;d.line([(0,Y),(im.width,Y)],fill=(255,255,0) if y%50==0 else (200,200,200),width=1)
    if y%20==0:d.text((2,Y+2),str(y),fill=(255,40,40))
im.save(sys.argv[6])
