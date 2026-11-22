import numpy as np, json
from PIL import Image
from scipy import ndimage
from skimage import measure
s=np.asarray(Image.open('data/gmhba/sat.png').convert('RGB')).astype(int)
y0,x0=1500-380,1500-230; sub=s[y0:1500-120,x0:1500-60]; r,g,b=sub[...,0],sub[...,1],sub[...,2]
m=ndimage.binary_closing((b>r+30)&(b>g+15),iterations=4); m=ndimage.binary_opening(m,iterations=2)
lab,n=ndimage.label(m); k=np.argmax(np.bincount(lab.ravel())[1:])+1; m=ndimage.binary_fill_holes(lab==k)
c=max(measure.find_contours(m.astype(float),0.5),key=len); c=measure.approximate_polygon(c,1.5)
P=[[round(float(x+x0-1500),1),round(float(1500-(y+y0)),1)] for y,x in c[:-1]]
print(len(P),int(m.sum()),P)
json.dump(P,open('out/gmhba/court_poly.json','w'))
