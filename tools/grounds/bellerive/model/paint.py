# Hand-painted textures for Bellerive Oval (no photo pixels): every surface is drawn from numbers read off the
# Google Earth views (colours sampled by eye, layouts measured). PPM px per metre; tiles.json gives each tile's size
# in metres (u along the ground / wall, v up the section or wall).
import numpy as np, json, os
from PIL import Image
R = np.random.default_rng(7); OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex') + '/'
os.makedirs(OUT, exist_ok=True)
PPM = 96; TILE = {}


def blotch(h, w, scale, amp):
    """soft low-frequency blotching (weathering): sum of upsampled noise octaves, periodic so tiles wrap"""
    out = np.zeros((h, w))
    for k, s in enumerate((scale, scale / 2, scale / 4)):
        gh, gw = max(2, int(round(h / (s * PPM)))), max(2, int(round(w / (s * PPM))))
        g = R.normal(0, 1, (gh, gw)); g = np.concatenate([g, g[:1]], 0); g = np.concatenate([g, g[:, :1]], 1)
        yi = np.linspace(0, gh, h, endpoint=False); xi = np.linspace(0, gw, w, endpoint=False)
        y0 = yi.astype(int); x0 = xi.astype(int); fy = (yi - y0)[:, None]; fx = (xi - x0)[None, :]
        fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
        a = g[y0][:, x0]; b = g[y0][:, x0 + 1]; c = g[y0 + 1][:, x0]; d = g[y0 + 1][:, x0 + 1]
        out += (a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy) * amp / (k + 1)
    return out


class T:
    """canvas W x H metres; (u, z) metres with z up from the bottom edge"""
    def __init__(s, W, H, col, n=3.0, bl=(2.0, 6.0)):
        s.W, s.H = W, H; s.w, s.h = int(round(W * PPM)), int(round(H * PPM))
        s.a = np.ones((s.h, s.w, 3)) * np.array(col, float) + R.normal(0, n, (s.h, s.w, 1))
        if bl: s.a += blotch(s.h, s.w, *bl)[:, :, None]
    def Y(s, z): return int(round((s.H - z) * PPM))
    def X(s, u): return int(round(u * PPM))
    def rect(s, u0, u1, z0, z1, col=None, mul=None, n=1.5):
        y0, y1 = max(0, s.Y(z1)), min(s.h, s.Y(z0)); x0, x1 = max(0, s.X(u0)), min(s.w, s.X(u1))
        if y1 <= y0 or x1 <= x0: return
        if mul is not None: s.a[y0:y1, x0:x1] *= mul
        else: s.a[y0:y1, x0:x1] = np.array(col, float) + R.normal(0, n, (y1 - y0, x1 - x0, 1))
    def hl(s, z, t, col=None, mul=0.7, u0=0, u1=None): s.rect(u0, s.W if u1 is None else u1, z - t / 2, z + t / 2, col, None if col else mul)
    def vl(s, u, t, z0=0, z1=None, col=None, mul=0.75): s.rect(u - t / 2, u + t / 2, z0, s.H if z1 is None else z1, col, None if col else mul)
    def streaks(s, n, z0, z1, mul=0.88, wid=(0.05, 0.25)):
        """rain streaks running down from z1 toward z0"""
        for _ in range(n):
            u = R.uniform(0, s.W); w = R.uniform(*wid); L = R.uniform(0.3, 1.0) * (z1 - z0)
            y0, y1 = s.Y(z1), s.Y(z1 - L); x0, x1 = s.X(u), s.X(u + w)
            if y1 > y0 and x1 > x0:
                s.a[y0:y1, x0:min(x1, s.w)] *= np.linspace(mul, 1.0, y1 - y0)[:, None, None]
    def grime_bottom(s, z1, mul=0.82):
        y = s.Y(z1); s.a[y:] *= np.linspace(1.0, mul, s.h - y)[:, None, None]
    def save(s, name):
        Image.fromarray(np.clip(s.a, 0, 255).astype(np.uint8)).save(OUT + name + '.png'); TILE[name] = (s.W, s.H)


def sd(name):
    a = np.asarray(Image.open(OUT + name + '.png').convert('L'), float); return a.std()


# ---- seats: empty blue plastic seats in rows, 0.8 m row pitch on the rake (v up the rake), 0.5 m seat width;
# white aisle steps every 10 m (GE i180: white stair strips between blocks of ~20 seats)
def seats(name, seat, shade, step_col=(210, 212, 210), aisle=10.0):
    t = T(aisle, 4.0, (120, 124, 128), n=3, bl=(1.5, 4))
    for r in range(5):
        z = r * 0.8
        t.rect(0, aisle, z, z + 0.32, (150, 152, 150))                      # concrete tread
        t.hl(z + 0.32, 0.04, mul=0.6)
        for u in np.arange(0.0, aisle - 1.2, 0.5):                          # seat pans and backs
            t.rect(u + 0.04, u + 0.46, z + 0.30, z + 0.62, seat, n=4)
            t.rect(u + 0.06, u + 0.44, z + 0.62, z + 0.78, shade, n=4)
            t.rect(u + 0.04, u + 0.46, z + 0.26, z + 0.30, mul=0.55)        # shadow under the seat lip
        t.hl(z + 0.79, 0.03, mul=0.55)
    t.rect(aisle - 1.2, aisle, 0, 4.0, step_col, n=4)                       # aisle stair
    for r in range(10): t.hl(r * 0.4, 0.05, mul=0.7, u0=aisle - 1.2, u1=aisle)
    t.vl(aisle - 1.2, 0.05, mul=0.6); t.vl(aisle, 0.05, mul=0.6)
    t.save(name)


seats('seats_blue', (44, 78, 118), (34, 60, 92))
seats('seats_dark', (40, 44, 52), (30, 33, 40))
# ---- concrete: pale grey with formwork joints every 3 m, blotches, streaks
t = T(6.0, 3.0, (176, 176, 170), n=4, bl=(1.2, 9)); t.vl(0.02, 0.04, mul=0.75); t.vl(3.0, 0.04, mul=0.8)
t.hl(0.02, 0.04, mul=0.8); t.streaks(14, 0, 3); t.save('conc_grey')
t = T(6.0, 3.0, (160, 162, 160), n=4, bl=(1.2, 9)); t.vl(0.02, 0.05, mul=0.7); t.streaks(16, 0, 3); t.grime_bottom(0.8); t.save('tier_wall')
# ---- boundary fence: navy panels (ads left off), 2.4 m panels with joints, a pale top rail
t = T(4.8, 1.2, (34, 46, 78), n=4, bl=(0.8, 8))
for u in (0.0, 2.4): t.vl(u + 0.02, 0.05, col=(120, 128, 140))
t.rect(0, 4.8, 1.12, 1.2, (196, 198, 196)); t.hl(1.1, 0.03, mul=0.5); t.grime_bottom(0.3, 0.75); t.save('fence')
# ---- stand back wall under the roof: dark glazing with mullions every 1.5 m
t = T(6.0, 4.0, (44, 56, 70), n=3, bl=(1.5, 6))
for u in np.arange(0, 6, 1.5): t.vl(u, 0.07, col=(120, 130, 140))
t.hl(2.0, 0.05, (100, 110, 120)); t.save('backwall')
# ---- white roof deck: ribbed metal sheet, ribs every 0.19 m, sheet laps every 8 m, grime toward the gutter
t = T(8.0, 8.0, (226, 228, 226), n=2.5, bl=(2.5, 7))
for u in np.arange(0, 8, 0.19): t.vl(u, 0.035, mul=0.86)
t.hl(0.04, 0.08, mul=0.8); t.vl(0.03, 0.06, mul=0.78); t.streaks(10, 0, 8, mul=0.9, wid=(0.2, 0.6)); t.grime_bottom(1.5, 0.86)
t.save('roof_white')
t = T(8.0, 4.0, (116, 122, 128), n=3, bl=(2, 6))                                      # soffit: purlins every 1.2 m
for z in np.arange(0, 4, 1.2): t.hl(z, 0.12, (84, 88, 94))
t.save('roof_soffit')
t = T(6.0, 1.0, (214, 216, 214), n=3, bl=(1, 6)); t.hl(0.05, 0.1, mul=0.7); t.vl(0.02, 0.04, mul=0.8); t.streaks(12, 0, 1); t.save('roof_fascia')
# ---- Boon Stand facade (GE f180): grey panels above, glazing band below with mullions every 1.8 m
t = T(7.2, 14.0, (150, 158, 166), n=3, bl=(2, 6))
for u in (0.0, 3.6): t.vl(u + 0.02, 0.05, mul=0.8)
for z in (8.0, 11.0): t.hl(z, 0.04, mul=0.82)
t.rect(0, 7.2, 1.0, 5.2, (52, 66, 78)); t.a[t.Y(5.2):t.Y(1.0)] *= np.linspace(1.15, 0.9, t.Y(1.0) - t.Y(5.2))[:, None, None]
for u in np.arange(0, 7.2, 1.8): t.vl(u, 0.1, 1.0, 5.2, (200, 204, 206))
t.hl(5.2, 0.25, (200, 204, 206)); t.hl(1.0, 0.15, (170, 174, 176)); t.streaks(20, 5.3, 14); t.grime_bottom(1.0)
t.save('fac_boon')

# ---- Members / north building (GE i330, x330): two glazed levels, white slab edges, dark tinted glass, mullions 1.5 m
t = T(6.0, 11.0, (40, 52, 62), n=3, bl=(1.5, 6))
for z0, z1 in ((0.0, 4.6), (5.6, 10.2)):
    t.a[t.Y(z1):t.Y(z0)] *= np.linspace(1.25, 0.85, t.Y(z0) - t.Y(z1))[:, None, None]
    for u in np.arange(0, 6, 1.5): t.vl(u, 0.08, z0, z1, (150, 158, 164))
t.rect(0, 6, 4.6, 5.6, (214, 216, 214)); t.hl(5.0, 0.04, mul=0.8); t.rect(0, 6, 10.2, 11.0, (206, 208, 206))
t.hl(1.05, 0.06, (190, 196, 198)); t.save('glass_members')
# white rendered outer wall with small square windows in two rows (x330)
t = T(8.0, 17.0, (222, 222, 216), n=3, bl=(2, 7))
for u in (1.6, 5.6):
    for z in (6.2, 10.4, 14.2): t.rect(u - 0.55, u + 0.55, z, z + 1.0, (46, 56, 66)); t.rect(u - 0.6, u + 0.6, z - 0.08, z, (180, 180, 176))
t.vl(0.02, 0.04, mul=0.85); t.hl(3.0, 0.03, mul=0.88); t.streaks(18, 0, 17, mul=0.9); t.grime_bottom(1.2); t.save('fac_members')
# flat white membrane roof with lap seams every 2 m and walkway pads
t = T(8.0, 8.0, (218, 220, 218), n=3, bl=(2, 9))
for u in np.arange(0, 8, 2.0): t.vl(u, 0.03, mul=0.9)
t.rect(3.4, 4.2, 0, 8, (176, 178, 176)); t.streaks(8, 0, 8, mul=0.92, wid=(0.3, 0.8)); t.save('roof_flat')
# plant boxes: galvanised louvred casings
t = T(3.0, 2.5, (150, 156, 160), n=3, bl=(1, 6))
for z in np.arange(0.2, 2.3, 0.12): t.hl(z, 0.035, mul=0.75)
t.vl(1.5, 0.05, mul=0.7); t.rect(0, 3, 2.35, 2.5, (176, 180, 182)); t.save('plant')
# Ponting skylight wedges: translucent white panels with glazing bars, one face lit and one in shade
for nm, base in (('skylight', (210, 222, 228)), ('skylight_dk', (120, 146, 166))):
    t = T(4.0, 4.0, base, n=3, bl=(1.5, 6))
    for u in np.arange(0, 4, 1.0): t.vl(u, 0.08, mul=0.7)
    for z in np.arange(0, 4, 1.0): t.hl(z, 0.06, mul=0.75)
    t.streaks(8, 0, 4, mul=0.85, wid=(0.2, 0.5)); t.save(nm)
# old Northern Stand: tan corrugated skillion roof, white painted walls
t = T(4.0, 5.0, (196, 170, 128), n=3, bl=(1.5, 7))
for u in np.arange(0, 4, 0.076): t.vl(u, 0.025, mul=0.84)
t.streaks(10, 0, 5, mul=0.9, wid=(0.2, 0.5)); t.save('roof_tan')
t = T(6.0, 4.0, (224, 222, 214), n=3, bl=(1.5, 7)); t.hl(0.6, 0.05, mul=0.8); t.vl(0.02, 0.05, mul=0.8)
t.streaks(10, 0, 4); t.grime_bottom(0.6, 0.78); t.save('nstand_wall')
t = T(1.0, 1.0, (226, 228, 226), n=5, bl=(0.5, 8)); t.hl(0.5, 0.06, mul=0.78); t.vl(0.5, 0.05, mul=0.82); t.streaks(4, 0, 1, mul=0.85); t.save('steel_white')
t = T(1.0, 1.0, (150, 154, 156), n=5, bl=(0.5, 8)); t.hl(0.5, 0.04, mul=0.8); t.vl(0.3, 0.04, mul=0.85); t.save('steel_galv')
# east terrace treads: weathered concrete with expansion joints every 2.5 m, lichen
t = T(5.0, 0.95, (178, 176, 166), n=5, bl=(0.8, 9))
for u in (0.0, 2.5): t.vl(u + 0.02, 0.04, mul=0.7)
t.hl(0.9, 0.06, mul=0.82); t.save('terrace')
# grass hill: dry summer grass, mown stripes, worn patches
t = T(10.0, 10.0, (138, 140, 92), n=10, bl=(2.5, 16))
for u in np.arange(0, 10, 2.5): t.rect(u, u + 1.25, 0, 10, mul=np.array([1.06, 1.05, 1.0]))
for _ in range(14):
    u, z, r = R.uniform(0, 10), R.uniform(0, 10), R.uniform(0.3, 1.0); t.rect(u, u + r, z, z + r * 0.6, mul=np.array([1.25, 1.12, 1.15]))
t.save('grass_hill')
# concourse apron: concrete slabs 3 m with saw joints, oil stains
t = T(6.0, 6.0, (158, 156, 150), n=5, bl=(1.5, 10))
for u in (0.0, 3.0): t.vl(u + 0.02, 0.04, mul=0.72); t.hl(u + 0.02, 0.04, mul=0.72)
t.save('apron')
# scoreboard: grey cladded back, blank dark screen (no ads), white lamp heads
t = T(4.0, 8.0, (196, 200, 202), n=3, bl=(1.5, 6))
for u in np.arange(0, 4, 1.0): t.vl(u, 0.04, mul=0.8)
for z in np.arange(0, 8, 2.0): t.hl(z, 0.04, mul=0.82)
t.streaks(10, 0, 8); t.save('scoreboard_back')
t = T(4.0, 2.0, (22, 26, 32), n=4, bl=(1, 4))
for u in np.arange(0, 4, 0.5): t.vl(u, 0.02, mul=0.6)
for z in np.arange(0, 2, 0.5): t.hl(z, 0.02, mul=0.6)
t.a[:t.h // 3] *= 1.35
for _ in range(40):
    u, z = R.uniform(0, 3.8), R.uniform(0, 1.8); t.rect(u, u + 0.5, z, z + 0.5, mul=R.uniform(0.6, 1.6))
t.save('screen')
t = T(3.0, 6.0, (220, 222, 220), n=3, bl=(1.5, 7)); t.hl(3.0, 0.04, mul=0.85); t.streaks(12, 0, 6); t.grime_bottom(1.0); t.save('tower')
t = T(6.8, 3.8, (60, 64, 70), n=3, bl=None)
for i in range(6):
    for j in range(3):
        u, z = 0.35 + i * 1.06, 0.3 + j * 1.15; t.rect(u, u + 0.9, z, z + 0.95, (226, 230, 232)); t.rect(u + 0.2, u + 0.7, z + 0.2, z + 0.75, (250, 250, 244))
t.save('lamps')

# ---- NINJA STADIUM tower sign (GE x330, hand-lettered): two vertical panels reading bottom to top.
# North face: white panel, black regular capitals. West face: navy panel, white bold capitals.
from PIL import ImageDraw, ImageFont
def sign(name, bg, fg, font, W=1.8, H=15.0):
    w, h = int(H * PPM), int(W * PPM); im = Image.new('RGB', (w, h), bg); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(font, int(h * 0.62)); txt = 'NINJA STADIUM'
    # GE x330: lettering on the lower three quarters; above it the white cap carries a round navy emblem (ring + stroke),
    # and the navy panel stops below the cap (left of the strip = bottom once rotated)
    x0, y0, x1, y1 = d.textbbox((0, 0), txt, font=f); sx = (w * 0.66) / (x1 - x0)
    tmp = Image.new('RGB', (x1 - x0 + 8, y1 - y0 + 8), bg); ImageDraw.Draw(tmp).text((4 - x0, 4 - y0), txt, font=f, fill=fg)
    tmp = tmp.resize((int(tmp.width * sx), int(tmp.height * 0.9)), Image.LANCZOS)
    im.paste(tmp, (int(w * 0.05), (h - tmp.height) // 2))
    cap = int(w * 0.76); d.rectangle((cap, 0, w, h), fill=(236, 238, 236))
    cx, cy, r = int(w * 0.87), h // 2, int(h * 0.36); nv = (30, 36, 62)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=nv, width=max(3, r // 6))
    d.line((cx - r * 0.55, cy + r * 0.55, cx + r * 0.55, cy - r * 0.55), fill=nv, width=max(3, r // 6))
    a = np.asarray(im.rotate(90, expand=True), float)          # reads bottom to top
    a += R.normal(0, 2.5, a.shape[:2] + (1,)) + blotch(a.shape[0], a.shape[1], 1.5, 4)[:, :, None]
    tt = T(W, H, bg, n=0, bl=None); tt.a = a; tt.save(name)
sign('sign_ninja_w', (236, 238, 236), (24, 26, 30), 'C:/Windows/Fonts/arial.ttf')
sign('sign_ninja_d', (30, 36, 62), (240, 242, 244), 'C:/Windows/Fonts/arialbd.ttf')

# ---- Ponting Stand skin (GE x270, f270): faceted translucent white panels, a band of navy triangles, open undercroft
def fac_ponting():
    W, H = 25.0, 20.0; t = T(W, H, (214, 220, 224), n=3, bl=(2, 6)); im = Image.new('L', (t.w, t.h), 0); d = ImageDraw.Draw(im)
    X = lambda u: u * PPM; Y = lambda z: (H - z) * PPM
    tris = []   # (polygon in metres, colour)
    for k in range(2):                                   # top band: inverted triangles under the roof edge
        u = k * 12.5
        tris += [([(u, 20), (u + 12.5, 20), (u + 6.25, 14)], (228, 232, 234)), ([(u + 6.25, 14), (u + 12.5, 20), (u + 18.75, 14)], (200, 210, 216))]
    tris += [([(0, 14), (6.25, 14), (0, 20)], (200, 210, 216))]
    for k in range(2):                                   # middle band: navy triangles between pale ones
        u = k * 12.5
        tris += [([(u, 8), (u + 12.5, 8), (u + 6.25, 14)], (64, 82, 146) if k == 0 else (186, 198, 208)),
                 ([(u + 6.25, 14), (u + 18.75, 14), (u + 12.5, 8)], (78, 96, 156) if k == 1 else (206, 214, 220))]
    tris += [([(0, 14), (6.25, 14), (0, 8)], (206, 214, 220)), ([(18.75, 14), (25, 14), (25, 8)], (64, 82, 146))]
    for k in range(4):                                   # lower band: slanted pale facets tucking in
        u = k * 6.25; tris += [([(u, 8), (u + 6.25, 8), (u + 6.25, 4.6), (u, 4.6)], (172, 184, 192) if k % 2 else (186, 196, 204))]
    for poly, col in tris:
        m = Image.new('L', (t.w, t.h), 0); ImageDraw.Draw(m).polygon([(X(u), Y(z)) for u, z in poly], fill=255)
        mk = np.asarray(m) > 0; t.a[mk] = np.array(col, float) + R.normal(0, 3, (mk.sum(), 1))
        d.line([(X(u), Y(z)) for u, z in poly + [poly[0]]], fill=255, width=9)
    t.a += blotch(t.h, t.w, 2, 5)[:, :, None]
    ln = np.asarray(im) > 0; t.a[ln] = t.a[ln] * 0.3 + np.array([238, 242, 244]) * 0.7
    for z in (8.0, 14.0): t.hl(z, 0.12, (236, 240, 242))
    t.rect(0, W, 0, 4.6, (58, 64, 72)); t.a[t.Y(4.6):t.Y(0)] *= np.linspace(0.8, 1.2, t.Y(0) - t.Y(4.6))[:, None, None]
    for u in np.arange(2.0, W, 8.33): t.vl(u, 0.45, 0, 4.6, (214, 216, 214))
    t.hl(4.6, 0.25, (150, 158, 164)); t.save('fac_ponting')
fac_ponting()


if __name__ == '__main__':
    json.dump(TILE, open(OUT + 'tiles.json', 'w', newline=''), indent=0)
    for k in sorted(TILE): print(f'{k:16s} stddev {sd(k):5.1f}')
