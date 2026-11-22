# Measure Olympic Boulevard / forecourt paving from the 0.5 m satellite.
# Crop = sat_1km px (640,170)-(900,430); pav_patch.png shows it at 0.25 m per display px.
import numpy as np
from PIL import Image
im = np.asarray(Image.open('data/accor/sat.png').convert('RGB'), np.float32); H, W = im.shape[:2]; cx, cy = W // 2, H // 2
def m(p): return ((p[0] * 2000 / 1400 - 1000) * 0.5, -(p[1] * 2000 / 1400 - 1000) * 0.5)
X0, Y0 = m((640, 170)); a, b = int(cx + X0 / 0.5), int(cy - Y0 / 0.5)
def at(dx, dy, r=6):   # display px -> mean rgb of a (2r x 2r) display-px box
    sx, sy = a + dx // 2, b + dy // 2; return im[sy - r // 2:sy + r // 2, sx - r // 2:sx + r // 2].reshape(-1, 3).mean(0).round()
for k, p in {'plaza_base': (200, 330), 'plaza_base2': (110, 300), 'buff_band': (300, 545), 'buff_band2': (225, 470),
             'road_charcoal': (395, 290), 'road_buff_x': (470, 345), 'red_strip': (300, 105)}.items():
    print(k, at(*p))
# band period: luminance along a line across the plaza parallel to the boulevard (display px (120,240)->(330,690))
t = np.linspace(0, 1, 400); xs = (120 + 210 * t) / 2 + a; ys = (240 + 450 * t) / 2 + b
L = np.array([im[int(y) - 1:int(y) + 2, int(x) - 1:int(x) + 2].mean() for x, y in zip(xs, ys)])
seg = np.hypot(210, 450) * 0.25; d = t * seg
hi = L > np.percentile(L, 70); edges = np.flatnonzero(np.diff(hi.astype(int)))
print('line length m', round(seg, 1), 'band edges m', [round(d[e], 1) for e in edges])
