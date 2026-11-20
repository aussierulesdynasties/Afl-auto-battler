# Hand-made textures for Cazaly's Stadium (Cairns, 2022-24), painted in code: no photo pixels. TILE[name] = metres per tile (u, v).
# Colours are read off the Commons photos (ref/) and the Google Earth captures (ge/); every pattern is drawn here.
import numpy as np, json, math, os
from PIL import Image, ImageDraw, ImageFont
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


def concrete(name, col, pu=3.0, pv=1.5, tile=(6.0, 6.0), streak=0.12):
    h = w = N; a = base(h, w, col, 5, 20); xu = N / tile[0]; yv = N / tile[1]
    for k in range(int(tile[0] / pu)): a[:, int(k * pu * xu):int(k * pu * xu) + 4] *= 0.66
    for k in range(int(tile[1] / pv)): a[int(k * pv * yv):int(k * pv * yv) + 4] *= 0.66
    weather(a, streak, 16, 70); save(name, a, tile)


def deck(name, col, pitch=0.3, tile=(6.0, 6.0), grime=18):
    """ribbed roof sheeting: ribs every 'pitch' m across u, a sheet lap at the top, dirt runs down the pans"""
    h = w = N; x = np.arange(w) / w * (tile[0] / pitch)
    rib = np.where((x % 1) < 0.16, 0.74, 1.0) + 0.05 * np.cos(2 * math.pi * x)
    a = np.ones((h, w, 3)) * np.array(col, float) * rib[None, :, None] + fine(h, w, 2)[:, :, None] + noise(h, w, 10, grime)[:, :, None]
    a[0:5] *= 0.72
    for _ in range(40):
        xx = R.integers(0, w); L = R.integers(h // 4, h); d = R.uniform(0.05, 0.14); a[:L, xx:xx + R.integers(3, 10)] *= 1 - d
    save(name, a, tile)


# ---- 3D seat plastic, one material per colour (UV 0-1 per face): moulded rim darker, a soft sheen down the middle ----
SEATS = {'s_blue': (56, 74, 118), 's_orange': (206, 112, 42), 's_grey': (168, 170, 174),            # grandstand mix (Fosnez photo)
         's_maroon': (116, 34, 42), 's_gold': (226, 170, 34), 's_teal': (36, 126, 120)}              # boundary seats (photos 01, 04-06)
for nm, col in SEATS.items():
    a = base(128, 128, col, 2, 6)
    a[:, :8] *= 0.78; a[:, -8:] *= 0.78; a[:6] *= 0.85; a[-6:] *= 0.7
    a[:, 40:88] *= (1 + 0.10 * np.sin(np.linspace(0, math.pi, 48)))[None, :, None]
    save(nm, a, (1, 1))
# concrete treads and risers: plain grey, a dark nosing line, scuffing
a = base(512, 512, (150, 148, 142), 5, 14); a[:10] *= 0.7; weather(a, 0.06, 10, 20, top_dark=False); save('conc_tread', a, (2.0, 0.8))
concrete('conc_wall', (184, 180, 172))
concrete('conc_kerb', (196, 192, 184), 1.2, 0.6, (2.4, 1.2), 0.05)
# paving behind the fence: 1.2 m broom-finished slabs, saw joints, stains
a = base(N, N, (176, 170, 160), 7, 22); p = N / 2.4
for k in range(2): a[int(k * 1.2 * p):int(k * 1.2 * p) + 3] *= 0.72; a[:, int(k * 1.2 * p):int(k * 1.2 * p) + 3] *= 0.72
for j in range(0, N, 3): a[j:j + 1] *= 0.97
for _ in range(25):
    cx, cy, rr = R.integers(0, N), R.integers(0, N), R.integers(10, 60); yy, xx = np.ogrid[:N, :N]
    a[((yy - cy) ** 2 + (xx - cx) ** 2) < rr * rr] *= R.uniform(0.86, 0.95)
save('paving', a, (2.4, 2.4))
# grass outside the boundary: mown stripes 6 m, clover patches, worn spots (photos 04-06: lush tropical green)
a = base(N, N, (82, 132, 52), 10, 26); xx = np.arange(N)
a *= np.where((xx // (N // 2)) % 2 == 0, 1.04, 0.96)[None, :, None]
for _ in range(60):
    cx, cy, rr = R.integers(0, N), R.integers(0, N), R.integers(6, 30); yy, x2 = np.ogrid[:N, :N]
    a[((yy - cy) ** 2 + (x2 - cx) ** 2) < rr * rr] *= np.array(R.choice([(0.9, 0.95, 0.85), (1.08, 1.05, 1.0)]))
a += fine(N, N, 8)[:, :, None] * np.array((0.8, 1.0, 0.6)); save('grass', a, (12.0, 12.0))

# ---- boundary fence: galvanised chain wire 1.1 m on pipe posts (photo 01). RGBA: diamonds open ----
W_, H_ = 512, 512; a = np.zeros((H_, W_, 4)); yy, xx = np.mgrid[:H_, :W_]
p = 512 / (1.0 / 0.06)
wire = (((xx + yy) % p) < 2.2) | (((xx - yy) % p) < 2.2)
a[..., :3] = np.array((150, 156, 158)) + fine(H_, W_, 10)[:, :, None]; a[..., 3] = np.where(wire, 255, 0)
save('mesh', a, (1.0, 1.0))

# ---- roof sheeting and steel ----
deck('roof_white', (222, 224, 224)); deck('roof_grey', (166, 170, 172)); deck('roof_soffit', (204, 206, 206), grime=12)
deck('roof_club', (188, 190, 190), pitch=0.6, grime=20)
a = base(512, 1024, (232, 234, 232), 4, 16); xu = 1024 / 4.0
for k in range(2): a[:, int(k * 2 * xu):int(k * 2 * xu) + 6] *= 0.7
a[470:] *= 0.82; weather(a, 0.14, 14, 40); save('fascia', a, (4.0, 2.0))
for nm, col in (('steel_white', (232, 234, 232)), ('steel_galv', (152, 156, 160)), ('paint_white', (234, 234, 230)),
                ('paint_black', (34, 36, 40))):
    lite = col[0] > 100
    a = base(256, 256, col, 6, 22 if lite else 8); a[:, 120:126] *= 0.7 if lite else 1.35; a[:, 0:4] *= 0.75 if lite else 1.3
    if lite: weather(a, 0.14, 16, 16)
    save(nm, a, (2.0, 2.0))
# aluminium bleacher planks: 250 mm extruded boards, ribs along the plank, oxidised streaks (GE n290 NW bleacher)
a = base(256, 512, (186, 190, 192), 4, 12)
for k in range(0, 256, 32): a[k:k + 3] *= 0.7
for k in range(0, 256, 8): a[k:k + 1] *= 0.9
save('alu', a, (2.0, 0.5))
# tensile marquee fabric: off-white PVC, seam lines every 1.5 m, grey dirt toward the low edges
a = base(512, 512, (236, 236, 230), 3, 10)
for k in range(4): a[:, int(k * 128):int(k * 128) + 3] *= 0.86
a *= np.linspace(1.0, 0.86, 512)[:, None, None]; save('tent', a, (6.0, 6.0))


# ---- facades (row 0 = top) ----
def facade(name, col, draw, tile=(6.0, 3.6), w=1024, h=616, streak=0.12):
    a = base(h, w, col, 3, 10); pu = w / tile[0]; pv = h / tile[1]; draw(a, pu, pv, h, w); weather(a, streak, 12, 40); save(name, a, tile)


def _clad(a, pu, pv, h, w):     # light grey Colorbond wall cladding: vertical ribs every 0.25 m, a dark plinth
    for k in range(int(6 / 0.25)): a[:, int(k * 0.25 * pu):int(k * 0.25 * pu) + 3] *= 0.86
    a[int(3.3 * pv):] *= 0.75


def _club(a, pu, pv, h, w):     # leagues club, one tile = 6 m x 9 m: white fascia band, a grey-tinted glass level, rendered base
    a[:int(1.0 * pv)] = np.array((236, 236, 232)) + fine(int(1.0 * pv), w, 3)[:, :, None]
    g0, g1 = int(1.6 * pv), int(4.4 * pv); a[g0:g1] = np.array((62, 76, 88)) + noise(g1 - g0, w, 6, 18)[:, :, None]
    for k in range(5): a[g0:g1, int(k * 1.5 * pu):int(k * 1.5 * pu) + 6] = (196, 200, 202)
    a[int(4.4 * pv):int(4.8 * pv)] = (210, 210, 206)
    for k in range(2): a[int(5.6 * pv):int(7.6 * pv), int((0.6 + k * 3) * pu):int((2.4 + k * 3) * pu)] = (70, 80, 90)


def _gstand(a, pu, pv, h, w):   # grandstand rear wall under the roof, one tile = 6 m x 3.6 m: corporate glazing with mullions
    a[int(0.3 * pv):int(2.9 * pv)] = np.array((44, 52, 60)) + noise(int(2.9 * pv) - int(0.3 * pv), w, 6, 16)[:, :, None]
    for k in range(4): a[int(0.3 * pv):int(2.9 * pv), int(k * 1.5 * pu):int(k * 1.5 * pu) + 6] = (200, 202, 204)
    a[:int(0.3 * pv)] = (212, 212, 208); a[int(2.9 * pv):] = (206, 204, 198)


def _shed(a, pu, pv, h, w):     # small white block building (SE): white render, grey roller door, a window
    a[int(1.0 * pv):, int(0.8 * pu):int(3.6 * pu)] = (150, 154, 156)
    for k in range(int(2.6 * pv / 10)): a[int(1.0 * pv) + k * 10:int(1.0 * pv) + k * 10 + 2, int(0.8 * pu):int(3.6 * pu)] *= 0.8
    a[int(1.0 * pv):int(2.0 * pv), int(4.3 * pu):int(5.5 * pu)] = (60, 70, 80)


facade('clad_grey', (200, 202, 202), _clad); facade('club', (222, 220, 214), _club, (6.0, 9.0), 1024, 1536)
facade('gstand_back', (206, 204, 198), _gstand); facade('shed', (230, 230, 226), _shed)
# coaches' box (photos 09-11): matt black boarding, five slit windows along the top
a = base(512, 512, (30, 32, 36), 3, 6)
for k in range(0, 512, 48): a[:, k:k + 3] *= 1.4
for i in range(5): a[60:110, 40 + i * 92:110 + i * 92] = (12, 12, 14)
save('box_black', a, (3.0, 2.6))
# light tower head: 6 x 5 floodlights in a galvanised frame
a = np.ones((N, N, 3)) * np.array((160, 166, 170), float); cu, cv = N / 6, N / 5
for i in range(6):
    for j in range(5):
        x0, y0 = int(i * cu + 10), int(j * cv + 10); x1, y1 = int((i + 1) * cu - 10), int((j + 1) * cv - 10)
        a[y0:y1, x0:x1] = (110, 116, 120); a[y0 + 14:y1 - 14, x0 + 14:x1 - 14] = (214, 218, 216)
save('lamps', a, (1, 1))
# LED screen, switched off: dark modules, joints every 0.5 m
a = base(512, 512, (22, 24, 28), 3, 8)
for k in range(0, 512, 128): a[:, k:k + 3] *= 0.5; a[k:k + 3] *= 0.5
for k in range(0, 512, 8): a[:, k:k + 1] *= 0.85
save('screen_off', a, (2.0, 2.0))

# ---- name sign under the scoreboard (photos 07-08): black panel, white script name, red dot, white bold italic second word ----
SW_, SH_ = 2048, 320
im = Image.fromarray(np.clip(base(SH_, SW_, (26, 28, 32), 2, 4), 0, 255).astype(np.uint8)); dr = ImageDraw.Draw(im)
F1 = ImageFont.truetype('C:/Windows/Fonts/segoescb.ttf', 190); F2 = ImageFont.truetype('C:/Windows/Fonts/georgiaz.ttf', 130)
tw = dr.textlength('Cazalys', font=F1) + 110 + dr.textlength('Stadium', font=F2); x0 = (SW_ - tw) / 2; dr.text((x0, 20), 'Cazalys', font=F1, fill=(244, 244, 240))
x1 = x0 + dr.textlength('Cazalys', font=F1)
bb = dr.textbbox((x0, 20), 'Cazalys', font=F1); yb = bb[3]
dr.arc([x1 - 230, yb - 60, x1 + 10, yb + 22], 20, 160, fill=(244, 244, 240), width=7)   # swash under the name into the ball
dr.ellipse([x1 - 6, yb - 52, x1 + 84, yb + 6], fill=(206, 32, 38))   # red football (photo 07)
for k in range(5): dr.line([x1 + 22 + k * 10, yb - 36, x1 + 22 + k * 10, yb - 12], fill=(250, 236, 230), width=3)
dr.text((x1 + 110, yb), 'Stadium', font=F2, fill=(244, 244, 240), anchor='ls')
a = np.asarray(im, float) + noise(SH_, SW_, 10, 4)[:, :, None]; save('sign_cazalys', a, (10.0, 1.56))


# ---- entrance gate (photos 02, 09): black band, white bold italic caps with a wide gap; navy Hopgood sign; white roller shutters ----
GW, GH = 2048, 192
im = Image.fromarray(np.clip(base(GH, GW, (38, 40, 45), 2, 4), 0, 255).astype(np.uint8)); dr = ImageDraw.Draw(im)
FG = ImageFont.truetype('C:/Windows/Fonts/ariblk.ttf', 110)      # photo 01: upright heavy caps, warm grey, words span 9-92% of the band
txt = Image.new('L', (2400, 200), 0); dt = ImageDraw.Draw(txt); w1 = dt.textlength('CAZALYS', font=FG); gap = 0.08 * GW * 1500 / (0.83 * GW)
dt.text((0, 20), 'CAZALYS', font=FG, fill=255); dt.text((w1 + gap, 20), 'STADIUM', font=FG, fill=255); txt = txt.crop(txt.getbbox())
sh = 0.2; txt = txt.transform((txt.width + int(sh * txt.height), txt.height), Image.AFFINE, (1, sh, -sh * txt.height, 0, 1, 0), Image.BICUBIC)   # photo 01: heavy italic
txt = txt.resize((int(0.83 * GW), int(GH * 0.46)), Image.LANCZOS); col = Image.new('RGB', txt.size, (182, 176, 162))
im.paste(col, (int(0.09 * GW), int((GH - txt.height) / 2)), txt)
dr.rectangle([0, 0, GW, 10], fill=(70, 72, 76)); dr.rectangle([0, GH - 10, GW, GH], fill=(70, 72, 76))
a = np.asarray(im, float) + noise(GH, GW, 10, 3)[:, :, None]; save('sign_gate', a, (12.0, 1.125))
HW_, HH_ = 1024, 512
im = Image.fromarray(np.clip(base(HH_, HW_, (28, 38, 92), 2, 4), 0, 255).astype(np.uint8)); dr = ImageDraw.Draw(im)
FH1 = ImageFont.truetype('C:/Windows/Fonts/georgia.ttf', 64); FH2 = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 36)   # photo 02: plain serif, text spans 27-83% of the panel
L1 = "Jeff ‘Hoppy’ Hopgood"; x0, x1 = 0.27 * HW_, 0.83 * HW_
t1 = Image.new('L', (900, 120), 0); ImageDraw.Draw(t1).text((0, 10), L1, font=FH1, fill=255); t1 = t1.crop(t1.getbbox())
t1 = t1.resize((int(x1 - x0), int(t1.height * (x1 - x0) / t1.width)), Image.LANCZOS); W_ = Image.new('RGB', t1.size, (240, 240, 236))
im.paste(W_, (int(x0), 150), t1); dr.rectangle([int(x0), 150 + t1.height + 22, int(x1), 150 + t1.height + 27], fill=(240, 240, 236))
L2 = 'MEMORIAL  ENTRANCE'; w2 = dr.textlength(L2, font=FH2); dr.text(((x0 + x1 - w2) / 2, 150 + t1.height + 52), L2, font=FH2, fill=(240, 240, 236))
# AFL Queensland 'Q Cairns' shield at the left (photo 02, director 2026-11-20: "Paint it on"): hand-drawn at 4x then reduced
S4 = 4; lw, lh = 140, 250; L = Image.new('RGBA', (lw * S4, lh * S4), (0, 0, 0, 0)); dl = ImageDraw.Draw(L)
def sh_(m): return [(m + 6 * S4, 40 * S4), (lw * S4 - m - 6 * S4, 40 * S4), (lw * S4 - m - 6 * S4, 196 * S4), (lw * S4 / 2, lh * S4 - m), (m + 6 * S4, 196 * S4)]
dl.polygon(sh_(0), fill=(236, 236, 232, 255)); dl.polygon(sh_(5 * S4), fill=(118, 30, 48, 255))   # white edge, maroon shield
cx, cy = lw * S4 / 2, 112 * S4; dl.ellipse([cx - 40 * S4, cy - 52 * S4, cx + 40 * S4, cy + 52 * S4], outline=(240, 240, 236, 255), width=17 * S4)   # the Q
dl.line([cx + 8 * S4, cy + 22 * S4, cx + 36 * S4, cy + 66 * S4], fill=(240, 240, 236, 255), width=17 * S4)
dl.ellipse([cx - 13 * S4, cy - 22 * S4, cx + 13 * S4, cy + 22 * S4], fill=(150, 44, 52, 255))   # football inside the Q
for k in (-10, -3, 4, 11): dl.line([cx - 5 * S4, cy + k * S4, cx + 5 * S4, cy + k * S4], fill=(236, 220, 214, 255), width=2 * S4)
rc = (lw * S4 / 2, 30 * S4); r_ = 30 * S4   # AFL roundel on top
dl.ellipse([rc[0] - r_, rc[1] - r_, rc[0] + r_, rc[1] + r_], fill=(236, 236, 232, 255)); dl.ellipse([rc[0] - r_ + 6 * S4, rc[1] - r_ + 6 * S4, rc[0] + r_ - 6 * S4, rc[1] + r_ - 6 * S4], fill=(30, 52, 132, 255))
dl.chord([rc[0] - r_ + 6 * S4, rc[1] - r_ + 6 * S4, rc[0] + r_ - 6 * S4, rc[1] + r_ - 6 * S4], 0, 180, fill=(200, 32, 44, 255))
FA = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 26 * S4); dl.text(rc, 'AFL', font=FA, fill=(250, 250, 248, 255), anchor='mm')
by = 186 * S4; dl.rectangle([2 * S4, by, lw * S4 - 2 * S4, by + 36 * S4], fill=(242, 242, 238, 255), outline=(150, 150, 150, 255), width=S4)   # CAIRNS banner
FC = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 22 * S4); dl.text((lw * S4 / 2, by + 18 * S4), 'CAIRNS', font=FC, fill=(118, 30, 48, 255), anchor='mm')
L = L.resize((lw, lh), Image.LANCZOS); im.paste(L, (80, 66), L)
a = np.asarray(im, float) + noise(HH_, HW_, 10, 3)[:, :, None]; save('sign_hopgood', a, (5.0, 2.5))
a = base(256, 256, (226, 228, 228), 2, 5)
for k in range(0, 256, 16): a[k:k + 2] *= 0.86
save('shutter', a, (2.0, 2.0))
a = base(256, 256, (58, 52, 48), 2, 6)
for k in range(0, 256, 128): a[k:k + 3] *= 0.6
save('soffit_dark', a, (2.4, 2.4))

json.dump(TILE, open(OUT + 'tiles.json', 'w', newline=''), indent=0)
for nm in sorted(TILE):
    g = np.asarray(Image.open(OUT + nm + '.png').convert('L'), float); print(f'{nm:16s} grey sd {g.std():5.1f}')
