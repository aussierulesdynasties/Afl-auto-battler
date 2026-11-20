import sys
from PIL import Image,ImageDraw
r=Image.open(sys.argv[1]).convert('RGBA');ph=Image.open('prev/photo_full.png').convert('RGBA')
x0,y0,x1,y1=1000,830,1300,1070;S=3
def cr(im):return im.crop((x0,y0,x1,y1)).resize(((x1-x0)*S,(y1-y0)*S),Image.LANCZOS)
p=cr(ph);rr=cr(r);comp=p.copy();comp.alpha_composite(rr)
bl=Image.blend(p,comp,0.5)
# outline of the model drawn on the photo
ed=rr.split()[3].point(lambda a:255 if a>0 else 0)
from PIL import ImageFilter
e=ed.filter(ImageFilter.FIND_EDGES);ov=p.copy();ov.paste((0,255,255,255),mask=e)
W,H=p.size;o=Image.new('RGB',(W*2,H*2),'black')
for k,im in enumerate([p,comp,bl,ov]):o.paste(im.convert('RGB'),((k%2)*W,(k//2)*H))
d=ImageDraw.Draw(o)
for k,t in enumerate(['photo o2','model, photo camera','50% blend','model outline on photo']):d.text(((k%2)*W+8,(k//2)*H+8),t,fill=(255,255,0))
o.save(sys.argv[2])
