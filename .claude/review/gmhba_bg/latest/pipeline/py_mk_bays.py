"""Hand-made car park tile tex/mt/park_bays.png: 512 x 512 px = 15.6 m along the rows (6 bays of 2.6 m) x 16 m across
(6 m aisle, two 5 m bay rows, pale line between the rows, bay-end lines). Asphalt grain and oil stains. python -E py_mk_bays.py"""
import os, numpy as np
from PIL import Image, ImageFilter
H = os.path.dirname(os.path.abspath(__file__)); R = np.random.default_rng(7); N = 512
u = (np.arange(N) + 0.5) / N * 15.6; v = (np.arange(N) + 0.5) / N * 16.0; U, V = np.meshgrid(u, v)
a = np.full((N, N), 96.0)
a[V < 6.0] = 80.0                                        # aisle, worn darker
bay = V >= 6.0
a[bay & (np.mod(U, 2.6) < 0.14)] = 178.0                 # bay-end lines
a[np.abs(V - 11.0) < 0.12] = 190.0                       # line between the two bay rows
a[np.abs(V - 6.0) < 0.1] = 150.0                         # kerb edge of each row
st = bay & (np.abs(np.mod(U, 2.6) - 1.3) < 0.5) & ((np.abs(V - 8.2) < 0.9) | (np.abs(V - 13.8) < 0.9))
a[st] *= np.where(R.random(st.sum()) < 0.5, 0.86, 0.94)  # oil stains where cars sit
a += R.normal(0, 5, (N, N))
img = np.stack([a, a * 1.0, a * 0.98], -1)
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.5)).save(os.path.join(H, 'tex', 'mt', 'park_bays.png'))
print('ok')
