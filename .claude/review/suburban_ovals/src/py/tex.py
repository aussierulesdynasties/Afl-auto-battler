"""Hand-made (procedural) textures for the six generic suburban ovals.
No photo pixels: every texel is drawn here. Colours are daylight material colours.
    python tex.py OUTDIR
Each texture records its real-world size in TEX_M (metres across one tile) so the
Blender builder can set UVs at true scale.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1] if len(sys.argv) > 1 else "tex"
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)
TEX_M = {}


def noise(n, scale, octaves=3, seed=0):
    """Tileable value noise in 0..1 (bilinear upsample of wrapped random grids)."""
    r = np.random.default_rng(seed)
    acc = np.zeros((n, n)); amp = 1.0; tot = 0
    for o in range(octaves):
        g = max(2, int(scale * 2 ** o))
        grid = r.random((g, g))
        xs = np.arange(n) * g / n
        i0 = np.floor(xs).astype(int); f = xs - i0; i1 = (i0 + 1) % g; i0 %= g
        f = f * f * (3 - 2 * f)
        a = grid[np.ix_(i0, i0)] * (1 - f)[None, :] + grid[np.ix_(i0, i1)] * f[None, :]
        b = grid[np.ix_(i1, i0)] * (1 - f)[None, :] + grid[np.ix_(i1, i1)] * f[None, :]
        acc += amp * (a * (1 - f)[:, None] + b * f[:, None]); tot += amp; amp *= 0.5
    return acc / tot


def save(name, arr, metres, mode="RGB"):
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    Image.fromarray(arr, mode).save(os.path.join(OUT, name + ".png"))
    TEX_M[name] = metres


def tint(base, var, n, s=4, seed=1, oct=3):
    v = noise(n, s, oct, seed)[..., None] - 0.5
    return np.array(base, float)[None, None, :] * (1 + var * v)


# ---------- ground ----------
def grass(name, base, stripes, n=1024, metres=16.0, seed=3):
    a = tint(base, 0.22, n, 6, seed, 4)
    fine = (rng.random((n, n)) - 0.5)[..., None] * 18
    a += fine
    if stripes:  # mower stripes 4 m wide along v
        x = np.arange(n) * metres / n
        band = ((x // 4.0) % 2)[None, :, None]
        a *= 1 + 0.025 * (band * 2 - 1)
    save(name, a, metres)


grass("turf", (84, 128, 54), True, metres=16.0)
grass("turf_dry", (112, 132, 62), False, metres=16.0, seed=5)   # bank / surround grass, drier
grass("turf_tropic", (64, 124, 50), True, metres=16.0, seed=8)


def earth(name, base, n=1024, metres=8.0, seed=11):
    a = tint(base, 0.25, n, 8, seed, 4) + (rng.random((n, n)) - 0.5)[..., None] * 26
    pebble = rng.random((n, n)) > 0.993
    a[pebble] = np.array(base) * 1.35
    save(name, a, metres)


earth("red_earth", (168, 82, 46))
earth("gravel", (150, 140, 124), seed=12)


def asphalt(n=1024, metres=8.0):
    a = tint((62, 63, 64), 0.18, n, 10, 21, 4) + (rng.random((n, n)) - 0.5)[..., None] * 40
    save("asphalt", a, metres)


asphalt()


def concrete(name="concrete", base=(186, 182, 172), n=1024, metres=4.0, joint=2.0):
    a = tint(base, 0.10, n, 6, 31, 4) + (rng.random((n, n)) - 0.5)[..., None] * 10
    px = int(n * joint / metres)
    a[:, ::px] *= 0.62; a[::px, :] *= 0.62
    save(name, a, metres)


concrete()

# ---------- walls ----------
def brick(name, brick_col, mortar, n=1024, metres=2.4, spread=0.13, seed=41):
    """Stretcher bond, 230 x 76 mm bricks, 10 mm joints."""
    ppm = n / metres
    a = np.zeros((n, n, 3)); a[:] = mortar
    a += (rng.random((n, n)) - 0.5)[..., None] * 10
    r = np.random.default_rng(seed)
    bh, bw, j = 0.086 * ppm, 0.240 * ppm, 0.010 * ppm
    rows = int(round(n / bh)); bh = n / rows
    cols = int(round(n / bw)); bw = n / cols
    grain = noise(n, 40, 2, seed + 1)
    for ri in range(rows):
        off = (bw / 2) * (ri % 2)
        y0 = int(ri * bh + j / 2); y1 = int((ri + 1) * bh - j / 2)
        for ci in range(-1, cols + 1):
            x0 = int(ci * bw + off + j / 2); x1 = int((ci + 1) * bw + off - j / 2)
            c = np.array(brick_col, float) * (1 + spread * (r.random() * 2 - 1))
            c *= np.array([1 + 0.05 * (r.random() - .5), 1, 1 + 0.05 * (r.random() - .5)])
            for xa, xb in ((x0, x1), (x0 - n, x1 - n), (x0 + n, x1 + n)):
                xa2, xb2 = max(xa, 0), min(xb, n)
                if xb2 > xa2:
                    a[y0:y1, xa2:xb2] = c * (0.9 + 0.2 * grain[y0:y1, xa2:xb2, None])
    save(name, a, metres)


brick("brick_red", (150, 66, 44), (196, 190, 176))
brick("brick_cream", (214, 192, 152), (200, 196, 186), seed=43)
brick("brick_brown", (112, 70, 50), (176, 168, 156), seed=45)


def boards(name, col, n=1024, metres=1.2, board=0.15, vertical=False, gap_dark=0.55, grainv=0.06, seed=51):
    """Painted weatherboard / timber boards. Each board has a shadow line under its lap."""
    ppm = n / metres; bp = board * ppm
    a = np.zeros((n, n, 3)); a[:] = col
    a *= 1 + grainv * (noise(n, 3, 3, seed)[..., None] - .5)
    t = np.arange(n) % bp / bp
    shade = np.where(t > 0.9, gap_dark, 1 - 0.10 * t)  # lap shadow and slight slope
    if vertical:
        a *= shade[None, :, None]
    else:
        a *= shade[:, None, None]
    a += (rng.random((n, n)) - 0.5)[..., None] * 6
    save(name, a, metres)


boards("weatherboard_white", (236, 234, 226))
boards("weatherboard_cream", (232, 220, 186), seed=52)
boards("timber_old", (150, 116, 80), metres=1.2, board=0.15, vertical=True, gap_dark=0.45, grainv=0.25, seed=53)
boards("timber_green", (44, 86, 56), metres=1.2, board=0.15, vertical=True, gap_dark=0.5, grainv=0.12, seed=54)
boards("timber_deck", (128, 98, 70), metres=1.2, board=0.14, vertical=False, gap_dark=0.35, grainv=0.3, seed=55)


def corrugated(name, col, n=512, metres=1.52, pitch=0.076):
    """Corrugated / Colorbond sheet: sinusoidal ribs at 76 mm along u, lit from above."""
    x = np.arange(n) * metres / n
    s = 0.86 + 0.16 * np.sin(2 * math.pi * x / pitch)
    a = np.zeros((n, n, 3)); a[:] = col
    a *= s[None, :, None]
    a *= 1 + 0.03 * (noise(n, 2, 2, 61)[..., None] - .5)
    save(name, a, metres)


corrugated("iron_zinc", (186, 190, 192))
corrugated("iron_green", (62, 92, 70))      # Colorbond Cottage Green
corrugated("iron_red", (122, 44, 38))       # Manor Red
corrugated("iron_blue", (52, 74, 102))      # Deep Ocean
corrugated("iron_grey", (96, 100, 104))     # Woodland Grey
corrugated("iron_cream", (222, 212, 180))   # Classic Cream
corrugated("iron_rust", (150, 102, 72))


def cladding(name, col, n=512, metres=2.4, panel=1.2, seam=0.01):
    a = np.zeros((n, n, 3)); a[:] = col
    a *= 1 + 0.04 * (noise(n, 3, 2, 71)[..., None] - .5)
    p = int(n * panel / metres); w = max(2, int(n * seam / metres))
    for k in range(0, n, p):
        a[:, k:k + w] *= 0.55; a[k:k + w, :] *= 0.55
    save(name, a, metres)


cladding("clad_charcoal", (60, 62, 66))
cladding("clad_white", (226, 228, 228))
cladding("clad_timber", (166, 120, 78), panel=0.6)


def glass(name, n=1024, metres=4.8, bay=1.6, storey=3.2, tintc=(70, 96, 118)):
    """Glass curtain wall: sky reflection gradient (light top, darker bottom), dark mullions, transom."""
    ppm = n / metres
    y = np.arange(n) / n
    a = np.zeros((n, n, 3))
    sky = np.array([150, 176, 198], float); deep = np.array(tintc, float)
    within = (np.arange(n) * metres / n) % storey / storey
    mix = within[:, None, None]
    a[:] = sky * (1 - mix) * 0.85 + deep * mix
    # diagonal reflection streaks
    xx, yy = np.meshgrid(np.arange(n), np.arange(n))
    a *= (1 + 0.08 * np.sin((xx + yy) / n * 2 * math.pi * 2))[..., None]
    mw = max(3, int(0.06 * ppm))
    for k in np.arange(0, metres, bay):
        c = int(k * ppm); a[:, c:c + mw] = (52, 54, 58)
    for k in np.arange(0, metres, storey):
        c = int(k * ppm); a[c:c + int(0.25 * ppm), :] = (58, 60, 64)
    save(name, a, metres)


glass("glass_curtain")


def window_wall(name, wall, n=1024, metres=4.0, win_w=1.6, win_h=1.2, sill=1.0):
    """A wall texture tile carrying one aluminium window (for clubrooms). Height = metres (one storey 4 m)."""
    src = np.array(Image.open(os.path.join(OUT, wall + ".png")).convert("RGB").resize((n, n)), float)
    ppm = n / metres
    x0 = int((metres - win_w) / 2 * ppm); x1 = int((metres + win_w) / 2 * ppm)
    yb = n - int(sill * ppm); yt = n - int((sill + win_h) * ppm)
    f = max(3, int(0.05 * ppm))
    src[yt - f:yb + f, x0 - f:x1 + f] = (200, 202, 204)       # aluminium frame
    gy = np.linspace(0, 1, yb - yt)[:, None, None]
    src[yt:yb, x0:x1] = np.array([60, 78, 94]) * (1 - gy) + np.array([30, 36, 44]) * gy
    src[yt:yb, (x0 + x1) // 2 - f // 2:(x0 + x1) // 2 + f // 2] = (200, 202, 204)
    src[yb + f:yb + 2 * f, x0 - 2 * f:x1 + 2 * f] = (170, 170, 166)  # sill
    save(name, src, metres)


window_wall("brick_red_window", "brick_red")
window_wall("brick_cream_window", "brick_cream")
window_wall("weatherboard_window", "weatherboard_white")


def roller_door(name, col=(206, 206, 200), n=512, metres=3.0):
    a = np.zeros((n, n, 3)); a[:] = col
    t = (np.arange(n) * metres / n) % 0.08 / 0.08
    a *= (0.85 + 0.15 * np.sin(t * 2 * math.pi))[:, None, None]
    save(name, a, metres)


roller_door("roller_door")


# ---------- seating ----------
def seats(name, col, n=1024, metres=4.0, tread=0.8, seat_w=0.5, back=True):
    """Plastic tip-up seats on concrete treads, tread depth along v."""
    ppm = n / metres
    a = np.zeros((n, n, 3)); a[:] = (176, 172, 164)
    a *= 1 + 0.06 * (noise(n, 6, 3, 81)[..., None] - .5)
    tp = tread * ppm; sp = seat_w * ppm
    for r in range(int(metres / tread) + 1):
        y0 = int(r * tp); a[y0:y0 + max(2, int(0.02 * ppm)), :] *= 0.55   # riser shadow
        ys0 = int(y0 + 0.12 * ppm); ys1 = int(y0 + (0.48 if back else 0.32) * ppm)
        for c in range(int(metres / seat_w) + 1):
            x0 = int(c * sp + 0.05 * ppm); x1 = int((c + 1) * sp - 0.05 * ppm)
            a[ys0:ys1, x0:x1] = np.array(col) * (1 + 0.04 * rng.standard_normal())
            a[ys0:ys0 + int(0.06 * ppm), x0:x1] = np.array(col) * 1.18     # top edge highlight
    save(name, a, metres)


seats("seats_maroon", (128, 30, 38))
seats("seats_blue", (34, 70, 140))
seats("seats_green", (30, 104, 62))
seats("seats_white", (224, 226, 226))


def bench_timber(name="bench_timber", n=1024, metres=4.0, tread=0.8):
    """Old grandstand: timber bench planks on timber treads (stepped)."""
    ppm = n / metres
    a = np.zeros((n, n, 3)); a[:] = (120, 92, 64)
    a *= 1 + 0.2 * (noise(n, 20, 2, 91)[..., None] - .5)
    for r in range(int(metres / tread) + 1):
        y0 = int(r * tread * ppm)
        a[y0:y0 + 3, :] *= 0.5
        for k in range(3):
            yy = int(y0 + (0.1 + k * 0.1) * ppm)
            a[yy:yy + int(0.085 * ppm), :] = np.array((176, 150, 108)) * (1 + 0.1 * (noise(n, 30, 2, 92 + k)[yy:yy + int(0.085 * ppm), :, None] - .5))
    save(name, a, metres)


bench_timber()


# ---------- fences and alpha cards ----------
def picket(n=512, metres=1.2, h=1.0, col=(242, 242, 236)):
    """White picket fence, RGBA, height h in a square of `metres`."""
    ppm = n / metres
    a = np.zeros((n, n, 4))
    pw = 0.07 * ppm; pitch = 0.12 * ppm
    top = n - int(h * ppm)
    for k in range(int(n / pitch) + 1):
        x0 = int(k * pitch); x1 = int(k * pitch + pw)
        a[top + int(0.03 * ppm):, x0:x1, :3] = col; a[top + int(0.03 * ppm):, x0:x1, 3] = 255
        cx = (x0 + x1) / 2
        for yy in range(top, top + int(0.03 * ppm)):   # pointed top
            half = (yy - top) / (0.03 * ppm) * pw / 2
            a[yy, int(cx - half):int(cx + half) + 1, :3] = col; a[yy, int(cx - half):int(cx + half) + 1, 3] = 255
        a[top:, x1:x1 + 2, :3] = np.array(col) * 0.7     # shadow edge
    for rail in (0.25, 0.8):                             # rails
        y = n - int(rail * ppm)
        a[y:y + int(0.06 * ppm), :, :3] = np.array(col) * 0.86; a[y:y + int(0.06 * ppm), :, 3] = 255
    save("picket", a, metres, "RGBA")


picket()


def pipe_rail(n=512, metres=1.2, col=(236, 236, 230)):
    """Boundary pipe-rail fence: two white rails on posts (country / council)."""
    ppm = n / metres
    a = np.zeros((n, n, 4))
    for rail, th in ((1.0, 0.06), (0.55, 0.05)):
        y = n - int(rail * ppm)
        g = np.linspace(1.1, 0.7, int(th * ppm))[:, None, None]
        a[y:y + int(th * ppm), :, :3] = np.array(col) * g; a[y:y + int(th * ppm), :, 3] = 255
    x0 = int(0.55 * ppm); a[n - int(1.03 * ppm):, x0:x0 + int(0.06 * ppm), :3] = col; a[n - int(1.03 * ppm):, x0:x0 + int(0.06 * ppm), 3] = 255
    save("pipe_rail", a, metres, "RGBA")


pipe_rail()


def chainlink(n=512, metres=1.0, col=(150, 154, 156)):
    ppm = n / metres
    a = np.zeros((n, n, 4))
    cell = 0.06 * ppm
    xx, yy = np.meshgrid(np.arange(n), np.arange(n))
    p1 = (xx + yy) % cell; p2 = (xx - yy) % cell          # distance (along the diagonal) to the nearest wire
    d1 = np.minimum(p1, cell - p1) / 1.414; d2 = np.minimum(p2, cell - p2) / 1.414
    m = np.minimum(d1, d2) < 1.3
    a[m, :3] = col; a[m, 3] = 255
    save("chainlink", a, metres, "RGBA")


chainlink()


def gum_leaves(name, base=(92, 110, 70), n=1024, seed=101, silver=0.0):
    """Eucalypt crown card: clumps of narrow drooping leaves, RGBA (transparent gaps). 8 m across."""
    r = np.random.default_rng(seed)
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx, cy = n / 2, n / 2
    cy = n * 0.44
    for _ in range(230):  # clumps inside an irregular crown that fills most of the card
        ang = r.uniform(0, 2 * math.pi); rad = math.sqrt(r.uniform(0, 1)) * 0.44 * n * (0.8 + 0.2 * math.sin(3 * ang))
        x = cx + rad * math.cos(ang); y = cy + rad * math.sin(ang) * 0.8
        shade = 0.78 + 0.3 * (cy - y) / n   # top of the crown catches more light
        for _ in range(60):
            lx = x + r.normal(0, 26); ly = y + r.normal(0, 20)
            L = r.uniform(16, 32); a = r.uniform(math.pi * 0.35, math.pi * 0.65)  # drooping
            k = r.uniform(0.62, 1.15) * shade
            c = tuple(int(min(255, v * k + silver * 60)) for v in base) + (255,)
            d.line([(lx, ly), (lx + L * math.cos(a), ly + L * math.sin(a))], fill=c, width=int(r.uniform(3, 5)))
    # a few visible branches
    for _ in range(0):   # branches come from the 3D limbs, not the card
        a = r.uniform(-2.6, -0.5); L = r.uniform(0.15, 0.35) * n
        d.line([(cx, n * 0.98), (cx + L * math.cos(a), n * 0.98 + L * math.sin(a))], fill=(200, 190, 170, 255), width=7)
    save(name, np.array(im, float), 8.0, "RGBA")


gum_leaves("gum_leaves")
gum_leaves("gum_leaves_b", base=(104, 118, 82), seed=103, silver=0.25)
gum_leaves("pine_leaves", base=(46, 74, 44), seed=105)   # cypress windbreak


def palm_frond(n=1024, seed=111):
    """Coconut / royal palm crown seen side-on: arching fronds with leaflets. RGBA, 8 m across."""
    r = np.random.default_rng(seed)
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    # ONE frond, laid along v (top = base at the crown, bottom = tip): build.py bends it as a strip.
    cx = n / 2
    for y in range(4, n - 4, 15):
        t = y / n
        half = n * 0.46 * math.sin(math.pi * (0.08 + 0.84 * t))   # leaflets longest mid-frond
        g = int(r.uniform(95, 135))
        for s in (-1, 1):
            ex = cx + s * half; ey = y + half * 0.55                     # leaflets sweep toward the tip
            d.line([(cx, y), (ex, ey)], fill=(46, g, 48, 255), width=4)
            d.line([(cx, y + 2), (ex, ey + 2)], fill=(34, int(g * 0.8), 38, 255), width=2)
    d.line([(cx, 0), (cx, n)], fill=(150, 140, 80, 255), width=9)          # midrib
    save("palm_frond", np.array(im, float), 8.0, "RGBA")


palm_frond()


def bark(name, base, n=512, metres=1.0, seed=121, streak=True):
    a = tint(base, 0.25, n, 4, seed, 3)
    if streak:
        v = noise(n, 30, 2, seed + 1)
        a *= (0.85 + 0.3 * v[:, :1].T)[..., None] if False else (0.85 + 0.3 * np.repeat(v[:1, :], n, 0))[..., None]
    save(name, a, metres)


bark("bark_gum", (214, 206, 190))           # smooth pale gum bark
bark("bark_dark", (92, 76, 62), seed=123)
bark("palm_trunk", (150, 136, 116), seed=125)


# ---------- scoreboards and signs ----------
def font(px):
    for f in ("arialbd.ttf", "C:/Windows/Fonts/arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(f, px)
        except Exception:
            pass
    return ImageFont.load_default()


LETTERS = False   # director 2026-11-18 "C: no lettering": words off every board; score digits stay


def scoreboard_manual(n=1024):
    """Old manual scoreboard face, 8 m x 4 m: painted dark green, white headings, black number boards."""
    W, H = n, n // 2
    im = Image.new("RGB", (W, H), (32, 72, 46)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W - 1, H - 1], outline=(236, 236, 230), width=8)
    f1 = font(40); f2 = font(26); f3 = font(64)
    if LETTERS: d.text((W * 0.05, H * 0.08), "HOME", font=f1, fill=(240, 240, 232))
    if LETTERS: d.text((W * 0.05, H * 0.55), "AWAY", font=f1, fill=(240, 240, 232))
    cols = ["GOALS", "BEHINDS", "TOTAL"]
    for i, c in enumerate(cols):
        x = W * (0.32 + i * 0.22)
        if LETTERS: d.text((x, H * 0.02), c, font=f2, fill=(240, 240, 232))
        for row, val in ((0, ("7", "9", "51")), (1, ("5", "11", "41"))):
            y = H * (0.14 + row * 0.47)
            d.rectangle([x, y, x + W * 0.17, y + H * 0.33], fill=(20, 20, 20), outline=(220, 220, 214), width=3)
            d.text((x + W * 0.05, y + H * 0.06), val[i], font=f3, fill=(246, 246, 240))
    if LETTERS: d.text((W * 0.05, H * 0.42), "QTR", font=f2, fill=(240, 220, 120))
    for q in range(4):
        x = W * (0.14 + q * 0.04); d.rectangle([x, H * 0.42, x + W * 0.03, H * 0.48], fill=(240, 220, 120) if q < 3 else (20, 20, 20))
    save("scoreboard_manual", np.array(im, float), 8.0)


scoreboard_manual()


def scoreboard_led(n=1024):
    """Small modern LED scoreboard, 8 m x 4 m: black panel, amber/white digits."""
    W, H = n, n // 2
    im = Image.new("RGB", (W, H), (14, 14, 16)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W - 1, H - 1], outline=(70, 72, 76), width=10)
    f1 = font(46); f3 = font(90)
    if LETTERS: d.text((W * 0.06, H * 0.12), "HOME", font=f1, fill=(240, 240, 240))
    if LETTERS: d.text((W * 0.06, H * 0.58), "AWAY", font=f1, fill=(240, 240, 240))
    for row, s in ((0, "7.9  51"), (1, "5.11 41")):
        d.text((W * 0.40, H * (0.06 + row * 0.47)), s, font=f3, fill=(255, 186, 40))
    save("scoreboard_led", np.array(im, float), 8.0)


scoreboard_led()


def sign(name, text, bg, fg, n=1024, aspect=6, metres=12.0):
    W, H = n, n // aspect
    im = Image.new("RGB", (W, H), bg); d = ImageDraw.Draw(im)
    f = font(int(H * 0.55))
    tw = d.textlength(text, font=f)
    d.text(((W - tw) / 2, H * 0.2), text, font=f, fill=fg)
    save(name, np.array(im, float), metres)


sign("sign_club", "FOOTBALL CLUB", (240, 240, 236), (30, 50, 110))
sign("sign_sponsor1", "LOCAL HARDWARE", (210, 40, 36), (255, 255, 255))
sign("sign_sponsor2", "BAKERY  •  BUTCHER", (24, 70, 140), (255, 255, 255))
sign("sign_sponsor3", "MOTORS", (250, 200, 30), (20, 20, 20))
sign("sign_sponsor4", "HOTEL", (20, 110, 60), (255, 255, 255))

# shade sail fabric
def sail(name, col, n=256):
    a = np.zeros((n, n, 3)); a[:] = col
    xx, yy = np.meshgrid(np.arange(n), np.arange(n))
    a *= (0.94 + 0.06 * (((xx // 3) + (yy // 3)) % 2))[..., None]   # knitted HDPE weave
    save(name, a, 0.5)


sail("sail_white", (236, 236, 230))
sail("sail_sand", (214, 196, 156))
sail("sail_teal", (40, 132, 134))

# goal post padding (generic blue) and white paint
for nm, c in (("pad_blue", (30, 70, 150)), ("pad_red", (180, 30, 36)), ("white_paint", (244, 244, 240)),
              ("steel_grey", (128, 132, 136)), ("dark_metal", (46, 48, 52)), ("black_rubber", (26, 26, 28))):
    a = np.zeros((64, 64, 3)); a[:] = c; a *= 1 + 0.02 * (rng.random((64, 64, 1)) - .5)
    save(nm, a, 1.0)


# ---------- added for type 4 (Euroa): painted concrete block, pale blue iron, doors ----------
def block(name, col, n=1024, metres=2.4, bw=0.39, bh=0.19, j=0.010, seed=141):
    """Painted concrete (Besser) block, 390 x 190 mm, stretcher bond, painted over so joints are shallow."""
    ppm = n / metres
    a = np.zeros((n, n, 3)); a[:] = col
    a *= 1 + 0.035 * (noise(n, 24, 3, seed)[..., None] - .5)
    a += (rng.random((n, n)) - 0.5)[..., None] * 7
    rows = int(round(metres / bh)); ph = n / rows
    cols = int(round(metres / bw)); pw = n / cols
    jw = max(2, int(j * ppm))
    for ri in range(rows):
        y = int(ri * ph); a[y:y + jw, :] *= 0.80; a[y + jw:y + jw + 1, :] *= 1.04
        off = (pw / 2) * (ri % 2)
        for ci in range(-1, cols + 1):
            x = int(ci * pw + off) % n; y1 = int((ri + 1) * ph)
            a[y:y1, x:x + jw] *= 0.82
    save(name, a, metres)


block("block_grey", (176, 180, 180))
block("block_greyblue", (178, 186, 190), seed=143)
window_wall("block_grey_window", "block_grey", win_w=2.4, win_h=1.0, sill=1.9)
corrugated("iron_skyblue", (112, 138, 172))   # pale steel-blue Colorbond (Euroa stand and wing roofs)


def door(name, col=(240, 240, 236), frame=(150, 152, 150), n=256):
    """Flush door, 1 x 2.1 m, filling the quad (uvrect 0..1): frame, kick plate, lever handle."""
    a = np.zeros((n * 2, n, 3)); a[:] = col
    a *= 1 + 0.02 * (rng.random((n * 2, n, 1)) - .5)
    f = 10
    a[:f, :] = frame; a[:, :f] = frame; a[:, -f:] = frame
    a[-int(n * 0.28):, f:-f] *= 0.93                    # kick plate
    hy = n; a[hy - 6:hy + 6, int(n * 0.70):int(n * 0.86)] = (70, 72, 74)   # lever
    save(name, a, 1.0)


door("door_white")
door("door_black", col=(38, 40, 42), frame=(90, 92, 94))

json.dump(TEX_M, open(os.path.join(OUT, "tex_m.json"), "w"), indent=1)
print(len(TEX_M), "textures")
