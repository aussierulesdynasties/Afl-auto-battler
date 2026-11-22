"""Car parks as they were: each surface lot's asphalt colour, its bay layout and the cars parked in it, read from a
close straight-down aerial (Esri World Imagery z19, ~0.25 m a pixel; SAT_RELEASE = a Wayback release for a closed
ground's era). Colours and positions only: no aerial pixels go into the scene.
usage (after prep.py): cars.py spec.json -> data/<g>/carparks.json
  lots[osm id] = {colour [r,g,b] asphalt median, th: bay rows' direction (rad), pv/pu: bay grid phase (m) or null when
  the cars don't sit on a 16 m two-row grid, cars: [[x, y, heading rad, r, g, b], ...]}"""
import sys, os, json, math, io, time, urllib.request
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
spec = json.load(open(sys.argv[1])); name = spec['name']
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, 'data', name)
import aerial19 as _a19
_a19.setup(spec, D); from aerial19 import aerial, S, KX, KY, NEAR, lat0, lon0
def area(A): return 0.5 * np.sum(A[:, 0] * np.roll(A[:, 1], -1) - A[:, 1] * np.roll(A[:, 0], -1))
BLD = [np.array(b['p'], float) for b in json.load(open(os.path.join(D, 'prep', 'buildings.json')))]   # prep's buildings (OSM + Overture)
BB = np.array([[*b.min(0), *b.max(0)] for b in BLD])
out = {}
for el in json.load(open(os.path.join(D, 'osm.json'), encoding='utf-8'))['elements']:
    t = el.get('tags', {})
    if el['type'] != 'way' or t.get('amenity') != 'parking' or t.get('parking') in ('multi-storey', 'underground') or t.get('surface') in ('grass', 'gravel', 'dirt') or not el.get('geometry'): continue
    p = [((g['lon'] - lon0) * KX, (g['lat'] - lat0) * KY) for g in el['geometry'] if g]
    if p[0] == p[-1]: p = p[:-1]
    if len(p) < 3 or max(max(abs(a), abs(b)) for a, b in p) > NEAR - 10: continue
    A = np.array(p, float)
    if abs(area(A)) < 60 or abs(area(A)) > 200000: continue
    x0, y0 = A.min(0) - 2; x1, y1 = A.max(0) + 2
    img, xs, ys = aerial(x0, y0, x1, y1)
    h, w = img.shape[:2]
    mk = Image.new('L', (w, h), 0); ImageDraw.Draw(mk).polygon([((x - x0) / S, (y1 - y) / S) for x, y in A], fill=1)
    inner = ndi.binary_erosion(np.asarray(mk) > 0, iterations=4)          # 1 m in from the lot's edge (kerbs, hedges)
    bm = Image.new('L', (w, h), 0); dr = ImageDraw.Draw(bm)                 # buildings standing in the lot (a mall inside its car park)
    for k in np.nonzero((BB[:, 2] > x0) & (BB[:, 0] < x1) & (BB[:, 3] > y0) & (BB[:, 1] < y1))[0]:
        dr.polygon([((x - x0) / S, (y1 - y) / S) for x, y in BLD[k]], fill=1)
    inner &= ~ndi.binary_dilation(np.asarray(bm) > 0, iterations=6)
    if inner.sum() < 400: continue
    R, G, B = img[..., 0], img[..., 1], img[..., 2]
    veg = (G > R + 6) & (G >= B)                                           # tree crowns, lawn strips
    lum = img.mean(-1)
    ok = inner & ~veg
    if ok.sum() < 400: continue
    # the asphalt: the lot's commonest shade (an outline also takes in white cars, footpaths, kerbs, beds and sand)
    lc = lum[ok]; hh, ee = np.histogram(lc, bins=64, range=(0, 256)); pk = ee[np.argmax(ndi.uniform_filter1d(hh.astype(float), 3))] + 2
    sel = np.abs(lc - pk) < 10; med = np.median(img[ok][sel], 0) if sel.sum() > 100 else np.median(img[ok], 0); ml = med.mean()
    dist = np.abs(img - med).max(-1)
    # cars: peaks of the lot's difference from its asphalt at car scale (a roof is ~1.8 m across). Bright or coloured
    # roofs first; a dark peak (a dark car, or a car's shadow) counts only with no bright car within 3 m of it.
    sig = 0.8 / S; sep = int(round(2.3 / S)) | 1
    def peaks(m, thr):
        f = ndi.gaussian_filter(m, sig) - ndi.gaussian_filter(m, 3 * sig)   # car-sized, not a building's or tree's shadow
        pk = (f == ndi.maximum_filter(f, size=sep)) & (f > thr) & ok
        jj, ii = np.nonzero(pk); return np.stack([xs[ii], ys[jj]], 1) if len(jj) else np.zeros((0, 2)), jj, ii
    lift = np.where(ok, np.maximum(dist * (lum > ml - 12), 0), 0)
    sink = np.where(ok, np.maximum(ml - lum, 0), 0)
    Pl, jl, il = peaks(lift, 14.0); Pd, jd, idd = peaks(sink, 14.0)
    keep = [k for k in range(len(Pd)) if len(Pl) == 0 or np.hypot(*(Pl - Pd[k]).T).min() > 3.0]
    P = np.vstack([Pl, Pd[keep]]); J = np.concatenate([jl, jd[keep]]); I = np.concatenate([il, idd[keep]])
    r_ = int(round(0.6 / S))
    cols = [np.median(img[max(0, j - r_):j + r_ + 1, max(0, i - r_):i + r_ + 1].reshape(-1, 3), 0) for j, i in zip(J, I)]
    # rows: a car's nearest neighbour stands beside it in its row, ~2.5 m away; the rows run along that direction
    th_r = None
    if len(P) >= 8:
        dd = np.hypot(P[:, None, 0] - P[None, :, 0], P[:, None, 1] - P[None, :, 1]); np.fill_diagonal(dd, 1e9)
        nn = dd.argmin(1); vec = P[nn] - P; m_ = (dd.min(1) > 1.8) & (dd.min(1) < 3.4)
        if m_.sum() >= 6:
            a2 = 2 * np.arctan2(vec[m_, 1], vec[m_, 0]); th_r = 0.5 * math.atan2(np.sin(a2).mean(), np.cos(a2).mean())
    # each car faces across its own row: the row direction where it stands (neighbour pairs within 20 m), as one lot
    # can hold blocks of rows at different angles
    hd_ = np.full(len(P), (th_r if th_r is not None else 0.0) + math.pi / 2)
    if th_r is not None:
        for k in range(len(P)):
            w_ = m_ & (np.hypot(*(P - P[k]).T) < 20.0)
            if w_.sum() >= 5:
                a2 = 2 * np.arctan2(vec[w_, 1], vec[w_, 0]); hd_[k] = 0.5 * math.atan2(np.sin(a2).mean(), np.cos(a2).mean()) + math.pi / 2
    # a car standing clear of others shows its own length: its roof patch's long axis, where the patch is long enough
    src = np.concatenate([np.zeros(len(Pl), int), np.ones(len(keep), int)]); sm = [ndi.gaussian_filter(lift, 0.3 / S), ndi.gaussian_filter(sink, 0.3 / S)]
    rw = int(round(2.8 / S)); oy, ox = np.mgrid[-rw:rw + 1, -rw:rw + 1]; disc = np.hypot(ox, oy) <= rw
    iso = np.ones(len(P), bool) if len(P) < 2 else (np.sort(np.hypot(P[:, None, 0] - P[None, :, 0], P[:, None, 1] - P[None, :, 1]), 1)[:, 1] > 3.4)
    for k in np.nonzero(iso)[0]:
        f_ = sm[src[k]]; j, i = J[k], I[k]
        if j < rw or i < rw or j + rw >= f_.shape[0] or i + rw >= f_.shape[1]: continue
        win = f_[j - rw:j + rw + 1, i - rw:i + rw + 1]; wt = np.clip(win - 0.5 * f_[j, i], 0, None) * disc
        lab_, _ = ndi.label(wt > 0); wt = wt * (lab_ == lab_[rw, rw])
        if wt.sum() <= 0: continue
        mx, my = (wt * ox).sum() / wt.sum(), (wt * oy).sum() / wt.sum()
        cxx = (wt * (ox - mx) ** 2).sum(); cyy = (wt * (oy - my) ** 2).sum(); cxy = (wt * (ox - mx) * (oy - my)).sum()
        ev, evec = np.linalg.eigh(np.array([[cxx, cxy], [cxy, cyy]]))
        if ev[1] > 2.25 * max(ev[0], 1e-6): hd_[k] = math.atan2(-evec[1, 1], evec[0, 1])   # image rows run south
    cars = [(P[k], float(hd_[k]), cols[k]) for k in range(len(P))]
    E = np.diff(np.vstack([A, A[:1]]), axis=0); e = E[np.argmax(np.hypot(E[:, 0], E[:, 1]))]; th = math.atan2(e[1], e[0])
    pv = pu = None
    if th_r is not None:
        th = th_r
        cs, sn = math.cos(th), math.sin(th)
        U = np.array([c[0][0] * cs + c[0][1] * sn for c in cars]); V = np.array([-c[0][0] * sn + c[0][1] * cs for c in cars])
        def fit(P, per, cen, sig):
            best = (-1, 0)
            for ph in np.arange(0, per, 0.05):
                d = np.min([np.abs(((P - ph - c0 + per / 2) % per) - per / 2) for c0 in cen], 0)
                s = np.exp(-d * d / (2 * sig * sig)).sum()
                if s > best[0]: best = (s, ph)
            return best[1]
        pv = fit(V, 16.0, (8.5, 13.5), 0.6)
        dv = np.min([np.abs(((V - pv - c0 + 8) % 16) - 8) for c0 in (8.5, 13.5)], 0)
        on = dv < 1.0
        if on.mean() >= 0.6:
            pu = fit(U[on], 2.6, (1.3,), 0.35)
            # cars on the grid stand in their bays, square to the rows
            for i in np.nonzero(on)[0]:
                r = [((V[i] - pv - c0 + 8) % 16) - 8 for c0 in (8.5, 13.5)]; vv = V[i] - min(r, key=abs)
                uu = pu + 1.3 + round((U[i] - pu - 1.3) / 2.6) * 2.6
                c, hd, col = cars[i]
                cars[i] = (np.array([uu * cs - vv * sn, uu * sn + vv * cs]), th + math.pi / 2, col)
        else: pv = None
    cap = 160.0 / max(med.max(), 1); md = (med * min(1.0, cap)).round().tolist()
    out[str(el['id'])] = {'colour': md, 'th': th, 'pv': pv, 'pu': pu,
                          'cars': [[round(float(c[0]), 2), round(float(c[1]), 2), round(float(hd), 3), *[int(v) for v in col]] for c, hd, col in cars]}
    print(el['id'], 'lot', int(abs(area(A))), 'm2 cars', len(cars), 'grid' if pv is not None else 'no grid', 'asphalt', [int(v) for v in med])
json.dump(out, open(os.path.join(D, 'carparks.json'), 'w'))
print('CARPARKS lots', len(out), 'cars', sum(len(v['cars']) for v in out.values()), 'on a grid', sum(v['pv'] is not None for v in out.values()))
