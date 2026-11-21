from PIL import Image
import numpy as np
s=np.asarray(Image.open('out/peoplefirst/ov/sat1400.png').convert('RGB').resize((1400,1400),Image.BOX)).astype(float)
t=np.asarray(Image.open('out/peoplefirst/ortho/top.png').convert('RGB')).astype(float)
def water_sat(a):
    r,g,b=a[...,0],a[...,1],a[...,2]; L=a.mean(2); return (L<55)&(b>=r-4)
def water_mod(a):
    r,g,b=a[...,0],a[...,1],a[...,2]; return (b>r+25)&(b>g+5)
ws,wm=water_sat(s),water_mod(t)
from scipy import ndimage
ws=ndimage.binary_opening(ws,iterations=2); ws=ndimage.binary_closing(ws,iterations=3)
inter=(ws&wm).sum(); uni=(ws|wm).sum()
print('water area m2 aerial',ws.sum(),'model',wm.sum(),'IoU',round(inter/uni,3))
v=np.zeros((1400,1400,3),np.uint8); v[ws&wm]=(60,60,200); v[ws&~wm]=(0,200,0); v[~ws&wm]=(220,40,40)
Image.fromarray(v).save('out/peoplefirst/ov/water_diff.png')
