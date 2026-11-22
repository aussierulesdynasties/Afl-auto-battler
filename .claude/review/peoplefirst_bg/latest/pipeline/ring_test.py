import numpy as np
src=open('meas_table.py',encoding='utf-8').read()
cut=src.index("spec = json.load"); cut2=src.index("rows.append(('Water area")
exec(src[:cut]); exec(src[cut:cut2])
from scipy import ndimage
lab,n=ndimage.label(W1); gb=s[...,1].astype(float)-s[...,2]
for k in range(1,n+1):
    m=lab==k; a=int(m.sum())
    if a<100: continue
    ring=ndimage.binary_dilation(m,iterations=12)&~ndimage.binary_dilation(m,iterations=3)
    ys,xs=np.nonzero(m); W2o=(W2&m).sum()/a
    print(a, int(xs.mean()-700), int(700-ys.mean()), 'ringGB %.1f'%np.median(gb[ring]), 'inModel %.2f'%W2o)
