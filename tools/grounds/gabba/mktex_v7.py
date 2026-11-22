# Gabba v7 textures (MCG standard pass, 2026-11-22), drawn here like mktex_hand.py: no photo pixels.
# Colours read off Google Earth 3D (outside) and a 2019 photo sphere taken on the ground (inside).
#   facade_v7.png   one bay of the outside wall, 13 m wide x 25 m tall: grey precast podium to 10.5 m, then
#                   charcoal cladding panels (Google Earth: the wall behind the white steel reads near-black).
#   roofunder.png   the membrane seen from below: pale grey with a faint green tint (director's rule for roof
#                   undersides), seams every 3 m.
#   girder.png      dark grey painted steel for the rafters and ring truss under the roof.
#   boxglass_v7.png the corporate boxes' glass between the tiers: dark neutral glass (was blue).
import numpy as np, os
from PIL import Image, ImageDraw
R = np.random.default_rng(77)
os.makedirs('htex', exist_ok=True)


def save(a, name):
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save('htex/' + name); print(name, a.shape[1], a.shape[0])


PPM = 24
W, H = int(13 * PPM), int(25 * PPM)
a = np.zeros((H, W, 3), float)
z = (H - 1 - np.arange(H))[:, None] / PPM          # metres above the ground
x = np.arange(W)[None, :] / PPM
pod = z < 6.0          # grey precast to the first floor (Google Earth: the charcoal runs down to about 6 m)
a[:] = (62, 61, 60)                                  # charcoal cladding (warm: the sky light already cools it)
a[np.broadcast_to(pod, (H, W))] = (122, 122, 118)    # grey precast podium
# cladding: panels 1.3 m wide, 3.0 m tall, dark reveal joints
joint = ((x % 1.3) < 0.05) & ~pod | (((z - 6.0) % 3.0) < 0.06) & ~pod
a[joint] = (40, 41, 44)
# podium: precast panels 3.25 m x 3.5 m and their joints
pj = (((x % 3.25) < 0.06) | ((z % 3.5) < 0.06)) & pod
a[pj] = (100, 100, 97)
# rain streaks down the podium, panel tone wobble on the cladding
tone = R.normal(0, 3.0, (int(25 / 3) + 2, int(13 / 1.3) + 2))
a += np.where(~pod[..., None] & np.ones((H, W, 1), bool), tone[(np.clip(z - 6.0, 0, 99) // 3).astype(int), (x // 1.3).astype(int)][..., None], 0)
for _ in range(40):
    sx = R.integers(0, W); top = R.uniform(1.5, 10.0); ln = R.uniform(0.8, 3.0)
    m = (np.arange(H)[:, None] >= int((25 - top) * PPM)) & (np.arange(H)[:, None] < int((25 - top + ln) * PPM))
    a[m[:, 0], sx:sx + 2] -= 10
a += R.normal(0, 2.0, a.shape[:2])[..., None]
save(a, 'facade_v7.png')

# roof underside: 6 m x 6 m tile, pale grey-green, seams every 3 m, faint mottle
S = 192
b = np.zeros((S, S, 3), float); b[:] = (242, 235, 218)   # cream PTFE as the photo sphere shows it (lit through by the sun in a match: membrane_lit)
yy, xx = np.mgrid[0:S, 0:S]
b[(xx % (S // 2)) < 2] = (214, 208, 194)
b += (np.asarray(Image.fromarray((R.random((8, 8)) * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC), float)[..., None] / 255 - 0.5) * 10
save(b, 'roofunder.png')

# girder steel: 64 x 64, dark grey paint
g = np.zeros((64, 64, 3), float); g[:] = (74, 76, 78); g += R.normal(0, 2.5, (64, 64))[..., None]
save(g, 'girder.png')

# box glass: dark neutral glass only; its mullions, sill and head are modelled in build.py (no frames painted on)
c = np.zeros((166, 384, 3), float)
c[:] = np.linspace(92, 46, 166)[:, None, None] * np.array([1.0, 1.02, 1.06])
# the top 0.9 m of the 2.6 m face: the LED ribbon along the front of the boxes (photo sphere), shown as plain blocks of
# colour (no lettering, director 2026-11-18): dark board, club and sponsor colours in 3 m runs
rib = int(166 * 0.9 / 2.6)
c[:rib] = (22, 24, 32)
cols = [(28, 70, 160), (232, 190, 40), (30, 30, 36), (120, 30, 50), (40, 150, 80), (230, 230, 226)]
for k in range(2):
    cc = cols[R.integers(len(cols))]; x0 = k * 192
    c[6:rib - 6, x0 + 10:x0 + 182] = cc
save(c, 'boxglass_v7.png')
