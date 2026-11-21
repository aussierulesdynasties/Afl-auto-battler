"""MCG hi-res ground layer, painted at bake resolution (0.366 m/px) by bake_ground.py.
Surfaces traced from the aerial (data/mcg/sat.png, reference only; no photo pixels are used):
the Jolimont/Richmond rail yard ballast, Melbourne Park courts with line markings, Garden Square,
the round garden, lawns and plazas. Every surface is a hand-made procedural texture."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SS = 2  # mask supersampling

# ---- traced shapes (scene metres: x east, y north) -------------------------------------------
CORRIDOR = [(-720, 380), (-629, 365), (-569, 312), (-529, 262), (-474, 222), (-414, 168), (-300, 108),
            (-251, 54), (-155, -5), (-100, -75), (-3, -140), (146, -214), (300, -288), (397, -314),
            (500, -346), (720, -390), (720, -505), (597, -467), (400, -445), (390, -383), (240, -352),
            (130, -323), (-30, -290), (-100, -240), (-183, -125), (-274, -61), (-366, 12), (-451, 78),
            (-583, 162), (-640, 190), (-720, 210)]
# Melbourne Park plazas (grey paving), traced around Rod Laver, Kia Arena and Garden Square
PLAZA = [(-503, -15), (-347, -15), (-300, -50), (-247, -93), (-192, -147), (-192, -257), (-247, -303),
         (-260, -340), (-384, -340), (-448, -257), (-503, -211), (-567, -129)]
# outdoor courts: (cx, cy, angle deg, colour key); hard courts carry full line markings
COURTS = [(-187.5, -219.5, 0, 'blue'),
          # eastern Melbourne Park courts south of the rail (aerial x -6..97, y -364..-413)
          (1, -388, 0, 'blue'), (15, -388, 0, 'blue'), (29, -388, 0, 'blue'), (43, -388, 0, 'blue'),
          (70, -388, 0, 'blue'), (87, -388, 0, 'blue'),
          (133, -417, 0, 'dark'), (148, -417, 0, 'dark'), (163, -417, 0, 'dark'), (178, -417, 0, 'dark'),
          (193, -417, 0, 'dark'),
          (207, -425, 0, 'clay'), (221, -425, 0, 'clay'), (235, -425, 0, 'clay'), (249, -425, 0, 'clay'),
          (263, -425, 0, 'clay')]
# covered courts in the NW (blue and white roofs seen from above): (x0, y0, x1, y1, colour)
COVERS = [(-625, 116, -601, 154, 'blue'), (-596, 111, -571, 149, 'blue'), (-571, 68, -548, 106, 'blue'),
          (-541, 57, -517, 96, 'blue'), (-511, 51, -486, 89, 'blue'), (-609, 24, -583, 64, 'blue'),
          (-579, 23, -554, 63, 'blue'), (-548, 13, -524, 51, 'blue'),
          (-634, 135, -622, 154, 'white'), (-603, 119, -593, 149, 'white'), (-618, 91, -605, 111, 'white'),
          (-550, 64, -538, 94, 'white'), (-520, 63, -508, 86, 'white'), (-557, 21, -544, 50, 'white')]
LAWNS = [('circle', (-311, -301, 57)), ('circle', (-411, -54, 27)),
         ('rect', (-359, -262, -325, -230)), ('rect', (-313, -257, -302, -230)),
         ('rect', (-256, -298, -219, -262)), ('rect', (-384, -303, -366, -280))]
PATH_RINGS = [(-311, -301, 57, 3.0), (-411, -54, 27, 2.0), (-411, -54, 12, 1.6)]
CARPARK = [(-485, -15, -347, 49)]

COL = dict(ballast=(108, 88, 80), plaza=(150, 146, 140), path=(178, 172, 160), lawn=(78, 118, 52),
           blue=(44, 104, 168), blue_out=(30, 74, 132), dark=(48, 66, 62), dark_out=(36, 50, 48),
           clay=(184, 98, 60), clay_out=(170, 88, 54), white=(226, 228, 230), cover_blue=(36, 82, 168),
           asphalt=(70, 72, 74), line=(236, 238, 236))


def noise(h, w, scale_px, seed, octaves=4):
    """value noise in [-1,1], hand-made grain (no photo)"""
    rng = np.random.default_rng(seed); out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    s = scale_px
    for o in range(octaves):
        gh, gw = max(2, int(h / s) + 2), max(2, int(w / s) + 2)
        g = Image.fromarray((rng.random((gh, gw)) * 255).astype(np.uint8))
        out += amp * (np.asarray(g.resize((w, h), Image.BICUBIC), np.float32) / 127.5 - 1); tot += amp
        amp *= 0.55; s = max(1.0, s / 2.2)
    return out / tot


class Painter:
    def __init__(self, out, NE, box):
        self.out = out; self.S = out.shape[0]; self.m = 2 * NE / self.S; self.NE = NE
        x0, y0, x1, y1 = box
        self.c0 = int((x0 + NE) / self.m); self.r0 = int((NE - y1) / self.m)
        self.c1 = int((x1 + NE) / self.m); self.r1 = int((NE - y0) / self.m)
        self.h = self.r1 - self.r0; self.w = self.c1 - self.c0
        self.reg = out[self.r0:self.r1, self.c0:self.c1].astype(np.float32)

    def px(self, x, y):
        return (((x + self.NE) / self.m - self.c0) * SS, ((self.NE - y) / self.m - self.r0) * SS)

    def mask(self, draw_fn):
        im = Image.new('L', (self.w * SS, self.h * SS), 0); draw_fn(ImageDraw.Draw(im), self.px)
        return np.asarray(im.resize((self.w, self.h), Image.BOX), np.float32) / 255.0

    def fill(self, a, rgb):
        a = a[..., None]; self.reg = self.reg * (1 - a) + np.asarray(rgb, np.float32) * a

    def tex(self, a, rgb, grain, scale_m, seed, streak=None):
        """paint colour rgb modulated by hand-made grain (fraction) at feature size scale_m"""
        n = noise(self.h, self.w, scale_m / self.m, seed)
        if streak is not None:  # fine directional streaks (ballast between tracks)
            yy, xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
            ang = np.deg2rad(streak); d = (xx * np.sin(ang) + yy * np.cos(ang)) * self.m
            n = n * 0.7 + 0.3 * np.sin(d * 2 * np.pi / 1.9)
        fine = noise(self.h, self.w, 0.12 / self.m + 1, seed + 7, 2)
        col = np.asarray(rgb, np.float32)[None, None] * (1 + grain * n + 0.5 * grain * fine)[..., None]
        a = a[..., None]; self.reg = self.reg * (1 - a) + col * a

    def commit(self):
        self.out[self.r0:self.r1, self.c0:self.c1] = np.clip(np.round(self.reg), 0, 255).astype(np.uint8)


def poly(pts):
    return lambda d, P: d.polygon([P(x, y) for x, y in pts], fill=255)


def rect(x0, y0, x1, y1, ang=0, cx=None, cy=None):
    if ang == 0:
        return poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    c, s = np.cos(np.deg2rad(ang)), np.sin(np.deg2rad(ang))
    pts = [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c)
           for x, y in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]
    return poly(pts)


def circ(cx, cy, r):
    def f(d, P):
        a, b = P(cx - r, cy + r); c, e = P(cx + r, cy - r); d.ellipse([a, b, c, e], fill=255)
    return f


def court_lines(cx, cy):
    """ITF doubles court 23.77 x 10.97 m, long axis north-south; lines 5 cm (drawn 0.12 m to survive 0.37 m/px)"""
    L, W, Sg, Sv, t = 23.77 / 2, 10.97 / 2, 8.23 / 2, 6.40, 0.12
    segs = [(-W, -L, W, -L), (-W, L, W, L), (-W, -L, -W, L), (W, -L, W, L), (-Sg, -L, -Sg, L), (Sg, -L, Sg, L),
            (-Sg, -Sv, Sg, -Sv), (-Sg, Sv, Sg, Sv), (0, -Sv, 0, Sv), (0, -L, 0, -L + 0.3), (0, L - 0.3, 0, L)]
    def f(d, P):
        for x0, y0, x1, y1 in segs:
            a = P(cx + x0 - t, cy + y0 - t); b = P(cx + x1 + t, cy + y1 + t)
            d.rectangle([min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])], fill=255)
    return f


def paint(out, NE):
    P = Painter(out, NE, (-720, -520, 720, 400))
    # rail yard: corridor polygon intersected with the aerial's ballast-coloured ground (traced, then smoothed)
    corr = P.mask(poly(CORRIDOR))
    s = Image.open(__file__.replace('hilayer.py', 'data/mcg/sat.png')).convert('RGB')
    sm, sh = 0.5, 700  # sat: 0.5 m/px over +-700 m
    x0, y1 = (P.c0 * P.m - NE), (NE - P.r0 * P.m)
    crop = s.crop((int((x0 + sh) / sm), int((sh - y1) / sm), int((x0 + P.w * P.m + sh) / sm), int((sh - y1 + P.h * P.m) / sm)))
    a = np.asarray(crop.resize((P.w, P.h), Image.BILINEAR), np.int16); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = (r + g + b) / 3
    bal = ((r - b >= -4) & (r - b <= 60) & (lum >= 55) & (lum <= 175) & (g <= r + 4) & (b <= g + 6)).astype(np.uint8) * 255
    del a, r, g, b, lum
    bm = Image.fromarray(bal).filter(ImageFilter.MedianFilter(7)).filter(ImageFilter.MaxFilter(31)).filter(ImageFilter.MinFilter(31))
    bm = bm.filter(ImageFilter.MinFilter(9)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(8))
    bal = (np.asarray(bm, np.float32) / 255.0 > 0.5).astype(np.uint8) * 255   # clean traced outline
    bal = np.asarray(Image.fromarray(bal).filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255.0 * corr
    P.tex(bal, COL['ballast'], 0.16, 0.5, 11)
    print('ballast m2 %.0f' % (bal.sum() * P.m * P.m))
    # Melbourne Park plazas: fine hand-laid grey pavers (0.6 m), no 6 m checker
    pl = P.mask(poly(PLAZA)) * (1 - corr)
    P.tex(pl, COL['plaza'], 0.10, 0.6, 21)
    cp = P.mask(lambda d, F: [rect(*c)(d, F) for c in CARPARK])
    P.tex(cp, COL['asphalt'], 0.08, 1.5, 22)
    for kind, v in LAWNS:
        mk = P.mask(circ(*v) if kind == 'circle' else rect(*v)); P.tex(mk, COL['lawn'], 0.16, 1.2, 31)
    for cx, cy, rr, wd in PATH_RINGS:
        ring = np.clip(P.mask(circ(cx, cy, rr)) - P.mask(circ(cx, cy, rr - wd)), 0, 1); P.tex(ring, COL['path'], 0.06, 0.8, 41)
    for i, (x0, y0, x1, y1, c) in enumerate(COVERS):
        mk = P.mask(rect(x0, y0, x1, y1)); P.tex(mk, COL['cover_blue' if c == 'blue' else 'white'], 0.06, 3.0, 50 + i)
    print('covers', len(COVERS), 'lawns', len(LAWNS))
    P.commit()
