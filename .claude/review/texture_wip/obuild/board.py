import sys
from PIL import Image,ImageDraw,ImageChops
ph=Image.open('photo.jpg').convert('RGBA');r=Image.open(sys.argv[1]).convert('RGBA')
bg=Image.new('RGBA',ph.size,(120,140,160,255));ren=Image.alpha_composite(bg,r)
ov=Image.blend(ph,Image.alpha_composite(ph,r),0.5)
# edge overlay: render alpha edges in red on the photo
a=r.split()[3].point(lambda v:255 if v>128 else 0)
from PIL import ImageFilter
e=ImageChops.difference(a.filter(ImageFilter.MaxFilter(3)),a)
import numpy as np
g=np.asarray(r.convert('L')).astype(float);gx=np.abs(np.diff(g,axis=1,prepend=0));gy=np.abs(np.diff(g,axis=0,prepend=0))
m=Image.fromarray(((gx+gy)>28).astype('uint8')*255)
ov2=ph.copy();ov2.paste((255,0,0,255),mask=ImageChops.lighter(m,e))
mode=sys.argv[3] if len(sys.argv)>3 else 'board'
if mode=='board':
    W,H=ph.size;out=Image.new('RGB',(W,H*3+0),(0,0,0))
    out.paste(ph.convert('RGB'),(0,0));out.paste(ren.convert('RGB'),(0,H));out.paste(ov.convert('RGB'),(0,2*H))
    d=ImageDraw.Draw(out)
    for i,t in enumerate(('PHOTO','RENDER (matched camera)','OVERLAY 50%')):d.rectangle([0,i*H,330,i*H+40],fill=(0,0,0));d.text((10,i*H+12),t,fill=(255,255,255))
    out.save(sys.argv[2])
else:
    ov2.convert('RGB').save(sys.argv[2])
