"""Crop the ground paint around the yard streak hits (x 140..250, y -60..200) and list its colours."""
import json, collections
from PIL import Image
import numpy as np
meta = json.load(open('data/marvel/prep/meta.json')); NE = meta['near']
im = Image.open('data/marvel/prep/ground.png').convert('RGB'); N = im.size[0]
def px(x, y): return int((x + NE) / (2 * NE) * N), int((NE - y) / (2 * NE) * N)
x0, y0 = px(100, 260); x1, y1 = px(300, -100)
c = im.crop((x0, y0, x1, y1)); c.resize((c.size[0] * 4, c.size[1] * 4), Image.NEAREST).save('out/marvel/close/ground_yard.png')
A = np.array(c).reshape(-1, 3); C = collections.Counter(map(tuple, A))
print('NE', NE, 'crop', x0, y0, x1, y1)
for k, v in C.most_common(8): print('COL', k, v)
B = collections.Counter(map(tuple, A[A.sum(1) > 420])); print('BRIGHT', B.most_common(5))
P = json.load(open('spec/marvel.json'))['palette']
for k, v in P.items():
    if isinstance(v, list) and len(v) == 3 and isinstance(v[0], int) and sum(v) > 420: print('PAL', k, v)
