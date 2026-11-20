# Hand-made textures for Manuka Oval (director 2026-11-18: no photo pixels; photos are reference for colour and layout only).
# Every tile is painted at real scale; TILES records how many metres one tile covers (u, v).
import numpy as np, json, math, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont
rng = np.random.default_rng(7)
OUT = 'tex'; os.makedirs(OUT, exist_ok=True)
TILES = {}

def noise(h, w, s, amp):
    """smooth value noise: random grid of size s px, bilinear-upscaled"""
    g = rng.normal(0, 1, (h // s + 2, w // s + 2)).astype(np.float32)
    im = Image.fromarray(g).resize((w + 2 * s, h + 2 * s), Image.BILINEAR)
    return np.array(im)[s:s + h, s:s + w] * amp

def save(name, arr, mu, mv):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(f'{OUT}/{name}.png'); TILES[name] = (mu, mv)

def wrapnoise(h, w, s, amp):
    # tileable: blend noise with its rolled copy
    n = noise(h, w, s, amp); return (n + np.roll(n, w // 2, 1) + np.roll(n, h // 2, 0) + np.roll(np.roll(n, h // 2, 0), w // 2, 1)) / 2

# ---------- seats: x along the row (0.5 m per seat), y up the rake (0.8 m per row)
SEAT_W, ROW = 0.5, 0.8
def seats(name, pick, nseat=32, nrow=8, ppm=64):
    W, H = int(nseat * SEAT_W * ppm), int(nrow * ROW * ppm)
    img = Image.new('RGB', (W, H), (196, 192, 184)); d = ImageDraw.Draw(img)
    sw, rh = SEAT_W * ppm, ROW * ppm
    for r in range(nrow):
        y0 = H - (r + 1) * rh      # row r counted from the bottom of the tile (v grows up the rake)
        d.rectangle([0, y0 + rh * 0.80, W, y0 + rh], fill=(120, 117, 112))           # step riser in shade
        for s in range(nseat):
            c = np.array(pick(r, s), float); x0 = s * sw
            back = tuple(int(v) for v in c); pan = tuple(int(v) for v in np.clip(c * 1.10 + 6, 0, 255)); sh = tuple(int(v) for v in c * 0.6)
            d.rounded_rectangle([x0 + sw * 0.05, y0 + rh * 0.04, x0 + sw * 0.95, y0 + rh * 0.42], radius=int(sw * 0.12), fill=back)
            d.rectangle([x0 + sw * 0.06, y0 + rh * 0.42, x0 + sw * 0.94, y0 + rh * 0.72], fill=pan)
            d.rectangle([x0 + sw * 0.06, y0 + rh * 0.72, x0 + sw * 0.94, y0 + rh * 0.80], fill=sh)
    a = np.array(img, float) + wrapnoise(H, W, 8, 3)[..., None]
    save(name, a, nseat * SEAT_W, nrow * ROW)

def jit(c, k=10): return np.clip(np.array(c) + rng.normal(0, k, 3), 0, 255)
TEAL = (38, 138, 166)
seats('seats_teal', lambda r, s: jit(TEAL, 6))
seats('seats_white', lambda r, s: jit((236, 236, 232), 4))
seats('seats_red', lambda r, s: jit((186, 44, 42), 6))
# north/west upper tiers: scattered mix read off the reference (mostly dark, red, orange; some white, yellow, teal)
PAL = [((52, 55, 62), .30), ((196, 48, 38), .24), ((228, 118, 36), .18), ((236, 234, 228), .12), ((238, 176, 46), .08), (TEAL, .05), ((120, 60, 90), .03)]
cols = [c for c, _ in PAL]; pw = np.array([p for _, p in PAL]); pw /= pw.sum()
MIX = rng.choice(len(cols), size=(12, 48), p=pw)
seats('seats_multi', lambda r, s: jit(cols[MIX[r, s]], 6), nseat=48, nrow=12)

# ---------- concrete: 2 m slabs with saw joints
def slab(name, base, tile=4.0, joint=2.0, ppm=128, k=5, jcol=-28):
    n = int(tile * ppm); a = np.ones((n, n, 3)) * np.array(base, float)
    a += wrapnoise(n, n, 24, k)[..., None] + wrapnoise(n, n, 3, k * 0.6)[..., None]
    j = int(joint * ppm)
    for p in range(0, n, j): a[p:p + 2] += jcol; a[:, p:p + 2] += jcol
    save(name, a, tile, tile)
slab('conc', (204, 199, 190))
slab('pave', (168, 164, 156), tile=2.4, joint=0.4, k=6, jcol=-22)

# ---------- profiled metal roofs: ribs every 0.25 m running along v
def roof(name, base, tile=4.0, pitch=0.25, ppm=128):
    n = int(tile * ppm); a = np.ones((n, n, 3)) * np.array(base, float)
    x = np.arange(n) / ppm; ph = (x % pitch) / pitch
    prof = np.where(ph < 0.12, 18, np.where(ph < 0.2, -16, 0))          # lit rib face, shaded rib face
    a += prof[None, :, None] + wrapnoise(n, n, 40, 2)[..., None]
    save(name, a, tile, tile)
roof('roof_white', (236, 237, 239))
roof('roof_grey', (128, 133, 140))
roof('roof_pav', (96, 110, 126))

# ---------- painted render / white building walls: 1.2 m panel joints
def wall(name, base, pw_=1.2, ph_=3.0, ppm=128):
    W, H = int(pw_ * 4 * ppm), int(ph_ * ppm); a = np.ones((H, W, 3)) * np.array(base, float)
    a += wrapnoise(H, W, 30, 2)[..., None]
    for p in range(0, W, int(pw_ * ppm)): a[:, p:p + 2] -= 18
    a[:2] -= 18
    save(name, a, pw_ * 4, ph_)
wall('white', (238, 240, 241))
wall('fence', (242, 242, 240), pw_=2.4, ph_=1.2)

# ---------- Media and Function Centre: ebony Stryum boards (160/300 mm) behind bronze louvre blades
def bronze(ppm=160, tw=2.4, th=2.4):
    W, H = int(tw * ppm), int(th * ppm); a = np.ones((H, W, 3)) * np.array((44, 42, 44), float)
    y = 0.0; k = 0
    while y < th:                                   # board joints, alternating 160 and 300 mm
        p = int(y * ppm); a[p:p + 2] = (24, 23, 25); a[p + 2:p + 3] = (70, 68, 70)
        y += 0.16 if k % 2 == 0 else 0.30; k += 1
    for x in np.arange(0, tw, 0.6):                 # louvre support rods
        p = int(x * ppm); a[:, p:p + 4] = (60, 58, 60)
    for z in np.arange(0, th, 0.3):                 # bronze blades: lit top edge, body, shadow under
        p = int(z * ppm); a[p:p + 3] = (148, 112, 74); a[p + 3:p + 9] = (112, 80, 50); a[p + 9:p + 15] = a[p + 9:p + 15] * 0.55
    a += wrapnoise(H, W, 20, 3)[..., None]
    save('bronze', a, tw, th)
bronze()

# ---------- Media Centre (refs: Fairview close-up, Kane aerials): Ebony matt Stryum boards, 160/300 mm alternating
def _ebony(a, ppm, th):
    y = 0.0; k = 0
    while y < th:
        p = int(y * ppm); a[p:p + 2] = (22, 21, 23); a[p + 2:p + 3] = (66, 64, 67)
        y += 0.16 if k % 2 == 0 else 0.30; k += 1
def mc_ebony(ppm=160, tw=2.4, th=2.4):
    W, H = int(tw * ppm), int(th * ppm); a = np.ones((H, W, 3)) * np.array((40, 38, 41), float)
    _ebony(a, ppm, th); a += wrapnoise(H, W, 20, 3)[..., None]; save('mc_ebony', a, tw, th)
mc_ebony()
def mc_field(ppm=64, tw=6.0, th=14.0):
    """oval face: ebony boards with two continuous glass ribbons (z 6.4-8.8 and 10.2-13.0), mullions every 1.5 m"""
    W, H = int(tw * ppm), int(th * ppm); a = np.ones((H, W, 3)) * np.array((40, 38, 41), float)
    _ebony(a, ppm, th); a += wrapnoise(H, W, 20, 3)[..., None]
    for z0, z1 in ((6.4, 8.8), (10.2, 13.0)):
        r0, r1 = H - int(z1 * ppm), H - int(z0 * ppm); v = np.linspace(0, 1, r1 - r0)[:, None, None]
        a[r0:r1] = np.array((120, 140, 156), float) * (1 - v) + np.array((52, 66, 78), float) * v
        for x in np.arange(0, tw, 1.5): q = int(x * ppm); a[r0:r1, q:q + 3] = (28, 28, 30)
        a[r0:r0 + 3] = (28, 28, 30); a[r1 - 3:r1] = (28, 28, 30)
    save('mc_field', a, tw, th)
mc_field()

# ---------- glazing: 1.5 m mullions, transom every 3 m, sky-reflecting glass
def glass(ppm=128, tw=6.0, th=6.0):
    W, H = int(tw * ppm), int(th * ppm); v = np.linspace(0, 1, H)[:, None, None]
    a = np.array((58, 72, 86), float) * (1 - v) + np.array((110, 130, 148), float) * v + np.zeros((H, W, 3))
    for x in np.arange(0, tw, 1.5): p = int(x * ppm); a[:, p:p + 6] = (200, 202, 204)
    for z in np.arange(0, th, 3.0): p = int(z * ppm); a[p:p + 8] = (200, 202, 204)
    save('glass', a, tw, th)
glass()

# ---------- grass: turf with 10 m mowing stripes along world x; hill grass rougher
def grass(name, base, tile=20.0, ppm=24, stripe=10.0, sk=7):
    n = int(tile * ppm); a = np.ones((n, n, 3)) * np.array(base, float)
    a += wrapnoise(n, n, 2, 6)[..., None] * np.array([0.6, 1, 0.5]) + wrapnoise(n, n, 30, 4)[..., None]
    if stripe:
        x = np.arange(n) / ppm; a += np.where((x // stripe) % 2 == 0, sk, -sk)[None, :, None]
    save(name, a, tile, tile)
grass('turf', (114, 120, 66), sk=4)   # olive like the reference, soft mowing stripes
grass('hill', (96, 132, 52), stripe=0)
grass('lawn', (92, 112, 54), stripe=0)

# ---------- steel and dark metal
def plain(name, base, k=4, tile=2.0, ppm=64):
    n = int(tile * ppm); a = np.ones((n, n, 3)) * np.array(base, float) + wrapnoise(n, n, 6, k)[..., None]; save(name, a, tile, tile)
plain('tower', (206, 208, 210))
plain('dark', (58, 61, 66))

# ---------- gate banner (Corroboree Group Oval), drawn by hand: black trapezoid, sunburst, white lettering
def banner(W=628, H=1024):
    bw, tw = 3.139, 1.204
    img = Image.new('RGB', (W, H), (26, 26, 28)); d = ImageDraw.Draw(img)
    save('banner', np.array(img, float), 1, 1); return   # "C: no lettering": blank black panel
    cx, cy = W / 2, H * 0.36; R = W * 0.26
    for i in range(16):
        t = 2 * math.pi * i / 16; ex, ey = cx + R * math.cos(t), cy + R * math.sin(t)
        d.line([cx, cy, ex, ey], fill=(240, 240, 240), width=6)
        col = [(214, 58, 58), (120, 160, 220), (232, 160, 60), (240, 240, 240)][i % 4]
        rr = 14 if i % 2 == 0 else 9; d.ellipse([ex - rr, ey - rr, ex + rr, ey + rr], fill=col)
    d.ellipse([cx - 38, cy - 38, cx + 38, cy + 38], fill=(228, 150, 58))
    def font(sz):
        for f in ('C:/Windows/Fonts/segoeuib.ttf', 'C:/Windows/Fonts/arialbd.ttf'):
            if os.path.exists(f): return ImageFont.truetype(f, sz)
    f1 = font(64); f2 = font(38)
    for txt, y, f in (('Corroboree', H * 0.62, f1), ('Group Oval', H * 0.70, f1), ('M A N U K A', H * 0.79, f2)):
        w = d.textlength(txt, font=f); d.text((cx - w / 2, y), txt, font=f, fill=(245, 245, 245))
    save('banner', np.array(img, float), 1, 1)
banner()
# ---------- south signed buildings (painted from the reference: white facade, "manukaoval" lettering, grey roller doors)
def logo(d, x, ztop, length, ppm, H):
    """manukaoval wordmark fitted to `length` metres (swoosh included): blue swoosh, 'manuka' blue, 'oval' orange"""
    def font(sz):
        for f in ('C:/Windows/Fonts/segoeuib.ttf', 'C:/Windows/Fonts/arialbd.ttf'):
            if os.path.exists(f): return ImageFont.truetype(f, sz)
    sz = 100; f = font(sz); w = d.textlength('manukaoval', font=f) + 2.4 * sz / 1.25 * 0.45
    sz = int(sz * length * ppm / w); f = font(sz); hgt = sz / 1.25 / ppm
    y = H - ztop * ppm; px = x * ppm
    r = hgt * ppm * 0.45; d.arc([px, y + r * 0.3, px + 2 * r, y + r * 0.3 + 2 * r], 150, 390, fill=(28, 92, 170), width=max(3, int(r * 0.35)))
    px += 2.4 * r
    d.text((px, y), 'manuka', font=f, fill=(24, 86, 168)); px += d.textlength('manuka', font=f)
    d.text((px, y), 'oval', font=f, fill=(222, 140, 52)); px += d.textlength('oval', font=f)
    return px / ppm
def cgo(d, x, band, ppm):
    """Corroboree Group Oval lockup in the navy band: sunburst, two lines of white text, 'MANUKA' spaced"""
    def font(sz):
        for f in ('C:/Windows/Fonts/segoeuib.ttf', 'C:/Windows/Fonts/arialbd.ttf'):
            if os.path.exists(f): return ImageFont.truetype(f, sz)
    cx, cy = x * ppm + band * 0.45, band * 0.5; R = band * 0.32
    for i in range(16):
        t = 2 * math.pi * i / 16; ex, ey = cx + R * math.cos(t), cy + R * math.sin(t)
        d.line([cx, cy, ex, ey], fill=(240, 240, 240), width=2)
        col = [(214, 58, 58), (120, 160, 220), (232, 160, 60), (240, 240, 240)][i % 4]; rr = 3 if i % 2 == 0 else 2
        d.ellipse([ex - rr, ey - rr, ex + rr, ey + rr], fill=col)
    d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(228, 150, 58))
    f1 = font(int(band * 0.30)); f2 = font(int(band * 0.16)); tx = cx + R + band * 0.25
    d.text((tx, band * 0.12), 'Corroboree Group Oval', font=f1, fill=(245, 245, 245))
    d.text((tx, band * 0.58), 'M A N U K A', font=f2, fill=(220, 220, 220))
def facade_tex(name, L, Hm, doors, logos, ppm=64):
    W, H = int(L * ppm), int(Hm * ppm)
    a = np.ones((H, W, 3)) * np.array((240, 241, 242), float) + wrapnoise(H, W, 20, 2)[..., None]
    for p in range(0, W, int(1.2 * ppm)): a[:, p:p + 2] -= 12          # wall panel joints
    a[:int(0.25 * ppm)] = (70, 74, 80)                                  # dark coping / deck edge
    a[H - int(0.3 * ppm):] = (150, 152, 152)                            # plinth
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(img)
    for x0, x1, z0, z1 in doors:                                        # grey roller doors with slats
        d.rectangle([x0 * ppm, H - z1 * ppm, x1 * ppm, H - z0 * ppm], fill=(176, 182, 188))
        for z in np.arange(z0, z1, 0.1): d.line([x0 * ppm, H - z * ppm, x1 * ppm, H - z * ppm], fill=(160, 166, 172), width=1)
        d.rectangle([x0 * ppm, H - z1 * ppm, x1 * ppm, H - z0 * ppm], outline=(120, 124, 128), width=2)
    band = int(1.4 * ppm); d.rectangle([0, 0, W, band], fill=(28, 34, 58))   # navy fascia band, top 1.4 m
    # director 2026-11-18 "C: no lettering": the navy band stays, blank (no lockup)
    save(name, np.array(img, float), 1, 1)
# sign building: 27.8 m long, 7.5 m; reference px 840..1100 -> metres via the traced base points; doors 15.0-18.6 and 22.4-25.6 m
facade_tex('sign_bld', 27.80, 7.5, [(15.0, 18.6, 0.6, 4.9), (22.4, 25.6, 0.6, 4.9)], [(4.2, 6.9, 6.5), (16.2, 6.9, 6.5)])
facade_tex('se_bld', 50.40, 5.0, [], [(4.6, 4.6, 6.5)])
json.dump(TILES, open(f'{OUT}/tiles.json', 'w'), indent=0)
# ---------- pavilion walls: white ground floor with dark windows, upper verandah (white posts, balustrade), white fascia
def pav_wall(ppm=64, tw=6.0, th=7.0):
    W, H = int(tw * ppm), int(th * ppm); a = np.ones((H, W, 3)) * np.array((238, 239, 238), float) + wrapnoise(H, W, 16, 2)[..., None]
    Z = lambda z: H - int(z * ppm)
    for z in np.arange(0, 3.0, 0.15): a[Z(z) - 1:Z(z)] -= 14                  # weatherboards
    for x in (0.75, 3.75): a[Z(2.6):Z(0.6), int(x * ppm):int((x + 1.5) * ppm)] = (52, 60, 70)   # windows
    a[Z(6.2):Z(3.0)] = (70, 72, 74)                                          # verandah recess in shade
    for x in (0.0, 3.0): a[Z(6.2):Z(3.0), int(x * ppm):int(x * ppm) + 10] = (236, 236, 234)  # posts
    a[Z(4.1):Z(4.0)] = (236, 236, 234)
    for x in np.arange(0, tw, 0.12): a[Z(4.0):Z(3.0), int(x * ppm):int(x * ppm) + 2] = (220, 220, 218)  # balusters
    a[Z(7.0):Z(6.2)] = (244, 244, 242); a[Z(6.2):Z(6.2) + 3] = (150, 150, 150)
    save('pav_wall', a, tw, th)
pav_wall()
json.dump(TILES, open(f'{OUT}/tiles.json', 'w'), indent=0)
print(TILES)

# north upper tier east of 88 deg: mostly navy with scattered red and orange (reference z/ref_navy.png)
NPAL = [((24, 30, 56), .62), ((52, 55, 62), .10), ((178, 50, 40), .14), ((220, 112, 40), .10), ((230, 228, 222), .04)]
ncols = [c for c, _ in NPAL]; npw = np.array([p for _, p in NPAL]); npw /= npw.sum()
NMIX = rng.choice(len(ncols), size=(12, 48), p=npw)
seats('seats_navy', lambda r, s: jit(ncols[NMIX[r, s]], 5), nseat=48, nrow=12)
# ---------- stair aisles: light concrete, a tread every 0.4 m up the rake with a pale nosing line
def stairs(ppm=128, tw=1.2, th=1.6):
    W, H = int(tw * ppm), int(th * ppm)
    a = np.ones((H, W, 3)) * np.array((182, 178, 170), float) + wrapnoise(H, W, 6, 4)[..., None]
    for z in np.arange(0, th, 0.4):
        p = int(z * ppm); a[p:p + 10] -= 34; a[p + 10:p + 16] = (236, 232, 222)
    save('stairs', a, tw, th)
stairs()
plain('canopy', (222, 225, 228))   # west stand canopies: light grey sheeting
# ---------- light-tower head: lamp grid on a grey frame (whole head = one tile, uv 0..1)
def lamps(W=512, H=1024, rows=9, cols=11):
    img = Image.new('RGB', (W, H), (150, 152, 156)); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W - 1, H - 1], outline=(200, 202, 204), width=10)
    for r in range(rows):
        y = H * (0.12 + 0.82 * r / (rows - 1)); d.line([0, y + 22, W, y + 22], fill=(110, 112, 116), width=6)
        for c in range(cols):
            x = W * (0.06 + 0.88 * c / (cols - 1)); rr = 19
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(70, 72, 78)); d.ellipse([x - rr + 5, y - rr + 5, x + rr - 5, y + rr - 5], fill=(244, 244, 238))
    save('lamps', np.array(img, float), 1, 1)
lamps()
json.dump(TILES, open(f'{OUT}/tiles.json', 'w'), indent=0)

# ---------- tree foliage: leaf clusters painted as small lit/shaded blobs (three tints read off the reference)
def leaves(name, base, ppm=48, tile=4.0):
    n = int(tile * ppm); img = Image.new('RGB', (n, n), tuple(int(c * 0.55) for c in base)); d = ImageDraw.Draw(img)
    for _ in range(int(n * n / 30)):
        x, y = rng.uniform(0, n, 2); r = rng.uniform(2, 6); k = rng.uniform(0.7, 1.25)
        d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(min(255, c * k)) for c in base))
    save(name, np.array(img, float) + wrapnoise(n, n, 4, 4)[..., None], tile, tile)
leaves('leaf_bright', (104, 150, 40))
leaves('leaf_pale', (138, 128, 104))   # dusty deodar cedars
leaves('leaf_dark', (64, 92, 48))
plain('bark', (96, 84, 72))
plain('asphalt', (74, 76, 80), k=5, tile=4.0)
slab('gravel', (150, 110, 84), tile=4.0, joint=4.0, k=7, jcol=0)
json.dump(TILES, open(f'{OUT}/tiles.json', 'w'), indent=0)
