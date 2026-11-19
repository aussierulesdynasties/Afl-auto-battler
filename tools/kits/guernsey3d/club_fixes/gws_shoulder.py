# GWS (as Gold Coast, gcs_shoulder.py): the photo's armhole is deeper than our body's, so with the armpit binding on the body's armpit the
# collar sits up the neck. Rows above the armpit are pressed toward it so the shoulder top lands where every other
# club's does (frame row 246, body y 1.595); the armpit row and everything below it are untouched.
import numpy as np, json
from PIL import Image
A = 189.0 + (1.62 - 1.37) * 2310   # armpit row in the frame (766.5)
TOP = 246.0
ks = {}
for side in ('front', 'back'):
    flat = np.array(Image.open('ref/GWS_%s.png' % side).convert('RGB'))
    cloth = flat.sum(2) < 735
    top = np.where(cloth.any(1))[0].min()
    k = (A - TOP) / (A - top)
    ks[side] = k
    for name in ('ref/GWS_%s.png' % side, 'ref/GWS_%s_photo.png' % side):
        im = np.array(Image.open(name).convert('RGB'))
        out = np.full_like(im, 255)
        out[int(A):] = im[int(A):]
        for r in range(int(TOP), int(A)):
            src = A - (A - r) / k
            r0 = int(np.floor(src)); f = src - r0
            out[r] = (im[r0] * (1 - f) + im[min(r0 + 1, im.shape[0] - 1)] * f).round()
        Image.fromarray(out.astype(np.uint8)).save(name)
    print(side, 'top row', top, '-> 246, rows above the armpit pressed to %.3f' % k)
json.dump(ks, open('gws_shoulder.json', 'w'))
