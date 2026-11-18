# crop mu.png with pixel grid: python mc.py x0 y0 w h scale out
import sys;from PIL import Image,ImageDraw
x0,y0,w,h,sc=map(int,sys.argv[1:6]);out=sys.argv[6]
im=Image.open('mu.png').convert('RGB').crop((x0,y0,x0+w,y0+h)).resize((w*sc,h*sc),Image.LANCZOS);d=ImageDraw.Draw(im)
for x in range(x0-x0%10+10,x0+w,10):
    X=(x-x0)*sc;d.line([(X,0),(X,8 if x%50 else 20)],fill=(255,255,0))
    if x%50==0:d.text((X+2,22),str(x),fill=(255,255,0))
for y in range(y0-y0%10+10,y0+h,10):
    Y=(y-y0)*sc;d.line([(0,Y),(8 if y%50 else 20,Y)],fill=(0,255,255))
    if y%50==0:d.text((22,Y-6),str(y),fill=(0,255,255))
im.save(out)
