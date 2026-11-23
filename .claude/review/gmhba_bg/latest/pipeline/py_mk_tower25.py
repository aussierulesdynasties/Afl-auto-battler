"""Hand-made facades for the remaining named Geelong towers (photos checked 2026-11-21 on Google Images), same tile
contract as py_mk_tower22.py: 256 px = 3.6 m bay x 3.2 m floor, alpha 255 = glass, alpha 0 = wall in its own colour.
gmhba: blue reflective curtain wall, fine vertical mullions (Cox, 60 Moorabool St)
worksafe: dark blue glass, tight pale vertical fins (peckvonhartel, 1 Malop St)
holiday: off-white precast grid, dark punched windows (Architectus, 40 Ryrie St)
rhotel: white frame, dark glass, terracotta vertical fins (10 Bellerine St)
edgewater: pale horizontal slab bands, dark glass balustrades (Fender Katsalidis, Eastern Beach Rd)
civic: clear glass curtain wall, thin floor bands (Wurriki Nyal, Cox)
rydges: cream render, punched windows with balcony recess (Rydges, Gheringhap St). python -E py_mk_tower25.py"""
import os, numpy as np
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); R = np.random.default_rng(25); N = 256
yy, xx = np.mgrid[0:N, 0:N]
def new(rgb, glass=False): a = np.zeros((N, N, 4)); a[..., :3] = rgb; a[..., 3] = 255 if glass else 0; return a
def wall(a, m, rgb): a[m, :3] = rgb; a[m, 3] = 0
def glass(a, m, rgb): a[m, :3] = rgb; a[m, 3] = 255
def save(k, a, n=3): a[..., :3] += R.normal(0, n, (N, N, 1)); Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(H, 'tex', 'fac', 'n_%s.png' % k))
a = new((58, 92, 132), True); a[..., :3] *= (0.92 + 0.16 * (yy / N))[..., None]   # sky gradient in the glass
wall(a, (xx % 85) < 4, (70, 76, 84)); wall(a, yy < 22, (52, 60, 70)); save('gmhba', a)
a = new((34, 56, 92), True); wall(a, (xx % 43) < 7, (196, 200, 204)); wall(a, yy < 12, (176, 180, 186)); save('worksafe', a)
a = new((226, 224, 218)); glass(a, (xx > 40) & (xx < 176) & (yy > 40) & (yy < 222), (40, 46, 54))
wall(a, (xx > 40) & (xx < 176) & (np.abs(yy - 150) < 3), (200, 198, 192)); wall(a, (xx >= 176) & (xx < 196), (206, 204, 198)); save('holiday', a)
a = new((236, 234, 228)); glass(a, (xx > 26) & (xx < 230) & (yy > 30) & (yy < 236), (36, 42, 48))
for f in (70, 128, 186): wall(a, (np.abs(xx - f) < 9) & (yy > 30) & (yy < 236), (176, 92, 56))
save('rhotel', a)
a = new((60, 72, 78), True); wall(a, yy < 58, (226, 224, 216)); glass(a, (yy >= 170), (78, 92, 96)); wall(a, (yy >= 166) & (yy < 172), (90, 90, 88)); save('edgewater', a)
a = new((112, 140, 156), True); wall(a, yy < 14, (196, 198, 196)); wall(a, (xx % 128) < 3, (150, 154, 156)); save('civic', a)
a = new((222, 214, 196)); glass(a, (xx > 56) & (xx < 200) & (yy > 44) & (yy < 226), (44, 48, 52))
wall(a, (xx > 50) & (xx < 206) & (yy >= 226) & (yy < 236), (232, 228, 216)); wall(a, (xx > 56) & (xx < 200) & (yy > 166) & (yy < 226), (170, 166, 156)); save('rydges', a)
print('ok')
