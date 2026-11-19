# hand-made textures (no photo pixels): every material painted procedurally at real scale, daylight colours.
# python paint.py  -> tex/*.png and tex/index.json {name: {w, h, v0?}} (metres per tile)
import numpy as np, json, os
from PIL import Image

os.makedirs('tex', exist_ok=True)
rng = np.random.default_rng(7)
INDEX = {}


def noise(h, w, scale_px, amp=1.0):
    """tileable smooth noise: white noise low-passed in the frequency domain (wraps at the edges)"""
    n = rng.standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None]; fx = np.fft.fftfreq(w)[None, :]
    f = np.exp(-((fx ** 2 + fy ** 2) * (scale_px ** 2) * 6.0))
    r = np.real(np.fft.ifft2(np.fft.fft2(n) * f))
    r = (r - r.mean()) / (r.std() + 1e-9)
    return r * amp


def col(c): return np.array(c, float)[None, None, :] / 255.0


def save(name, img, w, h, **kw):
    a = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(a).save('tex/%s.png' % name)
    INDEX[name] = dict(img='tex/%s.png' % name, w=w, h=h, **kw)


def base(H, W, c, grain=0.03, mott=0.05, mott_px=30):
    img = np.ones((H, W, 3)) * col(c)
    v = 1 + noise(H, W, 1.0, grain) + noise(H, W, mott_px, mott * 0.45)
    return img * v[..., None]


def vline(img, x, wpx, c, a=1.0):
    W = img.shape[1]; x0 = int(round(x)) % W
    for k in range(max(1, int(round(wpx)))):
        img[:, (x0 + k) % W] = img[:, (x0 + k) % W] * (1 - a) + col(c)[0] * a


def hline(img, y, hpx, c, a=1.0):
    H = img.shape[0]; y0 = int(round(y)) % H
    for k in range(max(1, int(round(hpx)))):
        img[(y0 + k) % H, :] = img[(y0 + k) % H, :] * (1 - a) + col(c)[0] * a


def streaks(img, n, c, a=0.35, wpx=(2, 6), lpx=(0.3, 0.9), top=True):
    """rain/rust streaks: thin darker runs falling from the top (or rising grime from the bottom), fading out"""
    H, W = img.shape[:2]
    for _ in range(n):
        x = int(rng.integers(0, W)); w = int(rng.integers(*wpx)); L = int(H * rng.uniform(*lpx)); y0 = int(rng.integers(0, H))
        f = np.linspace(1, 0, L) ** 1.5 * a
        for k in range(w):
            xx = (x + k) % W; ys = (y0 + np.arange(L)) % H
            img[ys, xx] = img[ys, xx] * (1 - f[:, None]) + col(c)[0] * f[:, None]


def foot_grime(img, frac, c, a=0.45):
    """wear and dirt toward the bottom of the tile (image row H-1 = bottom)"""
    H = img.shape[0]; n = int(H * frac); f = (np.linspace(0, 1, n) ** 2 * a)[:, None, None]
    img[H - n:] = img[H - n:] * (1 - f) + col(c) * f


def blotch(img, c, a=0.25, px=25, thr=0.8):
    """patchy stains: where smooth noise passes thr, blend toward c"""
    H, W = img.shape[:2]; m = np.clip((noise(H, W, px) - thr) / 1.2, 0, 1)[..., None] * a
    return img * (1 - m) + col(c) * m


def steel_tex(c, W_m, H_m, P_, seam_m):
    s_ = base(int(H_m * P_), int(W_m * P_), c, grain=0.05, mott=0.10, mott_px=20)
    for k in range(int(round(W_m / seam_m))):
        vline(s_, k * seam_m * P_, 3, tuple(v * 0.45 for v in c)); vline(s_, k * seam_m * P_ + 2, 1, tuple(min(255, v * 1.25) for v in c))
    s_ = blotch(s_, (96, 70, 52), 0.35, 12, 0.9)
    s_ = blotch(s_, (196, 198, 204), 0.3, 8, 1.2)  # chalked, chipped paint
    streaks(s_, 14, (80, 60, 46), 0.4)
    foot_grime(s_, 0.35, (60, 54, 48))
    return s_


# ---- field grass with mow stripes (8 m bands across the long axis), tile 16 m x 16 m, 40 px/m
P = 40; W = H = 16 * P
g = base(H, W, (62, 118, 50), grain=0.10, mott=0.05, mott_px=60)
stripe = np.where((np.arange(W) // (8 * P)) % 2 == 0, 1.07, 0.93)[None, :, None]
g = g * stripe
save('grass_field', g, 16.0, 16.0)
# ---- apron grass, no stripes; dull green read off the 1990 vertical (SE apron median 53, 88, 67)
ga = base(10 * P, 10 * P, (52, 86, 62), grain=0.14, mott=0.12, mott_px=50)
for k in range(5):  # mower runs 2 m wide, alternate light/dark
    ga[:, int(k * 2 * P):int((k * 2 + 1) * P)] *= 1.07
ga = blotch(ga, (100, 104, 78), 0.35, 30, 1.0)  # worn, dry patches
save('grass', ga, 10.0, 10.0)
# ---- grass banks (south, east, north-east): dull dark green read off the sunlit south bank in the 1990 vertical
# (median 76, 101, 74), mown across the slope every 1.5 m, darker clumps and dry worn patches
gb = base(8 * P, 8 * P, (72, 96, 68), grain=0.16, mott=0.14, mott_px=40)
for k in range(6):
    gb[int(k * 1.5 * P * 8 / 9):int((k * 1.5 + 0.75) * P * 8 / 9)] *= 1.06
gb = blotch(gb, (112, 112, 84), 0.40, 25, 0.9)
gb = blotch(gb, (44, 66, 50), 0.40, 18, 1.0)
save('grassbank', gb, 8.0, 8.0)

# ---- bowl seating: one bay (u in bay units) x 4 rows (0.85 m per row up the rake), 48 px/m on a 15 m bay
P = 48; BW = 15.0; RW = 0.85; NROW = 4
W = int(BW * P); H = int(RW * NROW * P)
s = base(H, W, (150, 146, 138), grain=0.04, mott=0.04)
for r in range(NROW):
    y0 = r * RW * P
    # riser shadow, then the bench (orange, slatted), then the concrete tread
    hline(s, y0, 2, (90, 88, 84))
    by = y0 + 0.08 * P
    for k in range(int(0.62 * P)):
        yy = int(by + k) % H
        sh = 0.90 + 0.12 * (k / (0.62 * P))
        s[yy, :] = col((196, 140, 96))[0] * sh * (1 + noise(1, W, 1.0, 0.03)[0][:, None])
    for k in range(3):  # slat gaps
        hline(s, by + (k + 1) * 0.155 * P, 1, (110, 60, 48), 0.6)
    hline(s, by + 0.62 * P, 2, (70, 50, 40), 0.7)  # bench shadow on the tread
# aisle: 1.2 m concrete stair with a step every half row and white kerbs
aw = int(1.2 * P)
s[:, :aw] = base(H, aw, (196, 194, 188), grain=0.04, mott=0.03)
for r in range(NROW * 2):
    y = r * RW / 2 * P
    s[int(y) % H, :aw] = col((110, 108, 104))[0]; s[(int(y) + 1) % H, :aw] = col((150, 148, 144))[0]
vline(s, 0, 3, (240, 240, 236)); vline(s, aw - 3, 3, (240, 240, 236))
save('seats', s, 1.0, RW * NROW, bay=True)
# covered stand seating (same rows, aisles every 15 m along the stand)
save('seats_m', s, BW, RW * NROW)

# ---- moulded plastic bucket seat (pan, back, pedestal), 0.5 m tile, 400 px/m: orange-tan shell, faded top,
# a darker moulded rim, scuffs and dust
P = 400; n_ = int(0.5 * P)
st = base(n_, n_, (196, 140, 96), grain=0.05, mott=0.10, mott_px=12)
yy, xx = np.mgrid[0:n_, 0:n_] / n_
rim = np.minimum(np.minimum(xx, 1 - xx), np.minimum(yy, 1 - yy))
st = st * (0.80 + 0.20 * np.clip(rim / 0.08, 0, 1))[..., None]
st = st * (1.06 - 0.12 * yy)[..., None]  # sun-faded toward the top
st = blotch(st, (120, 92, 70), 0.35, 6, 1.0)  # scuffs
st = blotch(st, (214, 196, 170), 0.25, 10, 1.2)  # dust
save('seat', st, 0.5, 0.5)

# ---- concrete (walkways, top band, ends): 6 m x 3 m, joints every 3 m, 64 px/m
P = 64
c = base(3 * P, 6 * P, (180, 177, 170), grain=0.05, mott=0.06, mott_px=40)
vline(c, 0, 2, (120, 118, 112)); vline(c, 3 * P, 2, (120, 118, 112))
save('concrete', c, 6.0, 3.0)
# ---- concourse path: 2 m slabs
c = base(3 * P, 4 * P, (170, 168, 162), grain=0.06, mott=0.05, mott_px=30)
vline(c, 0, 2, (115, 112, 108)); vline(c, 2 * P, 2, (115, 112, 108))
save('path', c, 4.0, 3.0)
# ---- red-brown gravel concourse (decomposed granite) and the dry grass bank
P = 40
gr = base(8 * P, 8 * P, (168, 110, 78), grain=0.12, mott=0.07, mott_px=40)
save('gravel', gr, 8.0, 8.0)
b = base(8 * P, 8 * P, (82, 60, 52), grain=0.10, mott=0.10, mott_px=50)  # dry brown grass outside the bowl, read off ref46 (80,57,52)
save('bank', b, 8.0, 8.0)

# ---- roof deck: grey metal, ribs every 0.3 m running front to back (u = along the stand), 64 px/m
P = 64
r = base(6 * P, int(3 * P), (84, 86, 94), grain=0.03, mott=0.04, mott_px=60)
for k in range(10):
    x = k * 0.3 * P
    vline(r, x, 2, (108, 110, 118)); vline(r, x + 2, 2, (62, 64, 72))
save('roof', r, 3.0, 6.0)
ru = base(6 * P, 6 * P, (112, 114, 120), grain=0.04, mott=0.08)
for k in range(20):  # sheet ribs every 0.3 m
    vline(ru, k * 0.3 * P, 2, (88, 90, 96)); vline(ru, k * 0.3 * P + 2, 1, (136, 138, 144))
for k in range(4):  # purlins every 1.5 m
    hline(ru, k * 1.5 * P, 6, (70, 72, 78)); hline(ru, k * 1.5 * P + 6, 2, (140, 142, 148))
ru = blotch(ru, (90, 84, 78), 0.3, 20, 1.0)
save('roof_under', ru, 6.0, 6.0)

# ---- white concrete walls: panels 3 m x 1.5 m
P = 64
w = base(3 * P, 6 * P, (226, 223, 214), grain=0.03, mott=0.04)
vline(w, 0, 2, (170, 168, 160)); vline(w, 3 * P, 2, (170, 168, 160)); hline(w, 0, 2, (180, 178, 170))
save('white', w, 6.0, 3.0)
# ---- facade blocks: white to 2.1 m, blue window band 2.1-5.4 m with white mullions every 0.9 m, white parapet to 6 m (from the plaza at -2.5)
P = 64; z0 = -2.5; z1 = 6.0
H = int((z1 - z0) * P); W = int(3.6 * P)
f = base(H, W, (226, 223, 214), grain=0.03, mott=0.03)
ya = int((z1 - 5.4) * P); yb = int((z1 - 2.1) * P)  # image rows run top (6 m) to bottom (plaza)
f[ya:yb] = base(yb - ya, W, (48, 74, 152), grain=0.03, mott=0.04)
for k in range(4):
    x = int(k * 0.9 * P)
    f[ya:yb, x:x + int(0.14 * P)] = col((232, 232, 228))[0]
hline(f, ya, 3, (120, 120, 118)); hline(f, yb - 3, 3, (200, 198, 190))
save('facade', np.flipud(f), 3.6, z1 - z0, v0=z0)

# ---- fence: bare painted fence (director: no boards), white panels, joints every 3 m, foot grime
P = 64; H = int(1.15 * P); W = int(24 * P)
fe = base(H, W, (232, 232, 226), grain=0.02, mott=0.03)
for k in range(8):
    x0 = int(k * 3 * P)
    fe[:, x0:x0 + 2] = col((150, 150, 148))[0]
g = np.linspace(0, 1, H)[:, None, None]
fe = fe * (1 - 0.18 * np.clip((g - 0.75) / 0.25, 0, 1))
fe[:int(0.06 * P)] = col((215, 215, 210))[0]; fe[-int(0.08 * P):] = col((90, 90, 90))[0]
save('fence', np.flipud(fe), 24.0, 1.15)

# ---- light tower shaft: concrete, formwork lines every 0.6 m, pour joints every 3 m (u = round the shaft)
P = 64
t = base(6 * P, int(1.8 * P), (176, 176, 178), grain=0.05, mott=0.09, mott_px=40)
for k in range(3):
    vline(t, k * 0.6 * P, 2, (140, 140, 142), 0.8)
for y in (0, 3 * P):  # pour joints with a rain run below each
    hline(t, y, 3, (120, 120, 124))
streaks(t, 10, (120, 118, 116), 0.4)
t = blotch(t, (150, 146, 136), 0.3, 15, 0.9)
save('tower', t, 1.8, 6.0)
# ---- painted steel (end trusses, scoreboard legs): blue
save('steel', steel_tex((58, 88, 168), 2.0, 2.0, P, 1.0), 2.0, 2.0)
# ---- lamp head: grey frame, 4 rows x 10 lamps facing the field
P = 48; W = int(11 * P); H = int(6.5 * P)
L = base(H, W, (150, 150, 156), grain=0.03, mott=0.03)
yy, xx = np.mgrid[0:H, 0:W]
for i in range(4):
    for j in range(10):
        cx = (j + 0.5) * W / 10; cy = (i + 0.5) * H / 4; rr = np.hypot(xx - cx, yy - cy)
        L[rr < 0.42 * P] = col((70, 70, 76))[0]
        L[rr < 0.34 * P] = col((236, 236, 226))[0]
for i in range(5):
    hline(L, i * H / 4, 3, (95, 95, 100))
save('lamp', L, 11.0, 6.5)
# ---- scoreboard: dark face in a white frame
P = 48; W = int(22 * P); H = int(7 * P)
sb = base(H, W, (28, 28, 32), grain=0.03, mott=0.03)
fr = int(0.3 * P)
sb[:fr] = sb[-fr:] = col((232, 232, 228))[0]; sb[:, :fr] = sb[:, -fr:] = col((232, 232, 228))[0]
save('board', sb, 22.0, 7.0)

# ---- flat roofs of the facade blocks: dark grey membrane, 6 m tile, laps every 1 m
P = 48
rf = base(6 * P, 6 * P, (88, 90, 96), grain=0.06, mott=0.10, mott_px=40)
for k in range(6):  # membrane laps every 1 m: a dark seam and the lit lap edge
    hline(rf, k * P, 3, (60, 62, 68)); hline(rf, k * P + 3, 1, (120, 122, 128))
rf = blotch(rf, (120, 116, 106), 0.4, 20, 0.9)  # dried ponding stains
save('roof_flat', rf, 6.0, 6.0)
# ---- rear masts: grey painted steel
save('mast', steel_tex((128, 128, 132), 2.0, 2.0, 64, 1.0), 2.0, 2.0)
# ---- stair flights: concrete, a tread edge every 0.3 m along the flight, 4 m wide tile
P = 64
st = base(int(3 * P), 4 * P, (178, 175, 168), grain=0.05, mott=0.04)
for k in range(10):
    hline(st, k * 0.3 * P, 2, (118, 116, 110)); hline(st, k * 0.3 * P + 2, 1, (205, 202, 196))
save('stairs', st, 4.0, 3.0)
# ---- plaza paving behind the stand: grey asphalt, 10 m tile
P = 32
pa = base(10 * P, 10 * P, (128, 126, 124), grain=0.10, mott=0.025, mott_px=40)
save('asphalt', pa, 10.0, 10.0)
# ---- precast concrete wall: 3 m x 3 m panels, recessed joints, rain streaks under each joint, splash band at the foot
P = 48; WW = 12.0; HH = 12.0
W = int(WW * P); H = int(HH * P)
wl = base(H, W, (214, 210, 200), grain=0.035, mott=0.035, mott_px=50)
yy = np.arange(H)[:, None] / P  # metres down from the top of the tile (tile top = 12 m above the plaza)
for j in range(4):  # horizontal joints every 3 m
    y0 = int(j * 3 * P)
    hline(wl, y0, 3, (140, 137, 130)); hline(wl, y0 + 3, 1, (236, 233, 226))
for i in range(4):  # vertical joints every 3 m
    x0 = int(i * 3 * P)
    vline(wl, x0, 3, (140, 137, 130)); vline(wl, x0 + 3, 1, (236, 233, 226))
# streaks: thin darker runs falling from each horizontal joint, fading over 1-2.5 m
for j in range(4):
    for k in range(int(WW * 3)):
        x = int(rng.uniform(0, W)); w = int(rng.integers(2, 6)); L = rng.uniform(1.0, 2.8) * P; st = rng.uniform(0.10, 0.22)
        y0 = int(j * 3 * P) + 4
        for d in range(int(L)):
            f = st * (1 - d / L)
            for q in range(w):
                wl[(y0 + d) % H, (x + q) % W] *= (1 - f)
# grime at the foot: last 0.6 m above the plaza (bottom of the tile) darker, fading up
foot = np.clip(1 - (HH - yy - 0.0) / 0.9, 0, 1)[..., None] * 0.30
wl *= (1 - foot)
wl *= (1 - 0.10 * np.clip(noise(H, W, 90, 1.0), 0, 1))[..., None]  # broad water stains on the panels
save('wall', wl, WW, HH)
save('wall_z', wl, WW, HH, v0=-2.5)
# ---- stair treads (pale, lit from above) and risers (the shaded upright faces)
save('tread', base(96, 96, (214, 210, 200), grain=0.05, mott=0.04), 1.0, 1.0)
ri = base(96, 96, (158, 155, 148), grain=0.06, mott=0.10)
streaks(ri, 6, (120, 116, 110), 0.35); foot_grime(ri, 0.4, (96, 92, 86), 0.5)
save('riser', ri, 1.0, 1.0)
# ---- turnstile cabinet: painted steel, darker kick plate, a coin-counter window
P = 96; tw = int(1.1 * P); th_ = int(1.0 * P)
ts = base(th_, tw, (92, 108, 96), grain=0.04, mott=0.03)
ts[-int(0.2 * P):] = base(int(0.2 * P), tw, (60, 66, 62), grain=0.05, mott=0.02)
ts[int(0.12 * P):int(0.24 * P), int(0.15 * P):int(0.35 * P)] = col((215, 218, 210))[0]
hline(ts, int(0.12 * P), 2, (40, 44, 42)); hline(ts, int(0.24 * P), 2, (40, 44, 42))
save('turnstile', ts, 1.1, 1.0, v0=-2.5)
# ---- step nosing: dark grey anti-slip strip
no = base(64, 64, (70, 70, 72), grain=0.08, mott=0.06)
for k in range(0, 64, 4):  # anti-slip ribs
    vline(no, k, 1, (40, 40, 42)); vline(no, k + 1, 1, (110, 110, 112))
save('nosing', no, 1.0, 1.0)
# ---- handrail and gate steel
save('rail', steel_tex((150, 152, 156), 1.0, 1.0, 64, 0.5), 1.0, 1.0)
P = 64; gw = int(5 * P); gh = int(2.4 * P)
gt = np.ones((gh, gw, 3)) * col((215, 120, 80))
gt *= (1 + noise(gh, gw, 1.0, 0.02))[..., None]
for k in range(0, gw, int(0.15 * P)):  # vertical bars with gaps (darker behind)
    gt[:, k + int(0.04 * P):k + int(0.15 * P)] *= 0.72
gt[:int(0.1 * P)] = col((200, 105, 68))[0]; gt[-int(0.1 * P):] = col((200, 105, 68))[0]
save('gate', np.flipud(gt), 5.0, 2.4, v0=9.0)
# ---- ground behind the stand: pale concrete pavers, lawn, car park asphalt with bays
P = 48
pv = base(int(6 * P), int(6 * P), (205, 192, 176), grain=0.05, mott=0.05, mott_px=40)
for k in range(10):
    hline(pv, k * 0.6 * P, 1, (170, 158, 144), 0.7); vline(pv, k * 0.6 * P, 1, (170, 158, 144), 0.7)
hline(pv, 0, 2, (150, 140, 128)); vline(pv, 0, 2, (150, 140, 128)); hline(pv, 3 * P, 2, (150, 140, 128)); vline(pv, 3 * P, 2, (150, 140, 128))
save('pavers', pv, 6.0, 6.0)
P = 32
lw = base(int(12 * P), int(12 * P), (64, 90, 66), grain=0.14, mott=0.06, mott_px=60)
dry = (np.clip(noise(int(12 * P), int(12 * P), 110, 1.0), -1, 1) * 0.5 + 0.5)[..., None] * 0.25
lw = lw * (1 - dry) + col((110, 108, 84)) * dry
save('lawn', lw, 12.0, 12.0)
# car park, measured on ref46: pairs of 5 m bays either side of a 4 m grass strip, 7.5 m aisles; a pair every 21.5 m.
# u across the rows (u = 0 at the grass strip's centre), v along the rows (a bay line every 2.5 m)
P = 32; W = int(21.5 * P); H = int(5 * P)
cp = base(H, W, (100, 98, 100), grain=0.10, mott=0.04, mott_px=40)
def ux(m): return int(round(m * P))
gs = base(H, ux(2.0), (86, 112, 58), grain=0.14, mott=0.05)
cp[:, :ux(2.0)] = gs; cp[:, ux(19.5):] = base(H, W - ux(19.5), (86, 112, 58), grain=0.14, mott=0.05)
for x in (ux(2.0), ux(19.5) - 4):  # concrete kerbs round the strip
    cp[:, x:x + 4] = col((190, 186, 178))[0]
for v in (0, int(2.5 * P)):
    cp[v:v + 3, ux(2.0):ux(7.0)] = col((228, 228, 222))[0]; cp[v:v + 3, ux(14.5):ux(19.5)] = col((228, 228, 222))[0]
cp[:, ux(7.0):ux(7.0) + 3] = col((228, 228, 222))[0]; cp[:, ux(14.5) - 3:ux(14.5)] = col((228, 228, 222))[0]
save('carpark', cp, 21.5, 5.0)
json.dump(INDEX, open('tex/index.json', 'w'), indent=1)
print('painted', len(INDEX), sorted(INDEX))
