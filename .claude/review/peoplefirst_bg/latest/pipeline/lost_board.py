import numpy as np
src=open('meas_table.py',encoding='utf-8').read()
cut=src.index("spec = json.load"); cut2=src.index("rows.append(('Water area")
exec(src[:cut]); exec(src[cut:cut2])
W0=ws_(s); W0&=~_bm; lost=W0&~W1
from PIL import Image
o=s.copy()*0.6; o[lost]=[255,0,0]; o[W1]=o[W1]*0.4+np.array([0,120,255])*0.6
Image.fromarray(o.astype(np.uint8)).save('out/peoplefirst/water_lost.png')
lab,n=ndimage.label(lost); sz=ndimage.sum(lost,lab,range(1,n+1))
for k in np.argsort(-sz)[:10]:
    ys,xs=np.nonzero(lab==k+1); print(int(sz[k]),int(xs.mean()-700),int(700-ys.mean()))
print('lost',int(lost.sum()))
