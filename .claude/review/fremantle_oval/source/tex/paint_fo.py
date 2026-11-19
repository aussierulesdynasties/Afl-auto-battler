# Fremantle Oval texture pass (row 202 2b). Director: "texture it by fucking hand to look the same but not like a
# fucking BLURRY PHOTO". Every map is painted from module sizes in metres (texpaint.py, from the Marvel pass): no photo
# pixels. Colours keep each material's own colour (keep_mean, sRGB). Writes tex/<material>.png + tex/tiles.json
# (repeat size in metres per map) and tex/stddev.txt (grey stddev, floor 10).
import json, os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from texpaint import Canvas, save, gstd
D = os.path.dirname(os.path.abspath(__file__))
MATS = json.load(open(os.path.join(D, 'mats.json')))
def srgb(c):
    c = np.clip(np.asarray(c, float), 0, 1); return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)

def sheet(col, seed, pitch=0.076, tile=6.0):
    # corrugated / profiled roof sheet: a rib every `pitch` down the slope (v), sheet side-laps every 0.76 m,
    # end laps every 6 m, fastener rows every 1.2 m, dirt settling beside the ribs, rain streaks from the laps
    c = Canvas(tile, tile, col, seed); c.mottle(0.05, (3, 1.0, 0.3))
    x = np.arange(c.n) / c.pu; ph = (x % pitch) / pitch
    c.mul((1 + 0.10 * np.cos(2 * np.pi * ph))[None, :])
    for i in range(int(tile / 0.76) + 1): c.vline(i * 0.76, 0.02, tuple(np.array(col) * 0.70), 0.8)
    c.hline(0.0, 0.05, tuple(np.array(col) * 0.62)); c.hline(0.06, 0.02, tuple(np.minimum(np.array(col) * 1.08, 1)), 0.6)
    for j in range(int(tile / 1.2)):
        for i in range(int(tile / (pitch * 4))):
            u = (i * 4 + 2) * pitch; v = j * 1.2 + 0.3
            cy, cx = int(v * c.pv), int(u * c.pu); c.a[cy - 1:cy + 2, cx - 1:cx + 2] *= 0.6
    c.streaks([0.06, 3.06], per_m=1.4, length=(0.4, 2.4), width=(0.02, 0.12), amt=0.25)
    c.mul(1 - 0.06 * np.clip(c.noise(0.5, 2.5), 0, 3)); c.grain(0.012); c.keep_mean(); return c

def render(col, seed, pw=3.0, ph=3.0, tile=6.0):
    # cement render / painted block wall: control joints every 3 m, per-panel tone, rain streaks under the joints,
    # splash-back grime at the foot, hairline cracks
    c = Canvas(tile, tile, col, seed); c.mottle(0.05, (1.8, 0.6, 0.15))
    c.panels(pw, ph, joint=0.012, dark=0.55, tone=0.04)
    c.streaks([0.0, 3.0], per_m=1.2, length=(0.4, 2.2), amt=0.22)
    c.grime_bottom(0.6, 0.18, band=tile); c.speckle(0.8, (0.006, 0.02), 0.2); c.grain(0.014); c.keep_mean(); return c

def paint(col, seed, tile=4.0, seam=2.0):
    # painted steel / fascia / trim: seams, chipped wear, grime toward the bottom
    c = Canvas(tile, tile, col, seed); c.mottle(0.06, (1.5, 0.4, 0.1))
    dk = tuple(np.array(col) * 0.6 + 0.01); lt = tuple(np.minimum(np.array(col) * 1.25 + 0.06, 1))
    for i in range(int(tile / seam)): c.vline(i * seam, 0.014, dk); c.vline(i * seam + 0.012, 0.006, lt, 0.7)
    c.hline(0.0, 0.014, dk)
    c.speckle(2.0, (0.004, 0.012), 0.35, light=True); c.speckle(1.0, (0.01, 0.03), 0.2)
    c.streaks([0.0], per_m=1.0, length=(0.3, 1.5), amt=0.2); c.grime_bottom(0.8, 0.18)
    c.grain(0.015); c.keep_mean(); return c

def boards(col, seed, gap=0.15, tile=4.8):
    # weatherboards: a lapped board every 15 cm, shadow under each lap, board ends staggered every 4.8 m
    c = Canvas(tile, tile, col, seed); c.mottle(0.04, (1.5, 0.5, 0.1))
    y = np.arange(c.n) / c.pv; r = (y % gap) / gap
    c.mul((0.86 + 0.18 * r)[:, None])
    for k in range(int(tile / gap)): c.hline(k * gap, 0.018, tuple(np.array(col) * 0.42))
    for k in range(int(tile / gap)):
        u = (k * 1.7) % tile; v0 = k * gap
        yy = slice(int(v0 * c.pv), int((v0 + gap) * c.pv)); xx = int(u * c.pu)
        c.a[yy, xx:xx + 2] *= 0.7
    c.streaks([0.0], per_m=0.8, length=(0.3, 1.5), amt=0.15); c.grime_bottom(0.6, 0.15)
    c.grain(0.012); c.keep_mean(); return c

def brick(col, seed, mortar=(0.70, 0.66, 0.58), bw=0.23, bh=0.086, tile=2.76):
    # stretcher bond: 230 x 76 mm bricks + 10 mm joints, every brick its own tone, mortar a little recessed
    c = Canvas(tile, tile, col, seed)
    y, x = np.mgrid[0:c.n, 0:c.n]; um = x / c.pu; vm = y / c.pv
    row = np.floor(vm / bh).astype(int); off = (row % 2) * bw / 2
    colx = np.floor(((um + off) % tile) / bw).astype(int)
    T = 1 + 0.08 * c.R.normal(size=(row.max() + 2, colx.max() + 2)); c.mul(T[row, colx])
    du = ((um + off) % bw); dv = vm % bh
    J = (du < 0.010) | (dv < 0.010)
    c.a[J] = np.array(mortar) * (0.9 + 0.1 * c.R.random(J.sum()))[:, None]
    c.mottle(0.05, (1.0, 0.3, 0.08)); c.grime_bottom(0.6, 0.15); c.grain(0.02); c.keep_mean(); return c

def stone(col, seed, tile=2.4):
    # coursed limestone rubble (g36 boundary wall, read at scale): courses 0.15-0.21 m, stones 0.10-0.20 m long,
    # dark grey rough stones (each its own tone) set in wide pale lime mortar that shows round every stone
    c = Canvas(tile, tile, col, seed); R = c.R
    hs = R.uniform(0.15, 0.21, 40); hs = hs[:np.searchsorted(np.cumsum(hs), tile) + 1]; hs *= tile / hs.sum()
    vb = np.concatenate([[0], np.cumsum(hs)]); y, x = np.mgrid[0:c.n, 0:c.n]; um = x / c.pu; vm = y / c.pv
    row = np.clip(np.searchsorted(vb, vm, side='right') - 1, 0, len(hs) - 1)
    T = np.ones((c.n, c.n)); E = np.zeros((c.n, c.n))
    for r in range(len(hs)):
        ws = R.uniform(0.10, 0.20, 60); ws = ws[:np.searchsorted(np.cumsum(ws), tile) + 1]; ws *= tile / ws.sum()
        ub = np.concatenate([[0], np.cumsum(ws)]); off = R.uniform(0, tile); m = row == r
        uu = (um[m] - off) % tile; k = np.clip(np.searchsorted(ub, uu, side='right') - 1, 0, len(ws) - 1)
        T[m] = np.clip(1 + 0.12 * R.normal(size=len(ws)), 0.75, 1.25)[k]
        du = np.minimum(uu - ub[k], ub[k + 1] - uu); dv = np.minimum(vm[m] - vb[r], vb[r + 1] - vm[m])
        E[m] = np.minimum(du * 1.0, dv * 1.3)
    J = E < 0.028 + 0.007 * c.noise(0.02)                          # mortar, ragged stone outlines
    mort = c.col * 0.7 + 0.3 * c.col.mean(); stonec = c.col * 0.22 + np.array([0.36, 0.38, 0.36])   # grey stone, cream lime mortar
    c.a[J] = mort; c.a[~J] = stonec * T[~J][:, None]
    c.mul(np.where(J, 1 + 0.04 * c.noise(0.01), 1 + 0.10 * c.noise(0.005) + 0.06 * c.noise(0.03)))   # rough pitted stone face
    c.mottle(0.05, (0.8, 0.2, 0.05)); c.speckle(30, (0.003, 0.010), 0.3); c.grime_bottom(0.6, 0.18)
    c.grain(0.03); return c

def concrete(col, seed, tile=4.8):
    # poured concrete (terraces, decks, aprons): no formwork blocks; trowel mottling, saw cuts every 2.4 m, dark
    # water and dirt stains, pale efflorescence, small pits and chips
    c = Canvas(tile, tile, col, seed); c.mottle(0.07, (1.2, 0.35, 0.08))
    for u in (0.0, 2.4): c.vline(u, 0.006, tuple(np.array(col) * 0.70), 0.8)
    for v in (0.0, 2.4): c.hline(v, 0.006, tuple(np.array(col) * 0.70), 0.8)
    S = np.clip(c.noise(0.6) + 0.35 * c.noise(0.12) - 0.6, 0, 3); c.mul(1 - 0.22 * np.clip(S, 0, 1))
    L = np.clip(c.noise(0.4) - 1.0, 0, 3); c.mul(1 + 0.10 * np.clip(L, 0, 1))
    c.streaks([0.0, 2.4], per_m=0.6, length=(0.2, 1.0), amt=0.15)
    c.speckle(6, (0.004, 0.015), 0.25); c.speckle(0.4, (0.05, 0.25), 0.10)
    c.grime_bottom(0.5, 0.14); c.grain(0.022); c.keep_mean(); return c

def asphalt(col, seed, tile=6.0):
    c = Canvas(tile, tile, col, seed); c.mottle(0.08, (2.5, 0.6, 0.1)); c.grain(0.10)
    c.speckle(3, (0.004, 0.012), 0.35, light=True); c.speckle(0.3, (0.1, 0.4), 0.15)
    c.keep_mean(); return c

def pavers(col, seed, tile=2.4):
    c = Canvas(tile, tile, col, seed)
    y, x = np.mgrid[0:c.n, 0:c.n]; um = x / c.pu; vm = y / c.pv
    row = np.floor(vm / 0.3).astype(int); off = 0.0 * row   # square 0.3 m pavers laid in a grid (g23)
    cx = np.floor(((um + off) % tile) / 0.3).astype(int)
    T = 1 + 0.03 * c.R.normal(size=(row.max() + 2, cx.max() + 2)); c.mul(T[row, cx])
    J = (((um + off) % 0.3) < 0.007) | ((vm % 0.3) < 0.007); c.a[J] *= 0.78
    c.mottle(0.06, (1.0, 0.3)); c.speckle(1.5, (0.01, 0.04), 0.25); c.grain(0.02); c.keep_mean(); return c

def glass(col, seed, tile=6.0, pw=1.5, ph=2.4):
    # tinted glazing: each pane reflects a slightly different sky (lighter at the top), dirt at the pane foot
    c = Canvas(tile, tile, col, seed); y, x = np.mgrid[0:c.n, 0:c.n]; um = x / c.pu; vm = y / c.pv
    t = (vm % ph) / ph; pane = (np.floor(um / pw) + 7 * np.floor(vm / ph)).astype(int); pt = 1 + 0.04 * c.R.normal(size=64)
    base = np.array(col); c.a = (base * 1.08 * (1 - t[..., None]) + base * 0.95 * t[..., None]) * pt[pane % 64][..., None]
    c.mul(1 + 0.06 * c.noise(0.8, 2.0)); c.grime_bottom(0.25, 0.15, band=ph, col=(0.5, 0.47, 0.42))
    for i in range(int(tile / pw)): c.vline(i * pw, 0.04, tuple(base * 0.5))
    for j in range(int(tile / ph) + 1): c.hline(j * ph, 0.05, tuple(base * 0.5))
    c.grain(0.01); c.keep_mean(); return c

def seats(col, seed, tile=5.4):
    # one row of empty moulded seats seen from above (the geometry already makes each row): a seat pan every
    # 0.45 m along the row (u), dark gap between seats, lit front lip, scuffed centres, slight per-seat fade
    c = Canvas(tile, tile, col, seed); x = np.arange(c.n) / c.pu; base = np.array(col)
    s = (x % 0.45); seat = np.floor(x / 0.45).astype(int); tone = 1 + 0.06 * c.R.normal(size=seat.max() + 2)
    prof = np.where(s < 0.035, 0.30, np.where(s < 0.06, 0.75, np.where(s > 0.415, 1.30, 1.0)))
    c.mul((prof * tone[seat])[None, :] * np.ones((c.n, 1)))
    y = np.arange(c.n) / c.pv; c.mul((0.92 + 0.10 * np.abs(np.sin(np.pi * (y % 0.9) / 0.9)))[:, None])
    c.speckle(1.5, (0.02, 0.06), 0.18); c.mottle(0.04, (1.5, 0.4)); c.grain(0.01); c.keep_mean(); return c

def timber(col, seed, tile=4.8, gaps=True):
    # bench slats along the row: a 90 mm slat + 15 mm gap, grain along u, weathered ends every 4.8 m
    c = Canvas(tile, tile, col, seed); y = np.arange(c.n) / c.pv; s = y % 0.105
    if gaps: c.mul(np.where(s < 0.015, 0.35, np.where(s < 0.022, 1.25, 1.0))[:, None] * np.ones((1, c.n)))
    slat = np.floor(y / 0.105).astype(int); c.mul((1 + 0.08 * c.R.normal(size=slat.max() + 2))[slat][:, None] * np.ones((1, c.n)))
    c.mul(1 + 0.08 * c.noise(1.5, 0.004)); c.vline(0.0, 0.01, tuple(base * 0.4 for base in col))
    c.speckle(2, (0.004, 0.012), 0.3); c.grain(0.02); c.keep_mean(); return c

def plastic(col, seed, tile=2.0):
    # moulded plastic chairs / painted boards: sun fade blotches, scuffs, dirt in the low corners
    c = Canvas(tile, tile, col, seed); c.mottle(0.07, (0.8, 0.25, 0.06)); c.speckle(6, (0.005, 0.02), 0.3)
    c.speckle(3, (0.01, 0.03), 0.15, light=True); c.grime_bottom(0.4, 0.2, band=1.0); c.grain(0.02); c.keep_mean(); return c

def leaves(col, seed, tile=3.0):
    # vine / foliage: overlapping leaf blobs, darker gaps, lit tops
    c = Canvas(tile, tile, col, seed); base = np.array(col)
    c.a = c.a * 0.45
    y, x = np.ogrid[0:c.n, 0:c.n]
    for _ in range(int(220 * tile * tile)):
        cx, cy = c.R.uniform(0, c.n, 2); r = c.R.uniform(0.03, 0.08) * c.pu; t = c.R.uniform(0.75, 1.35)
        x0, x1, y0, y1 = int(cx - r), int(cx + r) + 1, int(cy - r), int(cy + r) + 1
        xs = np.arange(x0, x1); ys = np.arange(y0, y1)
        m = (((xs - cx) / r) ** 2)[None, :] + (((ys - cy) / (r * 0.6)) ** 2)[:, None] < 1
        sub = c.a[np.ix_(ys % c.n, xs % c.n)]; lit = np.clip(1.2 - (ys[:, None] - cy) / r * 0.3, 0.8, 1.3)
        sub[m] = (base * t * lit)[m] if np.ndim(lit) == 3 else (base * t)[None, :] * lit.repeat(len(xs), 1)[m][:, None]
        c.a[np.ix_(ys % c.n, xs % c.n)] = sub
    c.grain(0.03); c.keep_mean(); return c

def solar(col, seed, tile=2.04):
    # PV panels 1.0 x 1.7 m: 6 x 10 cells, silver busbars, aluminium frame
    c = Canvas(tile, tile * 1.68 / 1.02 / 1.0, col, seed); y, x = np.mgrid[0:c.n, 0:c.n]; um = x / c.pu; vm = y / c.pv
    c.mul(1 + 0.06 * c.noise(0.3)); c.mul(np.where(((um % (1.02 / 6)) < 0.006) | ((vm % (1.68 / 10)) < 0.006), 0.6, 1.0))
    c.vline(0.0, 0.03, (0.70, 0.72, 0.74)); c.vline(1.02, 0.03, (0.70, 0.72, 0.74)); c.hline(0.0, 0.03, (0.70, 0.72, 0.74))
    c.vline(1.02 / 12, 0.004, (0.55, 0.57, 0.62), 0.6); c.grain(0.01); c.keep_mean(); return c

def grass(col, seed, tile=3.0):
    c = Canvas(tile, tile, col, seed); c.mottle(0.12, (1.2, 0.3, 0.05)); c.grain(0.10)
    c.speckle(4, (0.005, 0.02), 0.3, light=True); c.keep_mean(); return c

# family per material (name -> painter, kwargs); anything not listed is painted steel/trim (paint)
FAM = {
    'roof_white': (sheet, {}), 'roof_cream': (sheet, {}), 'roof_zinc': (sheet, {}), 'roof_zinc_x': (sheet, {}),
    'roof_zinc_pav': (sheet, {'pitch': 0.5}), 'roof_dark': (sheet, {}), 'roof_blue': (sheet, {}), 'roof_ns': (sheet, {'pitch': 0.2}),
    'soffit': (sheet, {'pitch': 0.2}), 'corr_white_h': (sheet, {}),
    'render_cream': (render, {}), 'render_white': (render, {}), 'cream_quoin': (render, {'pw': 0.6, 'ph': 0.3, 'tile': 3.6}),
    'white_paint': (paint, {}), 'cream_boards': (boards, {}), 'red_brick': (brick, {}), 'brick': (brick, {}),
    'brick_pink': (brick, {'mortar': (0.93, 0.91, 0.89)}), 'limestone': (stone, {}), 'concrete': (concrete, {}),
    'asphalt': (asphalt, {}), 'pavers': (pavers, {}), 'glass': (glass, {}), 'hq_glass': (glass, {}), 'glass_green': (glass, {}),
    'seat_green': (plastic, {}), 'seat_white': (plastic, {}), 'seat_navy': (plastic, {}), 'seat_timber': (timber, {}), 'seat_plank': (timber, {'gaps': False}),
    'fig': (leaves, {}), 'pine': (leaves, {}), 'vine': (leaves, {}), 'solar': (solar, {}), 'kerb_grass': (grass, {}),
    'dirt': (grass, {}), 'step_dark': (concrete, {}), 'mid_grey': (render, {}),
}
ONLY = [n for n in os.environ.get('ONLY', '').split(',') if n]   # repaint just these maps, keep the rest
TILES = json.load(open(os.path.join(D, 'tiles.json'))) if ONLY else {}
OLD = {l.split()[0]: l.rstrip() for l in open(os.path.join(D, 'stddev.txt'))} if ONLY else {}
std = []
for i, (name, m) in enumerate(sorted(MATS.items())):
    if m['area'] <= 0 and m['objs'] == 0: continue
    if ONLY and name not in ONLY:
        if name in OLD: std.append(OLD[name])
        continue
    fn, kw = FAM.get(name, (paint, {}))
    col = tuple(float(v) for v in srgb(m['col']))
    c = fn(col, 100 + i, **kw)
    a = c.img()     # no stddev floor (director 2026-11-19): a map passes when it looks like its photo crop
    p = os.path.join(D, name + '.png'); save(a, p); TILES[name] = [c.tu, c.tv]
    std.append('%-18s %6.1f  %-9s %7d m2' % (name, round(gstd(p), 1), fn.__name__, round(m['area'])))
json.dump(TILES, open(os.path.join(D, 'tiles.json'), 'w'), indent=0)
with open(os.path.join(D, 'stddev.txt'), 'w', newline='') as f:
    for s in std: f.write(s + '\n')
print('\n'.join(s for s in std if not ONLY or s.split()[0] in ONLY))
