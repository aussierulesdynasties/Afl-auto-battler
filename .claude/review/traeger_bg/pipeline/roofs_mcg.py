"""Roof class per building from the aerial (reference only: the colour picks a hand-made material, no pixels used).
Writes data/mcg/prep/roof_class.json aligned with buildings.json, and a check board."""
import json, os
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, 'data', 'mcg'); PR = os.path.join(D, 'prep')
SATF = 'sat1500' if os.path.exists(os.path.join(D, 'sat1500.png')) else 'sat'   # 1.5 km aerial covers every footprint
sj = json.load(open(os.path.join(D, SATF + '.json'))); H, M = sj['half_m'], sj['m_per_px']
a = np.asarray(Image.open(os.path.join(D, SATF + '.png')).convert('RGB'), float); N = a.shape[0]
B = json.load(open(os.path.join(PR, 'buildings.json')))
def px(x, y): return ((x + H) / M, (H - y) / M)
# hand palette: class -> (material, tint 0-255). The aerial median picks the nearest class.
CLS = {'terracotta': ('tile', (164, 82, 58)), 'red_metal': ('metal', (128, 52, 44)), 'slate': ('metal', (74, 78, 84)),
       'zinc': ('metal', (150, 154, 156)), 'cream': ('metal', (206, 200, 184)), 'green_metal': ('metal', (78, 96, 80))}
def classify(m):
    r, g, b = m; L = (r + g + b) / 3
    if r - g > 20 and r - b > 20: return 'terracotta' if L > 80 else 'red_metal'   # tile reads warm even when weathered pale
    if g - r > 12 and g - b > 10: return 'green_metal'   # weaker green casts are shade or canopy edge, not painted metal
    if L < 95: return 'slate'
    if L > 165 and r >= b: return 'cream'
    return 'zinc'
from scipy import ndimage as ndi
def judge(s, b):
    """class, or '?'+reason when this image cannot show the roof colour"""
    s = s[s.max(1) > 12]   # drop imagery voids (black tiles)
    if len(s) < 4: return '?void'
    if ((s[:, 1] - s[:, 0] > 8) & (s[:, 1] - s[:, 2] > 8)).mean() > 0.35: return '?canopy'
    warm = ((s[:, 0] - s[:, 1] > 20) & (s[:, 0] - s[:, 2] > 20)).mean(); m_ = np.median(s, 0)
    dwarm = ((s[:, 0] - s[:, 1] > 10) & (s[:, 0] - s[:, 2] > 12) & (s.mean(1) < 95)).mean()
    if warm > 0.4: return 'terracotta' if (m_.mean() > 80 or b['c'] == 'house') else 'red_metal'
    if dwarm > 0.5: return 'terracotta' if b['c'] == 'house' else 'red_metal'
    if m_.mean() < 60 and np.ptp(m_) < 12: return '?shadow'   # deep cast shadow: not a roof colour
    return classify(m_)
def sample(img, P, mpp):
    xs = [p[0] for p in P]; ys = [p[1] for p in P]; h_, w_ = img.shape[:2]
    x0, x1, y0, y1 = int(max(0, min(xs))), int(min(w_, max(xs) + 1)), int(max(0, min(ys))), int(min(h_, max(ys) + 1))
    if x1 - x0 < 2 or y1 - y0 < 2: return None
    mk = Image.new('L', (x1 - x0, y1 - y0), 0); ImageDraw.Draw(mk).polygon([(x - x0, y - y0) for x, y in P], fill=255)
    mk = np.asarray(mk) > 0
    if mk.sum() < 6: return None
    core = ndi.distance_transform_edt(np.pad(mk, 1))[1:-1, 1:-1] * mpp >= 1.5
    if core.sum() >= 4: mk = core
    return img[y0:y1, x0:x1][mk]
out = []; SRC = []
for b in B:
    s_ = sample(a, [px(x, y) for x, y in b['p']], M)
    out.append(None if s_ is None else judge(s_, b)); SRC.append('esri')
# second date: Google z19 straight-down (reference only), where shadow and canopy fall differently
import math, urllib.request, time
LAT0, LON0 = -37.820011, 144.983442; KX = 111320 * math.cos(math.radians(LAT0)); KY = 110540; Z = 19; NT = 2 ** Z
GT = os.path.join(D, 'gsat_tiles'); os.makedirs(GT, exist_ok=True)
def gtile(tx, ty):
    p = os.path.join(GT, f'{Z}_{tx}_{ty}.jpg')
    if not os.path.exists(p):
        for k in range(4):
            try:
                r = urllib.request.urlopen(urllib.request.Request(f'https://mt1.google.com/vt/lyrs=s&x={tx}&y={ty}&z={Z}', headers={'User-Agent': 'scene-reference/0.1'}), timeout=60).read()
                open(p, 'wb').write(r); break
            except Exception as e: print('retry', e); time.sleep(3)
    return np.asarray(Image.open(p).convert('RGB'), float)
def gpx(x, y):
    lon = LON0 + x / KX; lat = LAT0 + y / KY
    return ((lon + 180) / 360 * NT * 256, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * NT * 256)
GMPP = 156543.03392 * math.cos(math.radians(LAT0)) / NT
for i, c in enumerate(out):
    if c is not None and not c.startswith('?'): continue
    P = [gpx(x, y) for x, y in B[i]['p']]
    tx0 = int(min(p[0] for p in P) // 256) - 0; tx1 = int(max(p[0] for p in P) // 256); ty0 = int(min(p[1] for p in P) // 256); ty1 = int(max(p[1] for p in P) // 256)
    if (tx1 - tx0 + 1) * (ty1 - ty0 + 1) > 16: continue
    img = np.concatenate([np.concatenate([gtile(tx, ty) for tx in range(tx0, tx1 + 1)], 1) for ty in range(ty0, ty1 + 1)], 0)
    s_ = sample(img, [(u - tx0 * 256, v - ty0 * 256) for u, v in P], GMPP)
    g = None if s_ is None else judge(s_, B[i])
    if g is not None and not g.startswith('?'): out[i] = g; SRC[i] = 'google_z19'
    else: SRC[i] = 'sv_needed:' + str(c) + '/' + str(g)
_SVO = os.path.join(HERE, '..', 'heights', 'sv_roofs_out.json')   # mcg-sv's Street View roof colours for roofs both aerials hide
if os.path.exists(_SVO):
    for x in json.load(open(_SVO)):
        c_ = x.get('class') or x.get('roof_class') or x.get('colour_class')
        if c_ in CLS and SRC[x['id']].startswith('sv_needed'): out[x['id']] = c_; SRC[x['id']] = 'streetview:' + str(x.get('heading', ''))
        elif c_ is not None and c_ not in CLS: print('SV roof class not in palette', x['id'], c_)
SV = [i for i, s_ in enumerate(SRC) if s_.startswith('sv_needed')]
json.dump([{'id': i, 'lonlat': [LON0 + float(np.mean(B[i]['p'], 0)[0]) / KX, LAT0 + float(np.mean(B[i]['p'], 0)[1]) / KY], 'why': SRC[i]} for i in SV], open(os.path.join(HERE, '..', 'heights', 'sv_roofs.json'), 'w'), indent=0)
json.dump(SRC, open(os.path.join(PR, 'roof_src.json'), 'w'))
from collections import Counter as _C0
print('sources', _C0(s_.split(':')[0] for s_ in SRC), 'sv list', len(SV), _C0(SRC[i] for i in SV).most_common(6))
# footprints hidden by canopy or an imagery void: the class most common among the 8 nearest classified houses (same street)
from scipy.spatial import cKDTree
CEN = np.array([np.mean(b['p'], 0) for b in B]); okk = [i for i, c in enumerate(out) if c is not None and not c.startswith('?')]; kt = cKDTree(CEN[okk])
from collections import Counter as _C
for i, c in enumerate(out):
    if c is None or c.startswith('?'): out[i] = _C(out[okk[j]] for j in kt.query(CEN[i], 8)[1]).most_common(1)[0][0]
json.dump({'classes': CLS, 'per_building': out}, open(os.path.join(PR, 'roof_class.json'), 'w'))
from collections import Counter
print(Counter(c for c, b in zip(out, B) if b['c'] == 'house'))
im = Image.fromarray(a.astype(np.uint8)); d = ImageDraw.Draw(im)
for c, b in zip(out, B):
    if c and b['c'] in ('house', 'block'): d.polygon([px(x, y) for x, y in b['p']], fill=CLS[c][1], outline=(255, 255, 0))
im.save(os.path.join(PR, 'roof_overlay.png'))
import math, shapely
from shapely.geometry import Polygon, Point, MultiPoint
# ---- plane roof helpers: every roof face is a planar polygon in a local (u, v) frame, clipped to the footprint and
# triangulated flat, so no face can spike. z of each face comes from its own plane.
def lin_z(p0, p1, p2):
    A = np.array([[p[0], p[1], 1.0] for p in (p0, p1, p2)]); c_ = np.linalg.solve(A, [p[2] for p in (p0, p1, p2)])
    return lambda u_, v_: c_[0] * u_ + c_[1] * v_ + c_[2]
def hip_faces(a0, a1, b0, b1, slope, cap):
    hw = min(a1 - a0, b1 - b0) / 2; d = min(hw, cap / slope); z = d * slope
    i0, i1, j0, j1 = a0 + d, a1 - d, b0 + d, b1 - d
    F_ = [([(a0, b0), (a1, b0), (i1, j0), (i0, j0)], lin_z((a0, b0, 0), (a1, b0, 0), (i0, j0, z))),
          ([(a0, b1), (i0, j1), (i1, j1), (a1, b1)], lin_z((a0, b1, 0), (a1, b1, 0), (i0, j1, z))),
          ([(a0, b0), (i0, j0), (i0, j1), (a0, b1)], lin_z((a0, b0, 0), (a0, b1, 0), (i0, j0, z))),
          ([(a1, b0), (a1, b1), (i1, j1), (i1, j0)], lin_z((a1, b0, 0), (a1, b1, 0), (i1, j0, z)))]
    if i1 - i0 > 1e-3 and j1 - j0 > 1e-3: F_.append(([(i0, j0), (i1, j0), (i1, j1), (i0, j1)], lambda u_, v_: z))
    return F_
def mesh_faces(FACES, to_w, to_uv, pg, vs, F):
    def addv(p, z): vs.append([round(float(p[0]), 3), round(float(p[1]), 3), round(float(z), 3)]); return len(vs) - 1
    for poly_uv, zfn in FACES:
        pu = Polygon(poly_uv)
        if not pu.is_valid or pu.area < 1e-4: continue
        cl = Polygon([tuple(to_w(*q)) for q in poly_uv]).buffer(0).intersection(pg)
        for g_ in getattr(cl, 'geoms', [cl]):
            if g_.geom_type != 'Polygon' or g_.area < 0.01: continue
            for t in shapely.delaunay_triangles(g_).geoms:
                if not g_.buffer(1e-6).contains(t.centroid): continue
                F.append([addv(q, zfn(*to_uv(np.array(q)))) for q in list(t.exterior.coords)[:3]])
def quad(vs, F, p0, p1, z00, z01, z10, z11):
    n = len(vs); r = lambda a: round(float(a), 3)
    vs += [[r(p0[0]), r(p0[1]), r(z00)], [r(p1[0]), r(p1[1]), r(z10)], [r(p1[0]), r(p1[1]), r(z11)], [r(p0[0]), r(p0[1]), r(z01)]]
    F += [[n, n + 1, n + 2], [n, n + 2, n + 3]]
def vwall(prof, v_, to_w, pg, vs, F):
    """vertical wall at constant v: prof = [(u, ztop)], wall from z 0 to ztop, only segments inside the footprint"""
    pb = pg.buffer(0.05)
    for (u0, z0), (u1, z1) in zip(prof, prof[1:]):
        p0, p1 = to_w(u0, v_), to_w(u1, v_)
        if pb.contains(Point(*p0)) and pb.contains(Point(*p1)): quad(vs, F, p0, p1, 0, z0, 0, z1)
# ---- hipped roofs for houses whose footprint is not a simple rectangle (L, U, courtyard): a single gable cannot cover them.
# Roof height at a point = tan(28 deg) x its distance to the nearest eave, capped at the ridge height (the hip-roof rule, as a
# straight skeleton gives); sampled on a 1 m lattice plus the outline, Delaunay-triangulated, triangles outside the footprint dropped.
import math, shapely
from shapely.geometry import Polygon, Point, MultiPoint
TAN = math.tan(math.radians(28)); hips = {}
for i, b in enumerate(B):
    if b['c'] != 'house': continue
    P = np.array(b['p'], float); best = None
    for j in range(len(P)):
        e = P[(j + 1) % len(P)] - P[j]; l = float(np.hypot(*e))
        if l < 0.5: continue
        ax = e / l; pv = np.array([-ax[1], ax[0]]); uu = P @ ax; vv = P @ pv; ar = np.ptp(uu) * np.ptp(vv)
        if best is None or ar < best[0]: best = (ar, pv, vv)
    ar, pv, vv = best; vc = (vv.min() + vv.max()) / 2; d = vv - vc
    cr = sum(1 for j in range(len(P)) if d[j] * d[(j + 1) % len(P)] < 0)
    pg = Polygon(P).buffer(0)
    if pg.is_empty or pg.geom_type != 'Polygon': continue
    if cr <= 2 and pg.area / ar >= 0.8: continue
    rh = min(4.0, max(0.5, np.ptp(vv) / 2) * TAN)
    # L / U / courtyard: cover the footprint with its largest box-frame rectangles (0.5 m raster), each a plain hip roof;
    # where two wings meet, their hips interpenetrate and form the valleys a real L-shaped hip roof has.
    ax2 = np.array([pv[1], -pv[0]]); uu2 = P @ ax2; G = 0.5
    us = np.arange(uu2.min() + G / 2, uu2.max(), G); vsg = np.arange(vv.min() + G / 2, vv.max(), G)
    MK = np.array([[pg.contains(Point(*(ax2 * u_ + pv * v_))) for v_ in vsg] for u_ in us], bool); cov = np.zeros_like(MK); rects = []
    for _ in range(6):
        best = None; nu, nv = MK.shape; hgt = np.zeros(nv, int)
        for r in range(nu):
            hgt = np.where(MK[r], hgt + 1, 0); st = []
            for c in range(nv + 1):
                hc = hgt[c] if c < nv else 0; s0 = c
                while st and st[-1][1] >= hc:
                    s0, hh = st.pop()
                    if hh >= 4 and c - s0 >= 4:
                        gain = int((~cov[r - hh + 1:r + 1, s0:c]).sum())
                        if best is None or gain > best[0]: best = (gain, r - hh + 1, r + 1, s0, c)
                st.append((s0, hc))
        if best is None or best[0] < 16: break
        _, r0, r1, c0, c1 = best; cov[r0:r1, c0:c1] = True
        rects.append((us[r0] - G / 2, us[r1 - 1] + G / 2, vsg[c0] - G / 2, vsg[c1 - 1] + G / 2))
        if cov[MK].mean() > 0.96: break
    if not rects: continue
    vs = []; F = []; FA = []
    for (a0, a1, b0, b1) in rects: FA += hip_faces(a0, a1, b0, b1, TAN, rh)
    mesh_faces(FA, lambda u_, v_: ax2 * u_ + pv * v_, lambda q: (q @ ax2, q @ pv), pg, vs, F)
    hips[i] = {'v': vs, 'f': F, 'rh': round(rh, 2)}
# ---- Victorian row terraces: narrow (<= 9.5 m) and deep (>= 1.4 x width). The street end is the short end with open ground 4 m out.
# Main roof over the front Df = min(depth, 9) m: ridge parallel to the street (pitch 30 deg), with party walls standing 0.3 m proud on
# both long sides and a front parapet; behind it the rear wing is hipped with its ridge capped at 1.5 m. Height = max of the two.
from shapely.strtree import STRtree
from shapely.geometry import LineString
polys = [Polygon(b['p']).buffer(0) for b in B]; tree_ = STRtree(polys); T30 = math.tan(math.radians(30)); nter = 0; ridge_ok = [0, 0]
for i, b in enumerate(B):
    if b['c'] != 'house': continue
    pg = polys[i]
    if pg.is_empty or pg.geom_type != 'Polygon': continue
    P = np.array(pg.exterior.coords[:-1]); best = None
    for j in range(len(P)):
        e = P[(j + 1) % len(P)] - P[j]; l = float(np.hypot(*e))
        if l < 0.5: continue
        ax = e / l; uu = P @ ax; vv = P @ np.array([-ax[1], ax[0]])
        if best is None or np.ptp(uu) * np.ptp(vv) < best[0]: best = (np.ptp(uu) * np.ptp(vv), ax, uu, vv)
    _, ax, uu, vv = best
    if np.ptp(uu) < np.ptp(vv): ax = np.array([-ax[1], ax[0]]); uu, vv = P @ ax, P @ np.array([-ax[1], ax[0]])
    W_, L_ = np.ptp(vv), np.ptp(uu)
    if not (W_ <= 9.5 and L_ >= 1.4 * W_) or pg.area / (W_ * L_) < 0.7: continue
    pv = np.array([-ax[1], ax[0]]); vc = (vv.min() + vv.max()) / 2
    def open_at(u_):
        q = Point(*(ax * u_ + pv * vc))
        return not any(polys[n].contains(q) for n in tree_.query(q) if n != i)
    o0, o1 = open_at(uu.min() - 4), open_at(uu.max() + 4)
    if o0 == o1: o0 = True; o1 = False                       # both or neither open: take the end nearest... the min end (logged below)
    uf, sgn = (uu.min(), 1) if o0 else (uu.max(), -1)
    Df = min(L_, 9.0); rf = (Df / 2) * T30; vmin, vmax = vv.min(), vv.max()
    # aerial check of ridge direction: a ridge parallel to the street splits the main roof into a lit and a shaded slope along u
    cen = [ax * (uf + sgn * u_) + pv * v_ for u_ in np.linspace(1, Df - 1, 9) for v_ in np.linspace(vmin + 1, vmax - 1, 5)]
    if Df > 3 and W_ > 3 and abs(np.mean(P[:, 0])) < H - 5 and abs(np.mean(P[:, 1])) < H - 5:
        Lm = np.array([a[int(np.clip(px(*c_)[1], 0, N - 1)), int(np.clip(px(*c_)[0], 0, N - 1))].mean() for c_ in cen]).reshape(9, 5)
        across = abs(Lm[:4].mean() - Lm[5:].mean()); along = abs(Lm[:, :2].mean() - Lm[:, 3:].mean())
        ridge_ok[0 if across >= along else 1] += 1
        if along > 1.3 * across and along > 4: continue                                # aerial: ridge runs front-to-back here, keep the gable
    # explicit planes in the (u from the street, v across) frame. Main roof: gable over the front Df m, ridge parallel to the
    # street. Party walls on both long sides follow the gable profile 0.3 m proud; front parapet 0.5 m above the eave.
    # Rear wing: a single-slope skillion falling to the back, its high edge tucked under the main roof's back slope.
    Lr = L_ - Df; ph = 0.3
    def w(u_, v_): return ax * (uf + sgn * u_) + pv * v_
    def uv_(q): return ((q @ ax - uf) * sgn, q @ pv)
    FACES = [([(0, vmin), (Df / 2, vmin), (Df / 2, vmax), (0, vmax)], lin_z((0, vmin, 0), (Df / 2, vmin, rf), (0, vmax, 0))),
             ([(Df / 2, vmin), (Df, vmin), (Df, vmax), (Df / 2, vmax)], lin_z((Df, vmin, 0), (Df / 2, vmin, rf), (Df, vmax, 0))),
             ([(0, vmin), (0.3, vmin), (0.3, vmax), (0, vmax)], lambda u_, v_: 0.5)]
    for vb, vi in ((vmin, vmin + 0.25), (vmax - 0.25, vmax)):
        FACES += [([(0, vb), (Df / 2, vb), (Df / 2, vi), (0, vi)], lin_z((0, vb, ph), (Df / 2, vb, rf + ph), (0, vi, ph))),
                  ([(Df / 2, vb), (Df, vb), (Df, vi), (Df / 2, vi)], lin_z((Df, vb, ph), (Df / 2, vb, rf + ph), (Df, vi, ph)))]
    if Lr > 0.5:
        sk = min(rf * 0.6, Lr * math.tan(math.radians(12))); us_ = Df - sk / T30
        FACES.append(([(us_, vmin), (L_, vmin), (L_, vmax), (us_, vmax)], lin_z((us_, vmin, sk), (L_, vmin, 0), (us_, vmax, sk))))
    vs = []; F = []
    mesh_faces(FACES, w, uv_, pg, vs, F)
    prof = [(0, ph), (Df / 2, rf + ph), (Df, ph)]
    for v_ in (vmin, vmin + 0.25, vmax - 0.25, vmax): vwall(prof, v_, w, pg, vs, F)
    for u_ in (0.0, 0.3): quad(vs, F, w(u_, vmin), w(u_, vmax), 0, 0.5, 0, 0.5)
    hips[i] = {'v': vs, 'f': F, 'rh': round(rf, 2), 'terrace': 1}; nter += 1
print('terraces', nter, 'aerial shading split front/back (ridge parallel to street)', ridge_ok[0], 'split side/side', ridge_ok[1])
json.dump(hips, open(os.path.join(PR, 'roof_hip.json'), 'w'))
print('hipped houses', len(hips), 'triangles', sum(len(h['f']) for h in hips.values()))
