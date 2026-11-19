# press_traced.py CODE: the Gold Coast shoulder press (gcs_shoulder.py) for a club already traced. The rows above the
# armpit (frame row 766.5) are pressed so the top cloth row lands on frame row 246 like every club; the same row map is
# applied to the design and to both refs (flat and photo), so they stay in register. Armpit and below are untouched.
import sys, json, numpy as np
from PIL import Image
code = sys.argv[1]
A, TOP = 189.0 + (1.62 - 1.37) * 2310, 246.0
ks = {}
for side in ('front', 'back'):
    d = np.array(Image.open('design_%s_%s.png' % (code, side)))
    top = np.where((d[..., 3] > 0).any(1))[0].min()
    k = (A - TOP) / (A - top)
    ks[side] = k
    if top >= TOP - 2:
        print(side, 'top', top, 'already at 246'); continue
    for name in ('design_%s_%s.png' % (code, side), 'ref/%s_%s.png' % (code, side), 'ref/%s_%s_photo.png' % (code, side)):
        im = np.array(Image.open(name)).astype(float)
        bgv = 0 if im.shape[2] == 4 else 255
        out = np.full_like(im, bgv)
        out[int(A):] = im[int(A):]
        for r in range(int(TOP), int(A)):
            src = A - (A - r) / k
            r0 = int(np.floor(src)); f = src - r0
            out[r] = im[r0] * (1 - f) + im[min(r0 + 1, im.shape[0] - 1)] * f
        Image.fromarray(out.round().astype(np.uint8)).save(name)
    print(side, 'top row', top, '-> 246, rows above the armpit pressed to %.3f' % k)
json.dump(ks, open('%s_shoulder.json' % code.lower(), 'w'))
