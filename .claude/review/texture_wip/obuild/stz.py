import sys
from PIL import Image,ImageDraw,ImageFilter
r=Image.open(sys.argv[1]).convert('RGBA');ph=Image.open('prev/photo_full.png').convert('RGBA')
x0,y0,x1,y1=[int(v) for v in sys.argv[3].split(',')];S=int(sys.argv[4])
def cr(im):return im.crop((x0,y0,x1,y1)).resize(((x1-x0)*S,(y1-y0)*S),Image.LANCZOS)
p=cr(ph);rr=cr(r);comp=p.copy();comp.alpha_composite(rr)
def grid(im):
    d=ImageDraw.Draw(im)
    for x in range(x0-x0%10+10,x1,10):d.line([((x-x0)*S,0),((x-x0)*S,im.size[1])],fill=(255,0,255,160) if x%50==0 else (255,255,0,90));d.text(((x-x0)*S+2,2),str(x),fill=(255,0,255))
    for y in range(y0-y0%10+10,y1,10):d.line([(0,(y-y0)*S),(im.size[0],(y-y0)*S)],fill=(255,0,255,160) if y%50==0 else (255,255,0,90));d.text((2,(y-y0)*S+2),str(y),fill=(255,0,255))
    return im
W,H=p.size;o=Image.new('RGB',(W*2,H),'black');o.paste(grid(p).convert('RGB'),(0,0));o.paste(grid(comp).convert('RGB'),(W,0));o.save(sys.argv[2])
