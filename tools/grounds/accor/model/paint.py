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




# ---- 3D seat plastic: one moulded shell, a darker rim, a soft sheen down the middle. UV 0-1 per face ----
# colours read off ref/Stadium_Australia_07-04-23.jpg (empty rows in daylight): lower tier light aqua, upper tiers grey-teal
def shell(name, col):
    a = base(128, 128, col, 2, 6)
    a[:, :8] *= 0.80; a[:, -8:] *= 0.80; a[:6] *= 0.86; a[-6:] *= 0.72
    a[:, 40:88] *= (1 + 0.10 * np.sin(np.linspace(0, math.pi, 48)))[None, :, None]
    save(name, a, (1, 1))


shell('seat_aqua', (138, 188, 198)); shell('seat_teal', (112, 150, 164)); shell('seat_plastic', (138, 188, 198))
# concrete treads and risers: pale grey, dark nosing line, scuffs
a = base(512, 512, (150, 150, 146), 5, 14); a[:10] *= 0.68; weather(a, 0.06, 10, 20, top_dark=False); save('conc_tread', a, (2.0, 0.8))


# ---- concrete: precast panels 3.0 x 1.5 m with joints, rain streaks, blotches ----
def concrete(name, col, pu=3.0, pv=1.5, tile=(6.0, 6.0)):
    h = w = N; a = base(h, w, col, 5, 20); xu = N / tile[0]; yv = N / tile[1]
    for k in range(int(tile[0] / pu)): a[:, int(k * pu * xu):int(k * pu * xu) + 4] *= 0.68
    for k in range(int(tile[1] / pv)): a[int(k * pv * yv):int(k * pv * yv) + 4] *= 0.68
    weather(a, 0.12, 16, 70); save(name, a, tile)


concrete('conc_wall', (182, 180, 174))
# paving: apron concrete slabs 1.2 m, saw joints, stains
a = base(N, N, (150, 146, 140), 6, 20); p = N / 2.4
for k in range(2): a[int(k * 1.2 * p):int(k * 1.2 * p) + 3] *= 0.72; a[:, int(k * 1.2 * p):int(k * 1.2 * p) + 3] *= 0.72
save('paving', a, (2.4, 2.4))
# fence: white boundary panels, dark capping rail, grey kick board (tile 2 m x 1.1 m)
a = base(512, 1024, (226, 228, 224), 3, 8); px = 1024 / 2.0
for k in range(20): a[:, int(k * 0.1 * px):int(k * 0.1 * px) + 6] *= 0.8
a[:46] = (40, 48, 70); a[460:] = (110, 110, 106); weather(a, 0.08, 10, 30); save('fence', a, (2.0, 1.1))

# ---- roof top (GE top65, measured): translucent sheets in a diamond grid of glazing bars at +-45 deg in the local frame,
# bays 10 m a side (25-27 px at 0.3996 m/px). Bays are a pale/grey checker (Google Maps 3D: about a third of bays darker, scattered).
# One tile = 56.57 m = four bay diagonals, so the grid closes across tiles. Each bay gets its own slight tone. ----
def roof_top(name, col):
    # 32 x 32 bays per tile (226 m, about the whole roof) so the dark bays can form the large stepped blocks seen in
    # roof_above_008 / GE l180 (8-12 bays across, about 28% of the roof) instead of a repeating random checker
    NB = 32; W_ = 2048; TT = NB * 5 * math.sqrt(2); a = np.zeros((W_, W_, 3)); yy, xx = np.mgrid[0:W_, 0:W_] / W_ * TT
    d1, d2 = (xx + yy) / (10 * math.sqrt(2)), (xx - yy) / (10 * math.sqrt(2))
    k1, k2 = np.floor(d1).astype(int) % NB, np.floor(d2).astype(int) % NB
    g = np.random.default_rng(5); r = g.random((NB, NB)); f = np.fft.fftfreq(NB)
    r = np.real(np.fft.ifft2(np.fft.fft2(r) * np.exp(-(f[:, None] ** 2 + f[None, :] ** 2) * (2 * math.pi * 2.2) ** 2 / 2)))
    dark = r > np.quantile(r, 0.72)
    tt = g.uniform(-6, 6, (NB, NB)) - 22 * dark; tone = tt[k1, k2][:, :, None]
    a[:] = np.array(col, float); a += tone + noise(W_, W_, 12, 6)[:, :, None] + fine(W_, W_, 2)[:, :, None]
    a[:, :, 2] += 6 * dark[k1, k2]   # the dark bays read blue-grey in the photo
    sheet = ((xx / 1.0) % 1 < 0.04)[:, :, None]; a = a * (1 - 0.06 * sheet)
    bar = ((np.abs(d1 - np.round(d1)) < 0.03) | (np.abs(d2 - np.round(d2)) < 0.03))[:, :, None]
    a = a * (1 - 0.30 * bar); save(name, a, (TT, TT))


roof_top('roof_top', (150, 158, 164))
# roof underside (photo 07-04-23): light translucent sheets between purlins every 2.5 m, a darker rafter line every 10 m
a = base(1024, 1024, (214, 222, 228), 2, 10); pu = 1024 / 10.0
for k in range(4): a[int(k * 2.5 * pu):int(k * 2.5 * pu) + 7] = (120, 126, 132)
for k in range(10): a[:, int(k * pu):int(k * pu) + 3] *= 0.86
a[:, 0:10] = (110, 116, 122)
save('roof_soffit', a, (10.0, 10.0))
a = base(512, 1024, (224, 226, 226), 4, 16); xu = 1024 / 4.0
for k in range(2): a[:, int(k * 2 * xu):int(k * 2 * xu) + 6] *= 0.7
a[480:] *= 0.8; weather(a, 0.14, 16, 40); save('fascia', a, (4.0, 2.0))
a = base(512, 512, (168, 170, 170), 5, 20); weather(a, 0.10, 16, 30, top_dark=False); save('roof_flat', a, (6.0, 6.0))

# ---- steel ----
for nm, col in (('steel_white', (232, 234, 232)), ('steel_galv', (150, 154, 158)), ('sign_back', (34, 46, 78))):
    a = base(256, 256, col, 6, 22); a[:, 120:126] *= 0.72; a[:, 0:4] *= 0.75; weather(a, 0.14, 16, 16); save(nm, a, (2.0, 2.0))

# ---- glass box fronts on the tier bands: dark tint, a mullion every 1.5 m, white sill and head (tile 6 x 3.5 m) ----
a = base(560, 960, (52, 62, 72), 3, 12); pu = 960 / 6.0; pv = 560 / 3.5
for k in range(4): a[:, int(k * 1.5 * pu):int(k * 1.5 * pu) + 8] = (150, 154, 156)
a[:30] = (216, 218, 216); a[-60:] = (200, 202, 200)
a[30:120] *= 1.25   # sky reflection near the head
save('box_glass', a, (6.0, 3.5))
# inner louvres between the top of the bowl and the roof: grey blades every 0.3 m, darker gaps
a = base(512, 512, (92, 98, 106), 3, 10); yv = 512 / 3.0   # GE: the gap under the roof reads as shadow
for k in range(10): a[int(k * 0.3 * yv):int(k * 0.3 * yv) + 18] *= 0.55
save('louvre', a, (3.0, 3.0))


# ---- facades: one tile = 8 m along x 18 m (the lower facade, image row 0 = top) ----
def facade_main():   # one tile = 8 m x the whole 38 m wall (GE l090/l270 side bays): tall pale blue-grey ribbed cladding between white
    # pilasters, a white band at 30 m, a dark window strip at 31-33.5 m, white parapet to the top; image row 0 = top
    w, h = 1024, 2432; pu = w / 8.0; pv = h / 38.0
    a = base(h, w, (196, 204, 214), 3, 12)   # signage_085, backs_067: pale blue-grey ribbed metal cladding, not mauve
    for k in range(32): a[:, int(k * pu / 4):int(k * pu / 4) + 4] *= 0.9           # vertical cladding ribs every 0.25 m
    Y = lambda z: int(h - z * pv)
    for k in (1, 2, 3): a[Y(k * 7.5) - 3:Y(k * 7.5) + 3] *= 0.86                  # panel joints
    a[Y(31.0):Y(30.0)] = (226, 226, 222); a[Y(33.5):Y(31.0)] = (40, 50, 62); a[:Y(33.5)] = (222, 222, 218)
    for k in range(8): a[Y(33.5):Y(31.0), int(k * pu):int(k * pu) + 6] = (190, 192, 192)
    a[Y(30.0):, 0:int(0.9 * pu)] = (228, 228, 224)                                   # white pilaster every 8 m
    weather(a, 0.0, 12, 0); save('facade_main', a, (8.0, 38.0))


facade_main()

# end facade (GE l000, l180): grey precast panels, a dark louvre band under the low end roof, pilasters every 8 m
a = base(2432, 1024, (128, 136, 146), 4, 16); pv = 2432 / 38.0; Y = lambda z: int(2432 - z * pv)
for k in range(1, 6): a[Y(k * 3.0) - 3:Y(k * 3.0) + 3] *= 0.8
a[:Y(16.0)] = (150, 156, 162); a[Y(22.0):Y(16.0)] = (60, 66, 74)
for k in range(30): a[Y(22.0):Y(16.0)][int(k * 0.2 * pv):int(k * 0.2 * pv) + 4] = (120, 126, 134)
a[Y(16.0):, 0:int(0.6 * 128)] = (176, 180, 184)
weather(a, 0.0, 14, 0); save('facade_end', a, (8.0, 38.0))
# upper facade: the back of the upper tier, white raking soffit panels with steel struts every 8 m
a = base(1024, 1024, (214, 214, 210), 3, 14); pu = 1024 / 8.0
for k in range(1): a[:, int(k * pu):int(k * pu) + 26] = (150, 154, 160)
for k in range(4): a[int(k * 256):int(k * 256) + 6] *= 0.7
weather(a, 0.0, 16, 0); save('facade_upper', a, (8.0, 8.0))

# ---- ramp towers: concrete ramp bands (1.3 m spandrels) over dark open floors, one helix turn per 4.5 m of height;
# the tile is a quarter of the drum (28.9 m), so the band climbs 1.125 m across it ----
w, h = 2048, 1024; tu, tv = 28.9, 9.0; a = np.zeros((h, w, 3))
yy, xx = np.mgrid[0:h, 0:w]; z = (h - yy) / h * tv + xx / w * 1.125
ph = (z % 4.5) / 4.5
band = ph < 0.72   # GE l090: spandrels ~70 % of each turn, thin dark gap
a[:] = np.array((70, 66, 62)); a[band] = np.array((200, 198, 192))   # pale grey concrete spandrels (GE l090)
a += noise(h, w, 10, 12)[:, :, None] + fine(h, w, 2)[:, :, None]
edge = (np.abs(ph - 0.72) < 0.012) | (ph < 0.012); a[edge] *= 0.75
for k in range(8): a[:, int(k * w / 8):int(k * w / 8) + 10][~band[:, int(k * w / 8):int(k * w / 8) + 10]] = (120, 122, 124)  # columns behind
save('ramp', a, (tu, tv))

# ---- name sign (GE l090, l270): navy panel, the A emblem in gold, ACCOR in wide white capitals, STADIUM under it ----
from PIL import ImageDraw, ImageFont
SW_, SH_ = 2560, 512
im = Image.fromarray(np.clip(base(SH_, SW_, (30, 44, 80), 2, 6), 0, 255).astype(np.uint8)); dr = ImageDraw.Draw(im)
gold = (196, 150, 104)
# boxes measured off the GE sign crop (ge/_sign.png): panel 915 px wide, emblem 5-18 %, ACCOR 20-94 % with caps
# 22-65 % of the height, STADIUM 51-94 % at 71-96 %; letters are wide geometric capitals set tight
def em(x, y): return (int(128 + x * 332), int(100 + y * 370))
dr.polygon([em(0, 1), em(0.42, 0), em(0.62, 0), em(0.40, 0.62), em(0.55, 0.62), em(0.62, 0.78), em(0.32, 0.78), em(0.24, 1)], fill=gold)
dr.polygon([em(0.62, 0), em(0.80, 0), em(1, 1), em(0.80, 1)], fill=(170, 124, 84))
FB = ImageFont.truetype('C:/Windows/Fonts/bahnschrift.ttf', 400)
try:
    FB.set_variation_by_name('Regular')
except Exception:
    pass
def word(txt, box, sp):   # draw txt in white, then scale it into box (x0, y0, x1, y1) on the panel
    t = Image.new('L', (4000, 600)); d = ImageDraw.Draw(t); x = 20
    for ch in txt: d.text((x, 50), ch, font=FB, fill=255); x += d.textlength(ch, font=FB) + sp
    t = t.crop(t.getbbox()).resize((box[2] - box[0], box[3] - box[1]), Image.LANCZOS)
    im.paste((240, 242, 244), (box[0], box[1]), t)
word('ACCOR', (512, 113, 2406, 333), 30)
word('STADIUM', (1306, 364, 2406, 492), 60)
a = np.asarray(im, float) + noise(SH_, SW_, 10, 4)[:, :, None]; save('sign_accor', a, (26.0, 5.2))

json.dump(TILE, open(OUT + 'tiles.json', 'w', newline=''), indent=0)
for nm in sorted(TILE):
    g = np.asarray(Image.open(OUT + nm + '.png').convert('L'), float); print(f'{nm:16s} grey sd {g.std():5.1f}')
