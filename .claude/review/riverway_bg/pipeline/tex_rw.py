"""Hand-painted (procedural, no photo pixels) Riverway textures. Facade convention (mat_facade): RGB is a multiplier on the
building's own colour where alpha 0; alpha 1 = glass shown as painted.
Writes tex/rw/: queens_0..3.png (whole-wall Queenslander: stumps/battens, 0.2 m weatherboards, windows, verandah rail, eave
shadow), com_<i>.png + com.json (tile metres + kind) for N commercial/civic/industrial facades, roof_metal_rib.png (3 m tile,
ribs every 0.2 m), water_ripple_n.png (8 m normal tile), pool.png (8 m), water_col.png is built later from the ground mask.
python -E tex_rw.py N"""
import sys, os, json, math
import numpy as np
from PIL import Image, ImageFilter
N = int(sys.argv[1]) if len(sys.argv) > 1 else 120
O = 'tex/rw'; os.makedirs(O, exist_ok=True)
rng = np.random.default_rng(42)
def noise(h, w, s, r):   # smooth value noise, feature size s px
    g = r.random((h // s + 3, w // s + 3))
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize(((w // s + 3) * s, (h // s + 3) * s), Image.BICUBIC), float)[:h, :w] / 255
def save(a, alpha, p):
    a = np.clip(a, 0, 255).astype(np.uint8)
    if alpha is None: Image.fromarray(a).save(p)
    else: Image.fromarray(np.dstack([a, (np.clip(alpha, 0, 1) * 255).astype(np.uint8)])).save(p)

# ---------- Queenslanders: whole wall, v 0 = ground, 1 = eave. 1024 x 1024 = 3.6 m wide x wall height ----------
for k in range(4):
    r = np.random.default_rng(100 + k); H = W = 1024
    yy, xx = np.mgrid[0:H, 0:W]; v = 1 - yy / H; xm = xx / W * 3.6
    img = np.ones((H, W, 3)) * 246; A = np.zeros((H, W))
    stump = 0.30 + 0.05 * k % 0.1   # under-house band (stumps + battens)
    # weatherboards 0.2 m: wall height ~4.5 m => 1024 px; board = 0.2/4.5*1024 = 45.5 px; shadow line under each lap
    bp = 1024 * 0.2 / 4.5; ph = (yy % bp) / bp
    img *= (0.80 + 0.20 * np.clip(ph * 3, 0, 1))[..., None] * 0 + 1
    img[(ph > 0.86)] *= 0.80; img[(ph > 0.93)] *= 0.88
    img *= (0.94 + 0.08 * noise(H, W, 48, r))[..., None]
    # under-house: dark void behind vertical battens every 0.1 m, stumps
    ub = v < stump
    bat = ((xm * 10) % 1) < 0.45
    img[ub & ~bat] = [70, 66, 60]; img[ub & bat] *= 0.92
    for sx in (0.3, 1.8, 3.3):
        img[ub & (np.abs(xm - sx) < 0.07)] = [150, 146, 138]
    img[(v >= stump) & (v < stump + 0.02)] = [200, 198, 192]   # bearer/floor line
    # verandah rail band + balusters at floor + 1 m
    rv = stump + 0.20
    img[(v > rv) & (v < rv + 0.022)] = [236, 236, 232]
    bal = (v > stump + 0.03) & (v < rv) & (((xm * 9) % 1) < 0.22)
    img[bal] = [240, 240, 236]
    # windows (1.2 x 1.1 m, louvred) with white frames
    nwin = 1 + (k % 2); xs = [1.8] if nwin == 1 else [0.95, 2.65]
    w0, w1 = stump + 0.20, stump + 0.20 + 0.29
    for cx in xs:
        wx = np.abs(xm - cx) < 0.6; wy = (v > w0) & (v < w1)
        fr = wx & wy & ~((np.abs(xm - cx) < 0.54) & (v > w0 + 0.012) & (v < w1 - 0.012))
        gl = wx & wy & ~fr
        img[fr] = [250, 250, 248]
        lv = ((yy % 14) < 4)
        img[gl] = [58, 70, 78]; img[gl & lv] = [110, 124, 132]; A[gl] = 1
        img[(np.abs(xm - cx) < 0.66) & (v > w1) & (v < w1 + 0.03)] = [160, 156, 150]   # hood shadow
    # eave shadow band at the top (verandah roof overhang)
    es = v > 0.90; img[es] *= (0.55 + 0.4 * ((1 - v[es]) / 0.10))[..., None]
    rafters = es & (((xm * 1.667) % 1) < 0.05); img[rafters] *= 0.8
    save(img, A, f'{O}/queens_{k}.png')

# ---------- commercial / civic / industrial: one bay x one storey per tile ----------
meta = []
for i in range(N):
    r = np.random.default_rng(1000 + i)
    kind = ['render', 'panel', 'cladding', 'glazed'][i % 4] if i >= 4 else ['render', 'panel', 'cladding', 'glazed'][i]
    bay = float(r.uniform(3.0, 6.5)); st = float(r.uniform(3.4, 4.2)); S = 512
    H = W = S; yy, xx = np.mgrid[0:H, 0:W]; u = xx / W; v = 1 - yy / H
    tone = r.uniform(0.86, 1.0)
    img = np.ones((H, W, 3)) * 245 * tone; A = np.zeros((H, W))
    img *= (0.93 + 0.09 * noise(H, W, int(r.integers(30, 90)), r))[..., None]
    streak = noise(H, W, 6, r)[:, :] * (1 - v) ** 0
    img *= (1 - 0.025 * noise(1, W, 9, r)[0][None, :, None] * (1 - v)[..., None])   # rain streaks under sills
    if kind == 'cladding':   # vertical ribbed sheet every 0.2 m, a roller door on some bays, high strip window
        rib = ((u * bay / 0.2) % 1); img *= (0.84 + 0.16 * (rib > 0.25))[..., None]
        if r.random() < 0.5:
            dw = r.uniform(0.45, 0.75); d = (np.abs(u - 0.5) < dw / 2) & (v < min(0.85, 3.0 / st))
            img[d] = np.array([150, 152, 150]) * r.uniform(0.8, 1.1); img[d & ((yy % 9) < 2)] *= 0.8
        sw = (v > 0.86) & (v < 0.93) & (np.abs(u - 0.5) < 0.4); img[sw] = [70, 82, 92]; A[sw] = 1
    else:
        if kind == 'panel':
            pw = float(r.choice([1.2, 1.5, 2.4, 3.0])); jx = ((u * bay / pw) % 1) < 0.012; jy = (v % 0.5) < 0.008
            img[jx | jy] *= 0.78
        if kind == 'render':
            img[(v > 0.0) & (v < 0.012)] *= 0.8
        ww = r.uniform(0.35, 0.8) if kind != 'glazed' else 0.92; wh = r.uniform(0.32, 0.55) if kind != 'glazed' else 0.78
        sill = r.uniform(0.25, 0.4) if kind != 'glazed' else 0.1
        nm = int(r.integers(1, 4)) if kind != 'glazed' else int(r.integers(2, 5))
        g = (np.abs(u - 0.5) < ww / 2) & (v > sill) & (v < sill + wh)
        mull = (((u - 0.5 + ww / 2) / ww * nm) % 1 < 0.04) & g
        gc = np.array([[52, 66, 78], [70, 88, 96], [40, 52, 58], [92, 108, 112]][int(r.integers(0, 4))]) * r.uniform(0.85, 1.1)
        img[g] = gc; img[g] *= (0.9 + 0.2 * (v[g] - sill) / wh)[..., None]; A[g] = 1
        img[mull] = [200, 200, 196]; A[mull] = 0
        fr = (np.abs(u - 0.5) < ww / 2 + 0.015) & (v > sill - 0.02) & (v < sill + wh + 0.015) & ~g & ~mull
        img[fr] = np.array([210, 210, 206]) * r.uniform(0.6, 1.0)
        if r.random() < 0.5:   # sunshade / awning band above the windows
            aw = (v > sill + wh + 0.03) & (v < sill + wh + 0.07); img[aw] *= 0.55
    save(img, A, f'{O}/com_{i}.png'); meta.append({'tw': round(bay, 2), 'th': round(st, 2), 'kind': kind})
json.dump(meta, open(f'{O}/com.json', 'w'))

# ---------- corrugated roof: 3 m tile, ribs every 0.2 m (15 per tile), sheet laps every 1.5 m along the fall ----------
S = 600; yy, xx = np.mgrid[0:S, 0:S]; ph = (xx / S * 15) % 1
prof = 0.86 + 0.14 * np.cos(ph * 2 * np.pi)   # rounded corrugation
img = np.ones((S, S, 3)) * 240 * prof[..., None]
img[((yy / S * 2) % 1) < 0.008] *= 0.8
img *= (0.95 + 0.07 * noise(S, S, 60, rng))[..., None]
save(img, np.zeros((S, S)), f'{O}/roof_metal_rib.png')

# ---------- water ripple normal (8 m tile, 512 px) ----------
S = 512; yy, xx = np.mgrid[0:S, 0:S] / S * 2 * np.pi
h = sum(np.sin(a * xx + b * yy + p) / (abs(a) + abs(b)) for a, b, p in [(5, 2, 0.3), (-3, 7, 1.1), (9, -4, 2.0), (2, 11, 0.7), (13, 5, 1.9), (-8, 9, 0.4)])
gx = np.gradient(h, axis=1); gy = np.gradient(h, axis=0); k = 0.6
n = np.dstack([-gx * k, -gy * k, np.ones_like(h)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
save((n * 0.5 + 0.5) * 255, None, f'{O}/water_ripple_n.png')

# ---------- lagoon pool (8 m tile): tile grid 0.25 m, darker tile-line bands every 2.5 m ----------
S = 1024; yy, xx = np.mgrid[0:S, 0:S] / S * 8
img = np.ones((S, S, 3)) * np.array([120, 190, 200])
img[((xx % 0.25) < 0.012) | ((yy % 0.25) < 0.012)] *= 0.93
band = (np.abs(((xx + 1.25) % 2.5) - 1.25) < 0.10); img[band] = [52, 104, 150]
img *= (0.95 + 0.08 * noise(S, S, 120, rng))[..., None]
save(img, None, f'{O}/pool.png')
print('tex_rw done', N)

# ---------- big flat roof (24 m tile, 2048 px): neutral multiplier on Surfmist/Shale grey; rib every 0.5 m, laps, grey skylights + plant ----------
S = 2048; yy, xx = np.mgrid[0:S, 0:S] / S * 24.0
img = np.ones((S, S, 3)) * 215
img *= (0.91 + 0.09 * np.cos((xx / 0.5) * 2 * np.pi))[..., None]
img[(yy % 6.0) < 0.04] *= 0.86                                   # sheet laps along the fall
rr = np.random.default_rng(7)
for x0, y0 in [(2.5, 3.0), (9.0, 3.0), (15.5, 3.0), (5.5, 15.0), (12.0, 15.0), (18.5, 15.0)]:   # skylights: small grey blocks
    m = (xx > x0) & (xx < x0 + 2.4) & (yy > y0) & (yy < y0 + 1.2); img[m] = [176, 176, 172]
for x0, y0 in [(4.0, 9.0), (17.0, 8.0), (10.0, 20.5)]:   # plant boxes / AC units with a short shadow
    m = (xx > x0) & (xx < x0 + 1.6) & (yy > y0) & (yy < y0 + 1.1); img[m] = [190, 190, 186]
    img[(xx > x0) & (xx < x0 + 1.6) & (yy > y0 + 1.1) & (yy < y0 + 1.6)] *= 0.62
img *= (0.97 + 0.04 * noise(S, S, 200, rr))[..., None]
save(img, np.zeros((S, S)), f'{O}/roof_flat_big.png')
# ---------- mall / big-box roof (48 m tile, 2048 px): Surfmist sheet bays in alternating tone, long skylight runs, plant clusters ----------
S = 2048; yy, xx = np.mgrid[0:S, 0:S] / S * 48.0
img = np.ones((S, S, 3)) * 215
img *= (0.93 + 0.07 * np.cos((xx / 0.5) * 2 * np.pi))[..., None]
img *= np.where((yy // 16.0) % 2 == 0, 1.0, 0.94)[..., None]          # sheet bays laid in 16 m runs, alternate tone
img[(yy % 16.0) < 0.3] *= 0.8                                            # bay joints / box gutters
for y0 in (5.0, 21.0, 37.0):                                              # long skylight runs, pale translucent sheet
    img[(yy > y0) & (yy < y0 + 1.6) & (xx > 3.0) & (xx < 45.0)] = [150, 158, 162]
for x0, y0 in [(6.0, 10.0), (28.0, 11.0), (14.0, 27.0), (36.0, 43.0)]:   # rooftop plant clusters with shadow
    img[(xx > x0) & (xx < x0 + 4.0) & (yy > y0) & (yy < y0 + 3.0)] = [128, 130, 128]
    img[(xx > x0) & (xx < x0 + 4.0) & (yy > y0 + 3.0) & (yy < y0 + 4.2)] *= 0.6
img *= (0.97 + 0.04 * noise(S, S, 300, np.random.default_rng(8)))[..., None]
save(img, np.zeros((S, S)), f'{O}/roof_mall.png')
