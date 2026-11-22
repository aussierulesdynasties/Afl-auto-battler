"""Hand-made facade variants (no photo pixels). RGBA tile 256 px = 3.6 m x 3.2 m (one bay, one storey).
alpha 0 = wall pattern (multiplied by the building's own colour), alpha 1 = window glass and frame (drawn colour).
tex/fac/h0..h7 (houses), tex/fac/b0..b11 (blocks). python -E py_mk_facades.py"""
import os
import numpy as np
from PIL import Image, ImageDraw
H = os.path.dirname(os.path.abspath(__file__)); O = os.path.join(H, 'tex', 'fac'); os.makedirs(O, exist_ok=True)
N = 256; PX = N / 3.6   # px per metre across; rows: 256 px = 3.2 m
PY = N / 3.2
rng = np.random.default_rng(7)

def wall(kind, base=214):
    a = np.full((N, N), float(base))
    if kind == 'brick':
        ch = 0.086 * PY; bw = 0.24 * PX
        for r in range(int(N / ch) + 1):
            y0 = int(r * ch); off = (bw / 2) * (r % 2)
            a[y0:y0 + 1] = base - 46
            for c in range(-1, int(N / bw) + 2):
                x0 = int(c * bw + off); tone = rng.normal(0, 9)
                a[y0 + 1:int((r + 1) * ch), max(0, x0 + 1):max(0, min(N, int(x0 + bw)))] += tone
                if 0 <= x0 < N: a[y0:int((r + 1) * ch), x0] = base - 46
    elif kind == 'weather':
        bh = 0.18 * PY
        for r in range(int(N / bh) + 1):
            y0 = int(r * bh); a[y0:y0 + 2] = base - 52; a[y0 + 2:y0 + 5] = base - 18
    elif kind == 'render':
        a += rng.normal(0, 5, (N, N))
    elif kind == 'panel':   # precast / tilt-up panels, 1.2 m joints
        a += rng.normal(0, 4, (N, N))
        for x in range(0, N, int(1.2 * PX)): a[:, x:x + 2] = base - 40
        a[int(1.6 * PY):int(1.6 * PY) + 2] = base - 34
    elif kind == 'block':   # concrete block 0.4 x 0.2 m
        for r in range(int(N / (0.2 * PY)) + 1):
            y0 = int(r * 0.2 * PY); a[y0:y0 + 1] = base - 36
            for c in range(-1, 12):
                x0 = int(c * 0.4 * PX + (0.2 * PX) * (r % 2))
                if 0 <= x0 < N: a[y0:int((r + 1) * 0.2 * PY), x0] = base - 36
        a += rng.normal(0, 4, (N, N))
    rgba = np.zeros((N, N, 4), np.uint8); rgba[..., :3] = np.clip(a, 0, 255)[..., None]; return rgba

GLASS = [(46, 56, 66), (70, 84, 96), (38, 44, 50), (96, 108, 118), (58, 70, 74)]
FRAME = [(232, 232, 226), (60, 58, 56), (150, 120, 88), (190, 192, 190), (30, 30, 32)]

def window(img, x0, y0, x1, y1, glass, frame, mull=0, trans=0, sill=False):
    d = ImageDraw.Draw(img); f = 0.05 * PX
    d.rectangle([x0, y0, x1, y1], fill=frame + (255,))
    d.rectangle([x0 + f, y0 + f, x1 - f, y1 - f], fill=glass + (255,))
    for i in range(1, mull + 1):
        x = x0 + (x1 - x0) * i / (mull + 1); d.rectangle([x - f / 2, y0, x + f / 2, y1], fill=frame + (255,))
    if trans: y = y0 + (y1 - y0) * trans; d.rectangle([x0, y - f / 2, x1, y + f / 2], fill=frame + (255,))
    # soft reflection streak on the glass
    d.polygon([(x0 + f, y0 + f), (x0 + (x1 - x0) * 0.35, y0 + f), (x0 + f, y0 + (y1 - y0) * 0.5)], fill=tuple(min(255, c + 22) for c in glass) + (255,))
    if sill: d.rectangle([x0 - f, y1, x1 + f, y1 + 0.06 * PY], fill=(200, 198, 192, 255))

def M(x): return x * PX
def Mv(y): return N - y * PY   # metres above floor -> row

HOUSE = [('brick', [(0.5, 3.0, 0.9, 2.3, 1, 0.0)]), ('brick', [(1.0, 2.6, 1.0, 2.1, 0, 0.3)]), ('weather', [(0.6, 2.9, 1.0, 2.2, 2, 0.0)]),
         ('weather', [(1.3, 2.3, 0.6, 2.4, 0, 0.25)]), ('render', [(0.3, 3.3, 0.5, 2.4, 3, 0.0)]), ('render', [(0.9, 2.7, 0.9, 2.2, 1, 0.3)]),
         ('brick', [(0.4, 1.6, 0.9, 2.2, 0, 0.3), (2.0, 3.2, 0.9, 2.2, 0, 0.3)]), ('weather', [(0.5, 1.5, 1.1, 2.1, 0, 0.0), (2.1, 3.1, 1.1, 2.1, 0, 0.0)])]
for i, (k, ws) in enumerate(HOUSE):
    im = Image.fromarray(wall(k, 214 if k != 'render' else 226)); g = GLASS[i % len(GLASS)]; fr = FRAME[i % 3 if k != 'weather' else 0]
    for x0, x1, y0, y1, mull, tr in ws: window(im, M(x0), Mv(y1), M(x1), Mv(y0), g, fr, mull, tr, sill=(k == 'brick'))
    im.save(os.path.join(O, 'h%d.png' % i))

BLOCK = [('panel', 'ribbon'), ('brick', 'punch2'), ('render', 'tall'), ('block', 'punch1'), ('panel', 'high'), ('render', 'ribbon_sp'),
         ('brick', 'arch'), ('panel', 'punch2'), ('render', 'grid'), ('block', 'high'), ('brick', 'tall'), ('render', 'shop')]
for i, (k, w) in enumerate(BLOCK):
    im = Image.fromarray(wall(k, 210 + 6 * (i % 3))); g = GLASS[(i + 2) % len(GLASS)]; fr = FRAME[(i + 1) % len(FRAME)]
    if w == 'ribbon': window(im, 0, Mv(2.5), N - 1, Mv(1.0), g, fr, 2)
    elif w == 'ribbon_sp': window(im, 0, Mv(2.2), N - 1, Mv(0.9), g, fr, 1); ImageDraw.Draw(im).rectangle([0, Mv(3.2), N, Mv(2.7)], fill=(150, 152, 150, 255))
    elif w == 'punch2': window(im, M(0.3), Mv(2.4), M(1.5), Mv(0.9), g, fr, 0, 0.3, True); window(im, M(2.1), Mv(2.4), M(3.3), Mv(0.9), g, fr, 0, 0.3, True)
    elif w == 'punch1': window(im, M(1.0), Mv(2.2), M(2.6), Mv(1.1), g, fr, 1)
    elif w == 'tall': window(im, M(1.2), Mv(2.8), M(2.4), Mv(0.4), g, fr, 0, 0.75, True)
    elif w == 'blank': pass
    elif w == 'arch':
        window(im, M(1.1), Mv(2.5), M(2.5), Mv(0.8), g, fr, 1, 0.25, True)
        ImageDraw.Draw(im).rectangle([M(1.0), Mv(2.75), M(2.6), Mv(2.5)], fill=(176, 172, 164, 255))
    elif w == 'grid':
        for xa in (0.2, 1.4, 2.6): window(im, M(xa), Mv(2.6), M(xa + 0.9), Mv(0.8), g, fr, 0, 0.5)
    elif w == 'high': window(im, M(0.2), Mv(2.9), M(3.4), Mv(2.3), g, fr, 3)
    elif w == 'shop': window(im, M(0.15), Mv(2.7), M(3.45), Mv(0.25), g, fr, 1, 0.82)
    im.save(os.path.join(O, 'b%d.png' % i))
print('facades', len(HOUSE), len(BLOCK))
