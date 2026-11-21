"""Hand-painted far-land tiles (seen from 1.5-12 km): tex/suburb.png (120 m, street grid, lots, roofs, yard trees)
and tex/cane.png (480 m, paddock patchwork with crop rows, headland tracks). Seamless (wrapped drawing)."""
import numpy as np, os
from PIL import Image, ImageDraw, ImageFilter
rng = np.random.default_rng(7); O = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex')
def wrap_draw(N, fn):
    big = Image.new('RGB', (3 * N, 3 * N)); d = ImageDraw.Draw(big); fn(d, N)
    t = big.crop((N, N, 2 * N, 2 * N)); acc = np.zeros((N, N, 3))
    for dy in range(3):
        for dx in range(3): acc = np.maximum(acc, np.asarray(big.crop((dx * N, dy * N, dx * N + N, dy * N + N))).astype(float))
    return acc
# ---- suburb: 120 m, 512 px (0.234 m/px)
N = 512; M = N / 120.0
img = np.zeros((N, N, 3)); img[:] = (112, 128, 84)   # lawn
im = Image.fromarray(img.astype(np.uint8)); d = ImageDraw.Draw(im)
roads = [0, 60]   # streets every 60 m both ways, 10 m reserve
for rx in roads:
    for k in (-1, 0, 1):
        x = (rx + k * 120) * M
        d.rectangle([x - 5 * M, 0, x + 5 * M, N], fill=(118, 116, 108)); d.rectangle([x - 3.5 * M, 0, x + 3.5 * M, N], fill=(84, 86, 88))
        d.rectangle([0, x - 5 * M, N, x + 5 * M], fill=(118, 116, 108)); d.rectangle([0, x - 3.5 * M, N, x + 3.5 * M], fill=(84, 86, 88))
roofs = [(178, 74, 52), (196, 198, 194), (160, 164, 166), (128, 132, 136), (204, 196, 178), (150, 70, 52), (96, 104, 112)]
for bx in (5, 65):
    for by in (5, 65):
        for side in (0, 1):            # two rows of lots per block, 50 m deep block
            for lot in range(3):
                x0 = bx + 2 + lot * 16.5; y0 = by + 3 + side * 26
                w = rng.uniform(9, 13); h = rng.uniform(8, 12); ox = x0 + rng.uniform(0, 15 - w); oy = y0 + (1 if side == 0 else 22 - h) * 1.0
                c = roofs[rng.integers(len(roofs))]
                d.rectangle([ox * M + 3, oy * M + 3, (ox + w) * M + 3, (oy + h) * M + 3], fill=(70, 78, 60))   # shadow
                d.rectangle([ox * M, oy * M, (ox + w) * M, (oy + h) * M], fill=c)
                sh = tuple(int(v * 0.82) for v in c)
                if w > h: d.rectangle([ox * M, (oy + h / 2) * M, (ox + w) * M, (oy + h) * M], fill=sh)   # hip/gable shade
                else: d.rectangle([(ox + w / 2) * M, oy * M, (ox + w) * M, (oy + h) * M], fill=sh)
                if rng.random() < 0.3: d.rectangle([(x0 + 1) * M, (y0 + 13 if side == 0 else y0 + 2) * M, (x0 + 5) * M, (y0 + 20 if side == 0 else y0 + 9) * M], fill=(70, 150, 170))  # pool
for _ in range(70):                   # yard trees
    x, y = rng.uniform(0, 120, 2); r = rng.uniform(2, 5); g = rng.uniform(0.8, 1.15)
    for k in (-120, 0, 120):
        for l in (-120, 0, 120):
            d.ellipse([(x + k - r) * M + 2, (y + l - r) * M + 2, (x + k + r) * M + 2, (y + l + r) * M + 2], fill=(52, 62, 44))
            d.ellipse([(x + k - r) * M, (y + l - r) * M, (x + k + r) * M, (y + l + r) * M], fill=(int(58 * g), int(98 * g), int(48 * g)))
a = np.asarray(im).astype(float) * (1 + 0.06 * rng.standard_normal((N, N, 1)))
im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
im.putalpha(0); im.save(os.path.join(O, 'suburb.png'))
# ---- cane: 480 m, 512 px (0.94 m/px)
N = 512; M = N / 480.0
im = Image.new('RGB', (N, N), (96, 92, 70)); d = ImageDraw.Draw(im)
crops = [tuple(int(v * f) for v in (112, 142, 70)) for f in (0.92, 0.96, 1.0, 1.04, 1.08, 0.94, 1.02)]   # within +-8% of the base green (texture session v7)
xs = [0, 110, 230, 340, 480]; ys = [0, 90, 200, 300, 400, 480]
for i in range(len(xs) - 1):
    for j in range(len(ys) - 1):
        x0, x1, y0, y1 = xs[i] + 4, xs[i + 1] - 4, ys[j] + 4, ys[j + 1] - 4
        c = np.array(crops[rng.integers(len(crops))], float)
        d.rectangle([x0 * M, y0 * M, x1 * M, y1 * M], fill=tuple(c.astype(int)))
        vert = rng.random() < 0.5
        for t in np.arange(0, 120, 1.6):       # crop rows
            cc = tuple((c * (0.86 if int(t / 1.6) % 2 else 1.0)).astype(int))
            if vert and x0 + t < x1: d.line([((x0 + t) * M, y0 * M), ((x0 + t) * M, y1 * M)], fill=cc)
            if not vert and y0 + t < y1: d.line([(x0 * M, (y0 + t) * M), (x1 * M, (y0 + t) * M)], fill=cc)
d.line([(0, 200 * M), (N, 200 * M)], fill=(118, 130, 92), width=2); d.line([(230 * M, 0), (230 * M, N)], fill=(118, 130, 92), width=2)
a = np.asarray(im).astype(float) * (1 + 0.05 * rng.standard_normal((N, N, 1)))
im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.5)); im.putalpha(0); im.save(os.path.join(O, 'cane.png'))
print('ok')

# ---- repeat break (texture session v7): 50/50 with a 2nd sample at 1/0.37 = 2.6x the tile, rotated 36.87 deg (3-4-5),
# contrast x1.414 around the mean. Seamless big tile = 13 tiles = 5 rotated samples. Plus faded copies (to the average) for 2.5-6 km.
from scipy import ndimage as ndi
def rbreak(name, T, NO=4096):
    a = np.asarray(Image.open(os.path.join(O, name + '.png')).convert('RGB'), np.float32); S = a.shape[0]; BIG = 13 * T; T2 = 2.6 * T
    g = (np.arange(NO) + 0.5) / NO * BIG; X, Y = np.meshgrid(g, g)
    def samp(u, v):
        x = (u % 1) * S; y = (v % 1) * S; x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = (x - x0)[..., None]; fy = (y - y0)[..., None]
        A = lambda yy, xx: a[yy % S, xx % S]
        return A(y0, x0) * (1 - fx) * (1 - fy) + A(y0, x0 + 1) * fx * (1 - fy) + A(y0 + 1, x0) * (1 - fx) * fy + A(y0 + 1, x0 + 1) * fx * fy
    c, s_ = 0.8, 0.6
    m = 0.5 * samp(X / T, Y / T) + 0.5 * samp((c * X - s_ * Y) / T2 + 0.31, (s_ * X + c * Y) / T2 + 0.63)
    av = m.reshape(-1, 3).mean(0); m = av + (m - av) * 1.414
    for f, sfx in ((1.0, ''), (0.7, '_f1'), (0.4, '_f2'), (0.15, '_f3')):
        im = Image.fromarray(np.clip(av + (m - av) * f, 0, 255).astype(np.uint8)); im.putalpha(0); im.save(os.path.join(O, name + '_rb' + sfx + '.png'))
    print(name, 'big tile %.0f m' % BIG, 'avg', av.round(1))
    return av.tolist()
import json
json.dump({'suburb': rbreak('suburb', 120.0), 'cane': rbreak('cane', 480.0)}, open(os.path.join(O, 'landuse_avg.json'), 'w'))
