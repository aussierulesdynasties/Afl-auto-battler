# Subiaco B (1997): hand-made procedural textures, no photo pixels. Shared materials (concrete, sheeting, brick,
# render, steel, pickets...) are the A2 set from mktexA2.py; the 1997-only ones are drawn here at 2048 px and
# downsampled to 1024 (supersampled = crisp edges). Tile sizes match the tile= argument in buildB.py.
import numpy as np, os, shutil
from PIL import Image, ImageDraw, ImageFilter
os.makedirs('texB', exist_ok=True)
for n in os.listdir('texA'): shutil.copy('texA/' + n, 'texB/' + n)
rng = np.random.default_rng(1997); S = 2048; O = 1024
yy, xx = np.mgrid[0:S, 0:S]
def save(a, n): Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((O, O), Image.LANCZOS).save('texB/' + n + '.png')
def grain(blur=0.8):
    n = rng.normal(0, 1, (S, S)); im = Image.fromarray(((n * 40 + 128).clip(0, 255)).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
    return (np.array(im, float) - 128) / 40
def blotch(scale=300):
    n = rng.normal(0, 1, (S // 32, S // 32)); im = Image.fromarray(((n * 40 + 128).clip(0, 255)).astype(np.uint8)).resize((S, S), Image.BICUBIC)
    return (np.array(im.filter(ImageFilter.GaussianBlur(scale / 16)), float) - 128) / 40
def tint(base, *f):
    a = np.zeros((S, S, 3)) + np.array(base, float)
    for g, k in f: a += g[..., None] * k
    return a
# ---- blue plastic tip-up seats on concrete treads: 0.80 m rows, 0.48 m seats (tile 4 m x 4 m: 5 rows)
M = S / 4.0
im = Image.fromarray(np.clip(tint([176, 174, 168], (grain(0.7), 4), (blotch(), 4)), 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
for r in range(5):
    y0 = r * 0.8 * M
    d.rectangle([0, y0, S, y0 + 0.14 * M], fill=(122, 120, 114))                      # riser in shade
    for k in range(int(4 / 0.48) + 1):
        x0 = k * 0.48 * M + 0.04 * M; g = int(rng.integers(-6, 7))
        d.rounded_rectangle([x0, y0 + 0.22 * M, x0 + 0.40 * M, y0 + 0.50 * M], radius=int(0.05 * M), fill=(34 + g, 88 + g, 168 + g))   # seat pan
        d.rounded_rectangle([x0, y0 + 0.50 * M, x0 + 0.40 * M, y0 + 0.64 * M], radius=int(0.04 * M), fill=(22 + g, 58 + g, 120 + g))   # back
        d.line([x0 + 0.04 * M, y0 + 0.25 * M, x0 + 0.36 * M, y0 + 0.25 * M], fill=(96, 150, 220), width=4)                            # lit lip
save(np.array(im, float), 'seatsb')
# ---- white aisle / walkway concrete: plain light concrete with 0.2 m steps and yellow-free nosing (tile 4 m)
a_ = tint([226, 224, 216], (grain(0.7), 4), (blotch(), 4)); a_[((yy / M) % 0.4) < 0.03] *= 0.82; save(a_, 'aisle')
# ---- multi-storey office/stand block (east), tile 16 m: 4 m storeys = 1.2 m beige precast spandrel + 2.8 m
# dark tinted glazing, aluminium mullions every 1.6 m, a shadow line under each slab edge
M = S / 16.0; v = yy / M; u = xx / M; st = v % 4.0
f = tint([46, 54, 62], (blotch(400), 5))
spd = st < 1.2; f[spd] = [204, 192, 168]; f += (grain(1.0) * 3)[..., None]
f[(st >= 1.2) & (st < 1.32)] = [70, 66, 60]                                          # slab shadow
f[(~spd) & ((u % 1.6) < 0.07)] = [168, 170, 172]                                     # mullions
f[(~spd) & ((st % 4.0 > 2.6) & (st % 4.0 < 2.66))] = [150, 152, 154]                 # transom
f[spd & ((u % 3.2) < 0.03)] *= 0.85                                                  # precast panel joints
save(f, 'facade')
# ---- near bowl back (south), tile 16 m: open concourse levels, 0.8 m concrete piers every 4 m, 0.7 m slab edge every 4 m
k_ = tint([40, 42, 48], (blotch(400), 4))
k_[(u % 4.0) < 0.6] = [150, 146, 138]; k_[(v % 4.0) < 0.4] = [164, 160, 150]
k_[((u % 4.0) >= 0.6) & ((u % 4.0) < 0.7)] *= 0.7                                     # pier shadow edge
k_[((v % 4.0) >= 0.4) & ((v % 4.0) < 0.5)] *= 0.7
k_ += (grain(1.0) * 4)[..., None]; save(k_, 'facaded')
# ---- bare construction pad (west end works), tile 12 m: pale concrete slabs, saw cuts every 6 m, tyre scuffs
M = S / 12.0; v = yy / M; u = xx / M
p = tint([214, 210, 200], (grain(0.9), 5), (blotch(500), 7))
p[((v % 6.0) < 0.04) | ((u % 6.0) < 0.04)] *= 0.8; save(p, 'pad')
# ---- grass bank behind the west boards, tile 8 m: longer unmown grass, darker and patchier than the arena
M = S / 8.0
b = tint([70, 102, 52], (grain(1.4), 9), (blotch(250), 10)); save(b, 'bank')
# ---- plain perimeter panels (no lettering, no sponsor colours): white painted sheet on a grey frame, tile 24 m
M = S / 24.0; u = xx / M; v = yy / M
w = tint([236, 236, 230], (grain(1.2), 2), (blotch(500), 3)); w[(u % 3.0) < 0.06] = [120, 120, 118]; w[(v < 0.4) | (v > 23.6)] = [120, 120, 118]
save(w, 'ads')
# ---- light-tower lamp head: grey steel frame holding 6 x 4 floodlights (round glass fronts, rims)
l = Image.new('RGB', (S, S), (92, 96, 100)); d = ImageDraw.Draw(l)
for i in range(6):
    for j in range(4):
        cx, cy = S / 12 + i * S / 6, S / 8 + j * S / 4; R = S / 14
        d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(52, 54, 58)); d.ellipse([cx - R * 0.8, cy - R * 0.8, cx + R * 0.8, cy + R * 0.8], fill=(214, 220, 226))
        d.ellipse([cx - R * 0.5, cy - R * 0.6, cx - R * 0.05, cy - R * 0.2], fill=(244, 246, 248))
d.rectangle([0, 0, S, S / 60], fill=(70, 72, 76)); save(np.array(l, float), 'lamps')
# ---- dark grey steel deck (near-right roof and the east end of the near roof read dark in the photo): 0.25 m ribs
M = S / 4.0; u = xx / M
dd = tint([66, 68, 70], (grain(1.0), 3), (blotch(400), 3)); ph = (u % 0.25) / 0.25
dd[ph < 0.10] *= 0.75; dd[(ph >= 0.10) & (ph < 0.16)] *= 1.2; save(dd, 'roofd')
print('ok', sorted(os.listdir('texB')))
