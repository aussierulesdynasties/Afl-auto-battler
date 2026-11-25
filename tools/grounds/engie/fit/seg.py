# Run from a work folder holding the Google Earth shots in ge/ (never committed; looking and measuring only).
import numpy as np, json, sys
from PIL import Image
from scipy import ndimage as nd
im=np.asarray(Image.open('ge/top3000.png').convert('RGB')).astype(float)
r,g,b=im[...,0],im[...,1],im[...,2]
grass=(g>r+6)&(g>b+2)
lab,n=nd.label(grass); c=lab[360,640]; field=lab==c
field=nd.binary_fill_holes(nd.binary_closing(field,iterations=4))
print('field px',field.sum())
Image.fromarray((field*255).astype(np.uint8)).save('field.png')
np.save('field.npy',field)
