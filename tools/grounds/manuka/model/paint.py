# Hand-painted textures for Manuka Oval (copied from Bellerive's painter) (no photo pixels): every surface is drawn from numbers read off the
# Google Earth views (colours sampled by eye, layouts measured). PPM px per metre; tiles.json gives each tile's size
# in metres (u along the ground / wall, v up the section or wall).
import numpy as np, json, os, math
from PIL import Image
R = np.random.default_rng(1929); OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex') + '/'
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
    def save(s, name, alpha=None):
        im = np.clip(s.a, 0, 255).astype(np.uint8)
        if alpha is not None:   # glass: a real alpha channel, so the panes are see-through and the rails solid
            im = np.dstack([im, np.clip(alpha * 255, 0, 255).astype(np.uint8)])
        Image.fromarray(im).save(OUT + name + '.png'); TILE[name] = (s.W, s.H)
    def mask(s, u0, u1, z0, z1, a, val):
        a[max(0, s.Y(z1)):s.Y(z0), max(0, s.X(u0)):min(s.w, s.X(u1))] = val


def sd(name):
    a = np.asarray(Image.open(OUT + name + '.png').convert('L'), float); return a.std()


# ---- seats: empty blue plastic seats in rows, 0.8 m row pitch on the rake (v up the rake), 0.5 m seat width;
# white aisle steps every 10 m (GE i180: white stair strips between blocks of ~20 seats)


# ================= Manuka (Google Earth 3D and from the field, 2026-11-22; colours by eye) =================
# ---- boundary fence: low dark padded wall, panels 2.4 m, a pale capping
t = T(4.8, 1.0, (40, 44, 52), n=4, bl=(0.8, 8))
for u in (0.0, 2.4): t.vl(u + 0.02, 0.04, col=(90, 96, 104))
t.rect(0, 4.8, 0.92, 1.0, (186, 188, 186)); t.grime_bottom(0.25, 0.8); t.save('fence')
t = T(2.0, 0.25, (196, 196, 192), n=4, bl=(0.5, 6)); t.save('fence_top')
# ---- concrete: pale warm grey with joints every 3 m
t = T(6.0, 3.0, (192, 188, 178), n=4, bl=(1.2, 9)); t.vl(0.02, 0.04, mul=0.8); t.vl(3.0, 0.04, mul=0.82); t.streaks(12, 0, 3); t.save('conc')
t = T(6.0, 3.0, (112, 112, 110), n=4, bl=(1.2, 8)); t.streaks(10, 0, 3, mul=0.9); t.save('conc_dk')
t = T(6.0, 3.0, (204, 200, 190), n=4, bl=(1.2, 10)); t.vl(0.02, 0.04, mul=0.85)
for u in np.arange(0.5, 6, 1.5): t.rect(u, u + 0.3, 0.3, 0.6, mul=0.92)
t.save('concourse')
t = T(4.0, 1.0, (190, 186, 176), n=4, bl=(1.0, 7)); t.vl(0.02, 0.03, mul=0.8); t.hl(0.95, 0.06, mul=0.85); t.save('tread')
t = T(4.0, 0.5, (168, 164, 156), n=4, bl=(1.0, 6)); t.grime_bottom(0.2, 0.85); t.save('riser')
t = T(6.0, 2.0, (196, 194, 186), n=4, bl=(1.2, 8)); t.vl(0.02, 0.05, mul=0.8); t.streaks(10, 0, 2); t.grime_bottom(0.5, 0.82); t.save('tier_wall')
t = T(6.0, 2.0, (214, 212, 204), n=4, bl=(1.2, 8)); t.vl(0.02, 0.05, mul=0.82); t.streaks(10, 0, 2); t.grime_bottom(0.5, 0.85); t.save('plinth')
t = T(8.0, 8.0, (226, 224, 216), n=3, bl=(2, 8)); t.vl(0.02, 0.04, mul=0.86); t.hl(4.0, 0.03, mul=0.9); t.streaks(16, 0, 8, mul=0.9); t.grime_bottom(1.0, 0.82)
t.save('render_white')
t = T(6.0, 6.0, (222, 206, 172), n=4, bl=(1.5, 9)); t.streaks(10, 0, 6, mul=0.92); t.grime_bottom(0.8, 0.85); t.save('render_cream')
# ---- back of the A-frame stands: the dark open back with the stand's frame, ads panels left off
t = T(6.0, 4.0, (54, 58, 64), n=3, bl=(1.5, 6))
for u in (0.0, 3.0): t.vl(u + 0.05, 0.1, col=(96, 100, 106))
t.hl(2.0, 0.06, (80, 84, 90)); t.save('backwall')
# ---- roofs: grey ribbed sheet (A-frame stands), white ribbed sheet (Bradman, media centre)
t = T(8.0, 8.0, (146, 150, 152), n=2.5, bl=(2.5, 7))
for u in np.arange(0, 8, 0.19): t.vl(u, 0.035, mul=0.86)
t.vl(0.03, 0.06, mul=0.78); t.streaks(10, 0, 8, mul=0.92, wid=(0.2, 0.6)); t.grime_bottom(1.5, 0.88); t.save('roof_grey')
t = T(8.0, 8.0, (232, 232, 228), n=2.5, bl=(2.5, 7))
for u in np.arange(0, 8, 0.19): t.vl(u, 0.035, mul=0.88)
t.vl(0.03, 0.06, mul=0.8); t.streaks(10, 0, 8, mul=0.92, wid=(0.2, 0.6)); t.grime_bottom(1.5, 0.88); t.save('roof_white')
t = T(8.0, 4.0, (118, 122, 120), n=3, bl=(2, 6))
for z in np.arange(0, 4, 1.2): t.hl(z, 0.12, (92, 96, 94))
t.save('roof_soffit')
t = T(6.0, 1.0, (46, 50, 56), n=3, bl=(1, 6)); t.hl(0.05, 0.08, mul=0.8); t.vl(0.02, 0.04, col=(70, 74, 80)); t.save('fascia_dark')
t = T(6.0, 2.6, (230, 230, 226), n=3, bl=(1, 7)); t.vl(0.02, 0.04, mul=0.86); t.streaks(16, 0, 2.6, mul=0.9); t.save('fascia_white')
t = T(6.0, 1.0, (36, 36, 38), n=3, bl=(1, 5)); t.hl(0.9, 0.06, (80, 80, 82)); t.save('rim_dark')
# ---- steel
t = T(1.0, 1.0, (228, 230, 228), n=5, bl=(0.5, 8)); t.save('steel_white')
t = T(1.0, 1.0, (150, 154, 156), n=5, bl=(0.5, 8)); t.save('steel_galv')
t = T(1.0, 1.0, (52, 54, 58), n=4, bl=(0.5, 6)); t.save('steel_dark')
t = T(3.0, 6.0, (196, 200, 202), n=3, bl=(1.5, 7)); t.hl(3.0, 0.04, mul=0.88); t.streaks(10, 0, 6); t.save('tower')
t = T(1.0, 1.0, (240, 240, 232), n=3, bl=(0.5, 5)); t.save('lamp_face')
# ---- glass
# The balustrade: tinted panes (40 % opaque) between stainless posts every 1.5 m, a handrail along the top.
t = T(3.0, 1.0, (170, 196, 206), n=3, bl=(0.8, 5)); t.hl(0.97, 0.06, (210, 214, 216))
for u in (0.0, 1.5, 3.0): t.vl(u, 0.05, col=(200, 204, 206))
al = np.full((t.h, t.w), 0.4); t.mask(0, 3.0, 0.94, 1.0, al, 1.0)
for u in (0.0, 1.5, 3.0): t.mask(u - 0.025, u + 0.025, 0, 1.0, al, 1.0)
t.save('glass_rail', al)
# The canopies: pale polycarbonate sheet, near opaque from above (Google Earth top-down reads (195, 219, 236) with the
# rafters showing through), ribbed every metre.
t = T(4.0, 4.0, (200, 220, 232), n=3, bl=(1, 5))
for u in np.arange(0, 4, 1.0): t.vl(u, 0.06, col=(230, 232, 232))
al = np.full((t.h, t.w), 0.82)
for u in np.arange(0, 4.01, 1.0): t.mask(u - 0.03, u + 0.03, 0, 4.0, al, 1.0)
t.save('canopy_glass', al)
t = T(6.0, 3.0, (44, 54, 64), n=3, bl=(1.5, 5))
for u in np.arange(0, 6, 1.5): t.vl(u, 0.07, col=(120, 126, 132))
t.a[:t.h // 3] *= 1.25; t.save('box_glass')
t = T(6.0, 3.4, (40, 48, 56), n=3, bl=(1.5, 5))
for u in np.arange(0, 6, 1.5): t.vl(u, 0.06, col=(90, 84, 76))
t.a[:t.h // 3] *= 1.2; t.save('glass_dark')
t = T(6.0, 3.4, (58, 70, 80), n=3, bl=(1.5, 5))
for u in np.arange(0, 6, 2.0): t.vl(u, 0.08, col=(180, 184, 186))
t.hl(1.1, 0.05, (180, 184, 186)); t.a[:t.h // 3] *= 1.2; t.save('media_glass')
t = T(1.2, 1.2, (40, 50, 60), n=3, bl=(0.5, 4)); t.a[:t.h // 2] *= 1.3; t.save('win_dark')
t = T(4.0, 1.0, (52, 54, 56), n=3, bl=(1, 5)); t.save('slab_dark')
# ---- bronze: the media centre's fins and walls
t = T(1.0, 3.0, (118, 92, 62), n=5, bl=(0.6, 10)); t.streaks(6, 0, 3, mul=0.88); t.save('bronze')
t = T(4.0, 4.0, (88, 72, 54), n=4, bl=(1.2, 8)); t.vl(0.02, 0.05, mul=0.8); t.hl(2.0, 0.04, mul=0.85); t.save('bronze_wall')
# ---- vomitories and plant
t = T(2.0, 2.0, (30, 32, 36), n=3, bl=(1.0, 4)); t.save('vom_dark')
t = T(3.0, 2.0, (176, 178, 176), n=3, bl=(1, 6))
for z in np.arange(0.2, 1.8, 0.12): t.hl(z, 0.035, mul=0.78)
t.save('plant')
# ---- the east bank: dry Canberra summer grass, the path, red-brown gravel, box hedge, stone piers
t = T(10.0, 10.0, (138, 140, 86), n=10, bl=(2.5, 16))
for u in np.arange(0, 10, 2.5): t.rect(u, u + 1.25, 0, 10, mul=np.array([1.04, 1.04, 1.02]))
t.save('grass_bank')
t = T(4.0, 4.0, (186, 182, 170), n=5, bl=(1.2, 8)); t.vl(0.02, 0.03, mul=0.85); t.hl(2.0, 0.03, mul=0.88); t.save('path')
t = T(2.0, 0.4, (200, 198, 190), n=4, bl=(0.5, 6)); t.save('kerb')
t = T(6.0, 6.0, (176, 116, 74), n=14, bl=(1.5, 14)); t.save('gravel')
t = T(3.0, 1.5, (54, 82, 46), n=16, bl=(0.4, 18)); t.save('hedge')
t = T(2.0, 2.0, (112, 108, 102), n=10, bl=(0.4, 12))
for z in np.arange(0, 2, 0.35): t.hl(z, 0.03, mul=0.75)
t.save('stone')
t = T(6.0, 6.0, (174, 172, 166), n=5, bl=(1.5, 9)); t.vl(0.02, 0.03, mul=0.86); t.hl(0.02, 0.03, mul=0.86); t.save('paving')
# ---- the Jack Fingleton Scoreboard: white paint over timber boards, black name boards with white lines
t = T(4.0, 4.0, (232, 232, 226), n=3, bl=(1.2, 7))
for z in np.arange(0, 4, 0.2): t.hl(z, 0.015, mul=0.93)
t.streaks(14, 0, 4, mul=0.9); t.save('scoreboard_white')
t = T(1.0, 1.0, (22, 24, 26), n=3, bl=None)
for z in np.arange(0.1, 1.0, 0.18): t.hl(z, 0.008, (120, 120, 118))
t.save('board_black')
# lettering band: "JACK FINGLETON SCOREBOARD" in black capitals on white (a painted sign, flat in reality)
from PIL import ImageDraw, ImageFont
im = Image.new('RGB', (2048, 96), (234, 234, 228)); dr = ImageDraw.Draw(im)
try:
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', 64)
except OSError:
    f = ImageFont.load_default()
txt = 'JACK  FINGLETON  SCOREBOARD'; w = dr.textlength(txt, font=f); dr.text(((2048 - w) / 2, 12), txt, fill=(24, 24, 26), font=f)
im.save(OUT + 'sb_lettering.png'); TILE['sb_lettering'] = (1, 1)
im = Image.new('RGB', (256, 256), (236, 236, 230)); dr = ImageDraw.Draw(im)
dr.ellipse([6, 6, 250, 250], outline=(30, 30, 30), width=10)
for k in range(12):
    a = math.radians(k * 30); dr.line([(128 + 100 * math.sin(a), 128 - 100 * math.cos(a)), (128 + 116 * math.sin(a), 128 - 116 * math.cos(a))], fill=(30, 30, 30), width=8)
dr.line([(128, 128), (128, 52)], fill=(20, 20, 20), width=9); dr.line([(128, 128), (186, 150)], fill=(20, 20, 20), width=9)
im.save(OUT + 'clock_face.png'); TILE['clock_face'] = (1, 1)
t = T(1.0, 1.0, (18, 20, 24), n=2, bl=None); t.save('screen')
# ---- the curator's residence: terracotta tiles
t = T(3.0, 3.0, (164, 82, 56), n=8, bl=(0.8, 12))
for z in np.arange(0, 3, 0.3): t.hl(z, 0.05, mul=0.78)
for u in np.arange(0, 3, 0.2): t.vl(u, 0.02, mul=0.9)
t.save('tile_red')

if __name__ == '__main__':
    json.dump(TILE, open(OUT + 'tiles.json', 'w', newline=''), indent=0)
    print(len(TILE), 'textures')
