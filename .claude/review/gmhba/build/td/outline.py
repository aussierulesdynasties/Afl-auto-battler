# model silhouette (non-black in the top-down render) traced on the satellite, world grid every 10 m
import sys;from PIL import Image,ImageDraw;import numpy as np
from scipy import ndimage
CX,CY,H,M=-10.75,-24.16,220.0,0.25
S=Image.open('sat19_local.png').convert('RGB');T=np.array(Image.open(sys.argv[1]).convert('RGB')).astype(int)
m=T.sum(2)>12;m=ndimage.binary_fill_holes(ndimage.binary_closing(m,iterations=2))
e=m&~ndimage.binary_erosion(m,iterations=2)
A=np.array(S);A[e]=(255,30,30);im=Image.fromarray(A);d=ImageDraw.Draw(im)
for x in range(-220,211,10):
    u=(x-CX+H)/M;d.line([(u,0),(u,im.height)],fill=(255,255,0) if x%50 else (0,255,255),width=1);d.text((u+2,2),str(x),fill=(255,255,0))
for y in range(-240,201,10):
    v=(CY+H-y)/M;d.line([(0,v),(im.width,v)],fill=(255,255,0) if y%50 else (0,255,255),width=1);d.text((2,v+2),str(y),fill=(255,255,0))
im.save(sys.argv[2]);np.save('mask.npy',m)
