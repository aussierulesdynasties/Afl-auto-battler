from PIL import Image; import numpy as np
for f in ['roof_metal','roof_corrugated','mv_city_far','mv_curtain_glass','mv_plaza_pavers','ground_detail']:
    im=Image.open('tex/%s.png'%f); a=np.asarray(im.convert('RGBA')).astype(float)
    print(f, im.mode, im.size, a[...,:3].mean((0,1)).round(1), 'alpha', a[...,3].min(), a[...,3].mean().round(1))
g=np.asarray(Image.open('data/marvel/prep/ground.png').convert('RGB')).astype(int); print('ground', g.shape)
for c in [(184,178,164),(176,174,166)]: print(c, (np.abs(g-c).max(2)<=3).mean().round(4))
