"""tex/road_asphalt.png (grey multiplier, 512 px = 8 m) -> tex/road_asphalt_{road,park}.png: one 104 m seamless tile (4096 px) =
50/50 of the asphalt at 8 m and a second sample at 20.8 m rotated 36.87 deg (3-4-5, so 104 m stays seamless) offset (0.31, 0.63),
x the spec's road / parking colour. Plus tex/pavers_paved.png. python -E mk_road_tex.py spec.json"""
import json, sys
import numpy as np
from PIL import Image
P = json.load(open(sys.argv[1]))['palette']
ra = np.asarray(Image.open('tex/road_asphalt.png').convert('L'), np.float32); S = ra.shape[0]
def samp(u, v):   # bilinear, wrapping; u, v in tiles
    x = (u % 1) * S; y = (v % 1) * S; x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = x - x0; fy = y - y0
    a = lambda yy, xx: ra[yy % S, xx % S]
    return (a(y0, x0) * (1 - fx) * (1 - fy) + a(y0, x0 + 1) * fx * (1 - fy) + a(y0 + 1, x0) * (1 - fx) * fy + a(y0 + 1, x0 + 1) * fx * fy)
BIG, N = 104.0, 4096
g = (np.arange(N) + 0.5) / N * BIG; X, Y = np.meshgrid(g, g)
c, s = 0.8, 0.6
m = 0.5 * samp(X / 8.0, Y / 8.0) + 0.5 * samp((c * X - s * Y) / 20.8 + 0.31, (s * X + c * Y) / 20.8 + 0.63)
m = m / m.mean(); m = 1 + (m - 1) * 1.15   # contrast lifted 1.15x around the mean (texture session)
for k, fn in (('road', 'road'), ('parking', 'park')):
    t = np.clip(m[..., None] * np.array(P[k], np.float32), 0, 255).astype(np.uint8)
    Image.fromarray(t).save('tex/road_asphalt_%s.png' % fn); print(fn, t.mean(), t.std())
pv = np.asarray(Image.open('tex/mv_plaza_pavers.png').convert('RGB'), np.float32)
t = np.clip(pv / pv.mean() * np.array(P.get('paved_pavers', [190, 188, 182]), np.float32), 0, 255).astype(np.uint8)
Image.fromarray(t).save('tex/pavers_paved.png'); print('pavers', t.mean(), t.std())
