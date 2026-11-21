"""MCG trees re-derived crown by crown from the straight-down satellite (reference only, no pixels used on the model).
Inside the satellite extent every tree is a detected crown (position, crown radius, kind from crown colour);
lawns with no crown stay open; no scatter, no street-tree filler. Outside the extent the old trees stay.
Writes data/mcg/prep/trees_mcg.json rows [x, y, kind, scale] and a check overlay."""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__)); G = 'mcg'
D = os.path.join(HERE, 'data', G); PR = os.path.join(D, 'prep')
sj = json.load(open(os.path.join(D, 'sat.json'))); H, M = sj['half_m'], sj['m_per_px']
spec = json.load(open(os.path.join(HERE, 'spec', G + '.json'))); kinds = spec['tree_kinds']   # elm, red_gum, plane
KR = {'elm': 6.5, 'red_gum': 7.0, 'plane': 5.5, 'ghost_gum': 4.6, 'mulga': 1.5}
a = np.asarray(Image.open(os.path.join(D, 'sat.png')).convert('RGB'), float); N = a.shape[0]
R, Gc, B = a[..., 0], a[..., 1], a[..., 2]; L = a.mean(2)
Ls = ndi.gaussian_filter(L, 1.5)
Lb = ndi.median_filter(ndi.zoom(L, 1 / 8, order=1), 7); Lb = ndi.zoom(Lb, N / Lb.shape[0], order=1)[:N, :N]
exg = ndi.gaussian_filter(2 * Gc - R - B, 1.5)
# crown (with its own shadow): darker than the local ground, not grey/blue (roofs, asphalt, water), leafy texture
tex = ndi.gaussian_filter(np.abs(L - Ls), 2)
crown = (Ls < Lb - 9) & (Ls < 95) & (exg > -2) & (tex > 2.2)
# never on buildings, roads, rails, water: rasterise those from OSM-derived data
def px(x, y): return ((x + H) / M, (H - y) / M)
blk = Image.new('L', (N, N), 0); bd = ImageDraw.Draw(blk)
for b in json.load(open(os.path.join(PR, 'buildings.json'))):
    bd.polygon([px(x, y) for x, y in b['p']], fill=255)
for f_ in ('rails.json',):
    p_ = os.path.join(PR, f_)
    if os.path.exists(p_):
        for ln in json.load(open(p_)): bd.line([px(x, y) for x, y in ln], fill=255, width=int(5 / M))
blk = np.asarray(blk) > 0
bonly = Image.new('L', (N, N), 0); bo = ImageDraw.Draw(bonly)
for b in json.load(open(os.path.join(PR, 'buildings.json'))): bo.polygon([px(x, y) for x, y in b['p']], fill=255)
bonly = np.asarray(bonly) > 0
blk = ndi.binary_dilation(blk, iterations=int(1 / M))
crown &= ~blk
crown = ndi.binary_opening(crown, iterations=2); crown = ndi.binary_fill_holes(ndi.binary_closing(crown, iterations=2))
lab, nl = ndi.label(crown); sz = ndi.sum(crown, lab, range(1, nl + 1))
crown = np.isin(lab, 1 + np.where(sz * M * M >= 8)[0])
# one tree per crown: local maxima of the distance transform, at least a crown radius apart
dt = ndi.distance_transform_edt(crown) * M
pk = (dt == ndi.maximum_filter(dt, size=int(7 / M))) & (dt >= 1.6)
ys, xs = np.nonzero(pk)
order = np.argsort(-dt[ys, xs]); taken = []
grid = {}
for i in order:
    x = xs[i] * M - H; y = H - ys[i] * M; r = float(dt[ys[i], xs[i]])
    cr = min(9.0, max(3.0, r * 1.35))
    gk = (int(x // 10), int(y // 10)); ok = True
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for (x2, y2, c2) in grid.get((gk[0] + dx, gk[1] + dy), []):
                if math.hypot(x - x2, y - y2) < 0.8 * max(cr, c2): ok = False; break
            if not ok: break
        if not ok: break
    if not ok: continue
    if r < 2.2 and float(crown[max(0,ys[i]-8):ys[i]+9, max(0,xs[i]-8):xs[i]+9].mean()) < 0.7: continue
    grid.setdefault(gk, []).append((x, y, cr)); taken.append((x, y, cr, ys[i], xs[i]))
# fill: canopy left uncovered by the crowns so far gets more trees (dense rows and clumps are many crowns)
yy, xx = np.mgrid[0:N, 0:N]
dens0 = ndi.uniform_filter(blk.astype(np.float32), size=int(30 / M))
for it in range(4):
    cov = np.zeros((N, N), bool)
    for x, y, cr, iy, ix in taken:
        w = int(cr / M) + 1; i0, i1, j0, j1 = max(0, iy - w), min(N, iy + w + 1), max(0, ix - w), min(N, ix + w + 1)
        cov[i0:i1, j0:j1] |= (yy[i0:i1, j0:j1] - iy) ** 2 + (xx[i0:i1, j0:j1] - ix) ** 2 <= (cr / M) ** 2
    un = crown & ~cov; un = ndi.binary_opening(un, iterations=2)
    du = ndi.distance_transform_edt(un) * M
    pk2 = (du == ndi.maximum_filter(du, size=int(6 / M))) & (du >= 2.0) & (dens0 < 0.10)
    ys2, xs2 = np.nonzero(pk2); added = 0
    for iy, ix in zip(ys2, xs2):
        x = ix * M - H; y = H - iy * M; cr = min(8.0, max(3.0, float(du[iy, ix]) * 1.6))
        taken.append((x, y, cr, iy, ix)); added += 1
    print('fill pass', it, 'added', added)
    if added < 20: break
print('crowns', len(taken))
dens = ndi.uniform_filter(bonly.astype(np.float32), size=int(30 / M))   # buildings only: a rail cutting is not a street
# kind from crown colour (sunlit part): bright green deciduous = elm (park avenues) / plane (street), olive-grey = gum
out = []
for x, y, cr, iy, ix in taken:
    w = int(cr / M); s_ = a[max(0, iy - w):iy + w, max(0, ix - w):ix + w].reshape(-1, 3)
    s_ = s_[s_.mean(1) > np.percentile(s_.mean(1), 60)]
    r_, g_, b_ = s_.mean(0); gr = g_ / max(1, r_ + g_ + b_)
    if gr < 0.33 or g_ < b_ * 1.02: continue   # grey or blue: a shadow of a stand, fence or wall, not leaves
    if dens[iy, ix] > 0.12: k = 'plane'
    elif gr < 0.375: k = 'red_gum'
    else: k = 'elm'
    ki = kinds.index(k)
    out.append([round(x, 1), round(y, 1), ki, round(cr / KR[k], 2)])
# prep.py rewrites trees.json on every run, so the derived set goes to its own file and scene.py prefers it
# false crowns checked by eye on the aerial (gate3/rich_zoom.png): shade strips between the Richmond courts and a dark car in the car park
DROP = [(54, 60, -400, -386), (143, 147, -380, -375)]
out = [t for t in out if not any(a0 <= t[0] <= a1 and b0 <= t[1] <= b1 for a0, a1, b0, b1 in DROP)]
ded = []; gd = {}
for t in sorted(out, key=lambda t: -t[3]):                     # one crown per 2 m: the fill pass could stack peaks along a thin strip
    gk = (int(t[0] // 2), int(t[1] // 2)); near = [u for i in (-1, 0, 1) for j in (-1, 0, 1) for u in gd.get((gk[0] + i, gk[1] + j), ())]
    if all((t[0] - u[0]) ** 2 + (t[1] - u[1]) ** 2 >= 4 for u in near): ded.append(t); gd.setdefault(gk, []).append(t)
out = ded
# street rows along Wellington Pde (north edge of Yarra Park): on the aerial they are straight, evenly spaced rows beside the road and its footpaths.
# Row lines are the OSM Wellington Pde carriageways and the footpaths running beside them. Each tree 1.5-12 m from its nearest line is placed by
# (arc length s, offset d); within each 100 m of a line, trees whose offsets sit together (gaps under 3 m) form one row, the row's offset is set
# to its median, and runs with even gaps on the aerial get even spacing between their first and last tree (no tree moves more than 3 m).
import math
sp = spec; KX = 111320 * math.cos(math.radians(sp['lat'])); KY = 110540
osm = json.load(open(os.path.join(D, 'osm.json'), encoding='utf8'))
def xy_(g): return ((g['lon'] - sp['lon']) * KX, (g['lat'] - sp['lat']) * KY)
wl = [[xy_(g) for g in e['geometry']] for e in osm['elements'] if e.get('type') == 'way' and e.get('geometry') and e.get('tags', {}).get('name') == 'Wellington Parade']
wpts = np.array([p for w in wl for p in w])
fw = [[xy_(g) for g in e['geometry']] for e in osm['elements'] if e.get('type') == 'way' and e.get('geometry') and e.get('tags', {}).get('highway') in ('footway', 'path', 'pedestrian')]
fw = [w for w in fw if sum(math.dist(w[i], w[i + 1]) for i in range(len(w) - 1)) > 60 and np.mean([np.min(np.hypot(*(wpts - p).T)) for p in w]) < 30]
class Line:
    def __init__(s, pts):
        c = np.array(pts, float); c = c[np.concatenate([[True], np.hypot(*np.diff(c, axis=0).T) > 0.5])]
        s.c = c; s.seg = np.diff(c, axis=0); s.sl = np.hypot(*s.seg.T); s.cs = np.concatenate([[0], np.cumsum(s.sl)])
    def proj(s, x, y):
        p = np.array([x, y]); t = np.clip(((p - s.c[:-1]) * s.seg).sum(1) / s.sl ** 2, 0, 1); q = s.c[:-1] + s.seg * t[:, None]
        dd = np.hypot(*(p - q).T); i = int(np.argmin(dd)); n = np.array([-s.seg[i, 1], s.seg[i, 0]]) / s.sl[i]
        return s.cs[i] + t[i] * s.sl[i], float(np.dot(p - q[i], n)), float(dd[i])
    def unproj(s, s_, d_):
        i = max(min(int(np.searchsorted(s.cs, s_)) - 1, len(s.sl) - 1), 0); t = (s_ - s.cs[i]) / s.sl[i]; n = np.array([-s.seg[i, 1], s.seg[i, 0]]) / s.sl[i]
        return s.c[i] + s.seg[i] * t + n * d_
lines = [Line(w) for w in wl + fw if len(w) > 1]
rows = {}; moved = 0
for t in out:
    if t[1] < 250 or abs(t[0]) > 700: continue
    best = None
    for li, L_ in enumerate(lines):
        s_, d_, dist = L_.proj(t[0], t[1])
        if best is None or dist < best[3]: best = (li, s_, d_, dist)
    li, s_, d_, dist = best
    if 1.5 < dist < 12: rows.setdefault((li, int(s_ // 100)), []).append((s_, d_, t))
rows2 = {}
for c, r in rows.items():
    r.sort(key=lambda z: z[1]); grp = [[r[0]]]
    for z in r[1:]:
        (grp[-1].append(z) if z[1] - grp[-1][-1][1] < 3.0 else grp.append([z]))
    for gi, g_ in enumerate(grp):
        if len(g_) >= 4 and np.std([z[1] for z in g_]) < 2.2: rows2[c + (gi,)] = g_
rows = rows2
for k, r in rows.items():
    if len(r) < 4: continue
    r.sort(key=lambda z: z[0]); dm = float(np.median([z[1] for z in r])); g = np.diff([z[0] for z in r]); gm = float(np.median(g))
    keep = [r[0]]
    for z in r[1:]:
        if z[0] - keep[-1][0] < 0.55 * gm: z[2][3] = -1; continue                      # a second peak inside one crown
        keep.append(z)
    i = 0
    while i < len(keep):                                                                 # runs with gaps within 0.7-1.4 of the median get even spacing
        j = i
        while j + 1 < len(keep) and 0.7 * gm < keep[j + 1][0] - keep[j][0] < 1.4 * gm: j += 1
        for m in range(i, j + 1):
            s2 = keep[i][0] + (keep[j][0] - keep[i][0]) * (m - i) / max(j - i, 1)
            x2, y2 = lines[k[0]].unproj(s2, dm); t = keep[m][2]
            if math.hypot(x2 - t[0], y2 - t[1]) > 3: continue
            moved += math.hypot(x2 - t[0], y2 - t[1]) > 0.3; t[0], t[1] = round(float(x2), 1), round(float(y2), 1)
        i = j + 1
out = [t for t in out if t[3] > 0]
print('street rows', sum(len(r) >= 4 for r in rows.values()), 'trees moved', moved)
old = json.load(open(os.path.join(PR, 'trees.json')))
keep_old = [list(t[:3]) + [1.0] for t in old if not (abs(t[0]) < H - 3 and abs(t[1]) < H - 3)]
json.dump(out + keep_old, open(os.path.join(PR, 'trees_mcg.json'), 'w'))
print('trees in sat', len(out), 'outside kept', len(keep_old), 'kinds', {k: sum(1 for t in out if kinds[t[2]] == k) for k in kinds})
np.save(os.path.join(PR, 'crown_mask.npy'), crown)
# overlay: crown circles on the aerial
im = Image.fromarray(a.astype(np.uint8)); d = ImageDraw.Draw(im)
colk = {'elm': (255, 0, 255), 'red_gum': (255, 200, 0), 'plane': (0, 220, 255)}
for x, y, ki, sc in out:
    cx, cy = px(x, y); rr = sc * KR[kinds[ki]] / M
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=colk[kinds[ki]], width=2)
im.save(os.path.join(PR, 'trees_overlay.png'))
