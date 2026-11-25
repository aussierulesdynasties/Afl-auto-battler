# Adelaide Oval for the game: the hand-made shaders of .claude/review/adelaide/tools/shade.py painted as tiling detail
# textures, one per material kind (no photo pixels). Each texture is grey detail (about 0.9 average) that the game
# multiplies by the model's own vertex colours, so the stands keep the colours read off the photos.
# python3 tools/grounds/adelaide/paint.py  -> tools/grounds/adelaide/tex/k<kind>.png + tiles.json (metres per tile)
import numpy as np, json, os, math
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'tex'); os.makedirs(OUT, exist_ok=True)
R = np.random.default_rng(7); N = 512; TILES = {}


def noise(n, cells, amp):   # tileable smooth noise
    g = R.normal(0, 1, (cells, cells)); g = np.tile(g, (3, 3))
    im = Image.fromarray(((g - g.min()) / np.ptp(g) * 255).astype(np.uint8)).resize((3 * n, 3 * n), Image.BICUBIC)
    return (np.asarray(im, float)[n:2 * n, n:2 * n] / 255 - 0.5) * amp


def grain(n, amp): return R.normal(0, amp, (n, n))


def cells(n, tile, pu, pv, spread):   # one tone per panel pu x pv metres
    ys, xs = np.mgrid[0:n, 0:n]; iu = (xs / n * tile[0] // pu).astype(int); iv = (ys / n * tile[1] // pv).astype(int)
    T = R.uniform(1 - spread, 1 + spread, (iv.max() + 1, iu.max() + 1)); return T[iv, iu]


def joints(a, tile, pu, pv, k=0.55, w=2):
    n = a.shape[0]
    for x in np.arange(0, tile[0], pu): a[:, int(x / tile[0] * n):int(x / tile[0] * n) + w] *= k
    for y in np.arange(0, tile[1], pv): a[int(y / tile[1] * n):int(y / tile[1] * n) + w] *= k
    return a


def streaks(a, n_runs, depth):
    n = a.shape[0]
    for _ in range(n_runs):
        x = R.integers(0, n); L = R.uniform(0.2, 0.8) * n; wd = R.integers(2, 7); y0 = R.integers(0, n)
        ys = np.arange(int(y0), int(y0 + L)) % n; fall = 1 - (np.arange(len(ys)) / L)
        for xx in range(x, x + wd): a[ys, xx % n] *= 1 - depth * fall
    return a


def save(kind, a, tile, rgb=None):
    a = np.clip(a, 0, 1)
    img = (a[:, :, None] * (np.array(rgb) if rgb is not None else np.ones(3)) * 255) if a.ndim == 2 else a * 255
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(os.path.join(OUT, 'k%d.png' % kind)); TILES[kind] = tile


# 0 plain painted surfaces: sheets 2.4 x 1.2 m, each faded its own way, chalky patches
t = (9.6, 9.6); a = 0.9 * cells(N, t, 2.4, 1.2, 0.07) + noise(N, 8, 0.12) + grain(N, 0.015); save(0, a, t)
# (the Hill's old painted seat rows, kind 1 until 2026-11-21: still drawn so the random stream, and every texture
# after it, stays as it was; kind 1 is now the paving, painted at the end)
_ = noise(N, 6, 0.05) + grain(N, 0.02)
# 2 concrete: 4 x 3 m panels, each cast its own tone, dark joints, mottle, aggregate, rain runs
t = (16.0, 12.0); a = 0.88 * cells(N, t, 4.0, 3.0, 0.09) * (1 + noise(N, 10, 0.25)) * (1 + grain(N, 0.06))
a = joints(streaks(a, 40, 0.2), t, 4.0, 3.0); save(2, a, t)
# 3 roof membrane: seams every 1.6 m, welded laps, cross welds every 4 m, dust drifts
t = (12.8, 16.0); a = 0.95 * (1 + noise(N, 6, 0.08)) * (1 + grain(N, 0.015)); n = N
for x in np.arange(0, t[0], 1.6):
    c = int(x / t[0] * n); a[:, c:c + 2] *= 0.75; a[:, c + 2:c + 5] *= 0.94
for y in np.arange(0, t[1], 4.0): a[int(y / t[1] * n)] *= 0.85
save(3, a, t)
# 4 steel: sheets 1.2 x 2.4 m each its own tone, seams, grime toward each sheet's bottom
t = (9.6, 9.6); a = 0.9 * cells(N, t, 1.2, 2.4, 0.07) * (1 + noise(N, 8, 0.12))
yy = (np.mgrid[0:N, 0:N][0] / N * t[1]) % 2.4 / 2.4; a *= 1 - 0.12 * yy ** 2
a = joints(a, t, 1.2, 2.4, 0.7); save(4, a, t)
# 5 glass: dark panes 1.5 x 3.2 m in aluminium frames (frame light, pane dark against the vertex colour)
t = (6.0, 6.4); a = np.full((N, N), 0.75) + noise(N, 4, 0.12); n = N
for x in np.arange(0, t[0], 1.5): c = int(x / t[0] * n); a[:, c:c + 4] = 1.0
for y in np.arange(0, t[1], 3.2): c = int(y / t[1] * n); a[c:c + 5] = 1.0
save(5, a, t)
# 6 brick: 230 x 76 mm bricks, 10 mm mortar, stretcher bond; colour from the vertex
t = (2.4, 2.4); ys, xs = np.mgrid[0:N, 0:N] / N * 2.4; row = np.floor(ys / 0.086)
off = np.where(row % 2 == 0, 0, 0.12); bx = np.floor((xs + off) / 0.24)
tone = R.uniform(0.82, 1.08, (int(row.max()) + 2, 12))[row.astype(int), (bx % 12).astype(int)]
mort = ((ys % 0.086) < 0.01) | (((xs + off) % 0.24) < 0.01)
a = np.where(mort, 1.25, tone) * (1 + grain(N, 0.04)) * 0.85; save(6, a, t)
# 7 grass: fine blades and soft patches (the match draws its own turf; this is the lawn outside the fence)
t = (10.0, 10.0); save(7, 0.9 + noise(N, 10, 0.12) + grain(N, 0.05), t)
# 8 fins: vertical fins 0.45 m apart with dark gaps
t = (3.6, 3.6); xs = np.mgrid[0:N, 0:N][1] / N * 3.6; a = np.where((xs % 0.45) < 0.32, 0.95, 0.4) + noise(N, 6, 0.06); save(8, a, t)
# 9 timber: boards 0.15 m with grain
t = (2.4, 2.4); ys, xs = np.mgrid[0:N, 0:N] / N * 2.4
a = 0.85 * R.uniform(0.85, 1.1, 17)[(ys // 0.15).astype(int) % 17] * (1 + 0.06 * np.sin(xs * 40 + noise(N, 8, 6))) * ((ys % 0.15) > 0.006)
save(9, a + 0.05, t)
# 10 copper cladding: vertical panels 0.6 m wide, each its own tone, dark standing seams
t = (7.2, 7.2); a = 0.9 * cells(N, t, 0.6, 7.2, 0.1) * (1 + noise(N, 8, 0.1)); a = joints(a, t, 0.6, 100, 0.4, 3); save(10, a, t)
# 11 banded stone: courses 0.6 m, block joints every 1.2 m, each its own tone
t = (7.2, 7.2); a = 0.9 * cells(N, t, 1.2, 0.6, 0.07) * (1 + noise(N, 8, 0.1)) * (1 + grain(N, 0.03)); a = joints(a, t, 1.2, 0.6, 0.7); save(11, a, t)
# 12 turf (the Hill): worn patches about 2 m across, blade noise
t = (12.0, 12.0); a = 0.92 + noise(N, 6, 0.25) + grain(N, 0.06); save(12, a, t)
# 13 scoreboard board: painted panels 1.2 x 0.55 m, dark joints, faded unevenly
t = (4.8, 4.4); a = 0.9 * cells(N, t, 1.2, 0.55, 0.05) * (1 + noise(N, 6, 0.06)); a = joints(a, t, 1.2, 0.55, 0.6); save(13, a, t)
# 1 paving (the Hill concourse and paths; kind 1 was the painted Hill seat rows, now real seats): 400 x 400 mm pale concrete pavers, stack bond, each its own tone, fine
# sand joints, light wear; no streaks (director 2026-11-21: "terrible texture work")
t = (4.8, 4.8); a = 0.92 * cells(N, t, 0.4, 0.4, 0.05) * (1 + noise(N, 12, 0.05)) * (1 + grain(N, 0.025))
a = joints(a, t, 0.4, 0.4, 0.78, 1); save(1, a, t)
# 14 ivy (the Western Grandstand's arcade, Google Earth: green with climbing plants): overlapping leaves 6-11 cm,
# each its own tone, dark gaps between; a tile 2 m square. Drawn last so every texture before it keeps its random stream
t = (2.0, 2.0); a = np.full((N, N), 0.42) + noise(N, 6, 0.06); ys, xs = np.mgrid[0:N, 0:N]
for _ in range(2600):
    cx, cy = R.uniform(0, N, 2); rr = R.uniform(0.03, 0.055) / t[0] * N; ang = R.uniform(0, math.pi); tone = R.uniform(0.78, 1.2)
    x0, x1, y0, y1 = int(cx - rr - 1), int(cx + rr + 2), int(cy - rr - 1), int(cy + rr + 2)
    X, Y = np.meshgrid(np.arange(x0, x1), np.arange(y0, y1)); dx, dy = X - cx, Y - cy
    u = dx * math.cos(ang) + dy * math.sin(ang); v = -dx * math.sin(ang) + dy * math.cos(ang)
    inside = (u / rr) ** 2 + (v / (rr * 0.75)) ** 2 < 1
    shade = tone * (1.0 - 0.18 * (v / rr))   # each leaf lit from above
    a[Y[inside] % N, X[inside] % N] = shade[inside]
save(14, a * (1 + grain(N, 0.03)), t)
json.dump(TILES, open(os.path.join(OUT, 'tiles.json'), 'w'), indent=1); print('painted', sorted(TILES))
