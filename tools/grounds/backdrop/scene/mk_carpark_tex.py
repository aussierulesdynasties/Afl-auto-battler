"""Hand-made car park tiles, 512 px = 15.6 m along the rows x 16 m across (python3 mk_carpark_tex.py):
tex/mt/park_bays.png  a 6 m aisle, then two 5 m bay rows; 0.1 m painted lines at the bay ends and between the rows
                      (lines the aerial shows as faint, so they stay thin), tyre wear in the aisle, oil where cars sit
tex/mt/park_plain.png the same asphalt with no lines (a lot whose bays the aerial cannot place)
The lot's own colour is the vertex colour (the aerial's median); these only carry the pattern around it."""
import os, numpy as np
from PIL import Image, ImageFilter
H = os.path.dirname(os.path.abspath(__file__)); N = 512
u = (np.arange(N) + 0.5) / N * 15.6; v = (np.arange(N) + 0.5) / N * 16.0; U, V = np.meshgrid(u, v)
def asphalt(seed):
    R = np.random.default_rng(seed)
    a = np.full((N, N), 170.0) + R.normal(0, 9, (N, N))   # bright, so the lot colour (vertex colour) needs little gain
    lo = np.asarray(Image.fromarray(R.normal(0, 1, (N // 16, N // 16)).astype(np.float32)).resize((N, N), Image.BICUBIC))
    return a + 7 * lo, R                                     # patched resurfacing, a few metres across
a, R = asphalt(7); p = a.copy()
bay = V >= 6.0
a[~bay] *= 0.96                                              # the aisle, worn
a[bay & (np.mod(U, 2.6) < 0.1)] = 255.0                      # bay-end lines
a[np.abs(V - 11.0) < 0.05] = 255.0                           # line between the two bay rows
st = bay & (np.abs(np.mod(U, 2.6) - 1.3) < 0.45) & ((np.abs(V - 8.4) < 0.8) | (np.abs(V - 13.6) < 0.8))
a[st] *= np.where(R.random(st.sum()) < 0.5, 0.9, 0.96)       # oil where cars sit
for img, fn in ((a, 'park_bays.png'), (p, 'park_plain.png')):
    Image.fromarray(np.clip(np.stack([img, img, img * 0.98], -1), 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)).save(os.path.join(H, 'tex', 'mt', fn))
print('ok')
