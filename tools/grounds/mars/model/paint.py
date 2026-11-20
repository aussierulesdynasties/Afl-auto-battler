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


# 3D seat plastic (aerial4, drone5): teal-green, a darker moulded rim and a soft sheen down the middle. UV 0-1 per face.
a = base(128, 128, (70, 100, 90), 2, 6)
a[:, :8] *= 0.78; a[:, -8:] *= 0.78; a[:6] *= 0.85; a[-6:] *= 0.7
a[:, 40:88] *= (1 + 0.10 * np.sin(np.linspace(0, math.pi, 48)))[None, :, None]
save('seat_plastic', a, (1, 1))
# embankment grass: mown blades, darker clumps, no stripes (hand-drawn; not pitch turf)
a = base(512, 512, (88, 122, 58), 10, 18) + noise(512, 512, 24, 16)[:, :, None]
for _ in range(900):
    x, y = R.integers(0, 510), R.integers(0, 506); a[y:y + 6, x:x + 1] *= R.uniform(0.75, 1.2)
save('grass_bank', a, (3.0, 3.0))
# Mars seat colours (press/aus_new.jpg): royal blue, grey-blue, cream (new upper tiers), white (old stands); same moulding
for nm, col in (('seat_blue', (38, 74, 150)), ('seat_greyblue', (112, 122, 142)), ('seat_cream', (206, 196, 172)), ('seat_white', (214, 218, 222)), ('seat_navyblue', (40, 60, 128)), ('seat_charcoal', (36, 42, 58)), ('seat_slategrey', (92, 100, 114))):
    a = base(128, 128, col, 2, 6); a[:, :8] *= 0.8; a[:, -8:] *= 0.8; a[:6] *= 0.86; a[-6:] *= 0.72
    a[:, 40:88] *= (1 + 0.08 * np.sin(np.linspace(0, math.pi, 48)))[None, :, None]; save(nm, a, (1, 1))
# concrete treads and risers under the seats: plain grey, a dark nosing line, scuffing
a = base(512, 512, (138, 138, 134), 5, 14); a[:10] *= 0.7; weather(a, 0.06, 10, 20, top_dark=False); save('conc_tread', a, (2.0, 0.8))

# ---- concrete: precast panels 3.0 x 1.5 m with joints, rain streaks, blotches ----
def concrete(name, col, pu=3.0, pv=1.5, tile=(6.0, 6.0)):
    h = w = N; a = base(h, w, col, 5, 20); xu = N / tile[0]; yv = N / tile[1]
    for k in range(int(tile[0] / pu)): a[:, int(k * pu * xu):int(k * pu * xu) + 4] *= 0.66
    for k in range(int(tile[1] / pv)): a[int(k * pv * yv):int(k * pv * yv) + 4] *= 0.66
    weather(a, 0.12, 16, 70); save(name, a, tile)


concrete('conc_wall', (176, 172, 164))
concrete('tri_void', (150, 158, 166), pu=6.0, pv=6.0, tile=(6.0, 6.0))  # what shows through the open triangles: pale grey concourse behind (photo 3.webp)
concrete('conc_block', (168, 166, 160), pu=0.4, pv=0.2, tile=(4.0, 4.0))  # grey concrete blockwork, 400 x 200 units
# paving: concourse concrete slabs 1.2 m, saw joints, stains
a = base(N, N, (112, 104, 98), 7, 24); p = N / 2.4
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
# old stands' roofs (finished-ground aerial press/gi/ta_aerial.jpg): white deck with a grey translucent sheet 1.4 m wide
# every 6 m along the arc, so the roof reads as white with radial grey stripes
deck('roof_skylit', (214, 216, 216)); _a = np.asarray(Image.open(os.path.join(OUT, 'roof_skylit.png')).convert('RGB'), float).copy()
_w = int(N * 2.2 / 10.0); _a[:, :_w] = _a[:, :_w] * 0.25 + np.array((128, 136, 142)) * 0.75; save('roof_skylit', _a, (10.0, 10.0))  # 2026 aerial: ~10 stripes over the 100 m west arc
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
# glulam timber rafters (press/aus_new.jpg): warm honey-orange, lamination lines every 45 mm along the member, grain streaks
a = base(256, 512, (196, 128, 66), 4, 14); yy = np.arange(256)
a *= (1 - 0.12 * ((yy % 11) < 2))[:, None, None]
for _ in range(60):
    y = R.integers(0, 256); a[y:y + R.integers(1, 3), R.integers(0, 300):] *= R.uniform(0.86, 0.96)
save('timber', a, (2.0, 0.6))

# ---- facades (one tile = 6 m along x 3.6 m = one floor; image row 0 = top) ----
def facade(name, col, draw, tile=(6.0, 3.6), w=1024, h=616, wx=True):
    a = base(h, w, col, 3, 10); pu = w / tile[0]; pv = h / tile[1]; draw(a, pu, pv, h, w)
    if wx: weather(a, 0.12, 12, 40)
    save(name, a, tile)


def _nw(a, pu, pv, h, w):     # NW stand back: grey render with a red-brick pier every 6 m and a dark vent band
    a[:, :int(1.0 * pu)] = np.array((142, 72, 58)) + fine(h, int(1.0 * pu), 6)[:, :, None]
    for k in range(int(3.6 / 0.26)): a[int(k * 0.26 * pv):int(k * 0.26 * pv) + 2, :int(1.0 * pu)] *= 0.8   # brick courses
    a[int(0.5 * pv):int(1.1 * pv), int(1.6 * pu):int(5.4 * pu)] = (78, 84, 90)
    for k in range(4): a[:, int((1.0 + k * 1.25) * pu):int((1.0 + k * 1.25) * pu) + 3] *= 0.8


def _lattice(a, pu, pv, h, w):  # N stand back, one tile = the full 8.9 m wall (aerial4): teal ribbed cladding, a lighter grey
    # band under the roof's rear edge; the white frame and X bracing are modelled (build.bracing), not painted
    a[:] = np.array((74, 107, 116)) + fine(h, w, 4)[:, :, None] + noise(h, w, 8, 10)[:, :, None]
    for k in range(int(6 / 0.25)): a[:, int(k * 0.25 * pu):int(k * 0.25 * pu) + 3] *= 0.86      # sheet ribs
    a[:int(1.6 * pv)] = np.array((168, 176, 178)) + fine(int(1.6 * pv), w, 3)[:, :, None]
    a[int(1.6 * pv):int(1.6 * pv) + 6] *= 0.6


def _es(a, pu, pv, h, w):     # east-south back: pale grey sheet cladding, white columns every 8.3 m (one per tile edge), dark louvres
    for k in range(int(6 / 0.5)): a[:, int(k * 0.5 * pu):int(k * 0.5 * pu) + 3] *= 0.84
    a[int(0.6 * pv):int(1.3 * pv), int(1.0 * pu):int(5.0 * pu)] = (70, 76, 84)
    for k in range(10): a[int(0.6 * pv) + int(k * 0.07 * pv):int(0.6 * pv) + int(k * 0.07 * pv) + 3, int(1.0 * pu):int(5.0 * pu)] = (120, 126, 132)


def _tri(a, pu, pv, h, w):     # Mars west/east backs (PTA 2017 photos): white folded triangle panels, ~1.5 x 1.2 m, dark open voids in some
    from PIL import ImageDraw
    im = Image.new('L', (w, h), 0); d = ImageDraw.Draw(im); sx, sy = 3.0 * pu, 2.6 * pv; rr = np.random.default_rng(5)
    for j in range(int(h / sy) + 1):
        for i in range(-1, int(w / sx) + 2):
            x0 = i * sx + (sx / 2 if j % 2 else 0); y0 = j * sy
            for tri, sh in (([(x0, y0), (x0 + sx, y0), (x0 + sx / 2, y0 + sy)], 0), ([(x0 + sx / 2, y0 + sy), (x0 + sx * 1.5, y0 + sy), (x0 + sx, y0)], 1)):
                v = 60 if rr.random() < 0.12 else int(rr.choice((240, 222, 200)))
                d.polygon(tri, fill=v, outline=110)
    L = np.asarray(im, float)
    a[:] = np.where(L[:, :, None] < 80, np.array((52, 56, 62)), L[:, :, None] * np.array((1.0, 1.0, 1.0)) * 0.97) + fine(h, w, 3)[:, :, None]


def _brick(a, pu, pv, h, w):   # new 2026 stand backs: red-brown brick, 0.23 x 0.086 m courses, a darker patterned header band every 1.2 m
    ch, cw = 0.086 * pv, 0.23 * pu; rr = np.random.default_rng(7); a[:] = (182, 176, 166)
    for j in range(int(h / ch) + 1):
        y0 = int(j * ch); off = cw / 2 if j % 2 else 0
        for i in range(-1, int(w / cw) + 2):
            x0 = int(i * cw + off); c = np.array((150, 74, 52)) * rr.uniform(0.85, 1.12)
            if (j // 3) % 14 == 0 and (i + j) % 2: c = np.array((92, 52, 40))
            a[y0:y0 + int(ch) - 2, max(0, x0):max(0, x0 + int(cw) - 2)] = c
        a[y0 + int(ch) - 2:y0 + int(ch)] = (182, 176, 166)


def _gunns(a, pu, pv, h, w):  # Gunns back: blue-grey panels 1.5 x 1.2 m, a window strip, maroon base band
    for k in range(4): a[:, int(k * 1.5 * pu):int(k * 1.5 * pu) + 4] *= 0.78
    for k in range(3): a[int(k * 1.2 * pv):int(k * 1.2 * pv) + 4] *= 0.78
    a[int(1.4 * pv):int(2.2 * pv), int(0.4 * pu):int(5.6 * pu)] = (52, 60, 72)
    for k in range(4): a[int(1.4 * pv):int(2.2 * pv), int((0.4 + k * 1.3) * pu):int((0.4 + k * 1.3) * pu) + 4] = (190, 196, 200)


def _cw(a, pu, pv, h, w):     # old Centre West, one tile = the full 12 m (row 0 = top): white fascia, light panel band
    # (the sign band), a tall dark glazed function level with a mullion every 1.5 m, light grey wall below with a window band
    a[:int(0.5 * pv)] = (232, 232, 228)
    b0, b1 = int(0.5 * pv), int(3.0 * pv); a[b0:b1] = np.array((206, 208, 206)) + fine(b1 - b0, w, 3)[:, :, None]
    g0, g1 = int(3.0 * pv), int(7.0 * pv)
    a[g0:g1] = np.array((40, 48, 56)) + fine(g1 - g0, w, 3)[:, :, None] + noise(g1 - g0, w, 6, 16)[:, :, None]
    for k in range(4): a[g0:g1, int(k * 1.5 * pu):int(k * 1.5 * pu) + 7] = (190, 194, 196)
    a[g1:g1 + 8] = (170, 172, 170)
    a[g1:] = np.array((188, 190, 188)) + fine(h - g1, w, 3)[:, :, None]
    a[int(8.4 * pv):int(9.4 * pv), :] = (58, 66, 74)
    for k in range(4): a[int(8.4 * pv):int(9.4 * pv), int(k * 1.5 * pu):int(k * 1.5 * pu) + 6] = (188, 190, 188)


def _boxes(a, pu, pv, h, w):  # Gunns box level: tinted glass with mullions every 1.5 m and a white sill
    a[:] = np.array((28, 36, 44)) + fine(h, w, 3)[:, :, None] + noise(h, w, 6, 18)[:, :, None]
    for k in range(4): a[:, int(k * 1.5 * pu):int(k * 1.5 * pu) + 6] = (196, 200, 202)
    a[int(2.9 * pv):] = (214, 216, 214); a[:int(0.3 * pv)] = (214, 216, 214)


facade('facade_nw', (176, 178, 176), _nw); facade('facade_lattice', (74, 107, 116), _lattice, (6.0, 8.9), 1024, 1520)
facade('facade_es', (196, 198, 198), _es); facade('facade_tri', (230, 230, 228), _tri, (6.0, 12.0), 1024, 2048, False); facade('facade_brick', (150, 74, 52), _brick); facade('facade_gunns', (110, 132, 146), _gunns)
facade('facade_cw', (226, 226, 222), _cw, (6.0, 12.0), 1024, 2048); facade('boxes_glass', (42, 52, 60), _boxes)
a = base(512, 512, (46, 56, 66), 2, 18); a[:, 250:258] = (180, 184, 186); a[250:258] = (180, 184, 186); save('glass', a, (3.0, 3.0))
# light tower head: 4 x 8 lamps in a white frame
a = np.ones((N, N, 3)) * np.array((230, 230, 226), float); cu, cv = N / 8, N / 4
for i in range(8):
    for j in range(4):
        x0, y0 = int(i * cu + 8), int(j * cv + 10); x1, y1 = int((i + 1) * cu - 8), int((j + 1) * cv - 10)
        a[y0:y1, x0:x1] = (170, 176, 180); a[y0 + 8:y1 - 8, x0 + 8:x1 - 8] = (86, 92, 98)
save('lamps', a, (1, 1))

# NE gap (scoreboard corner): pavilion render with a dark window band, blue rear panels of the roof seat banks, screen switched off
def _pav(a, pu, pv, h, w):     # white render, dark glazed band 1.0-2.6 m with a mullion every 1.5 m, grey plinth
    a[int(1.0 * pv):int(2.6 * pv)] = np.array((52, 60, 68)) + fine(int(2.6 * pv) - int(1.0 * pv), w, 3)[:, :, None]
    for k in range(4): a[int(1.0 * pv):int(2.6 * pv), int(k * 1.5 * pu):int(k * 1.5 * pu) + 6] = (200, 202, 200)
    a[int(3.3 * pv):] = (150, 152, 150)


def _panel(a, pu, pv, h, w):   # blue sheet panels, a light joint every 1.5 m and a white capping strip
    a[:] = np.array((54, 84, 96)) + fine(h, w, 4)[:, :, None] + noise(h, w, 8, 14)[:, :, None]
    for k in range(4): a[:, int(k * 1.5 * pu):int(k * 1.5 * pu) + 4] = (150, 170, 196)
    a[:int(0.25 * pv)] = (220, 222, 220)


def _sw(a, pu, pv, h, w):      # SW corner building, one tile = full 9 m height: white render, a window per 3 m bay on three floors (row 0 = top)
    for fl in (1.3, 4.1, 6.9):
        for k in range(2): a[int(fl * pv):int((fl + 0.9) * pv), int((0.9 + k * 3) * pu):int((2.1 + k * 3) * pu)] = (54, 62, 70)
    a[:int(0.4 * pv)] = (226, 226, 222)


facade('facade_sw', (218, 218, 214), _sw, (6.0, 9.0), 1024, 1536); facade('facade_pav', (214, 214, 208), _pav); facade('panel_blue', (54, 84, 96), _panel)
a = base(512, 512, (24, 26, 30), 4, 14)
for k in range(0, 512, 16): a[:, k:k + 2] *= 0.6; a[k:k + 2] *= 0.6        # LED module joints
a[:10] = (60, 62, 66); a[-10:] = (60, 62, 66); a[:, :10] = (60, 62, 66); a[:, -10:] = (60, 62, 66)
save('screen_off', a, (2.0, 2.0))
# scoreboard frames and backs (GE 2026 l225/l270 for the NE board, grandstand photo and GE l000/l180 for the SW board)
a = base(512, 512, (76, 108, 140), 3, 8); a[:, 250:254] *= 0.8; a[250:254] *= 0.8; weather(a, 0.08, 8, 12); save('board_frame', a, (2.0, 2.0))
a = base(512, 512, (60, 62, 66), 3, 10)
for k in range(0, 512, 128): a[:, k:k + 3] *= 0.7; a[k:k + 3] *= 0.7
save('board_back', a, (2.0, 2.0))
a = base(256, 256, (40, 46, 54), 3, 8); save('board_side', a, (2.0, 2.0))
# NE board back, one tile = the whole 11.6 x 7.9 m panel inside the white rim (GE 2026 l225): dark panel, club artwork
# hand-drawn: left half a mauve block logo over two white text lines and a white script line, right half a big maroon
# emblem outlined in white
from PIL import ImageDraw as _D
a = base(700, 1024, (34, 36, 46), 2, 6); im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = _D.Draw(im)
mv, wt, mr = (196, 150, 186), (226, 226, 232), (128, 36, 72)
pk = (214, 168, 196)
d.rounded_rectangle([60, 70, 420, 240], 20, fill=mv)                         # mauve block wordmark, dark letter cuts
for x, y0, y1 in ((110, 105, 205), (150, 70, 150), (205, 120, 240), (255, 70, 170), (300, 140, 240), (350, 95, 195)):
    d.rectangle([x, y0, x + 16, y1], fill=(34, 36, 46))
for y in (300, 352):                                                          # two text lines
    for x in range(70, 400, 24): d.rectangle([x, y, x + 16, y + 28], fill=wt)
d.line([(70, 452), (140, 440), (220, 456), (300, 438), (400, 450)], fill=wt, width=9)    # script line
E = [(0.30, 0.02), (0.62, 0.00), (0.86, 0.10), (0.98, 0.32), (0.90, 0.52), (0.98, 0.74), (0.80, 0.96), (0.52, 1.00),
     (0.40, 0.88), (0.56, 0.80), (0.70, 0.66), (0.50, 0.58), (0.20, 0.70), (0.04, 0.56), (0.12, 0.34), (0.02, 0.16)]
q = lambda u, v: (600 + u * 330, 70 + v * 560)
d.polygon([q(u, v) for u, v in E], fill=mr, outline=pk, width=14)           # emblem: maroon body, pale pink outline
d.line([q(0.22, 0.20), q(0.46, 0.12), q(0.72, 0.22), q(0.80, 0.40)], fill=pk, width=16)     # curling strokes
d.line([q(0.18, 0.44), q(0.42, 0.40), q(0.62, 0.48)], fill=wt, width=12)
d.line([q(0.60, 0.86), q(0.76, 0.78), q(0.86, 0.62)], fill=pk, width=12)
save('board_back_ne', np.asarray(im).astype(float), (11.6, 7.9))
a = base(256, 256, (112, 42, 46), 5, 14); weather(a, 0.12, 12, 10); save('steel_maroon', a, (2.0, 2.0))

# Name sign on the old Centre West front (photo ref/UTAS-Stadium-grandstand.jpg): light panel, red crest, two-line serif name.
# Lettering is drawn here with the system Georgia face; the crest is a hand-drawn rampant lion in the photo's red.
from PIL import ImageDraw, ImageFont
SW_, SH_ = 2048, 512
im = Image.fromarray(np.clip(base(SH_, SW_, (226, 228, 224), 3, 8), 0, 255).astype(np.uint8)); dr = ImageDraw.Draw(im)
dr.rectangle([0, 0, SW_ - 1, SH_ - 1], outline=(150, 152, 150), width=10)
red = (196, 30, 40)
red = (170, 34, 40); blk = (30, 26, 28)
lion = [(0.10, 0.16), (0.18, 0.08), (0.30, 0.02), (0.46, 0.06), (0.52, 0.16), (0.50, 0.28), (0.58, 0.40), (0.62, 0.55), (0.70, 0.62),
        (0.88, 0.48), (0.96, 0.30), (1.00, 0.22), (0.92, 0.26), (0.86, 0.44), (0.74, 0.66), (0.70, 0.78), (0.66, 0.98), (0.48, 0.98),
        (0.54, 0.90), (0.52, 0.80), (0.40, 0.86), (0.22, 0.84), (0.30, 0.76), (0.40, 0.70), (0.36, 0.58), (0.30, 0.46), (0.16, 0.50),
        (0.04, 0.58), (0.06, 0.50), (0.18, 0.40), (0.10, 0.36), (0.00, 0.30), (0.04, 0.24), (0.18, 0.30), (0.22, 0.26), (0.12, 0.24),
        (0.08, 0.20)]
cx0, cy0, ch = 110, 50, 410; cw = 0.62 * ch
L_ = lambda u, v: (cx0 + u * cw, cy0 + v * ch)
dr.polygon([L_(u, v) for u, v in lion], fill=red, outline=blk, width=7)
for k in range(5):   # mane
    dr.line([L_(0.26 + 0.05 * k, 0.07 + 0.02 * k), L_(0.20 + 0.06 * k, 0.24 + 0.02 * k)], fill=blk, width=7)
dr.ellipse([L_(0.17, 0.12), L_(0.22, 0.15)], fill=blk)                                       # eye
for (u0, v0, u1, v1) in ((0.02, 0.29, 0.10, 0.31), (0.05, 0.55, 0.12, 0.53), (0.50, 0.97, 0.62, 0.97), (0.24, 0.83, 0.34, 0.82)):
    dr.line([L_(u0, v0), L_(u1, v1)], fill=blk, width=6)                                      # claws
dr.line([L_(0.40, 0.50), L_(0.52, 0.66)], fill=blk, width=6); dr.line([L_(0.58, 0.60), L_(0.56, 0.82)], fill=blk, width=6)   # haunch, leg
F1 = ImageFont.truetype('C:/Windows/Fonts/georgia.ttf', 150); F2 = ImageFont.truetype('C:/Windows/Fonts/georgia.ttf', 96)
def spaced(y, txt, f, x=560, sp=14):
    for ch in txt:
        dr.text((x, y), ch, font=f, fill=(66, 66, 72)); x += dr.textlength(ch, font=f) + sp
    return x
x = spaced(70, 'UNIVERSITY', F1, 440); spaced(118, 'of', F2, x + 30, 4)
spaced(270, 'TASMANIA', F1, 440, 40)
a = np.asarray(im, float) + noise(SH_, SW_, 10, 6)[:, :, None]; save('sign_utas', a, (7.0, 1.75))

json.dump(TILE, open(OUT + 'tiles.json', 'w', newline=''), indent=0)
for nm in sorted(TILE):
    g = np.asarray(Image.open(OUT + nm + '.png').convert('L'), float); print(f'{nm:16s} grey sd {g.std():5.1f}')
