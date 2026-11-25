# 1:1 (or zoomed) crop with a labelled pixel grid, for reading coordinates by eye.
import sys
from PIL import Image, ImageDraw
def crop(path,cx,cy,half=120,zoom=3,step=20,out='crop.png'):
    im=Image.open(path).convert('RGB'); x0,y0=cx-half,cy-half
    c=im.crop((x0,y0,cx+half,cy+half)).resize((2*half*zoom,2*half*zoom),Image.NEAREST)
    d=ImageDraw.Draw(c)
    for v in range((x0//step+1)*step, cx+half, step):
        X=(v-x0)*zoom; d.line([(X,0),(X,c.height)],fill=(255,255,0) if v%100 else (255,0,0),width=1); d.text((X+2,2),str(v),fill=(255,255,0))
    for v in range((y0//step+1)*step, cy+half, step):
        Y=(v-y0)*zoom; d.line([(0,Y),(c.width,Y)],fill=(255,255,0) if v%100 else (255,0,0),width=1); d.text((2,Y+2),str(v),fill=(255,255,0))
    c.save(out)
if __name__=='__main__':
    a=sys.argv; crop(a[1],int(a[2]),int(a[3]),int(a[4]) if len(a)>4 else 120,int(a[5]) if len(a)>5 else 3,int(a[6]) if len(a)>6 else 20,a[7] if len(a)>7 else 'crop.png')
