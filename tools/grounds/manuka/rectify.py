"""Straighten one real bay of a close-up photo into a texture at real scale.
usage: python rectify.py SRC OUT TLx TLy TRx TRy BRx BRy BLx BLy WIDTH_M HEIGHT_M [PX_PER_M=100]
The four corners are the bay's corners in SRC pixels (top-left, top-right, bottom-right, bottom-left).
Output is WIDTH_M*ppm x HEIGHT_M*ppm, one bay, to be repeated once per modelled bay."""
import sys
import numpy as np
from PIL import Image

a = sys.argv
src, out = a[1], a[2]
pts = [float(v) for v in a[3:11]]
wm, hm = float(a[11]), float(a[12])
ppm = float(a[13]) if len(a) > 13 else 100.0
W, H = int(round(wm * ppm)), int(round(hm * ppm))
dst = [(0, 0), (W, 0), (W, H), (0, H)]
srcp = [(pts[0], pts[1]), (pts[2], pts[3]), (pts[4], pts[5]), (pts[6], pts[7])]
# PIL PERSPECTIVE maps output (x,y) -> input: x' = (a x + b y + c)/(g x + h y + 1), y' = (d x + e y + f)/(g x + h y + 1)
M = []
B = []
for (x, y), (u, v) in zip(dst, srcp):
    M.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
    M.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
coef = np.linalg.solve(np.array(M, float), np.array(B, float))
im = Image.open(src).convert('RGB')
im.transform((W, H), Image.PERSPECTIVE, tuple(coef), Image.BICUBIC).save(out)
print(out, W, H)
