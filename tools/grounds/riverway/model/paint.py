# Hand-made textures for Riverway Stadium (Townsville), painted in code: no photo pixels. TILE[name] = metres covered by one tile (u, v).
# Colours are read off the reference photos (ref/symonds-grandstand-riverway.jpg, ref/riverway-stadium.jpg) and the Google Earth 2024 views;
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
for nm, col in (('seat_plastic', (62, 150, 118)), ('seat_green', (70, 160, 104)), ('seat_teal', (48, 146, 140)), ('seat_blue', (58, 112, 176))):
    a = base(128, 128, col, 2, 6)   # Riverway shells: green, teal and blue (symonds-grandstand photo), moulded rim, sheen
    a[:, :8] *= 0.78; a[:, -8:] *= 0.78; a[:6] *= 0.85; a[-6:] *= 0.7
    a[:, 40:88] *= (1 + 0.10 * np.sin(np.linspace(0, math.pi, 48)))[None, :, None]
    save(nm, a, (1, 1))
# concrete treads and risers under the seats: plain grey, a dark nosing line, scuffing
a = base(512, 512, (138, 138, 134), 5, 14); a[:10] *= 0.7; weather(a, 0.06, 10, 20, top_dark=False); save('conc_tread', a, (2.0, 0.8))

# ---- concrete: precast panels 3.0 x 1.5 m with joints, rain streaks, blotches ----
def concrete(name, col, pu=3.0, pv=1.5, tile=(6.0, 6.0)):
    h = w = N; a = base(h, w, col, 5, 20); xu = N / tile[0]; yv = N / tile[1]
    for k in range(int(tile[0] / pu)): a[:, int(k * pu * xu):int(k * pu * xu) + 4] *= 0.66
    for k in range(int(tile[1] / pv)): a[int(k * pv * yv):int(k * pv * yv) + 4] *= 0.66
    weather(a, 0.12, 16, 70); save(name, a, tile)


concrete('conc_wall', (176, 172, 164))
# paving: concourse concrete slabs 1.2 m, saw joints, stains
a = base(N, N, (112, 104, 98), 7, 24); p = N / 2.4
for k in range(2): a[int(k * 1.2 * p):int(k * 1.2 * p) + 3] *= 0.7; a[:, int(k * 1.2 * p):int(k * 1.2 * p) + 3] *= 0.7
for _ in range(25):
    cx, cy, rr = R.integers(0, N), R.integers(0, N), R.integers(10, 60); yy, xx = np.ogrid[:N, :N]
    a[((yy - cy) ** 2 + (xx - cx) ** 2) < rr * rr] *= R.uniform(0.85, 0.95)
save('paving', a, (2.4, 2.4))

# ---- fence: white-painted boundary pickets/panel with a dark capping rail and kick board (tile 2 m x 1.1 m) ----
a = base(512, 1024, (44, 58, 50), 3, 6); px = 1024 / 2.0   # Riverway: dark green boundary fence, posts every 2 m, top rail
a[:40] = (70, 84, 76); a[:, :14] = (70, 84, 76); a[470:] = (96, 96, 92); weather(a, 0.06, 8, 20); save('fence', a, (2.0, 1.1))

# ---- roof sheeting: ribbed deck, ribs every 0.3 m across (u along the arc), sheet laps every 6 m down v, grime ----
def deck(name, col, pitch=0.3, tile=(6.0, 6.0), grime=18):
    h = w = N; x = np.arange(w) / w * (tile[0] / pitch)
    rib = np.where((x % 1) < 0.16, 0.74, 1.0) + 0.05 * np.cos(2 * math.pi * x)
    a = np.ones((h, w, 3)) * np.array(col, float) * rib[None, :, None] + fine(h, w, 2)[:, :, None] + noise(h, w, 10, grime)[:, :, None]
    a[0:5] *= 0.72                                    # sheet lap
    for _ in range(40):                                # dirt runs along the ribs (downslope)
        xx = R.integers(0, w); L = R.integers(h // 4, h); d = R.uniform(0.05, 0.14); a[:L, xx:xx + R.integers(3, 10)] *= 1 - d
    save(name, a, tile)


deck('roof_white', (214, 216, 216)); deck('roof_grey', (170, 174, 176)); deck('roof_soffit', (78, 82, 88), grime=10)
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

# ---- Riverway facades (one tile = 6 m along; image row 0 = top) ----
def facade(name, col, draw, tile=(6.0, 3.6), w=1024, h=616):
    a = base(h, w, col, 3, 10); pu = w / tile[0]; pv = h / tile[1]; draw(a, pu, pv, h, w); weather(a, 0.12, 12, 40); save(name, a, tile)


def _podium(a, pu, pv, h, w):   # cream render podium under the seats, 2.8 m: a joint every 3 m, darker plinth
    for k in range(2): a[:, int(k * 3 * pu):int(k * 3 * pu) + 4] *= 0.8
    a[-int(0.3 * pv):] *= 0.82; a[:int(0.12 * pv)] = (226, 222, 210)


def _glass(a, pu, pv, h, w):    # corporate level behind the seats, one tile 6 x 5 m: cream wall band on top, green-tinted glass
    a[int(1.4 * pv):int(4.4 * pv)] = np.array((44, 64, 60)) + fine(int(4.4 * pv) - int(1.4 * pv), w, 3)[:, :, None]
    for k in range(5): a[int(1.4 * pv):int(4.4 * pv), int(k * 1.2 * pu):int(k * 1.2 * pu) + 8] = (210, 206, 192)   # mullions
    a[int(4.4 * pv):] = (196, 188, 166)


def _back(a, pu, pv, h, w):     # stand back (GE l045): blue-grey sheet cladding, vertical ribs, a dark window strip
    for k in range(30): a[:, int(k * 0.2 * pu):int(k * 0.2 * pu) + 3] *= 0.86
    a[int(1.2 * pv):int(2.2 * pv), int(0.6 * pu):int(5.4 * pu)] = (52, 60, 70)
    a[-int(0.4 * pv):] = (150, 146, 136)


facade('podium', (214, 202, 176), _podium, (6.0, 2.8), 1024, 478)
facade('glass_corp', (220, 212, 190), _glass, (6.0, 5.0), 1024, 853)
facade('facade_back', (128, 146, 160), _back, (6.0, 3.6))
a = base(512, 512, (186, 206, 118), 3, 10); weather(a, 0.1, 10, 20); save('shelter_wall', a, (2.0, 2.0))   # pale lime (race photo)
a = base(512, 512, (224, 214, 160), 3, 10); a[:, ::32] *= 0.85; save('shelter_roof', a, (2.0, 2.0))
a = base(512, 512, (36, 112, 196), 3, 8); a[:, 250:256] *= 0.8; a[250:256] *= 0.8; save('sail_blue', a, (1, 1))
# grass bank between the fence and the outer path: hand-painted turf, mown bands 3 m, clumps and worn patches
a = base(N, N, (92, 128, 64), 6, 18); xu = N / 6.0
a[:, :int(3 * xu)] *= 1.06
for _ in range(60):
    cx, cy, rr = R.integers(0, N), R.integers(0, N), R.integers(6, 30); yy, xx = np.ogrid[:N, :N]
    a[((yy - cy) ** 2 + (xx - cx) ** 2) < rr * rr] *= R.uniform(0.88, 1.08)
save('grass_bank', a, (6.0, 6.0))
# light tower head: 4 x 8 lamps in a white frame
a = np.ones((N, N, 3)) * np.array((230, 230, 226), float); cu, cv = N / 8, N / 4
for i in range(8):
    for j in range(4):
        x0, y0 = int(i * cu + 8), int(j * cv + 10); x1, y1 = int((i + 1) * cu - 8), int((j + 1) * cv - 10)
        a[y0:y1, x0:x1] = (170, 176, 180); a[y0 + 8:y1 - 8, x0 + 8:x1 - 8] = (86, 92, 98)
save('lamps', a, (1, 1))
a = base(512, 512, (24, 26, 30), 4, 14)
for k in range(0, 512, 16): a[:, k:k + 2] *= 0.6; a[k:k + 2] *= 0.6        # LED module joints
a[:10] = (60, 62, 66); a[-10:] = (60, 62, 66); a[:, :10] = (60, 62, 66); a[:, -10:] = (60, 62, 66)
save('screen_off', a, (2.0, 2.0))
# scoreboard frames and backs (GE 2026 l225/l270 for the NE board, grandstand photo and GE l000/l180 for the SW board)
a = base(512, 512, (76, 108, 140), 3, 8); a[:, 250:254] *= 0.8; a[250:254] *= 0.8; weather(a, 0.08, 8, 12); save('board_frame', a, (2.0, 2.0))
a = base(512, 512, (60, 62, 66), 3, 10)
for k in range(0, 512, 128): a[:, k:k + 3] *= 0.7; a[k:k + 3] *= 0.7
save('board_back', a, (2.0, 2.0))

# name sign over the player race (photo ref/symonds-grandstand-riverway.jpg): white banner, navy semibold text, 8 x 0.65 m
from PIL import ImageDraw, ImageFont
FNT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'assets', 'fonts', 'Barlow-SemiBold.ttf')
def sign(name, text, wm, hm, bg, fg, px=2048, edge=None):
    W, H = px, max(32, int(px * hm / wm)); a = base(H, W, bg, 2, 4)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    sz = int(H * 0.72); f = ImageFont.truetype(FNT, sz)
    while d.textlength(text, font=f) > W * 0.94: sz -= 4; f = ImageFont.truetype(FNT, sz)
    x0, y0, x1, y1 = d.textbbox((0, 0), text, font=f); d.text(((W - (x1 - x0)) / 2 - x0, (H - (y1 - y0)) / 2 - y0), text, font=f, fill=fg)
    if edge: d.rectangle([0, 0, W - 1, H - 1], outline=edge, width=max(2, H // 24))
    save(name, np.asarray(im, float), (1, 1))
sign('sign_symonds', 'Andrew \u2018Roy\u2019 Symonds Grandstand', 8.0, 0.65, (244, 244, 240), (34, 40, 72))
sign('sign_home', 'HOME', 3.8, 0.42, (214, 216, 214), (40, 44, 60), 1024, (150, 152, 150))
sign('sign_away', 'AWAY', 3.8, 0.42, (214, 216, 214), (40, 44, 60), 1024, (150, 152, 150))

# player race gates under the canopy (race photo): dark steel bar gates in two leaves, a grey post between, 8 x 2.25 m
a = base(450, 1600, (34, 36, 40), 3, 8)
for k in range(0, 1600, 22): a[:, k:k + 5] = (70, 74, 80)
a[:, 780:820] = (120, 118, 112); a[:24] = (60, 62, 66); a[-20:] = (96, 94, 90)
save('race_gates', a, (1, 1))

json.dump(TILE, open(OUT + 'tiles.json', 'w', newline=''), indent=0)
for nm in sorted(TILE):
    g = np.asarray(Image.open(OUT + nm + '.png').convert('L'), float); print(f'{nm:16s} grey sd {g.std():5.1f}')
