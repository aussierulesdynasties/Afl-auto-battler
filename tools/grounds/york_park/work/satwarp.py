# Warp the straight-down satellite onto a GE view's ground plane (field height) and blend, to test the GE camera on ground features.
# Z0=-3 python work/satwarp.py view x0,y0,x1,y1 scale out [zplane]
import sys, numpy as np; sys.path.insert(0, 'work'); import gecam as G
from PIL import Image
v, box, sc, out = sys.argv[1:5]; zp = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
x0, y0, x1, y1 = (int(t) for t in box.split(',')); sc = float(sc)
c = G.cam(v); S = np.asarray(Image.open('sat/esri_025.png').convert('RGB'))
uu, vv = np.meshgrid(np.arange(x0, x1, 1 / sc), np.arange(y0, y1, 1 / sc))
D = (c['fwd'][None, None] * c['f'] + c['right'][None, None] * (uu - c['W'] / 2)[..., None] - c['up'][None, None] * (vv - c['H'] / 2)[..., None])
t = (zp + G.Z0 - c['C'][2]) / D[..., 2]; X = c['C'][0] + t * D[..., 0]; Y = c['C'][1] + t * D[..., 1]
pu = np.clip(((X + 260) * 4).astype(int), 0, 2079); pv = np.clip(((260 - Y) * 4).astype(int), 0, 2079)
W = S[pv, pu]
ge = Image.open(f'ge/{v}.png').convert('RGB').crop((x0, y0, x1, y1)).resize((W.shape[1], W.shape[0]), Image.LANCZOS)
Image.blend(ge, Image.fromarray(W.astype(np.uint8)), 0.5).save(out, quality=90); print(out)
