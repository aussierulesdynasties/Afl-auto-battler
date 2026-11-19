# Hand-made textures for York Park (2024-25), painted in code: no photo pixels. TILE[name] = metres covered by one tile (u, v).
# Colours are read off the reference photos (drone5, grandstand, aerial4) and the Google Earth views of the unchanged stands;
# every pattern (seat rows, ribs, joints, streaks, blotches) is drawn here.
import numpy as np, json, math, os
from PIL import Image, ImageFilter
R = np.random.default_rng(23); N = 1024
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex') + '/'; os.makedirs(OUT, exist_ok=True); TILE = {}


def save(name, a, tile):
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(OUT + name + '.png'); TILE[name] = tile


def noise(h, w, sc, amp):
    """tileable smooth noise: random grid, wrapped, bicubic upscale"""
    g = R.normal(0, 1, (sc, sc)); g = np.tile(g, (3, 3))
    im = Image.fromarray(((g - g.min()) / np.ptp(g) * 255).astype(np.uint8)).resize((3 * w, 3 * h), Image.BICUBIC)
    a = np.asarray(im, float)[h:2 * h, w:2 * w] / 255 - 0.5; return a * amp


def fine(h, w, amp): return R.normal(0, amp, (h, w))


def base(h, w, col, f=3, s=10):
    return np.ones((h, w, 3)) * np.array(col, float) + fine(h, w, f)[:, :, None] + noise(h, w, 16, s)[:, :, None]


def weather(a, streaks=0.10, blotch=14, n=60, top_dark=True):
    """rain streaks running down from the top edge (image row 0 = top) and soft blotching"""
    h, w, _ = a.shape
    a += noise(h, w, 9, blotch)[:, :, None]
    for _ in range(n):
        x = R.integers(0, w); L = R.uniform(0.15, 0.9) * h; wd = R.integers(2, 9); d = R.uniform(0.3, 1.0) * streaks
        y0 = R.integers(0, max(1, h // 6)) if top_dark else R.integers(0, h)
        ys = np.arange(int(y0), min(h, int(y0 + L)))
        fall = 1 - (ys - y0) / L
        for xx in range(x, min(w, x + wd)):
            a[ys, xx] *= (1 - d * fall)[:, None]
    return a


# ---- seats: one tile = 12 m along the tier x 3.2 m up the rake (4 rows of 0.8 m), aisle stair at u 0-1.1 ----
def seats(name, col, tread=(112, 114, 116), aisle=(140, 140, 138)):
    W, Hh = 2048, 1024; pu = W / 12.0; pv = Hh / 3.2; c0 = np.array(col, float)
    a = base(Hh, W, tread, 3, 8)
    Y = lambda v: Hh - int(round(v * pv))
    for r in range(4):
        v0 = r * 0.8
        for k in range(20):
            u0 = 1.1 + k * 0.54; c = c0 * (1 + R.normal(0, 0.04)); x0, x1 = int((u0 + 0.04) * pu), int((u0 + 0.50) * pu)
            a[Y(v0 + 0.40):Y(v0 + 0.14), x0:x1] = c * 1.08          # seat pan (lit)
            a[Y(v0 + 0.74):Y(v0 + 0.42), x0:x1] = c * 0.9           # backrest
            a[Y(v0 + 0.43):Y(v0 + 0.40), x0:x1] = c * 0.55          # crease
            a[Y(v0 + 0.14):Y(v0 + 0.08), x0:x1] = np.array(tread) * 0.55   # shadow under the pan
        a[Y(v0 + 0.80):Y(v0 + 0.76), int(1.1 * pu):] = np.array(tread) * 0.5   # riser shadow
    a[:, :int(1.1 * pu)] = np.array(aisle, float) + fine(Hh, int(1.1 * pu), 3)[:, :, None]
    for k in range(8): a[Y(k * 0.4 + 0.05):Y(k * 0.4), :int(1.1 * pu)] *= 0.7
    a[:, int(0.53 * pu):int(0.57 * pu)] = (214, 216, 214)              # handrail
    a += noise(Hh, W, 12, 10)[:, :, None]
    save(name, a, (12.0, 3.2))


seats('seats_green', (34, 88, 84))           # dark teal-green plastic seats (drone5, aerial4)

# ---- concrete: precast panels 3.0 x 1.5 m with joints, rain streaks, blotches ----
def concrete(name, col, pu=3.0, pv=1.5, tile=(6.0, 6.0)):
    h = w = N; a = base(h, w, col, 5, 20); xu = N / tile[0]; yv = N / tile[1]
    for k in range(int(tile[0] / pu)): a[:, int(k * pu * xu):int(k * pu * xu) + 4] *= 0.66
    for k in range(int(tile[1] / pv)): a[int(k * pv * yv):int(k * pv * yv) + 4] *= 0.66
    weather(a, 0.12, 16, 70); save(name, a, tile)


concrete('conc_wall', (176, 172, 164))
# paving: concourse concrete slabs 1.2 m, saw joints, stains
a = base(N, N, (178, 176, 170), 7, 24); p = N / 2.4
for k in range(2): a[int(k * 1.2 * p):int(k * 1.2 * p) + 3] *= 0.7; a[:, int(k * 1.2 * p):int(k * 1.2 * p) + 3] *= 0.7
for _ in range(25):
    cx, cy, rr = R.integers(0, N), R.integers(0, N), R.integers(10, 60); yy, xx = np.ogrid[:N, :N]
    a[((yy - cy) ** 2 + (xx - cx) ** 2) < rr * rr] *= R.uniform(0.85, 0.95)
save('paving', a, (2.4, 2.4))

# ---- fence: white-painted boundary pickets/panel with a dark capping rail and kick board (tile 2 m x 1.1 m) ----
a = base(512, 1024, (226, 228, 224), 3, 8); px = 1024 / 2.0
for k in range(20): a[:, int(k * 0.1 * px):int(k * 0.1 * px) + 6] *= 0.8   # picket gaps every 0.1 m
a[:46] = (54, 70, 66); a[460:] = (110, 110, 106); weather(a, 0.08, 10, 30); save('fence', a, (2.0, 1.1))

# ---- roof sheeting: ribbed deck, ribs every 0.3 m across (u along the arc), sheet laps every 6 m down v, grime ----
def deck(name, col, pitch=0.3, tile=(6.0, 6.0), grime=18):
    h = w = N; x = np.arange(w) / w * (tile[0] / pitch)
    rib = np.where((x % 1) < 0.16, 0.74, 1.0) + 0.05 * np.cos(2 * math.pi * x)
    a = np.ones((h, w, 3)) * np.array(col, float) * rib[None, :, None] + fine(h, w, 2)[:, :, None] + noise(h, w, 10, grime)[:, :, None]
    a[0:5] *= 0.72                                    # sheet lap
    for _ in range(40):                                # dirt runs along the ribs (downslope)
        xx = R.integers(0, w); L = R.integers(h // 4, h); d = R.uniform(0.05, 0.14); a[:L, xx:xx + R.integers(3, 10)] *= 1 - d
    save(name, a, tile)


deck('roof_white', (214, 216, 216)); deck('roof_grey', (170, 174, 176)); deck('roof_soffit', (190, 194, 198), grime=14)
deck('roof_flat', (150, 152, 152), pitch=0.6, grime=22)
# solar panels: 1.0 x 1.7 m modules, dark blue cells, silver frames, row gaps
a = np.ones((N, N, 3)) * np.array((38, 48, 72), float); mu, mv = N / 4.0, N / (1.7 * 2 / 1.7 * 1.7 * 2 / 1.7) / 1.0
mv = N / 3.4
for i in range(4): a[:, int(i * mu):int(i * mu) + 8] = (170, 176, 182)
for j in range(2): a[int(j * 1.7 * mv):int(j * 1.7 * mv) + 10] = (170, 176, 182)
for i in range(24): a[:, int(i * mu / 6):int(i * mu / 6) + 2] *= 0.8      # cell lines
for j in range(20): a[int(j * 1.7 * mv / 10):int(j * 1.7 * mv / 10) + 2] *= 0.8
a += noise(N, N, 8, 14)[:, :, None] + fine(N, N, 2)[:, :, None]; save('solar', a, (4.0, 3.4))
# fascia: white metal cladding with joints every 2 m, streaks
a = base(512, 1024, (226, 228, 226), 4, 18); xu = 1024 / 4.0
for k in range(2): a[:, int(k * 2 * xu):int(k * 2 * xu) + 6] *= 0.66
a[480:] *= 0.8
weather(a, 0.16, 16, 40); save('fascia', a, (4.0, 2.0))

# ---- steel: painted members with seams and wear ----
for nm, col in (('steel_white', (230, 232, 230)), ('steel_galv', (150, 154, 158)), ('paint_white', (232, 232, 228))):
    a = base(256, 256, col, 6, 26); a[:, 120:126] *= 0.7; a[:, 0:4] *= 0.75; weather(a, 0.16, 18, 16); save(nm, a, (2.0, 2.0))

# ---- facades (one tile = 6 m along x 3.6 m = one floor; image row 0 = top) ----
def facade(name, col, draw, tile=(6.0, 3.6), w=1024, h=616):
    a = base(h, w, col, 3, 10); pu = w / tile[0]; pv = h / tile[1]; draw(a, pu, pv, h, w); weather(a, 0.12, 12, 40); save(name, a, tile)


def _nw(a, pu, pv, h, w):     # NW stand back: grey render with a red-brick pier every 6 m and a dark vent band
    a[:, :int(1.0 * pu)] = np.array((142, 72, 58)) + fine(h, int(1.0 * pu), 6)[:, :, None]
    for k in range(int(3.6 / 0.26)): a[int(k * 0.26 * pv):int(k * 0.26 * pv) + 2, :int(1.0 * pu)] *= 0.8   # brick courses
    a[int(0.5 * pv):int(1.1 * pv), int(1.6 * pu):int(5.4 * pu)] = (78, 84, 90)
    for k in range(4): a[:, int((1.0 + k * 1.25) * pu):int((1.0 + k * 1.25) * pu) + 3] *= 0.8


def _lattice(a, pu, pv, h, w):  # N stand back: white X bracing over dark blue sheet, column every 6 m
    a[:] = np.array((46, 62, 98)) + fine(h, w, 4)[:, :, None]
    for k in range(int(3.6 / 0.4)): a[int(k * 0.4 * pv):int(k * 0.4 * pv) + 2] *= 0.8
    yy, xx = np.mgrid[0:h, 0:w]; u = xx / pu; v = yy / pv
    for d in (np.abs(u / 6 * 3.6 - v), np.abs((6 - u) / 6 * 3.6 - v)): a[d < 0.09] = (232, 234, 232)
    a[:, :int(0.3 * pu)] = (232, 234, 232); a[:int(0.2 * pv)] = (232, 234, 232)


def _es(a, pu, pv, h, w):     # east-south back: pale grey sheet cladding, white columns every 8.3 m (one per tile edge), dark louvres
    for k in range(int(6 / 0.5)): a[:, int(k * 0.5 * pu):int(k * 0.5 * pu) + 3] *= 0.84
    a[:, :int(0.35 * pu)] = (234, 234, 232)
    a[int(0.6 * pv):int(1.3 * pv), int(1.0 * pu):int(5.0 * pu)] = (70, 76, 84)
    for k in range(10): a[int(0.6 * pv) + int(k * 0.07 * pv):int(0.6 * pv) + int(k * 0.07 * pv) + 3, int(1.0 * pu):int(5.0 * pu)] = (120, 126, 132)


def _gunns(a, pu, pv, h, w):  # Gunns back: blue-grey panels 1.5 x 1.2 m, a window strip, maroon base band
    for k in range(4): a[:, int(k * 1.5 * pu):int(k * 1.5 * pu) + 4] *= 0.78
    for k in range(3): a[int(k * 1.2 * pv):int(k * 1.2 * pv) + 4] *= 0.78
    a[int(1.4 * pv):int(2.2 * pv), int(0.4 * pu):int(5.6 * pu)] = (52, 60, 72)
    for k in range(4): a[int(1.4 * pv):int(2.2 * pv), int((0.4 + k * 1.3) * pu):int((0.4 + k * 1.3) * pu) + 4] = (190, 196, 200)


def _cw(a, pu, pv, h, w):     # Centre West function building: white render, a full-width dark window band per floor, joints
    a[int(0.7 * pv):int(2.3 * pv)] = np.array((48, 58, 66)) + fine(int(2.3 * pv) - int(0.7 * pv), w, 3)[:, :, None]
    for k in range(5): a[int(0.7 * pv):int(2.3 * pv), int(k * 1.5 * pu):int(k * 1.5 * pu) + 6] = (208, 210, 208)
    a[int(0.7 * pv):int(0.7 * pv) + 6] *= 0.6


def _boxes(a, pu, pv, h, w):  # Gunns box level: tinted glass with mullions every 1.5 m and a white sill
    a[:] = np.array((42, 52, 60)) + fine(h, w, 3)[:, :, None] + noise(h, w, 6, 18)[:, :, None]
    for k in range(4): a[:, int(k * 1.5 * pu):int(k * 1.5 * pu) + 6] = (196, 200, 202)
    a[int(2.9 * pv):] = (214, 216, 214); a[:int(0.3 * pv)] = (214, 216, 214)


facade('facade_nw', (176, 178, 176), _nw); facade('facade_lattice', (46, 62, 98), _lattice)
facade('facade_es', (196, 198, 198), _es); facade('facade_gunns', (150, 164, 184), _gunns)
facade('facade_cw', (226, 226, 222), _cw); facade('boxes_glass', (42, 52, 60), _boxes)
a = base(512, 512, (46, 56, 66), 2, 18); a[:, 250:258] = (180, 184, 186); a[250:258] = (180, 184, 186); save('glass', a, (3.0, 3.0))
# light tower head: 4 x 8 lamps in a white frame
a = np.ones((N, N, 3)) * np.array((230, 230, 226), float); cu, cv = N / 8, N / 4
for i in range(8):
    for j in range(4):
        x0, y0 = int(i * cu + 8), int(j * cv + 10); x1, y1 = int((i + 1) * cu - 8), int((j + 1) * cv - 10)
        a[y0:y1, x0:x1] = (170, 176, 180); a[y0 + 8:y1 - 8, x0 + 8:x1 - 8] = (86, 92, 98)
save('lamps', a, (1, 1))

json.dump(TILE, open(OUT + 'tiles.json', 'w', newline=''), indent=0)
for nm in sorted(TILE):
    g = np.asarray(Image.open(OUT + nm + '.png').convert('L'), float); print(f'{nm:16s} grey sd {g.std():5.1f}')
