# photo | render on photo | 50% blend, plus a labelled 100 px grid
import sys;from PIL import Image,ImageDraw
ph=Image.open('../mv/mu.png').convert('RGB');r=Image.open(sys.argv[1]).convert('RGBA')
on=ph.copy();on.paste(r,(0,0),r)
bl=Image.blend(ph,on,0.5)
def grid(im):
    d=ImageDraw.Draw(im)
    for x in range(0,1920,100):d.line([(x,0),(x,1080)],fill=(255,255,255),width=1);d.text((x+2,2),str(x),fill=(255,255,0))
    for y in range(0,1080,100):d.line([(0,y),(1920,y)],fill=(255,255,255),width=1);d.text((2,y+2),str(y),fill=(255,255,0))
    return im
for n,im in(('on',on),('blend',bl)):grid(im).save(sys.argv[2]+'_'+n+'.jpg',quality=90)
