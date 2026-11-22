"""v3 hand-made tiles (texture session FAIL 2026-11-20): varied curtain walls, banded concrete, roof membrane,
shed ribs, car-park deck bays, parapet, higher-contrast rail bed. Appends sizes to tex/fc_sizes.json."""
from PIL import Image
import numpy as np, json
R = np.random.default_rng(23); N = 512
SIZES = json.load(open('tex/fc_sizes.json'))
for k in ('glass_silver_a', 'glass_silver_b'): SIZES.pop(k, None)
def px(m, t): return int(round(m / t * N))
def wall(lo, hi, cell=8):
    A = np.zeros((N, N, 4), np.float32); n = np.kron(R.random((N // cell, N // cell)), np.ones((cell, cell)))
    A[..., :3] = ((lo + (hi - lo) * n) * 255)[..., None]; return A
def pane(A, x0, y0, x1, y1, base, var):
    c = np.array(base, np.float32) * R.uniform(1 - var, 1 + var) + R.normal(0, 4, 3)
    g = np.linspace(1.15, 0.85, max(1, y1 - y0))[:, None, None]
    A[y0:y1, x0:x1, :3] = np.clip(c * g, 0, 255); A[y0:y1, x0:x1, 3] = 255
def save(name, A, tw, th, mode='RGBA'):
    Image.fromarray(np.clip(A, 0, 255).astype(np.uint8), mode).save('tex/%s.png' % name)
    if name.startswith('fc_'): SIZES[name[3:]] = [tw, th]

def curtain2(name, glass, bays, floor, spandrel, mull, var=0.18, nfl=4):
    """Varied bay widths, slim mullions, transoms, per-pane tint variation; spandrel = wall colour (vertex colour)."""
    tw, th = float(sum(bays)), nfl * floor; A = wall(0.9, 1.0); m = max(2, px(mull, tw))
    for f in range(nfl):
        y0 = px(f * floor, th); ys = y0 + px(spandrel, th); y1 = px((f + 1) * floor, th)
        A[y0:ys, :, :3] *= R.uniform(0.85, 1.0)   # spandrel panel shade
        A[ys - 2:ys, :, :3] = 0.55 * 255          # transom line
        x = 0.0
        for bw in bays:
            x0, x1 = px(x, tw), px(x + bw, tw); pane(A, x0 + m // 2, ys, x1 - m // 2, y1, glass, var)
            A[ys:y1, x0:x0 + m, 3] = 0; A[ys:y1, x0:x0 + m, :3] = 0.5 * 255   # mullion (wall colour, dark)
            x += bw
    save('fc_' + name, A, tw, th)
CW = {'navy': (30, 40, 58), 'slate': (62, 70, 80), 'green': (60, 84, 76), 'blue': (52, 78, 110), 'smoke': (48, 50, 54),
      'teal': (58, 92, 98), 'bronze': (82, 70, 58), 'ink': (24, 28, 34)}
LAY = {'c': ([1.2, 1.8, 1.2, 1.8], 3.7, 1.1, 0.07), 'd': ([3.0, 3.0, 1.5, 3.0], 3.9, 0.8, 0.10),
       'e': ([1.0, 1.0, 2.6, 1.0, 1.0, 2.6], 3.5, 1.4, 0.06)}
for t, g in CW.items():
    for l, (bays, fl, sp, mu) in LAY.items(): curtain2('glass_%s_%s' % (t, l), g, bays, fl, sp, mu)

def banded(name, floor=3.6, band=1.5, bay=1.5, glass=(40, 48, 58)):
    """Banded concrete: solid concrete floor bands with formwork joints, continuous ribbon glazing between."""
    tw, th = 8 * bay, 4 * floor; A = wall(0.88, 1.0, 4)
    for f in range(4):
        y0 = px(f * floor, th); yb = y0 + px(band, th); y1 = px((f + 1) * floor, th)
        A[y0:y0 + 3, :, :3] *= 0.72; A[yb - 2:yb, :, :3] *= 0.8   # band edges
        for k in range(0, N, px(1.2, tw)): A[y0:yb, k:k + 1, :3] *= 0.85   # formwork joints
        for b in range(8):
            x0, x1 = px(b * bay, tw), px((b + 1) * bay, tw); pane(A, x0 + 2, yb + 3, x1 - 2, y1, glass, 0.12)
            A[yb:y1, x0:x0 + 3, 3] = 0; A[yb:y1, x0:x0 + 3, :3] = 0.6 * 255
    save('fc_' + name, A, tw, th)
banded('banded_a'); banded('banded_b', 3.3, 1.1, 2.0, (56, 64, 72)); banded('banded_c', 4.0, 1.8, 1.25, (34, 38, 44))

def parapet():   # 1.1 m parapet: concrete with a light coping line on top, stains running down
    A = wall(0.84, 1.0, 4)
    A[:px(0.12, 1.2), :, :3] = 1.0 * 255
    for k in R.integers(0, N, 40): A[px(0.12, 1.2):, k:k + R.integers(3, 10), :3] *= R.uniform(0.75, 0.92)
    save('fc_parapet', A, 6.0, 1.2)
parapet()

def membrane():   # flat roof 24 m tile: 1.0 m membrane sheets, lapped seams, ponding/dirt stains, drains
    A = np.ones((N, N, 4), np.float32) * 255; A[..., 3] = 0; s = N / 24.0
    n = np.kron(R.random((N // 16, N // 16)), np.ones((16, 16))); A[..., :3] *= (0.92 + 0.08 * n)[..., None]
    for i in range(24):
        x = int(i * s); A[:, x:x + 2, :3] *= 0.78; A[:, x + 2:x + 3, :3] *= 1.05   # lapped seam
    for _ in range(14):   # ponding stains
        cx, cy, r = R.integers(0, N), R.integers(0, N), R.integers(20, 70); yy, xx = np.ogrid[:N, :N]
        d = np.hypot(((xx - cx + N // 2) % N) - N // 2, ((yy - cy + N // 2) % N) - N // 2) / r
        A[..., :3] *= (1 - 0.18 * np.clip(1 - d, 0, 1) ** 1.5)[..., None]
    for _ in range(4):
        x, y = R.integers(10, N - 10, 2); A[y - 4:y + 4, x - 4:x + 4, :3] = 0.35 * 255   # drains
    save('roof_membrane', A, 24, 24)
membrane()

def shed():   # trapezoidal metal deck, 24 m tile: rib every 0.25 m... at orbit range: 1 px pairs, laps every 6 m, rust streaks
    A = np.ones((N, N, 4), np.float32) * 255; A[..., 3] = 0; s = N / 24.0
    for i in range(int(24 / 0.5)):
        x = int(i * 0.5 * s); A[:, x:x + 2, :3] *= 0.7; A[:, x + 2:x + 4, :3] *= 1.08
    for j in range(4): A[int(j * 6 * s):int(j * 6 * s) + 2, :, :3] *= 0.75   # end laps
    for _ in range(60):   # weathering streaks along the fall
        x = R.integers(0, N); w = R.integers(2, 8); y0 = R.integers(0, N); L = R.integers(40, 200)
        ys = np.arange(y0, y0 + L) % N; A[ys[:, None], (np.arange(x, x + w) % N)[None, :], :3] *= R.uniform(0.72, 0.9)
    n = np.kron(R.random((N // 32, N // 32)), np.ones((32, 32))); A[..., :3] *= (0.85 + 0.15 * n)[..., None]
    save('roof_shed', A, 24, 24)
shed()

def deck():   # car-park roof deck 32 m tile: asphalt, 2.6 x 5.4 m bays in two rows each side of a 6.4 m aisle
    A = np.ones((N, N, 4), np.float32); A[..., 3] = 0; s = N / 32.0
    n = R.random((N, N)); A[..., :3] = (0.42 + 0.06 * n)[..., None] * 255
    rows = [(2.0, 7.4), (13.8, 19.2), (25.6, 31.0)]
    for y0, y1 in rows:
        A[int(y0 * s):int(y0 * s) + 2, :, :3] = 0.95 * 255
        for i in range(int(32 / 2.6) + 1):
            x = int(i * 2.6 * s); A[int(y0 * s):int(y1 * s), x:x + 2, :3] = 0.95 * 255
    for y in (10.6, 22.4):   # aisle arrows
        A[int(y * s) - 1:int(y * s) + 1, ::24, :3] = 0.9 * 255
    for _ in range(40):   # a few parked cars
        r = rows[R.integers(0, 3)]; i = R.integers(0, 12); c = R.choice([0.25, 0.6, 0.85, 0.4, 0.7])
        A[int((r[0] + 0.6) * s):int((r[1] - 0.6) * s), int((i * 2.6 + 0.4) * s):int((i * 2.6 + 2.2) * s), :3] = c * 255
    save('roof_deck', A, 32, 32)
deck()

def railbed():   # 4.4 m across x 2.6 m along: dark ballast bed, concrete sleepers every 0.65 m, rails at 1.6 m gauge
    W, L = 4.4, 2.6; A = np.zeros((N, N, 3), np.float32); n = R.random((N, N))
    A[:] = np.array([62, 57, 52]) * (0.75 + 0.5 * n[..., None])
    sx = lambda m: int(m / W * N)
    for k in range(4):
        y = int((k * 0.65 + 0.2) / L * N); h = int(0.26 / L * N)
        A[y:y + h, sx(0.95):sx(3.45)] = np.array([150, 146, 138]) * (0.9 + 0.1 * n[y:y + h, sx(0.95):sx(3.45), None])
    for xr in (2.2 - 0.8, 2.2 + 0.8):
        x = sx(xr); A[:, x - 6:x + 6] = (40, 34, 30); A[:, x - 2:x + 2] = (170, 168, 164)
    edge = np.clip(np.minimum(np.arange(N), N - 1 - np.arange(N)) / sx(0.5), 0, 1)   # shoulders fade to lighter gravel
    A[:] = A * edge[None, :, None] + np.array([128, 120, 108]) * (1 - edge[None, :, None]) * (0.85 + 0.3 * n[..., None])
    save('rail_bed', A, W, L, 'RGB'); SIZES['rail_bed'] = [W, L]
railbed()
json.dump(SIZES, open('tex/fc_sizes.json', 'w'), indent=1); print(len(SIZES), sorted(SIZES))
