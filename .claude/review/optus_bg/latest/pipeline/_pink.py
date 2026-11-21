import json
from PIL import Image; import numpy as np
s = json.load(open('spec/optus.json')); PAL = s['palette']
a = np.asarray(Image.open('data/optus/prep/ground.png').convert('RGB')).astype(int); n = a.shape[0]; m = 2 * 1500 / n
for k in ('plaza', 'path', 'sand', 'yard', 'paved'):
    c = PAL[k]; mk = np.all(np.abs(a - c) < 3, 2); ys, xs = np.nonzero(mk)
    if len(xs): print(k, mk.mean().round(4), 'x', int(xs.min() * m - 1500), int(xs.max() * m - 1500), 'y', int(1500 - ys.max() * m), int(1500 - ys.min() * m))
print(n, s.get('near_m'), [k for k in s if 'near' in k.lower()])
