# Weathering pass (runs after paint.py, paint2.py, paint3.py): hand-drawn detail on the flat textures, never photo pixels.
# Concrete: panel joints, rain streaks under joints and ledges, blotching. Roof sheet: ribs at the real pitch, sheet
# end laps, dirt along the ribs. Steel and fascias: seams, scuffs, grime toward the bottom. Ground: patching and wear.
# Every pass keeps the texture's mean colour (the colours were read off the photos), so only detail is added.
# Image row 0 is the top of the tile (v = 1); the last row is the bottom (v = 0, ground level on walls).
import numpy as np, json, math, os
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'tex') + '/'
TILE = json.load(open(OUT + 'tiles.json'))
R = np.random.default_rng(404)


def load(n): return np.asarray(Image.open(OUT + n + '.png').convert('RGB'), float)


def save(n, a, ref):
    a = a * (ref.reshape(-1, 3).mean(0) / np.maximum(a.reshape(-1, 3).mean(0), 1))  # keep the photo-read mean colour
    L = a.mean(2); sd = L.std()
    if sd < 10.5:  # dark finishes: the same drawn detail at more contrast (at most 3.5x) so it still reads at game distance
        m = a.reshape(-1, 3).mean(0); a = m + (a - m) * min(3.5, 10.5 / max(sd, 1e-6))
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(OUT + n + '.png')


def blot(h, w, cells, amp):
    """seamless (periodic) soft blotches: white noise low-passed in frequency space, scaled to +-amp"""
    f = np.fft.fft2(R.normal(0, 1, (h, w)))
    ky = np.fft.fftfreq(h)[:, None] * h / cells; kx = np.fft.fftfreq(w)[None, :] * w / cells
    g = np.real(np.fft.ifft2(f * np.exp(-(kx ** 2 + ky ** 2) * 1.5)))
    return g / (np.abs(g).max() + 1e-9) * amp


def ppm(a, n):
    tw, tv = TILE[n]; return a.shape[1] / tw, a.shape[0] / tv  # pixels per metre (u, v)


def streaks(a, n, count, length_m, dark, rows=None, width_m=(0.03, 0.12)):
    """rain streaks: thin dark runs that start at a ledge / joint row and fade downward (wrapping, so the tile repeats)"""
    h, w = a.shape[:2]; pu, pv = ppm(a, n)
    for _ in range(count):
        x = R.uniform(0, w); wd = max(1, int(R.uniform(*width_m) * pu)); y0 = int(R.choice(rows)) if rows is not None else int(R.uniform(0, h))
        L = max(4, int(R.uniform(0.3, 1.0) * length_m * pv)); k = R.uniform(0.5, 1.0) * dark
        ys = (y0 + np.arange(L)) % h; fade = (1 - np.arange(L) / L) ** 1.5
        xs = (int(x) + np.arange(wd)) % w; prof = np.sin(np.linspace(0, math.pi, wd + 2)[1:-1])
        a[np.ix_(ys, xs)] *= (1 - k * fade[:, None] * prof[None, :])[:, :, None]


def joints(a, n, du=None, dv=None, depth=0.25, w_m=0.012):
    h, w = a.shape[:2]; pu, pv = ppm(a, n); jw = max(2, int(w_m * pu))
    if du:
        for k in range(int(round(TILE[n][0] / du))):
            x = int(k * du * pu) % w; a[:, x:x + jw] *= 1 - depth; a[:, (x + jw) % w] *= 1 + depth * 0.4  # shadowed joint, lit lip
    if dv:
        for k in range(int(round(TILE[n][1] / dv))):
            y = int(k * dv * pv) % h; a[y:y + jw] *= 1 - depth; a[(y + jw) % h] *= 1 + depth * 0.4


def grime_bottom(a, amt):
    h = a.shape[0]; v = np.linspace(0, 1, h)[:, None, None]; a *= 1 - amt * v ** 2


def scuffs(a, n, count, size_m, amp):
    h, w = a.shape[:2]; pu, pv = ppm(a, n); yy, xx = np.mgrid[0:h, 0:w]
    for _ in range(count):
        cx, cy = R.uniform(0, w), R.uniform(0, h); rx, ry = R.uniform(0.4, 1) * size_m * pu, R.uniform(0.2, 0.6) * size_m * pv
        dx = (xx - cx + w / 2) % w - w / 2; dy = (yy - cy + h / 2) % h - h / 2
        a *= (1 + R.choice([-1, 1]) * amp * np.exp(-((dx / rx) ** 2 + (dy / ry) ** 2)))[:, :, None]


def mul(a, m): a *= (1 + m)[:, :, None]


# ---- concrete: precast panels, tier walls and fascias, undercrofts, plain facade walls ----
for n, du, dv, rows_v in (('conc_light', 3.0, 1.5, 1.5), ('conc_beige', 3.0, 1.5, 1.5), ('conc_grey', 3.0, 1.5, 1.5),
                          ('tier_wall', 2.0, None, 2.0), ('tier_fascia', 2.0, None, 2.0),
                          ('fac_endpale', 3.0, 4.0, 4.0), ('fac_plant', None, None, 4.0), ('backclad', None, None, 4.0),
                          ('uc_back', 3.0, None, 4.0), ('uc_soffit', 1.2, 6.0, None), ('fac_mcc', None, None, 4.0),
                          ('fac_nelight', None, None, 4.0)):
    if n not in TILE: continue
    a = load(n); ref = a.copy(); h, w = a.shape[:2]; pu, pv = ppm(a, n)
    mul(a, blot(h, w, max(2, TILE[n][0] / 1.5), 0.10) + blot(h, w, max(4, TILE[n][0] / 0.4), 0.04))  # blotching, large and small
    if du or dv: joints(a, n, du, dv, 0.22)
    if rows_v:  # streaks start under each ledge / joint line and run down the wall
        rows = [int(k * rows_v * pv) % h for k in range(max(1, int(round(TILE[n][1] / rows_v))))]
        streaks(a, n, int(6 * TILE[n][0] * TILE[n][1] / rows_v), min(rows_v, 2.5), 0.16, rows)
    if n.startswith('uc_soffit'): grime_bottom(a, 0.0)
    elif n not in ('uc_floor',): grime_bottom(a, 0.10)
    save(n, a, ref)

# ---- ground: concourse paving, terrace, undercroft floor, asphalt, gravel, grass ----
for n, cells, amp, jt in (('paving', 6, 0.10, 1.2), ('terrace', 4, 0.10, 0.6), ('uc_floor', 4, 0.12, 1.2),
                          ('asphalt', 4, 0.12, None), ('gravel', 6, 0.12, None), ('grass', 3, 0.10, None)):
    if n not in TILE: continue
    a = load(n); ref = a.copy(); h, w = a.shape[:2]
    mul(a, blot(h, w, cells, amp) + blot(h, w, cells * 6, amp * 0.4))
    if jt: joints(a, n, jt, jt, 0.18)
    scuffs(a, n, 10, 0.8, 0.10)  # patches, oil marks and worn spots
    if n == 'asphalt':  # patched cracks
        for _ in range(6):
            x = R.uniform(0, w); y = R.uniform(0, h)
            for s in range(400):
                x += R.normal(0, 1.2); y += 1; a[int(y) % h, int(x) % w] *= 0.6
    save(n, a, ref)

# ---- roof sheeting: ribs at the real pitch (0.3 m trough deck), sheet end laps every 6 m, dirt along the ribs ----
for n, pitch in (('roof_white', 0.3), ('roof_grey', 0.3), ('roof_soffit', 0.3), ('roof_teal', 0.3), ('roof_clear', 0.3)):
    if n not in TILE: continue
    a = load(n); ref = a.copy(); h, w = a.shape[:2]; pu, pv = ppm(a, n)
    x = (np.arange(w) / pu) % pitch / pitch
    rib = np.where(x < 0.12, -0.10, 0.0) + np.where((x >= 0.12) & (x < 0.17), 0.06, 0.0)  # rib shadow, lit crown
    dirt = blot(h, w, TILE[n][1] / 0.5, 1.0); dirt = np.clip(dirt, 0, None) * 0.18
    ribzone = np.exp(-((x - 0.06) / 0.10) ** 2)[None, :]
    mul(a, rib[None, :] - dirt * ribzone - blot(h, w, 3, 0.06) ** 2 * 4 + blot(h, w, 2, 0.05))
    lap = int(TILE[n][1] / 6.0 * h) if TILE[n][1] >= 6 else None  # one lap per tile on 3 m tiles: sheets are 6 m, so every other tile
    y = h // 2; a[y:y + max(2, int(0.02 * pv))] *= 0.82; a[y + max(2, int(0.02 * pv))] *= 1.06
    streaks(a, n, int(30 * TILE[n][0]), 1.5, 0.12, [y + 3], (0.02, 0.06))  # dirt washed down from the lap
    save(n, a, ref)

# ---- steel and fascias: seams, scuffs, grime toward the bottom ----
for n, seam in (('steel_white', 2.0), ('steel_blue', 2.0), ('steel_galv', 2.0), ('steel_dark', 2.0), ('screen', 1.0),
                ('paint_white', 2.0), ('fascia', 2.0), ('roof_fascia', 2.0), ('fac_blue', 1.5)):
    if n not in TILE: continue
    a = load(n); ref = a.copy(); h, w = a.shape[:2]; pu, pv = ppm(a, n)
    dark = ref.mean() < 60
    mul(a, blot(h, w, 2, 0.06 if not dark else 0.14) + blot(h, w, 10, 0.03 if not dark else 0.08))
    joints(a, n, seam, TILE[n][1] if n not in ('fac_blue',) else None, 0.20 if not dark else 0.30)
    scuffs(a, n, 12, 0.25, 0.08 if not dark else 0.25)
    rows = [int(0.08 * h)]
    streaks(a, n, int(12 * TILE[n][0]), TILE[n][1] * 0.7, 0.10 if not dark else 0.20, rows, (0.02, 0.08))
    if n == 'steel_galv':  # galvanising spangle
        mul(a, R.normal(0, 0.025, (h, w)))
    grime_bottom(a, 0.14 if not dark else 0.25)
    if dark:  # very dark finishes read as flat black: lift the wear with pale dust instead of only darkening
        a += (blot(h, w, 6, 1.0).clip(0, None) * 18)[:, :, None]
    save(n, a, ref)
# ---- corner strips (cs_<wall>, made plain by wallcols.py): the same blotching, rain streaks and foot grime as a wall ----
for n in [k for k in TILE if k.startswith('cs_')]:
    if not os.path.exists(OUT + n + '.png'): continue
    a = load(n); ref = a.copy(); h, w = a.shape[:2]; pv = ppm(a, n)[1]
    mul(a, blot(h, w, 2, 0.10) + blot(h, w, 4, 0.04))
    rows = [int(k * 4.0 * pv) % h for k in range(max(1, int(round(TILE[n][1] / 4.0))))]
    streaks(a, n, max(2, int(3 * TILE[n][1] / 4.0)), 2.5, 0.16, rows, (0.03, 0.08))
    grime_bottom(a, 0.10); save(n, a, ref)
print('weathered')
