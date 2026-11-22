"""Hand-made facade tiles for the Marvel rebuild (2026-11-20): one tile = 4 bays x 4 floors (carpark/cladding differ).
RGBA: alpha 255 = glass (rgb is the glass), alpha 0 = wall (rgb multiplies the building's own vertex colour).
Writes tex/fc_<name>.png and prints the tile size in metres for spec 'facades'."""
from PIL import Image
import numpy as np, json
R = np.random.default_rng(11); N = 512
def new(): return np.zeros((N, N, 4), np.float32)
def px(m, tile): return int(round(m / tile * N))
def put(A, x0, y0, x1, y1, rgb, a):
    A[y0:y1, x0:x1, :3] = rgb; A[y0:y1, x0:x1, 3] = a
def glass_pane(A, x0, y0, x1, y1, base, var=8):
    c = np.array(base, np.float32) + R.normal(0, var)
    h = max(1, y1 - y0); g = np.linspace(1.12, 0.9, h)[:, None, None]   # sky reflection brighter at the top of each pane
    A[y0:y1, x0:x1, :3] = np.clip(c[None, None, :] * g, 0, 255); A[y0:y1, x0:x1, 3] = 255
def wall_noise(A, lo=0.9, hi=1.0):
    n = R.random((N // 8, N // 8)); n = np.kron(n, np.ones((8, 8)))
    A[..., :3] = (lo + (hi - lo) * n)[..., None] * 255; A[..., 3] = 0
SIZES = {}
def save(name, A, tw, th):
    Image.fromarray(np.clip(A, 0, 255).astype(np.uint8), 'RGBA').save('tex/fc_%s.png' % name); SIZES[name] = [tw, th]

def curtain(name, glass, bay, floor, spandrel, mull=0.08):
    tw, th = 4 * bay, 4 * floor; A = new(); wall_noise(A, 0.94, 1.0)
    for f in range(4):
        y0 = px(f * floor, th); ys = px(spandrel, th)
        for b in range(4):
            x0 = px(b * bay, tw); m = max(1, px(mull, tw))
            glass_pane(A, x0 + m, y0 + ys, px((b + 1) * bay, tw) - m, px((f + 1) * floor, th), glass)
    save(name, A, tw, th)
curtain('glass_dark', (36, 44, 56), 1.5, 3.6, 0.9)
curtain('glass_teal', (58, 92, 98), 1.5, 3.6, 0.9)
curtain('glass_bronze', (82, 70, 58), 1.5, 3.6, 1.0)
curtain('glass_grey', (92, 102, 112), 3.0, 3.6, 1.2, 0.1)

def punched(name, bay, floor, ww, wh, sill, brick=False):
    tw, th = 4 * bay, 4 * floor; A = new(); wall_noise(A, 0.86, 1.0)
    if brick:   # 230 x 76 mm bricks, stretcher bond, 10 mm mortar
        ch = th * N / th / (th / 0.086); cy = 0.086 / th * N; cx = 0.24 / tw * N
        for r in range(int(N / cy) + 1):
            y0 = int(r * cy); off = (r % 2) * cx / 2
            for c in range(-1, int(N / cx) + 2):
                x0 = int(c * cx + off); A[y0:int(y0 + cy), max(0, x0):max(0, int(x0 + cx)), :3] *= R.uniform(0.82, 1.0)
            A[y0:y0 + 1, :, :3] = 0.72 * 255
        for c in range(int(N / cx) + 2):
            pass
    for f in range(4):
        A[px(f * floor, th):px(f * floor, th) + 2, :, :3] *= 0.8   # slab line
        for b in range(4):
            cx_ = (b + 0.5) * bay
            x0, x1 = px(cx_ - ww / 2, tw), px(cx_ + ww / 2, tw); y0, y1 = px(f * floor + sill, th), px(f * floor + sill + wh, th)
            A[y0 - 3:y0, x0 - 2:x1 + 2, :3] = 0.95 * 255 if not brick else 0.7 * 255   # sill / lintel
            glass_pane(A, x0, y0, x1, y1, (44, 52, 62), 10)
            A[y0:y1, (x0 + x1) // 2:(x0 + x1) // 2 + 2, 3] = 0; A[y0:y1, (x0 + x1) // 2:(x0 + x1) // 2 + 2, :3] = 0.6 * 255   # mullion
    save(name, A, tw, th)
punched('concrete', 3.0, 3.2, 2.3, 1.9, 0.7)
punched('brick', 3.0, 3.2, 1.4, 1.9, 0.7, brick=True)

def panels(name):
    bay, floor = 2.0, 3.4; tw, th = 4 * bay, 4 * floor; A = new(); wall_noise(A, 0.95, 1.0)
    for f in range(4):
        for b in range(4):
            k = R.choice([1.0, 0.8, 0.9, 0.66])
            A[px(f * floor, th):px((f + 1) * floor, th), px(b * bay, tw):px((b + 1) * bay, tw), :3] *= k
            A[px(f * floor, th):px((f + 1) * floor, th), px(b * bay, tw):px(b * bay, tw) + 2, :3] *= 0.7   # panel joint
        A[px(f * floor, th):px(f * floor, th) + 2, :, :3] *= 0.7
        for b in range(4):   # ribbon window 1.2 m
            glass_pane(A, px(b * bay, tw) + 3, px(f * floor + 1.0, th), px((b + 1) * bay, tw) - 3, px(f * floor + 2.2, th), (48, 56, 66), 6)
    save(name, A, tw, th)
panels('panel')

def cladding():
    tw, th = 8.0, 8.0; A = new(); wall_noise(A, 0.94, 1.0)
    rib = 0.25 / tw * N
    for i in range(int(N / rib) + 1):
        x = int(i * rib); A[:, x:x + 3, :3] *= 0.78; A[:, x + 3:x + 5, :3] *= 1.0
    A[N - px(0.4, th):, :, :3] *= 0.85   # flashing at the top
    save('cladding', A, tw, th)
cladding()

def carpark():
    tw, th = 32.0, 3.0; A = new(); wall_noise(A, 0.9, 1.0)
    op0, op1 = px(0.9, th), px(2.8, th)
    A[op0:op1, :, :3] = 0.16 * 255   # open deck: dark interior
    for c in range(4):
        x = px(c * 8.0, tw); A[op0:op1, x:x + px(0.5, tw), :3] = 0.85 * 255   # columns
        for k in range(3):   # parked cars in the gloom
            cx = px(c * 8.0 + 1.5 + k * 2.4, tw)
            col = R.choice([0.5, 0.35, 0.7, 0.25]); A[op1 - px(0.9, th):op1 - px(0.2, th), cx:cx + px(1.9, tw), :3] = col * 255
    A[op1:op1 + 4, :, :3] *= 0.8
    save('carpark', A, tw, th)
carpark()

def plant():   # rooftop plant: louvred grey box sides (alpha 0, multiplies vertex colour)
    A = new(); wall_noise(A, 0.9, 1.0)
    for i in range(0, N, 12): A[i:i + 4, :, :3] *= 0.7
    Image.fromarray(np.clip(A, 0, 255).astype(np.uint8), 'RGBA').save('tex/fc_plant.png'); SIZES['plant'] = [3.0, 3.0]
plant()

def sleepers():   # one tile = 3.2 m across the bed x 2.6 m along; dark brown-grey ballast, concrete sleepers, two rails
    W, L = 3.2, 2.6; A = np.zeros((N, N, 3), np.float32)
    n = R.random((N, N)); A[:] = (np.array([92, 84, 76]) * (0.82 + 0.36 * n[..., None]))
    for k in range(4):   # sleepers 0.24 m wide every 0.65 m, 2.5 m long
        y = int((k * 0.65 + 0.2) / L * N); h = int(0.24 / L * N)
        A[y:y + h, int(0.35 / W * N):int(2.85 / W * N)] = np.array([108, 102, 94]) * (0.92 + 0.08 * n[y:y + h, int(0.35 / W * N):int(2.85 / W * N), None])
    for xr in (1.6 - 0.8, 1.6 + 0.8):   # rails: rusty web, bright running surface
        x = int(xr / W * N); A[:, x - 7:x + 7] = (34, 32, 30); A[:, x - 1:x + 1] = (120, 118, 116)
    Image.fromarray(np.clip(A, 0, 255).astype(np.uint8)).save('tex/rail_bed.png'); SIZES['rail_bed'] = [W, L]
sleepers()
curtain('glass_navy_a', (30, 40, 58), 1.5, 3.6, 0.9, 0.08)
curtain('glass_navy_b', (30, 40, 58), 2.25, 3.8, 1.3, 0.12)
curtain('glass_slate_a', (62, 70, 80), 1.5, 3.6, 0.9, 0.08)
curtain('glass_slate_b', (62, 70, 80), 2.25, 3.8, 1.3, 0.12)
curtain('glass_green_a', (60, 84, 76), 1.5, 3.6, 0.9, 0.08)
curtain('glass_green_b', (60, 84, 76), 2.25, 3.8, 1.3, 0.12)
curtain('glass_blue_a', (52, 78, 110), 1.5, 3.6, 0.9, 0.08)
curtain('glass_blue_b', (52, 78, 110), 2.25, 3.8, 1.3, 0.12)
curtain('glass_smoke_a', (48, 50, 54), 1.5, 3.6, 0.9, 0.08)
curtain('glass_smoke_b', (48, 50, 54), 2.25, 3.8, 1.3, 0.12)
curtain('glass_silver_a', (118, 126, 134), 1.5, 3.6, 0.9, 0.08)
curtain('glass_silver_b', (118, 126, 134), 2.25, 3.8, 1.3, 0.12)
json.dump(SIZES, open('tex/fc_sizes.json', 'w'), indent=1); print(SIZES)
