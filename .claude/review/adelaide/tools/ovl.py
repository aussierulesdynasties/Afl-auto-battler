"""ovl.py RENDER OUT [x0,y0,x1,y1] : photo with the render's silhouette/edges drawn on top, plus 50% blend"""
import sys,os;from PIL import Image,ImageFilter,ImageChops
import numpy as np
ph=Image.open(os.environ.get('PHOTO','photos/crop.jpg')).convert('RGBA');r=Image.open(sys.argv[1]).convert('RGBA').resize(ph.size)
crop=[int(v) for v in sys.argv[3].split(',')] if len(sys.argv)>3 else None
# edges of render: luminance + alpha edges
a=np.array(r).astype(float);lum=a[...,:3].mean(-1)*(a[...,3]/255)
g=Image.fromarray(lum.astype('uint8')).filter(ImageFilter.FIND_EDGES)
e=np.array(g)>40
o=np.array(ph).copy();o[e]=[0,255,255,255]
blend=Image.blend(ph,Image.alpha_composite(ph,r),0.5)
ims=[Image.fromarray(o),blend]
if crop:ims=[i.crop(crop) for i in ims];s=2;ims=[i.resize((i.width*s,i.height*s)) for i in ims]
W=ims[0].width;H=ims[0].height
out=Image.new('RGB',(W,H*2));out.paste(ims[0],(0,0));out.paste(ims[1],(0,H));out.save(sys.argv[2])
