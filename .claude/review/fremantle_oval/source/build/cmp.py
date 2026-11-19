# cmp.py x0 y0 x1 y1 out [render]: photo | render | 50% overlay, full-res crop, pixel grid every 50 px
import sys
from PIL import Image, ImageDraw
x0,y0,x1,y1=map(int,sys.argv[1:5]);out=sys.argv[5];rp=sys.argv[6] if len(sys.argv)>6 else 'build/r_a04.png'
ph=Image.open('hunt/a04.jpg').convert('RGBA').crop((x0,y0,x1,y1))
r=Image.open(rp).convert('RGBA').crop((x0,y0,x1,y1))
rw=Image.new('RGBA',r.size,(255,255,255,255));rw.alpha_composite(r)
comp=ph.copy();comp.alpha_composite(r);ov=Image.blend(ph,comp,0.5)
w,h=ph.size;sc=min(1.0,1800/(3*w))
tiles=[t.convert('RGB').resize((int(w*sc),int(h*sc))) for t in (ph,rw,ov)]
W=sum(t.width for t in tiles)+20;H=tiles[0].height+16
b=Image.new('RGB',(W,H),(30,30,30));d=ImageDraw.Draw(b);x=0
for t in tiles:
    b.paste(t,(x,16));dd=ImageDraw.Draw(b)
    for gx in range((x0//50+1)*50,x1,50):
        px=x+int((gx-x0)*sc);c=(255,0,0) if gx%250==0 else (255,255,0)
        if gx%250==0: dd.line([(px,16),(px,16+t.height)],fill=c,width=1);dd.text((px+2,2),str(gx),fill=c)
    for gy in range((y0//50+1)*50,y1,50):
        py=16+int((gy-y0)*sc)
        if gy%250==0: dd.line([(x,py),(x+t.width,py)],fill=(255,0,0),width=1);dd.text((x+2,py+1),str(gy),fill=(255,0,0))
    x+=t.width+10
b.save(out,quality=90)
