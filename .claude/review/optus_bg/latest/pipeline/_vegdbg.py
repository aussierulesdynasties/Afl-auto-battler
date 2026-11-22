import numpy as np, json
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage import color
im=np.asarray(Image.open('data/optus/sat_hi_plaza.png').convert('RGB'))
l=color.rgb2lab(ndi.gaussian_filter(im/255.,(2,2,0)))
v=(l[...,1]<-3)|(l[...,0]<42)
v=ndi.binary_closing(ndi.binary_opening(v,iterations=8),iterations=8)
o=im.copy().astype(float); o[v]=o[v]*0.5+np.array([0,255,0])*0.5
o=Image.fromarray(o.astype(np.uint8)); d=ImageDraw.Draw(o)
J=json.load(open('spec/optus_fc_hand.json'))
d.line([((x-80)/.125,(135-y)/.125) for x,y in J['outline']+J['outline'][:1]],fill=(255,0,0),width=3)
o.save('_vegdbg.jpg',quality=85); print(o.size)
