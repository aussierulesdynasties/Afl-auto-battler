# Hand-made textures for a ground, painted in code (no photo pixels): python3 kit/paint.py tools/grounds/<slug>
# Generalised from riverway/model/paint.py. The common set (concrete, treads, paving, steel, fence mesh, lamps, screen)
# is always painted; each ground's own surfaces come from 'paint' in its <slug>.json: {name: {kind, col, ...}}.
# Kinds: seat (3D shell colour), render (plain wall, joints every 'joint' m), clad (ribbed sheet, ribs vertical),
# panel (composite panels 'pw' x 'ph' m), brick, glass (curtain wall, mullions every 'mull' m), windows (wall with a band
# of windows: 'sill'/'head' m, 'win' wide every 'every' m), deck (roof sheeting), grass, flat (one colour, light noise),
# etfe (translucent roof cushions), timber (glulam), louvre (horizontal slats).
import numpy as np, json, math, os, sys
from PIL import Image
GROUND = os.path.abspath(sys.argv[1]); SLUG = os.path.basename(GROUND)
D = json.load(open(os.path.join(GROUND, 'model', SLUG + '.json')))
R = np.random.default_rng(23); N = 1024
OUT = os.path.join(GROUND, 'model', 'tex') + '/'; os.makedirs(OUT, exist_ok=True); TILE = {}


def save(name, a, tile):
    if a.shape[2] == 4: Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA').save(OUT + name + '.png')
    else: Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(OUT + name + '.png')
    TILE[name] = tile


def noise(h, w, sc, amp):
    g = R.normal(0, 1, (sc, sc)); g = np.tile(g, (3, 3))
    im = Image.fromarray(((g - g.min()) / np.ptp(g) * 255).astype(np.uint8)).resize((3 * w, 3 * h), Image.BICUBIC)
    a = np.asarray(im, float)[h:2 * h, w:2 * w] / 255 - 0.5; return a * amp


def fine(h, w, amp): return R.normal(0, amp, (h, w))


def base(h, w, col, f=3, s=10):
    return np.ones((h, w, 3)) * np.array(col, float) + fine(h, w, f)[:, :, None] + noise(h, w, 16, s)[:, :, None]


def weather(a, streaks=0.10, blotch=14, n=60, top_dark=True):
    h, w, _ = a.shape
    a += noise(h, w, 9, blotch)[:, :, None]
    for _ in range(n):
        x = R.integers(0, w); L = R.uniform(0.15, 0.9) * h; wd = R.integers(2, 9); d = R.uniform(0.3, 1.0) * streaks
        y0 = R.integers(0, max(1, h // 6)) if top_dark else R.integers(0, h)
        ys = np.arange(int(y0), min(h, int(y0 + L))); fall = 1 - (ys - y0) / L
        for xx in range(x, min(w, x + wd)): a[ys, xx] *= (1 - d * fall)[:, None]
    return a


def seat_shell(nm, col):
    a = base(128, 128, col, 2, 6); a[:, :8] *= 0.78; a[:, -8:] *= 0.78; a[:6] *= 0.85; a[-6:] *= 0.7
    a[:, 40:88] *= (1 + 0.10 * np.sin(np.linspace(0, math.pi, 48)))[None, :, None]; save(nm, a, (1, 1))


def concrete(name, col, pu=3.0, pv=1.5, tile=(6.0, 6.0), streak=0.12):
    a = base(N, N, col, 5, 20); xu = N / tile[0]; yv = N / tile[1]
    for k in range(int(tile[0] / pu)): a[:, int(k * pu * xu):int(k * pu * xu) + 4] *= 0.7
    for k in range(int(tile[1] / pv)): a[int(k * pv * yv):int(k * pv * yv) + 4] *= 0.7
    weather(a, streak, 16, 70); save(name, a, tile)


def deck(name, col, pitch=0.3, tile=(6.0, 6.0), grime=18):
    h = w = N; x = np.arange(w) / w * (tile[0] / pitch)
    rib = np.where((x % 1) < 0.16, 0.74, 1.0) + 0.05 * np.cos(2 * math.pi * x)
    a = np.ones((h, w, 3)) * np.array(col, float) * rib[None, :, None] + fine(h, w, 2)[:, :, None] + noise(h, w, 10, grime)[:, :, None]
    a[0:5] *= 0.72
    for _ in range(40):
        xx = R.integers(0, w); L = R.integers(h // 4, h); d = R.uniform(0.05, 0.14); a[:L, xx:xx + R.integers(3, 10)] *= 1 - d
    save(name, a, tile)


# ---- the common set ----
seat_shell('seat_plastic', (120, 120, 120))
a = base(512, 512, (138, 138, 134), 5, 14); a[:10] *= 0.7; weather(a, 0.06, 10, 20, top_dark=False); save('conc_tread', a, (2.0, 0.8))
concrete('conc_wall', (176, 172, 164))
a = base(N, N, (112, 104, 98), 7, 24); p = N / 2.4
for k in range(2): a[int(k * 1.2 * p):int(k * 1.2 * p) + 3] *= 0.7; a[:, int(k * 1.2 * p):int(k * 1.2 * p) + 3] *= 0.7
save('paving', a, (2.4, 2.4))
a = base(N, N, (70, 70, 72), 6, 12); save('asphalt', a, (6.0, 6.0))
h, w = 564, 1024; px = w / 2.0; yy, xx = np.mgrid[:h, :w]; q = 0.06 * px   # chain-link fence, alpha cut-out
wire = (np.abs(((xx + yy) % q) - q / 2) > q / 2 - 1.5) | (np.abs(((xx - yy) % q) - q / 2) > q / 2 - 1.5)
post = (xx < 0.06 * px); rail = (yy < 0.05 * px) | (yy > h - 0.04 * px)
a = np.zeros((h, w, 4)); a[..., :3] = (168, 172, 174); a[..., :3] += fine(h, w, 4)[:, :, None]
a[post | rail, :3] *= 0.9; a[..., 3] = np.where(wire | post | rail, 255, 0); save('mesh', a, (2.0, 1.1))
h, w = 512, 1024; yy, xx = np.mgrid[:h, :w]; pk = w / 2.0 * 0.12   # white pickets 7 cm wide every 12 cm, two rails, alpha
picket = ((xx % pk) < pk * 0.58); rail = ((yy > 0.18 * h) & (yy < 0.24 * h)) | ((yy > 0.74 * h) & (yy < 0.80 * h))
a = np.zeros((h, w, 4)); a[..., :3] = (236, 236, 232); a[..., :3] += fine(h, w, 3)[:, :, None]; a[rail, :3] *= 0.92
a[..., 3] = np.where(picket | rail, 255, 0); save('pickets', a, (2.0, 1.1))
deck('roof_soffit', (78, 82, 88), grime=10)
a = base(512, 1024, (226, 228, 226), 4, 18); xu = 1024 / 4.0
for k in range(2): a[:, int(k * 2 * xu):int(k * 2 * xu) + 6] *= 0.66
a[480:] *= 0.8; weather(a, 0.16, 16, 40); save('fascia', a, (4.0, 2.0))
for nm, col in (('steel_white', (230, 232, 230)), ('steel_galv', (150, 154, 158)), ('paint_white', (232, 232, 228)), ('steel_dark', (58, 60, 64))):
    a = base(256, 256, col, 6, 26); a[:, 120:126] *= 0.7; a[:, 0:4] *= 0.75; weather(a, 0.16, 18, 16); save(nm, a, (2.0, 2.0))
a = np.ones((N, N, 3)) * np.array((230, 230, 226), float); cu, cv = N / 8, N / 4
for i in range(8):
    for j in range(4):
        x0, y0 = int(i * cu + 8), int(j * cv + 10); x1, y1 = int((i + 1) * cu - 8), int((j + 1) * cv - 10)
        a[y0:y1, x0:x1] = (170, 176, 180); a[y0 + 8:y1 - 8, x0 + 8:x1 - 8] = (86, 92, 98)
save('lamps', a, (1, 1))
a = base(512, 512, (24, 26, 30), 4, 14)
for k in range(0, 512, 16): a[:, k:k + 2] *= 0.6; a[k:k + 2] *= 0.6
a[:10] = (60, 62, 66); a[-10:] = (60, 62, 66); a[:, :10] = (60, 62, 66); a[:, -10:] = (60, 62, 66); save('screen_off', a, (2.0, 2.0))
a = base(512, 512, (60, 62, 66), 3, 10)
for k in range(0, 512, 128): a[:, k:k + 3] *= 0.7; a[k:k + 3] *= 0.7
save('board_back', a, (2.0, 2.0))
a = base(N, N, (92, 128, 64), 6, 18); xu = N / 6.0; a[:, :int(3 * xu)] *= 1.015
for _ in range(60):
    cx, cy, rr = R.integers(0, N), R.integers(0, N), R.integers(6, 30); yy, xx = np.ogrid[:N, :N]
    a[((yy - cy) ** 2 + (xx - cx) ** 2) < rr * rr] *= R.uniform(0.88, 1.08)
save('grass_bank', a, (6.0, 6.0))
a = base(N, N, (98, 126, 70), 5, 26)   # plain grass beyond the ground and under the field: no mown bands, so no stripes from afar
for _ in range(80):
    cx, cy, rr = R.integers(0, N), R.integers(0, N), R.integers(10, 60); yy, xx = np.ogrid[:N, :N]
    a[((yy - cy) ** 2 + (xx - cx) ** 2) < rr * rr] *= R.uniform(0.9, 1.06)
save('ground_grass', a, (12.0, 12.0))


# ---- the ground's own surfaces ----
def own(name, P):
    k = P['kind']; col = P['col']
    if k == 'seat': seat_shell(name, col)
    elif k == 'render':
        j = P.get('joint', 3.0); tile = P.get('tile', (6.0, 3.6)); a = base(616, 1024, col, 3, 10); pu = 1024 / tile[0]
        for i in range(int(tile[0] / j)): a[:, int(i * j * pu):int(i * j * pu) + 3] *= 0.84
        if P.get('streaks', True): weather(a, 0.08, 10, 30)
        save(name, a, tuple(tile))
    elif k == 'clad':
        tile = P.get('tile', (3.0, 3.0)); a = base(N, N, col, 2, 8); x = np.arange(N) / N * (tile[0] / P.get('rib', 0.25))
        a *= (np.where((x % 1) < 0.2, 0.8, 1.0) + 0.04 * np.cos(2 * math.pi * x))[None, :, None]; weather(a, 0.06, 8, 20); save(name, a, tuple(tile))
    elif k == 'panel':
        pw, ph = P.get('pw', 1.2), P.get('ph', 1.2); tile = (2 * pw, 2 * ph); a = base(512, 512, col, 2, 6)
        for t in (0, 256): a[:, t:t + 4] *= 0.66; a[t:t + 4] *= 0.66
        weather(a, 0.04, 6, 12); save(name, a, tile)
    elif k == 'brick':
        a = base(512, 1024, col, 10, 14); bh = 512 / 12; bw = 1024 / 8
        for r in range(12):
            y = int(r * bh); a[y:y + 4] = P.get('mortar', (190, 184, 172))
            off = (bw / 2) * (r % 2)
            for c in range(9):
                x = int(c * bw + off) % 1024; a[y:int(y + bh), x:x + 4] = P.get('mortar', (190, 184, 172))
                a[y + 4:int(y + bh), x + 4:min(1024, int(x + bw))] *= R.uniform(0.9, 1.08)
        save(name, a, (1.84, 0.92))
    elif k == 'glass':
        m = P.get('mull', 1.5); tile = (2 * m, P.get('floor', 3.6)); a = base(616, 1024, col, 2, 10)
        a += np.linspace(14, -10, 616)[:, None, None]   # sky reflection brighter at the top
        fc = P.get('frame', (60, 64, 70)); pu = 1024 / tile[0]
        for i in range(2): a[:, int(i * m * pu):int(i * m * pu) + 8] = fc
        a[:10] = fc; a[-26:] = P.get('spandrel', fc); save(name, a, tile)
    elif k == 'windows':
        tile = (P.get('every', 3.0), P.get('floor', 3.6)); W, H = 1024, int(1024 * tile[1] / tile[0]); a = base(H, W, col, 3, 10)
        pu = W / tile[0]; pv = H / tile[1]; wc = P.get('win_col', (44, 54, 62)); fc = P.get('frame', (200, 200, 196))
        x0 = int((tile[0] - P.get('win', 1.8)) / 2 * pu); x1 = int(W - x0); y0 = int(H - P.get('head', 2.6) * pv); y1 = int(H - P.get('sill', 1.0) * pv)
        a[y0:y1, x0:x1] = fc; a[y0 + 6:y1 - 6, x0 + 6:x1 - 6] = np.array(wc) + fine(y1 - y0 - 12, x1 - x0 - 12, 3)[:, :, None]
        a[y0 + 6:y0 + (y1 - y0) // 3, x0 + 6:x0 + (x1 - x0) // 3] += 16
        if P.get('streaks', True): weather(a, 0.06, 8, 16)
        save(name, a, tile)
    elif k == 'deck': deck(name, col, P.get('pitch', 0.3), tuple(P.get('tile', (6.0, 6.0))), P.get('grime', 18))
    elif k == 'grass':
        a = base(N, N, col, 6, 18)
        for _ in range(60):
            cx, cy, rr = R.integers(0, N), R.integers(0, N), R.integers(6, 30); yy, xx = np.ogrid[:N, :N]
            a[((yy - cy) ** 2 + (xx - cx) ** 2) < rr * rr] *= R.uniform(0.88, 1.08)
        save(name, a, (6.0, 6.0))
    elif k == 'flat':
        a = base(256, 256, col, 2, P.get('noise', 6)); save(name, a, tuple(P.get('tile', (2.0, 2.0))))
    elif k == 'etfe':   # translucent cushions 3 x 3 m in a diamond net, alpha about 0.45
        a = np.zeros((512, 512, 4)); a[..., :3] = np.array(col, float) + fine(512, 512, 3)[:, :, None]; a[..., 3] = P.get('alpha', 110)
        yy, xx = np.mgrid[:512, :512]; net = (np.abs((xx + yy) % 256 - 128) < 3) | (np.abs((xx - yy) % 256 - 128) < 3)
        a[net, :3] = (210, 212, 214); a[net, 3] = 235; a[..., :3] += np.where(((xx + yy) % 256) < 60, 12, 0)[..., None]
        save(name, a, (6.0, 6.0))
    elif k == 'timber':
        a = base(256, 1024, col, 4, 10); a += (6 * np.sin(np.linspace(0, 40, 256)))[:, None, None]; save(name, a, (4.0, 1.0))
    elif k == 'louvre':
        # vertical fins 'fin' m apart with dark gaps between them, and a dark slab edge every 'floor' m
        fin, fl = P.get('fin', 1.0), P.get('floor', 4.0); a = base(512, 512, col, 2, 6); x = np.arange(512) / 512 * (4.0 / fin)
        a *= np.where((x % 1) < 0.28, 0.42, 1.0 - 0.12 * (x % 1))[None, :, None]
        for t in range(0, 512, int(512 * fl / 4.0)): a[t:t + 12] *= 0.6
        weather(a, 0.05, 6, 14); save(name, a, (4.0, 4.0))
    else:
        raise SystemExit('unknown paint kind ' + k)


for name, P in D.get('paint', {}).items(): own(name, P)
json.dump(TILE, open(OUT + 'tiles.json', 'w', newline=''), indent=0)
print(len(TILE), 'textures in', OUT)
