import math
# swimming pools (exec'd from scene.py): OSM leisure=swimming_pool in the near square. Each pool: paver deck 3 m past the
# water edge, white coping 0.3 m, one flat water face 4 cm below the coping; lap pools (long side >= 40 m) get dark lane
# lines 0.25 m wide every 2.5 m along the long axis. Near-rectangular outlines are squared to their bounding rectangle.
# (texture session 2026-11-20)
_lat0, _lon0 = spec['lat'], spec['lon']; _KX = 111320 * math.cos(math.radians(_lat0))
def _off(P, d):   # mitred outward offset of a CCW polygon
    n = len(P); out = []
    for i in range(n):
        a, b, c = P[i - 1], P[i], P[(i + 1) % n]
        e1 = (b - a) / (np.linalg.norm(b - a) or 1); e2 = (c - b) / (np.linalg.norm(c - b) or 1)
        n1 = np.array([e1[1], -e1[0]]); n2 = np.array([e2[1], -e2[0]]); m = n1 + n2; m /= (np.linalg.norm(m) or 1)
        out.append(b + m * d / max(0.35, float(np.dot(m, n1))))
    return np.array(out)
def _area(A): return 0.5 * np.sum(A[:, 0] * np.roll(A[:, 1], -1) - A[:, 1] * np.roll(A[:, 0], -1))
def _rect(A):   # minimum-area bounding rectangle over edge directions: (corners CCW, centre, long axis unit, L, W)
    best = None
    for i in range(len(A)):
        e = A[(i + 1) % len(A)] - A[i]; n_ = np.linalg.norm(e)
        if n_ < 1e-6: continue
        u = e / n_; v = np.array([-u[1], u[0]]); pu, pv = A @ u, A @ v
        ar = (pu.max() - pu.min()) * (pv.max() - pv.min())
        if best is None or ar < best[0]: best = (ar, u, v, pu.min(), pu.max(), pv.min(), pv.max())
    ar, u, v, a0, a1, b0, b1 = best
    C = np.array([u * a + v * b for a, b in ((a0, b0), (a1, b0), (a1, b1), (a0, b1))])
    if a1 - a0 < b1 - b0: u, v, a0, a1, b0, b1 = v, -u, b0, b1, -a1, -a0
    return C, ar, u, (a1 - a0), (b1 - b0)
def _trim(A, R):   # squared rect: width between the long sides, length between the end edges; OSM notches ignored
    u = R[1] - R[0]; u = u / np.linalg.norm(u); v = np.array([-u[1], u[0]])
    Pu, Pv = [], []
    for i in range(len(A)):
        a_, b_ = A[i], A[(i + 1) % len(A)]; e = b_ - a_; n_ = np.linalg.norm(e)
        if n_ < 8: continue
        (Pv if abs(e @ u) / n_ > 0.9 else Pu if abs(e @ v) / n_ > 0.9 else []).extend([a_, b_])
    if len(Pu) < 4 or len(Pv) < 4: return R
    pu, pv = np.array(Pu) @ u, np.array(Pv) @ v
    return np.array([u * a_ + v * b_ for a_, b_ in ((pu.min(), pv.min()), (pu.max(), pv.min()), (pu.max(), pv.max()), (pu.min(), pv.max()))])
_W, _D, _C, _L = ([], []), ([], [], []), ([], []), ([], []); _FL = ([], []); _SINK = []
for _el in json.load(open(os.path.join(HERE, 'data', name, 'osm.json'), encoding='utf-8'))['elements']:
    if _el['type'] != 'way' or _el.get('tags', {}).get('leisure') != 'swimming_pool' or not _el.get('geometry'): continue
    _p = [((g['lon'] - _lon0) * _KX, (g['lat'] - _lat0) * 110540) for g in _el['geometry'] if g]
    if _p[0] == _p[-1]: _p = _p[:-1]
    if len(_p) < 3 or max(max(abs(a), abs(b)) for a, b in _p) > meta['near'] - 10: continue
    _A = np.array(_p, float)
    if _area(_A) < 0: _A = _A[::-1]
    _R, _ra, _u, _Ln, _Wd = _rect(_A)
    if abs(_area(_A)) > 0.80 * _ra and len(_A) <= 8: _A = _trim(_A, _R)   # squared: OSM steps on a rectangular pool are tracing noise
    if _area(_A) < 0: _A = _A[::-1]
    _dk = _off(_A, 4.0); _cp = _off(_A, 0.3); k = len(_A)
    _z = float(height(_dk[:, 0], _dk[:, 1]).mean()) + 0.04; print("pool ground range", round(float(np.ptp(height(_dk[:, 0], _dk[:, 1]))), 2))
    _SINK.append((_dk.copy(), _z))
    v, f, uv = _D; o = len(v); v += [(x, y, _z) for x, y in _dk] + [(x, y, _z) for x, y in _cp]
    for i in range(k):
        q = (o + i, o + (i + 1) % k, o + k + (i + 1) % k, o + k + i); f.append(q); uv += [(v[j][0] / 6.0, v[j][1] / 6.0) for j in q]
    v, f = _C; o = len(v); v += [(x, y, _z + 0.02) for x, y in _cp] + [(x, y, _z + 0.02) for x, y in _A]
    f += [(o + i, o + (i + 1) % k, o + k + (i + 1) % k, o + k + i) for i in range(k)]
    v, f = _W; o = len(v); v += [(x, y, _z - 0.20) for x, y in _A]; f.append(tuple(range(o, o + k)))
    v, f = _C; o = len(v); v += [(x, y, _z + 0.02) for x, y in _A] + [(x, y, _z - 0.22) for x, y in _A]; f += [(o + i, o + (i + 1) % k, o + k + (i + 1) % k, o + k + i) for i in range(k)]   # basin wall down to the water
    if _Ln >= 40 and k == 4:   # lap pool lane lines along the long axis, 2 m short of each end
        _c = _A.mean(0); _vv = np.array([-_u[1], _u[0]]); n_l = int(_Wd // 2.5)
        for j in range(1, n_l + 1):
            off = -_Wd / 2 + j * 2.5
            if off > _Wd / 2 - 1.0: break
            p0 = _c + _vv * off - _u * (_Ln / 2 - 0.3); p1 = _c + _vv * off + _u * (_Ln / 2 - 0.3); h_ = _vv * 0.08
            v, f = _L; o = len(v); v += [(*(p0 - h_), _z - 0.19), (*(p1 - h_), _z - 0.19), (*(p1 + h_), _z - 0.19), (*(p0 + h_), _z - 0.19)]
            f.append((o, o + 1, o + 2, o + 3))
            q0 = _c + _vv * (off - 1.25) - _u * (_Ln / 2 - 2); q1 = _c + _vv * (off - 1.25) + _u * (_Ln / 2 - 2); g_ = _vv * 0.15   # dark floor line mid-lane (photos)
            v, f = _FL; o = len(v); v += [(*(q0 - g_), _z - 0.195), (*(q1 - g_), _z - 0.195), (*(q1 + g_), _z - 0.195), (*(q0 + g_), _z - 0.195)]; f.append((o, o + 1, o + 2, o + 3))
def _flat(nm, rgb, rough, spec_=0.5):
    m = bpy.data.materials.new(nm); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb(rgb), 1); b.inputs['Roughness'].default_value = rough; b.inputs['Specular IOR Level'].default_value = spec_; return m
if _W[1]:
    _do = mk_obj('bg_pool_deck', _D[0], _D[1], mat_mul('pool_deck', os.path.join(HERE, 'tex', 'mt', 'mv_plaza_pavers.png'), 0.85, 1 / 0.534))
    _n = sum(len(q) for q in _D[1]); set_corner_col(_do.data, np.tile(np.array([*srgb([160, 156, 148]), 1.0]), (_n, 1))); set_uv(_do.data, _D[2])
    mk_obj('bg_pool_coping', _C[0], _C[1], _flat('pool_coping', [236, 236, 232], 0.7))
    mk_obj('bg_pool_water', _W[0], _W[1], _flat('pool_water', [55, 160, 215], 0.08, 0.3))
    if _L[1]: mk_obj('bg_pool_lanes', _L[0], _L[1], _flat('pool_lane', [165, 190, 220], 0.6, 0.2))
    if _FL[1]: mk_obj('bg_pool_floorlines', _FL[0], _FL[1], _flat('pool_floorline', [28, 62, 120], 0.2, 0.1))
    print('pools', len(_W[1]), 'lane lines', len(_L[1]))
# aquatic centre concourse (satellite: paved compound round the pools, lawn strips inside): OSM leisure=sports_centre
# sport=swimming outline as paving, then landuse=grass ways whose centre is inside it as lawn on top
_AQ, _AG = ([], [], []), ([], [])
_els = json.load(open(os.path.join(HERE, 'data', name, 'osm.json'), encoding='utf-8'))['elements']
_box = None
for _el in _els:
    _t = _el.get('tags', {})
    if _el['type'] == 'way' and _t.get('leisure') == 'sports_centre' and _t.get('sport') == 'swimming' and _el.get('geometry'):
        _p = [((g['lon'] - _lon0) * _KX, (g['lat'] - _lat0) * 110540) for g in _el['geometry'] if g]
        if _p[0] == _p[-1]: _p = _p[:-1]
        if max(max(abs(a), abs(b)) for a, b in _p) > meta['near'] - 10: continue
        _A = np.array(_p, float); _zz = float(height(_A[:, 0], _A[:, 1]).mean()) + 0.02
        v, f, uv = _AQ; o = len(v); v += [(x, y, _zz) for x, y in _A]; f.append(tuple(range(o, o + len(_A)))); uv += [(x / 6.0, y / 6.0) for x, y in _A]
        _box = (_A.min(0), _A.max(0), _zz)
        _SINK.append((_A.copy(), _zz + 0.25))   # concourse: terrain under it drops 0.10 m below so it is never covered
if _box is not None:
    for _el in _els:
        _t = _el.get('tags', {})
        if _el['type'] != 'way' or _t.get('landuse') != 'grass' or not _el.get('geometry'): continue
        _p = [((g['lon'] - _lon0) * _KX, (g['lat'] - _lat0) * 110540) for g in _el['geometry'] if g]
        if _p[0] == _p[-1]: _p = _p[:-1]
        _A = np.array(_p, float); _m = _A.mean(0)
        if not (np.all(_m > _box[0]) and np.all(_m < _box[1])): continue
        v, f = _AG; o = len(v); v += [(x, y, _box[2] + 0.01) for x, y in _A]; f.append(tuple(range(o, o + len(_A))))
if _AQ[1]:
    _ao = mk_obj('bg_aquatic_concourse', _AQ[0], _AQ[1], mat_mul('aq_concourse', os.path.join(HERE, 'tex', 'mt', 'mv_plaza_pavers.png'), 0.85, 1 / 0.534))
    _n = sum(len(q) for q in _AQ[1]); set_corner_col(_ao.data, np.tile(np.array([*srgb([196, 186, 166]), 1.0]), (_n, 1))); set_uv(_ao.data, [_AQ[2][i] for q in _AQ[1] for i in q])
    if _AG[1]: mk_obj('bg_aquatic_lawn', _AG[0], _AG[1], _flat('aq_lawn', [92, 124, 64], 0.9, 0.2))
    print('aquatic concourse', len(_AQ[1]), 'lawns', len(_AG[1]))
if _SINK:
    # basin cut: near-ground vertices inside each deck drop 0.35 m under it, so the deck sits flush and the
    # recessed water is not hidden by terrain (deck edge 4 m out covers the dip)
    def _pip(P, X):   # even-odd point-in-polygon, vectorised over points X
        r = np.zeros(len(X), bool); x, y = X[:, 0], X[:, 1]
        for i in range(len(P)):
            (x1, y1), (x2, y2) = P[i - 1], P[i]
            c = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-9) + x1); r ^= c
        return r
    _g = bpy.data.objects['bg_near_ground'].data; _gv = np.zeros(len(_g.vertices) * 3); _g.vertices.foreach_get('co', _gv); _gv = _gv.reshape(-1, 3)
    _ns = 0
    for _P, _zp in _SINK:
        _in = _pip(_P, _gv[:, :2]); _ns += int(_in.sum()); _gv[_in, 2] = np.minimum(_gv[_in, 2], _zp - 0.35)
    _g.vertices.foreach_set('co', _gv.ravel()); _g.update(); print('pool ground verts sunk', _ns)
# pedestrian plazas (highway=pedestrian, area=yes): paver surface on the outline, colour from the satellite median
_PZ = ([], [], [])
for _el in json.load(open(os.path.join(HERE, 'data', name, 'osm.json'), encoding='utf-8'))['elements']:
    _t = _el.get('tags', {})
    if _el['type'] != 'way' or _t.get('highway') != 'pedestrian' or _t.get('area') != 'yes' or not _el.get('geometry'): continue
    _p = [((g['lon'] - _lon0) * _KX, (g['lat'] - _lat0) * 110540) for g in _el['geometry'] if g]
    if _p[0] == _p[-1]: _p = _p[:-1]
    if len(_p) < 3 or max(max(abs(a), abs(b)) for a, b in _p) > meta['near'] - 10: continue
    _A = np.array(_p, float)
    if _area(_A) < 0: _A = _A[::-1]
    _hs = height(_A[:, 0], _A[:, 1]); v, f, uv = _PZ; o = len(v)
    v += [(x, y, float(z) + 0.06) for (x, y), z in zip(_A, _hs)]; f.append(tuple(range(o, o + len(_A)))); uv += [(x / 6.0, y / 6.0) for x, y in _A]
if _PZ[1]:
    _po = mk_obj('bg_plaza', _PZ[0], _PZ[1], mat_mul('plaza', os.path.join(HERE, 'tex', 'mt', 'mv_plaza_pavers.png'), 0.85, 1 / 0.534))
    _n = sum(len(q) for q in _PZ[1]); set_corner_col(_po.data, np.tile(np.array([*srgb([146, 136, 124]), 1.0]), (_n, 1)))
    set_uv(_po.data, [_PZ[2][i] for q in _PZ[1] for i in q]); print('plazas', len(_PZ[1]))
# car parks (amenity=parking, surface not grass): each lot's asphalt colour and the cars parked in it from the close
# aerial (cars.py -> carparks.json: colours and positions, never pixels). Bay lines only where the cars sit on a
# 16 m two-row grid (its direction and phase from the cars); elsewhere plain asphalt.
_CJ = os.path.join(HERE, 'data', name, 'carparks.json'); _CJ = json.load(open(_CJ)) if os.path.exists(_CJ) else {}
_CP = ([], [], [], []); _CQ = ([], [], [], []); _CARS = []; _SEEN = set()
for _el in json.load(open(os.path.join(HERE, 'data', name, 'osm.json'), encoding='utf-8'))['elements']:
    _t = _el.get('tags', {})
    if _el['type'] != 'way' or _t.get('amenity') != 'parking' or _t.get('parking') in ('multi-storey', 'underground') or _t.get('surface') in ('grass', 'gravel', 'dirt') or not _el.get('geometry'): continue
    _p = [((g['lon'] - _lon0) * _KX, (g['lat'] - _lat0) * 110540) for g in _el['geometry'] if g]
    if _p[0] == _p[-1]: _p = _p[:-1]
    if len(_p) < 3 or max(max(abs(a), abs(b)) for a, b in _p) > meta['near'] - 10: continue
    _A = np.array(_p, float)
    if _area(_A) < 0: _A = _A[::-1]
    if KFr is not None and all(np.hypot(*q) < KFr[int((np.degrees(np.arctan2(q[1], q[0])) % 360) // 2)] + 2 for q in _A): continue   # wholly under the ground model
    if _el['id'] in _SEEN: continue   # an era file can carry a way twice
    _SEEN.add(_el['id']); _L = _CJ.get(str(_el['id']))
    if _L: _CARS += _L['cars']
    _grid = bool(_L and _L['pv'] is not None) or (not _CJ)
    # draped on the ground: the outline every 6 m and a 6 m grid inside, triangulated, so a big lot follows the land
    # (one flat polygon 0.08 m up sank under every rise and the ground showed through)
    _B = []
    for _i in range(len(_A)):
        _a, _b = _A[_i], _A[(_i + 1) % len(_A)]; _nseg = max(1, int(np.hypot(*(_b - _a)) // 6))
        _B += [_a + (_b - _a) * t for t in np.arange(_nseg) / _nseg]
    _B = np.array(_B); _g0, _g1 = _A.min(0), _A.max(0)
    _GX, _GY = np.meshgrid(np.arange(_g0[0] + 3, _g1[0], 6.0), np.arange(_g0[1] + 3, _g1[1], 6.0)); _G = np.stack([_GX.ravel(), _GY.ravel()], 1)
    def _inside(Q, poly=_A):
        x, y = Q[:, 0], Q[:, 1]; r = np.zeros(len(Q), bool); j = len(poly) - 1
        for i in range(len(poly)):
            xi, yi = poly[i]; xj, yj = poly[j]
            r ^= ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / ((yj - yi) + 1e-12) + xi); j = i
        return r
    if len(_G): _G = _G[_inside(_G)]
    _Q = np.vstack([_B, _G]) if len(_G) else _B
    from scipy.spatial import Delaunay as _Dl
    try: _T = _Dl(_Q).simplices
    except Exception: continue
    _T = _T[_inside(_Q[_T].mean(1))]
    _hs = height(_Q[:, 0], _Q[:, 1]); v, f, uv, col = _CP if _grid else _CQ; o = len(v)
    v += [(x, y, float(z) + 0.1) for (x, y), z in zip(_Q, _hs)]; _P3 = _Q[_T]; _cr = (_P3[:, 1, 0] - _P3[:, 0, 0]) * (_P3[:, 2, 1] - _P3[:, 0, 1]) - (_P3[:, 1, 1] - _P3[:, 0, 1]) * (_P3[:, 2, 0] - _P3[:, 0, 0])
    f += [(o + int(t[0]), o + int(t[1]), o + int(t[2])) if c_ > 0 else (o + int(t[0]), o + int(t[2]), o + int(t[1])) for t, c_ in zip(_T, _cr)]   # all facing up
    _A = _Q
    if _L: _th, _pu, _pv = _L['th'], _L['pu'] or 0.0, _L['pv'] or 0.0
    else: _E = np.diff(np.vstack([_A, _A[:1]]), axis=0); _e = _E[np.argmax(np.hypot(_E[:, 0], _E[:, 1]))]; _th = math.atan2(_e[1], _e[0]); _pu = _pv = 0.0
    _cs, _sn = math.cos(_th), math.sin(_th)
    uv += [((x * _cs + y * _sn - _pu) / 15.6, (_pv - (-x * _sn + y * _cs)) / 16.0) for x, y in _A]   # bay rows run along th; image rows run down v
    col += [srgb(_L['colour'] if _L else PAL.get('parking', [92, 91, 88]))] * len(_A)
from mathutils import noise as _nz2
from PIL import Image
for _nm, (_v, _f, _uv, _col), _tex in (('bg_carparks', _CP, 'park_bays.png'), ('bg_carparks_plain', _CQ, 'park_plain.png')):
    if not _f: continue
    _im = np.asarray(Image.open(os.path.join(HERE, 'tex', 'mt', _tex)).convert('RGB'), np.float32) / 255
    _lin = np.where(_im <= 0.04045, _im / 12.92, ((_im + 0.055) / 1.055) ** 2.4).mean()
    _co = mk_obj(_nm, _v, _f, mat_mul(_nm[3:], os.path.join(HERE, 'tex', 'mt', _tex), 0.92, 1.0 / _lin))
    _lv = [i for q in _f for i in q]
    _nn = np.array([_nz2.noise(Vector((_v[i][0] / 40.0, _v[i][1] / 40.0, 0.5))) for i in _lv]); _m = 0.92 + 0.08 * np.clip(_nn * 0.5 + 0.5, 0, 1)
    _c = np.array([_col[i] for i in _lv]) * _m[:, None]
    set_corner_col(_co.data, np.hstack([_c, np.ones((len(_c), 1))])); set_uv(_co.data, [_uv[i] for i in _lv]); print(_nm, len(_f))
# the parked cars: a body and a glasshouse, each a lidless box (20 triangles); the roof and bonnet take the colour
# the aerial shows on that car, the side and end glass is dark. A car in six is a longer, taller wagon or ute.
if _CARS:
    _V, _F, _C = [], [], []
    _rng = np.random.default_rng(11)
    def _box(c, hd, L, W, z0, z1, Lt, Wt, dx, side, top):
        cs, sn = math.cos(hd), math.sin(hd); o = len(_V)
        for (l, w, z) in ((-L / 2, -W / 2, z0), (L / 2, -W / 2, z0), (L / 2, W / 2, z0), (-L / 2, W / 2, z0),
                          (dx - Lt / 2, -Wt / 2, z1), (dx + Lt / 2, -Wt / 2, z1), (dx + Lt / 2, Wt / 2, z1), (dx - Lt / 2, Wt / 2, z1)):
            _V.append((c[0] + l * cs - w * sn, c[1] + l * sn + w * cs, c[2] + z))
        for q, k in (((0, 1, 5, 4), side), ((1, 2, 6, 5), side), ((2, 3, 7, 6), side), ((3, 0, 4, 7), side), ((4, 5, 6, 7), top)):
            _F.append(tuple(o + i for i in q)); _C.extend([k] * 4)
    _gz = height(np.array([c[0] for c in _CARS]), np.array([c[1] for c in _CARS]))
    for (x, y, hd, r, g, b), z in zip(_CARS, _gz):
        big = _rng.random() < 1 / 6; L = 4.9 if big else 4.45; W = 1.85 if big else 1.78; H = 1.7 if big else 1.45
        if _rng.random() < 0.5: hd += math.pi
        paint = [*srgb([r, g, b]), 1.0]; low = [*(np.array(srgb([r, g, b])) * 0.7), 1.0]; glass = [*srgb([28, 32, 36]), 1.0]
        c = (x, y, float(z) + 0.08)
        _box(c, hd, L, W, 0.22, 0.9, L - 0.1, W - 0.04, 0.0, low, paint)                                         # body to the waist
        _box((c[0], c[1], c[2] + 0.9), hd, (2.9 if big else 2.5), W - 0.12, 0.0, H - 0.9, (2.6 if big else 1.6), W - 0.36, (-0.45 if big else -0.3), glass, paint)   # glasshouse
    _ob = mk_obj('bg_cars', _V, _F, mat_vcol('car_paint', 0.45)); set_corner_col(_ob.data, np.array(_C, np.float32)); print('cars', len(_CARS))
# what stands on the flat roofs (roofplant.py -> roofplant.json: positions, sizes and colours read from the close
# aerial): lidless boxes on the roof inside the parapet. Housings darkened by their own shade in the aerial lift a little.
_RPJ = os.path.join(HERE, 'data', name, 'roofplant.json')
if os.path.exists(_RPJ) and spec.get('real'):
    _BI = {b['_i']: b for b in BL}
    _V, _F, _C = [], [], []
    for bi, x, y, L, W, hd, ht, r, g, b_ in json.load(open(_RPJ)):
        b = _BI.get(bi)
        if b is None or b['c'] != 'block' or b.get('open') or (b.get('shed') and b['h'] <= 14): continue   # replaced by a landmark, or not a flat roof
        cxy = np.array(b['p'], float).mean(0); top = float(height(cxy[0], cxy[1])) + b['h']
        cs, sn = math.cos(hd), math.sin(hd); o = len(_V)
        c3 = np.array([r, g, b_], float); c3 = c3 * min(1.45, 190.0 / max(c3.max(), 1)) if c3.mean() < 110 else c3
        top_c = [*srgb(list(c3)), 1.0]; side_c = [*(np.array(srgb(list(c3))) * 0.75), 1.0]
        for zz in (top - 0.05, top + ht):
            for l, w in ((-L / 2, -W / 2), (L / 2, -W / 2), (L / 2, W / 2), (-L / 2, W / 2)):
                _V.append((x + l * cs - w * sn, y + l * sn + w * cs, zz))
        for q, k in (((0, 1, 5, 4), side_c), ((1, 2, 6, 5), side_c), ((2, 3, 7, 6), side_c), ((3, 0, 4, 7), side_c), ((4, 5, 6, 7), top_c)):
            _F.append(tuple(o + i for i in q)); _C.extend([k] * 4)
    if _F:
        _ob = mk_obj('bg_roof_plant', _V, _F, mat_vcol('roof_plant', 0.6)); set_corner_col(_ob.data, np.array(_C, np.float32)); print('roof plant', len(_F) // 5)
# cemeteries (landuse=cemetery; real place): the mapped paths are the aisles between the grave rows (close aerial: graves
# lie across the aisle, two rows head to head between neighbouring aisles, ~6 m apart, a plot every ~1.3 m). Each aisle
# side gets its row of plots 2.6 m out; six plots in ten carry an upright headstone (the rest a flat ledger slab, which
# the ground's colour already shows): 0.55-0.75 m wide, 0.6-1.1 m high, the odd obelisk to 1.6 m, of grey or dark
# granite, marble or sandstone. A stone is one double-sided face; none on the cemetery's own drives.
if spec.get('real'):
    from shapely.geometry import Polygon as _SPo, LineString as _SLs, Point as _SPt
    from shapely.ops import unary_union as _SUu
    from shapely.prepared import prep as _SPr
    _cem, _drv, _ais = [], [], []
    for _el in json.load(open(os.path.join(HERE, 'data', name, 'osm.json'), encoding='utf-8'))['elements']:
        _t = _el.get('tags', {})
        if _el['type'] != 'way' or not _el.get('geometry'): continue
        _p = [((g['lon'] - _lon0) * _KX, (g['lat'] - _lat0) * 110540) for g in _el['geometry'] if g]
        if len(_p) < 2 or max(max(abs(a), abs(b)) for a, b in _p) > meta['near'] - 10: continue
        if _t.get('landuse') == 'cemetery' or _t.get('amenity') == 'grave_yard':
            if len(_p) >= 4:
                _q = _SPo(_p); _cem.append(_q if _q.is_valid else _q.buffer(0))
        elif _t.get('highway') in ('path', 'footway'): _ais.append(_p)
        elif _t.get('highway'): _drv.append(_SLs(_p).buffer(3.2))
    if _cem:
        _CU = _SPr(_SUu(_cem)); _DU = _SPr(_SUu(_drv)) if _drv else None
        _rng = np.random.default_rng(17)
        _STONE = [[150, 150, 148], [176, 174, 168], [196, 194, 188], [92, 92, 96], [128, 122, 116], [210, 206, 198], [168, 150, 120]]
        _sx, _sy, _su, _sw, _sh, _sc = [], [], [], [], [], []
        for _p in _ais:
            _l = _SLs(_p)
            if _l.length < 2 or not _CU.intersects(_l): continue
            _n = int(_l.length // 1.3)
            for i in range(_n):
                a = _l.interpolate(i * 1.3 + 0.65); b = _l.interpolate(min(_l.length, i * 1.3 + 0.75))
                d = np.array([b.x - a.x, b.y - a.y]); L = float(np.hypot(*d))
                if L < 1e-6: continue
                u = d / L
                for s in (1, -1):
                    if _rng.random() > 0.6: continue
                    m = np.array([a.x, a.y]) + np.array([-u[1], u[0]]) * s * 2.6
                    pt = _SPt(*m)
                    if not _CU.contains(pt) or (_DU is not None and _DU.contains(pt)): continue
                    _sx.append(m[0]); _sy.append(m[1]); _su.append(u)
                    _sw.append(_rng.uniform(0.55, 0.75)); _sh.append(1.6 if _rng.random() < 0.05 else _rng.uniform(0.6, 1.1))
                    _sc.append(_STONE[int(_rng.integers(0, len(_STONE)))])
        if _sx:
            _gz = height(np.array(_sx), np.array(_sy))
            _V, _F, _C = [], [], []
            for x, y, u, w, h, c, z in zip(_sx, _sy, _su, _sw, _sh, _sc, _gz):
                o = len(_V); hw_ = u * w / 2; z = float(z)
                _V += [(x - hw_[0], y - hw_[1], z - 0.1), (x + hw_[0], y + hw_[1], z - 0.1), (x + hw_[0], y + hw_[1], z + h), (x - hw_[0], y - hw_[1], z + h)]
                _F.append((o, o + 1, o + 2, o + 3)); _C.extend([[*srgb(c), 1.0]] * 4)
            _mh = mat_vcol('headstone', 0.7); _mh.use_backface_culling = False
            _ob = mk_obj('bg_headstones', _V, _F, _mh); set_corner_col(_ob.data, np.array(_C, np.float32)); print('headstones', len(_F))
# shade canopies on the lawn between the 50 m pools (satellite: 4 square pyramid canopies, ~9.5 m, orange/blue/yellow/sage)
_SH = []
for _cx, _cy, _col in () if name != 'gmhba' else ((265, 175, (225, 110, 75)), (205, 330, (45, 60, 170)), (145, 515, (225, 205, 60)), (85, 680, (175, 195, 175))):
    _px, _py = 330 + _cx / 3, 380 + _cy / 3 - 40
    _SH.append(((_px - 500) / 5 - 165, -160 + (500 - _py) / 5, _col))
_hu = np.array([math.cos(math.radians(70)), math.sin(math.radians(70))]); _hv = np.array([-_hu[1], _hu[0]])
for _i, (_x, _y, _col) in enumerate(_SH):
    _c = np.array([_x, _y]); _g = float(height(np.array([_x]), np.array([_y]))[0]); _h = 4.75
    _cr = [_c + _hu * a * _h + _hv * b * _h for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    v = [(*p, _g + 3.2) for p in _cr] + [(_x, _y, _g + 4.3)]; f = [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]
    for p in _cr:   # posts
        o = len(v); d = 0.06; v += [(p[0] - d, p[1] - d, _g), (p[0] + d, p[1] - d, _g), (p[0] + d, p[1] + d, _g), (p[0] - d, p[1] + d, _g)] + [(p[0] - d, p[1] - d, _g + 3.2), (p[0] + d, p[1] - d, _g + 3.2), (p[0] + d, p[1] + d, _g + 3.2), (p[0] - d, p[1] + d, _g + 3.2)]
        f += [(o, o + 1, o + 5, o + 4), (o + 1, o + 2, o + 6, o + 5), (o + 2, o + 3, o + 7, o + 6), (o + 3, o, o + 4, o + 7)]
    _so = mk_obj('bg_pool_shade_%d' % _i, v, f, _flat('pool_shade_%d' % _i, list(_col), 0.8, 0.1))
print('pool shades', [(round(a), round(b)) for a, b, _ in _SH])
