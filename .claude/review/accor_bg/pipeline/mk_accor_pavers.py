"""Hand-made Olympic Park forecourt pavers: one 40 m tile (4096 px), laid along the boulevard axis (UV rotated in scene.py).
Measured on the 0.5 m satellite (_meas_pav2.py) and the Easter Show ground photo:
  base mauve-brown pavers   sat 143,124,116 -> albedo x0.9
  buff cross-band           sat 181,165,146, 11 m wide, one every 40 m (boulevard crossings at 39.5 m), centre at u = 13.5 m
  pavers                    225 x 112.5 mm interlocking, laid in stretcher bond
Overwrites tex/pavers_paved.png. python -E mk_accor_pavers.py"""
import numpy as np
from PIL import Image
rng = np.random.default_rng(5)
M = 40.0; N = 4096; px = N / M                     # 102.4 px per metre
BASE = np.array([143, 124, 116], np.float32) * 0.9
BUFF = np.array([181, 165, 146], np.float32) * 0.9
BAND_C, BAND_W = 13.5, 11.0
pw, ph = 0.225, 0.1125
rows = int(round(M / ph)); cols = int(round(M / pw))
pwp, php = N / cols, N / rows
img = np.zeros((N, N, 3), np.float32)
xc = (np.arange(N) + 0.5) / px                      # metres along u (boulevard axis)
band = np.abs(((xc - BAND_C + M / 2) % M) - M / 2) < BAND_W / 2
for r in range(rows):
    y0, y1 = int(r * php), int((r + 1) * php)
    off = (r % 2) * pwp / 2
    shade = 1 + rng.normal(0, 0.06, cols + 2)
    burnt = rng.random(cols + 2) < 0.05
    edges = (np.arange(-1, cols + 1) * pwp + off).astype(int)
    for c in range(cols + 1):
        xa, xb = max(0, edges[c]), min(N, edges[c + 1])
        if xb <= xa: continue
        k = shade[c] * (0.82 if burnt[c] else 1.0)
        seg = np.where(band[xa:xb, None], BUFF, BASE) * k + rng.normal(0, 1.5, 3)
        img[y0:y1, xa:xb] = seg[None]
        img[y0:y1, xa:xa + 1] *= 0.72               # joint
    img[y0:y0 + 1] *= 0.75
# fine grain only (no painted blotches)
img += rng.normal(0, 2.5, (N, N, 1))
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save('tex/pavers_paved.png')
print('accor pavers base', BASE.round(), 'band', BUFF.round(), 'tile m', M)
# tower cap panels (1 m tile): pale steel sheet with a seam and lamp lens rows, hand-painted
c = np.full((64, 64, 3), [200, 204, 206], np.float32) + rng.normal(0, 3, (64, 64, 1))
c[:, :2] *= 0.7; c[:2] *= 0.75
c[20:44, 14:50] = [228, 226, 200]; c[22:42, 16:48] = [246, 240, 210]
c[30:34] *= 0.9
Image.fromarray(np.clip(c, 0, 255).astype(np.uint8)).save('tex/accor_cap.png')
