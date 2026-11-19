# Hand-made textures for the Gabba. No photo pixels: every texel is drawn here.
# Photos were used only to read layout, sizes and colours (noted beside each part).
# Each image is drawn at 2x and downsampled for clean anti-aliased edges.
import numpy as np, math, os, json
from PIL import Image, ImageDraw, ImageFilter
os.makedirs('htex', exist_ok=True)
R = np.random.default_rng(7)
SS = 2

class Canvas:
    def __init__(s, wm, hm, ppm, bg):
        s.ppm = ppm * SS; s.W = int(round(wm * s.ppm)); s.H = int(round(hm * s.ppm)); s.hm = hm
        s.im = Image.new('RGB', (s.W, s.H), bg); s.d = ImageDraw.Draw(s.im)
    def X(s, x): return int(round(x * s.ppm))
    def Y(s, z): return int(round((s.hm - z) * s.ppm))          # z = metres above the bottom edge
    def rect(s, x0, z0, x1, z1, c):                               # metres, z up
        a, b, e, f = s.X(x0), s.Y(z1), s.X(x1) - 1, s.Y(z0) - 1
        if e >= a and f >= b: s.d.rectangle([a, b, e, f], fill=c)
    def hline(s, z, c, w=0.03): s.rect(0, z - w / 2, s.W / s.ppm, z + w / 2, c)
    def vline(s, x, z0, z1, c, w=0.03): s.rect(x - w / 2, z0, x + w / 2, z1, c)
    def grad(s, x0, z0, x1, z1, ctop, cbot):
        for zz in range(s.Y(z1), s.Y(z0)):
            t = (zz - s.Y(z1)) / max(1, s.Y(z0) - s.Y(z1)); c = tuple(int(a + (b - a) * t) for a, b in zip(ctop, cbot))
            s.d.line([(s.X(x0), zz), (s.X(x1) - 1, zz)], fill=c)
    def save(s, name, grain=0.0):
        im = s.im
        if grain:   # fine material grain at final resolution (aggregate, paint), not blur
            a = np.asarray(im).astype(float)
            a += R.normal(0, grain, a.shape[:2])[..., None]
            im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        im = im.resize((s.W // SS, s.H // SS), Image.LANCZOS)
        if grain:
            a = np.asarray(im).astype(float); a += R.normal(0, grain * 0.6, a.shape[:2])[..., None]
            im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        im.save('htex/' + name); print(name, im.size)

def tone(c, k): return tuple(max(0, min(255, int(v + k))) for v in c)

def weather(c, mo=0.0, mc=1.0, blots=0, br=(0.3, 1.2), bk=(-14, 8), streaks=0, sl=(0.5, 2.5), sk=-18, tops=None, grime=0.0, seed=1):
    # Hand-painted wear, drawn on the canvas and wrapped so the tile still repeats:
    # blots = soft patches lighter/darker (concrete blotching, fabric soiling); streaks = rain runs that start at a
    # ledge or joint (z in tops, else anywhere) and fade downward; grime = darkening towards the bottom of the tile.
    rg = np.random.default_rng(seed); W, H = c.W, c.H
    d = np.zeros((H, W), float)
    for _ in range(blots):
        r = rg.uniform(*br) * c.ppm; x0, y0 = rg.uniform(0, W), rg.uniform(0, H); k = rg.uniform(*bk)
        for ox in (-W, 0, W):
            for oy in (-H, 0, H):
                x, y = x0 + ox, y0 + oy
                if x + r < 0 or x - r > W or y + r < 0 or y - r > H: continue
                ys, xs = np.ogrid[max(0, int(y - r)):min(H, int(y + r) + 1), max(0, int(x - r)):min(W, int(x + r) + 1)]
                q = ((xs - x) ** 2 + (ys - y * 1.0) ** 2) / (r * r)
                d[ys, xs] += k * np.clip(1 - q, 0, 1) ** 2
    for k in range(3):   # mottling: random values on a coarse grid that divides the tile, smoothly enlarged (wraps)
        cm = mc / 2 ** k; nx, ny = max(1, round(W / c.ppm / cm)), max(1, round(H / c.ppm / cm))
        g = rg.normal(0, 1, (ny, nx)); g3 = np.tile(g, (3, 3))
        im = Image.fromarray(g3.astype(np.float32), 'F').resize((3 * W, 3 * H), Image.BICUBIC)
        d += mo / 1.6 ** k * np.asarray(im)[H:2 * H, W:2 * W]
    for _ in range(streaks):
        x = int(rg.uniform(0, W)); w = max(1, int(rg.uniform(0.02, 0.08) * c.ppm))
        y0 = c.Y(rg.choice(tops)) if tops else int(rg.uniform(0, H)); L = int(rg.uniform(*sl) * c.ppm); k = sk * rg.uniform(0.5, 1.0)
        for j in range(L):
            y = (y0 + j) % H; f = (1 - j / L) ** 1.5
            for i in range(w): d[y, (x + i) % W] += k * f
    d *= 2.2   # strength set so each big surface reads at grey stddev >= 10 like the photo crops
    if grime: d += grime * (np.arange(H)[:, None] / H) ** 2
    a = np.asarray(c.im).astype(float) + d[..., None]
    c.im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); c.d = ImageDraw.Draw(c.im)

# ---------------------------------------------------------------- facade bay (11.6 m wide, 25 m tall)
# Layout read off the Commons street photos (e1 south side, e4 Vulture St): precast concrete podium to 10.5 m,
# dark blue-grey cladding to 16 m, two window bands to 22 m, white horizontal louvres to the top.
BAY = 11.6
c = Canvas(BAY, 25.0, 64, (198, 198, 192))
CONC = (198, 198, 192)
for i in range(4):                                   # precast panels 2.9 m wide, joints at 2.6 / 5.2 / 7.8 m
    for z0, z1 in ((0, 2.6), (2.6, 5.2), (5.2, 7.8), (7.8, 10.5)):
        c.rect(i * 2.9, z0, (i + 1) * 2.9, z1, tone(CONC, R.integers(-6, 7)))
for i in range(5): c.vline(i * 2.9, 0, 10.5, (150, 150, 146), 0.03)
for z in (2.6, 5.2, 7.8):
    c.hline(z, (150, 150, 146), 0.03); c.rect(0, z - 0.05, BAY, z - 0.015, (210, 210, 205))
for i in range(4):                                   # formwork tie holes, 0.6 m grid, 0.4 m in from the joints
    for zz in np.arange(0.5, 10.3, 1.3):
        for xx in (0.5, 1.45, 2.4):
            x = i * 2.9 + xx; c.d.ellipse([c.X(x - 0.025), c.Y(zz + 0.025), c.X(x + 0.025), c.Y(zz - 0.025)], fill=(160, 160, 156))
CLAD = (86, 97, 114)
c.rect(0, 10.5, BAY, 16.0, CLAD)
for i in range(4):
    for k, (z0, z1) in enumerate(((10.5, 11.85), (11.85, 13.2), (13.2, 14.55), (14.55, 16.0))):
        c.rect(i * 2.9 + 0.012, z0 + 0.012, (i + 1) * 2.9 - 0.012, z1 - 0.012, tone(CLAD, (k % 2) * 4 - 2))
        c.hline(z1, (62, 70, 82), 0.025)
    c.vline(i * 2.9, 10.5, 16.0, (62, 70, 82), 0.025)
    x = i * 2.9 + 1.45                               # black cylinder wall light on each panel (e1)
    c.rect(x - 0.11, 14.7, x + 0.11, 15.15, (22, 24, 27)); c.rect(x - 0.11, 15.1, x + 0.11, 15.15, (60, 62, 66))
for z0 in (16.0, 19.0):                              # window bands: spandrel, sky-reflecting glass, mullions every 1.45 m
    c.rect(0, z0, BAY, z0 + 0.6, (74, 82, 94)); c.hline(z0 + 0.6, (50, 56, 64), 0.05)
    c.grad(0, z0 + 0.65, BAY, z0 + 2.9, (150, 178, 206), (82, 104, 130))
    for i in range(9): c.vline(i * 1.45, z0 + 0.6, z0 + 3.0, (54, 60, 70), 0.08)
    c.rect(0, z0 + 2.15, BAY, z0 + 2.21, (54, 60, 70))
    c.rect(0, z0 + 2.9, BAY, z0 + 3.0, (54, 60, 70))
    for i in range(8):                               # a soft sky streak across each pane, hand-placed
        x0 = i * 1.45 + 0.3; c.d.polygon([(c.X(x0), c.Y(z0 + 2.1)), (c.X(x0 + 0.25), c.Y(z0 + 2.1)), (c.X(x0 + 0.65), c.Y(z0 + 0.7)), (c.X(x0 + 0.4), c.Y(z0 + 0.7))], fill=(140, 166, 192))
c.rect(0, 22.0, BAY, 25.0, (236, 236, 230))          # white louvres: slats 0.12 m, shadow under each, posts every 1.45 m
for zz in np.arange(22.0, 25.0, 0.12):
    c.rect(0, zz, BAY, zz + 0.035, (176, 178, 176)); c.rect(0, zz + 0.035, BAY, zz + 0.05, (205, 206, 203))
for i in range(9): c.vline(i * 1.45, 22.0, 25.0, (246, 246, 242), 0.07); c.vline(i * 1.45 + 0.045, 22.0, 25.0, (190, 191, 188), 0.02)
c.rect(0, 24.9, BAY, 25.0, (246, 246, 242))
c.save('facade_bay.png', grain=2.5)

# ---------------------------------------------------------------- concrete (slab edges, concourse decks), 4 m tile
c = Canvas(4, 4, 96, (196, 196, 190))
for i in range(2):
    for j in range(2): c.rect(i * 2, j * 2, i * 2 + 2, j * 2 + 2, tone((196, 196, 190), R.integers(-5, 6)))
c.hline(0.015, (156, 156, 152), 0.03); c.vline(0.015, 0, 4, (156, 156, 152), 0.03)
weather(c, mo=5, mc=1.2, streaks=30, sl=(0.4, 1.8), sk=-22, tops=[4.0, 2.0], seed=11)
c.save('concrete.png', grain=3.0)
c = Canvas(4, 4, 64, (58, 60, 64)); c.hline(0.015, (40, 42, 45), 0.03); c.vline(2.0, 0, 4, (46, 48, 51), 0.02)
weather(c, mo=4, mc=0.8, blots=12, br=(0.04, 0.15), bk=(-10, 10), seed=12); c.save('darkdeck.png', grain=2.0)

# ---------------------------------------------------------------- footpath: light-tan concrete, 3 x 3.2 m saw-cut bays (Commons e2)
c = Canvas(3.0, 3.2, 128, (200, 192, 174))
c.rect(0, 0, 3.0, 3.2, (200, 192, 174))
c.hline(0.012, (148, 142, 128), 0.025); c.vline(0.012, 0, 3.2, (148, 142, 128), 0.025)
weather(c, mo=4, mc=1.0, blots=30, br=(0.03, 0.09), bk=(-26, -10), seed=13)   # gum spots, wear and water marks
c.save('path.png', grain=4.0)

# ---------------------------------------------------------------- white steel (booms, masts, light poles)
c = Canvas(1.0, 4.0, 64, (238, 238, 234))
for z in np.arange(0, 4.0, 2.0): c.hline(z + 0.01, (214, 214, 210), 0.02)   # weld ring every 2 m
for x in (0.25, 0.75): c.vline(x, 0, 4.0, (226, 226, 222), 0.015)          # longitudinal seam lines
weather(c, mo=4, mc=0.5, streaks=12, sl=(0.6, 1.9), sk=-24, tops=[2.0, 4.0], seed=14)
c.save('steel.png', grain=1.2)

# ---------------------------------------------------------------- roof fabric: one bay, u across 0-1, v = inner to outer edge 0-1
c = Canvas(12.0, 24.0, 32, (246, 246, 241))
for k in range(1, 6): c.hline(k * 4.0, (228, 228, 223), 0.06); c.hline(k * 4.0 + 0.08, (238, 238, 233), 0.05)   # panel seams across the bay every 4 m, with their lap (g49 bays)
c.rect(0, 0, 12, 0.25, (232, 232, 227)); c.rect(0, 23.75, 12, 24, (232, 232, 227))   # edge cable pockets
weather(c, mo=2.2, mc=3.0, streaks=70, sl=(1.5, 6.0), sk=-12, tops=[24.0, 12.0], seed=15)   # soiling, run-off from seams
u = np.arange(c.W) / c.ppm; e = np.clip(1 - np.minimum(u, 12.0 - u) / 2.5, 0, 1) ** 2   # dirt gathers in the valleys beside each boom
a_ = np.asarray(c.im).astype(float) - 30 * e[None, :, None]; c.im = Image.fromarray(np.clip(a_, 0, 255).astype(np.uint8)); c.d = ImageDraw.Draw(c.im)
c.save('membrane.png', grain=1.5)

# ---------------------------------------------------------------- seats: 24 deg of bowl per tile (64 seats), 4 rows of 1.0 m up the rake
# Colours (director via secretary 2026-11-18, no maroon): seat-by-seat mix measured on the sunlit east stand of g49:
# gold 50%, orange 15%, white 31%, blue 4% (blue = upper bound, few sunlit blue pixels). Same mix all round; shade is light, not paint.
GOLD, ORANGE, WHITE, BLUE = (226, 168, 30), (222, 120, 34), (236, 236, 230), (34, 64, 152)
MAROON = (122, 28, 44)
NSEAT, NROW = 64, 4
c = Canvas(32.0, 4.0, 64, (150, 150, 146))
for r in range(NROW):
    z0 = r * 1.0
    c.rect(0, z0, 32, z0 + 0.36, (128, 128, 124))                           # tread (in the shade of the row above)
    c.rect(0, z0 + 0.36, 32, z0 + 0.40, (86, 86, 84))                    # tread edge shadow
    for s in range(NSEAT):
        x0 = s * 0.5
        if s % 24 == 23:                                                     # aisle stair every 24 seats
            c.rect(x0, z0, x0 + 0.5, z0 + 1.0, (182, 182, 176)); c.rect(x0, z0 + 0.5, x0 + 0.5, z0 + 0.53, (130, 130, 126)); continue
        col = [GOLD, ORANGE, WHITE, BLUE][R.choice(4, p=[0.50, 0.15, 0.31, 0.04])]
        c.rect(x0 + 0.03, z0 + 0.40, x0 + 0.47, z0 + 0.58, tone(col, -40))   # seat pan (in its own shadow)
        c.rect(x0 + 0.03, z0 + 0.58, x0 + 0.47, z0 + 0.98, col)              # seat back
        c.rect(x0 + 0.03, z0 + 0.93, x0 + 0.47, z0 + 0.98, tone(col, 28))    # lit top edge of the back
        c.rect(x0 + 0.03, z0 + 0.58, x0 + 0.06, z0 + 0.98, tone(col, -20))
c.save('seats.png', grain=2.0)

# ---------------------------------------------------------------- glass band of the boxes in the bowl, 6 m tile
c = Canvas(6.0, 2.6, 64, (60, 72, 88))
c.grad(0, 0.1, 6, 2.5, (110, 132, 156), (52, 64, 80))
for i in range(5): c.vline(i * 1.5, 0, 2.6, (40, 44, 50), 0.07)
c.rect(0, 0, 6, 0.1, (40, 44, 50)); c.rect(0, 2.5, 6, 2.6, (40, 44, 50))
c.save('boxglass.png', grain=1.0)

# ---------------------------------------------------------------- 411 Vulture St: 19 m wide, 51.6 m tall; slabs are geometry at 4.35 + 3.8 k
# Read off the aerial and e1: blue-grey glass, dark frames every 1.5 m, white parapet on top, dark lobby glass at the base.
H4 = 51.6
c = Canvas(19.0, H4, 32, (96, 116, 136))
for k in range(13):
    z0 = 4.35 + 3.8 * k + 0.7; z1 = min(H4 - 0.6, z0 + 3.1)
    if z1 <= z0: continue
    c.grad(0, z0, 19, z1, (132, 156, 180), (84, 102, 122))
    c.rect(0, z0, 19, z0 + 1.0, (226, 228, 226))                            # white glass balustrade face at the slab edge
    c.rect(0, z0 + 0.95, 19, z0 + 1.0, (180, 184, 186))
    for i in range(14): c.vline(i * 1.5, z0 + 1.0, z1, (56, 62, 70), 0.07)
c.grad(0, 0, 19, 4.35, (70, 80, 92), (40, 46, 54))
for i in range(8): c.vline(i * 2.5, 0, 4.35, (28, 30, 34), 0.1)
c.rect(0, H4 - 0.95, 19, H4, (236, 236, 232))
c.save('t411.png', grain=1.5)
c = Canvas(19.0, 0.7, 64, (238, 238, 234))                                  # slab edge: white, shade on the underside
c.rect(0, 0, 19, 0.12, (196, 198, 196))
for i in range(2): c.rect(4.75 + i * 9.5, 0, 4.75 + i * 9.5 + 0.3, 0.7, (150, 152, 152))   # notch at every second balcony
c.save('t411_slab.png', grain=1.5)

# ---------------------------------------------------------------- Hyundai Centre wall: 11 m tile, 20 m tall (Commons e5 for layout)
# Blue cladding pier, grey precast panels on a 1.5 x 1.25 m grid, white vertical louvre boxes over dark glass, dark glazing at street level.
c = Canvas(11.0, 20.0, 48, (196, 196, 190))
for i in range(int(8 / 1.5) + 1):
    for j in range(16):
        c.rect(3 + i * 1.5, j * 1.25, 3 + (i + 1) * 1.5, (j + 1) * 1.25, tone((196, 196, 190), R.integers(-7, 8)))
for i in range(7): c.vline(3 + i * 1.5, 0, 20, (158, 158, 154), 0.025)
for j in range(17): c.rect(3, j * 1.25 - 0.012, 11, j * 1.25 + 0.012, (158, 158, 154))
BLUE_C = (44, 86, 170)
c.rect(0, 0, 3, 20, BLUE_C)
for j in range(1, 14): c.rect(0, j * 1.5 - 0.012, 3, j * 1.5 + 0.012, (32, 64, 128))
c.vline(1.5, 0, 20, (32, 64, 128), 0.025); c.vline(3.0, 0, 20, (30, 34, 40), 0.06)
c.rect(0, 18.6, 11, 20, BLUE_C); c.rect(0, 18.6, 11, 18.66, (32, 64, 128))
for zb in (6.2, 12.4):                                                     # louvre boxes 4.2 m wide, 3.2 m tall
    x0 = 4.6
    c.rect(x0, zb, x0 + 4.2, zb + 3.2, (34, 40, 48))
    c.rect(x0 - 0.1, zb + 3.1, x0 + 4.3, zb + 3.3, (60, 64, 70))
    for k in range(6):
        fx = x0 + 0.2 + k * 0.7
        c.rect(fx, zb + 0.1, fx + 0.22, zb + 3.1, (240, 240, 236)); c.rect(fx + 0.18, zb + 0.1, fx + 0.24, zb + 3.1, (170, 172, 172))
c.grad(3, 0, 11, 3.6, (70, 82, 96), (34, 40, 48))                          # street-level glazing
for i in range(6): c.vline(3 + i * 1.6, 0, 3.6, (24, 26, 30), 0.08)
c.rect(3, 3.6, 11, 3.75, (60, 64, 70))
c.save('hyundai.png', grain=2.0)
c = Canvas(6, 6, 48, (232, 234, 234))                                      # flat roofs: pale grey membrane, lapped sheets
for k in range(4): c.hline(k * 1.5 + 0.01, (206, 208, 208), 0.02)
weather(c, mo=5, mc=1.5, blots=6, br=(0.4, 0.9), bk=(-8, -4), streaks=10, sl=(0.4, 1.2), sk=-16, tops=[1.5, 3.0, 4.5, 6.0], seed=16)   # ponding stains, lap grime
c.save('roofdeck.png', grain=1.5)

# ---------------------------------------------------------------- screen block: pale grey cladding, 4 m tile
c = Canvas(4, 4, 64, (204, 208, 212))
for k in range(4): c.hline(k * 1.0 + 0.01, (170, 174, 178), 0.02)
c.vline(0.01, 0, 4, (170, 174, 178), 0.02)
c.save('screen.png', grain=1.2)

# ---------------------------------------------------------------- big screen face (photo 745-822 x 351-403): 22 x 18.4 m,
# pale blue screen in three panels with dark seams (photo y 358, 369, 383 -> z 15.8, 11.9, 7.0 above its 1.6 m base), light ledge at the foot
c = Canvas(22, 18.0, 64, (80, 148, 200))                # blank LED face, saturated blue as photo (70-90,140-160,190-205)
c.grad(0, 0, 22, 18.0, (88, 156, 204), (60, 128, 186))
c.rect(0, 16.5, 22, 18.0, (104, 146, 180))            # top cap, greyer (photo y 352-356)
for zz in (15.4, 11.5, 6.6): c.rect(0, zz - 0.16, 22, zz + 0.16, (20, 60, 100))
c.vline(0.04, 0, 18.0, (30, 60, 90), 0.08); c.vline(21.96, 0, 18.0, (30, 60, 90), 0.08)
c.save('scoreface.png', grain=1.0)

# ---------------------------------------------------------------- lamp head: fan of lamps in a grey frame (panorama photo for the layout)
# UV frame matches build.py tuv(): trapezoid inside a square with a 3/48 margin, top 2*WT wide, bottom 2*WB.
N = 1024; im = Image.new('RGB', (N * SS, N * SS), (78, 80, 84)); d = ImageDraw.Draw(im)
m = 3 / 48; WT, WB = 5.5, 3.5
def uvp(s, t):
    hw = WB + (WT - WB) * (t + 1) / 2
    u = m + (1 - 2 * m) * (s * hw + WT) / (2 * WT); v = m + (1 - 2 * m) * (t + 1) / 2
    return (u * N * SS, (1 - v) * N * SS)
d.polygon([uvp(-1, -1), uvp(1, -1), uvp(1, 1), uvp(-1, 1)], fill=(64, 66, 70))
ROWS = 8
for r in range(ROWS):
    t = -1 + (r + 0.5) * 2 / ROWS
    hw = WB + (WT - WB) * (t + 1) / 2; ncol = int(round(hw * 2 / 1.05))
    for k in range(ncol):
        s = -1 + (k + 0.5) * 2 / ncol
        cx_, cy_ = uvp(s, t); rr = 0.42 * (1 - 2 * m) * N * SS / (2 * WT)
        d.ellipse([cx_ - rr * 1.12, cy_ - rr * 1.12, cx_ + rr * 1.12, cy_ + rr * 1.12], fill=(40, 42, 46))
        d.ellipse([cx_ - rr, cy_ - rr, cx_ + rr, cy_ + rr], fill=(200, 202, 204))
        d.ellipse([cx_ - rr * 0.72, cy_ - rr * 0.72, cx_ + rr * 0.72, cy_ + rr * 0.72], fill=(248, 248, 236))
        d.ellipse([cx_ - rr * 0.6, cy_ - rr * 0.68, cx_ - rr * 0.1, cy_ - rr * 0.2], fill=(255, 255, 250))
im.resize((N, N), Image.LANCZOS).save('htex/lamphead.png'); print('lamphead.png')

# ---------------------------------------------------------------- playing surface: planar over the oval, 10 px/m
# Mowing stripes fitted to 316 band edges in the sunlit part of the aerial: 7.82 m bands, normal at 80 deg;
# bright (107,131,64) and dark (84,110,48). White square cover over the pitch at its four measured corners; boundary line.
exec(open('geo.py').read().split('def interp')[0])
import geo_pitch as GP
X0, Y0, X1, Y1 = GP.box
PPM = 10
W, H = int((X1 - X0) * PPM), int((Y1 - Y0) * PPM)
xs = X0 + (np.arange(W) + 0.5) / PPM; ys = Y1 - (np.arange(H) + 0.5) / PPM
XX, YY = np.meshgrid(xs, ys)
n = np.array(GP.n); s = XX * n[0] + YY * n[1]
band = np.floor((s - GP.phase) / GP.width).astype(int) % 2
BR, DKc = np.array([107, 131, 64]), np.array([84, 110, 48])
img = np.broadcast_to((BR + DKc) / 2.0, (H, W, 3)).astype(float).copy()   # director 2026-11-18: no mowing stripes, plain grass (mean of the two measured band colours)
img += R.normal(0, 5, (H, W))[..., None] * np.array([0.8, 1.0, 0.5])
im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
pix = lambda x, y: ((x - X0) * PPM, (Y1 - y) * PPM)
# director 2026-11-18: white pitch cover removed
d.line([pix(*p) for p in GP.boundary] + [pix(*GP.boundary[0])], fill=(236, 238, 232), width=2)
im.save('htex/grass.png'); print('grass.png', im.size)
