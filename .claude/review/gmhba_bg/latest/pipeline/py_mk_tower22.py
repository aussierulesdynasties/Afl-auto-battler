"""Hand-made facades for named Geelong buildings, tex/fac/n_<key>.png (256 px = one 3.6 m bay x 3.2 m floor, alpha 1 = glass,
wall part carries its own colour; the scene's wall vertex colour is white for these). From the research notes
(facades_research.md): Pivot House and Ryrie Home are brick with punched windows; TAC is precast with green/blue/red
aluminium sunshades; Barwon Water is a curtain wall behind a perforated metal screen; the Old Post Office is cream render;
St Mary's is bluestone with lancet windows (tile 4 m x 6 m). python -E py_mk_tower22.py"""
import os, numpy as np
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); R = np.random.default_rng(9); N = 256
yy, xx = np.mgrid[0:N, 0:N]
def save(k, a): Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(H, 'tex', 'fac', 'n_%s.png' % k))
def brick(rgb, k):
    a = np.zeros((N, N, 4)); a[..., :3] = rgb; a[..., 3] = 0
    cr = 9; row = yy // cr; off = (row % 2) * 9
    a[..., :3] *= (0.9 + 0.2 * ((((xx + off) // 18) * 7 + row * 13) % 5) / 4)[..., None]   # brick-to-brick shade
    a[(yy % cr == 0) | ((xx + off) % 18 == 0)] [..., :3] = 0
    m = (yy % cr == 0) | ((xx + off) % 18 == 0); a[m, :3] = np.array(rgb) * 0.55 + 70   # mortar
    w = (xx > 64) & (xx < 192) & (yy > 70) & (yy < 220)   # punched window 1.8 m x 1.9 m
    a[w, :3] = (30, 40, 48); a[w, 3] = 255; a[w & (np.abs(xx - 128) < 3), :3] = 60; a[w & (np.abs(xx - 128) < 3), 3] = 0
    a[(xx > 58) & (xx < 198) & (yy >= 220) & (yy < 228), :3] = 150; a[..., :3] += R.normal(0, 4, (N, N, 1)); save(k, a)
brick((150, 72, 52), 'pivot')        # 'Rustic Red' brick
brick((138, 84, 62), 'ryrie44')      # hand-laid wool-store brick
a = np.zeros((N, N, 4)); a[..., :3] = 196; a[..., 3] = 0   # TAC: precast spandrel, ribbon glazing, coloured sunshade panels
g = (yy > 96) & (yy < 236); a[g, :3] = (34, 46, 56); a[g, 3] = 255
pc = [(92, 150, 92), (70, 110, 160), (176, 64, 52)][0]
for i, c in enumerate([(92, 150, 92), (70, 110, 160), (176, 64, 52), (92, 150, 92)]):
    s = (xx >= i * 64 + 6) & (xx < i * 64 + 34) & (yy > 100) & (yy < 232); a[s, :3] = c; a[s, 3] = 0
a[..., :3] += R.normal(0, 3, (N, N, 1)); save('tac', a)
a = np.zeros((N, N, 4)); a[..., :3] = (40, 56, 66); a[..., 3] = 255   # Barwon Water: curtain wall + perforated draped screen
d = ((xx % 16 - 8) ** 2 + (yy % 16 - 8) ** 2) < (12 + 10 * np.sin(xx / N * 2 * np.pi)) ; sc = ~d
a[sc, :3] = (176, 172, 164); a[sc, 3] = 0; a[yy < 10, :3] = 120; a[yy < 10, 3] = 0; save('barwon', a)
a = np.zeros((N, N, 4)); a[..., :3] = (214, 200, 172); a[..., 3] = 0   # Old PO: cream render, arched sash windows, string course
w = (xx > 84) & (xx < 172) & (yy > 60) & (yy < 210) & ~((yy < 104) & (((xx - 128) ** 2 + (yy - 104) ** 2) > 44 ** 2))
a[w, :3] = (40, 44, 48); a[w, 3] = 255; a[(yy > 36) & (yy < 48), :3] = 232; a[(yy > 214) & (yy < 222), :3] = 190
a[..., :3] += R.normal(0, 3, (N, N, 1)); save('oldpo', a)
a = np.zeros((N, N, 4)); a[..., :3] = (84, 86, 90); a[..., 3] = 0   # bluestone: coursed ashlar blocks, a lancet window per 4 m bay
row = yy // 16; off = (row % 2) * 24; a[..., :3] *= (0.86 + 0.28 * R.random((N // 16 + 1, N // 48 + 2))[row, (xx + off) // 48])[..., None]
m = (yy % 16 == 0) | ((xx + off) % 48 == 0); a[m, :3] = (120, 120, 118)
w = (np.abs(xx - 128) < 22) & (yy > 40) & (yy < 220) & ~((yy < 80) & (np.abs(xx - 128) > (yy - 40) * 0.55))
a[w, :3] = (36, 40, 50); a[w, 3] = 255; a[..., :3] += R.normal(0, 3, (N, N, 1)); save('bluestone', a)
print('ok')
