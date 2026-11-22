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
_W, _D, _C, _L = ([], []), ([], [], []), ([], []), ([], [])
for _el in json.load(open(os.path.join(HERE, 'data', name, 'osm.json'), encoding='utf-8'))['elements']:
    if _el['type'] != 'way' or _el.get('tags', {}).get('leisure') != 'swimming_pool' or not _el.get('geometry'): continue
    _p = [((g['lon'] - _lon0) * _KX, (g['lat'] - _lat0) * 110540) for g in _el['geometry'] if g]
    if _p[0] == _p[-1]: _p = _p[:-1]
    if len(_p) < 3 or max(max(abs(a), abs(b)) for a, b in _p) > meta['near'] - 10: continue
    _A = np.array(_p, float)
    if _area(_A) < 0: _A = _A[::-1]
    _R, _ra, _u, _Ln, _Wd = _rect(_A)
    if abs(_area(_A)) > 0.80 * _ra: _A = _R   # squared: OSM steps on a rectangular pool are tracing noise
    if _area(_A) < 0: _A = _A[::-1]
    _dk = _off(_A, 3.0); _cp = _off(_A, 0.3); k = len(_A)
    _z = float(height(_dk[:, 0], _dk[:, 1]).max()) + 0.08
    v, f, uv = _D; o = len(v); v += [(x, y, _z) for x, y in _dk] + [(x, y, _z) for x, y in _cp]
    for i in range(k):
        q = (o + i, o + (i + 1) % k, o + k + (i + 1) % k, o + k + i); f.append(q); uv += [(v[j][0] / 6.0, v[j][1] / 6.0) for j in q]
    v, f = _C; o = len(v); v += [(x, y, _z + 0.02) for x, y in _cp] + [(x, y, _z + 0.02) for x, y in _A]
    f += [(o + i, o + (i + 1) % k, o + k + (i + 1) % k, o + k + i) for i in range(k)]
    v, f = _W; o = len(v); v += [(x, y, _z - 0.02) for x, y in _A]; f.append(tuple(range(o, o + k)))
    if _Ln >= 40 and k == 4:   # lap pool lane lines along the long axis, 2 m short of each end
        _c = _A.mean(0); _vv = np.array([-_u[1], _u[0]]); n_l = int(_Wd // 2.5)
        for j in range(1, n_l + 1):
            off = -_Wd / 2 + j * 2.5
            if off > _Wd / 2 - 1.0: break
            p0 = _c + _vv * off - _u * (_Ln / 2 - 2); p1 = _c + _vv * off + _u * (_Ln / 2 - 2); h_ = _vv * 0.125
            v, f = _L; o = len(v); v += [(*(p0 - h_), _z - 0.015), (*(p1 - h_), _z - 0.015), (*(p1 + h_), _z - 0.015), (*(p0 + h_), _z - 0.015)]
            f.append((o, o + 1, o + 2, o + 3))
def _flat(nm, rgb, rough, spec_=0.5):
    m = bpy.data.materials.new(nm); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb(rgb), 1); b.inputs['Roughness'].default_value = rough; b.inputs['Specular IOR Level'].default_value = spec_; return m
if _W[1]:
    _do = mk_obj('bg_pool_deck', _D[0], _D[1], mat_mul('pool_deck', os.path.join(HERE, 'tex', 'mt', 'mv_plaza_pavers.png'), 0.85, 1 / 0.534))
    _n = sum(len(q) for q in _D[1]); set_corner_col(_do.data, np.tile(np.array([*srgb([160, 156, 148]), 1.0]), (_n, 1))); set_uv(_do.data, _D[2])
    mk_obj('bg_pool_coping', _C[0], _C[1], _flat('pool_coping', [236, 236, 232], 0.7))
    mk_obj('bg_pool_water', _W[0], _W[1], _flat('pool_water', [40, 120, 165], 0.18, 0.12))
    if _L[1]: mk_obj('bg_pool_lanes', _L[0], _L[1], _flat('pool_lane', [25, 60, 95], 0.18, 0.12))
    print('pools', len(_W[1]), 'lane lines', len(_L[1]))
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
# car parks (amenity=parking, surface not grass): People First park asphalt, one 104 m seamless tile, 40 m mottle
_CP = ([], [], [])
for _el in json.load(open(os.path.join(HERE, 'data', name, 'osm.json'), encoding='utf-8'))['elements']:
    _t = _el.get('tags', {})
    if _el['type'] != 'way' or _t.get('amenity') != 'parking' or _t.get('parking') in ('multi-storey', 'underground') or _t.get('surface') in ('grass', 'gravel', 'dirt') or not _el.get('geometry'): continue
    _p = [((g['lon'] - _lon0) * _KX, (g['lat'] - _lat0) * 110540) for g in _el['geometry'] if g]
    if _p[0] == _p[-1]: _p = _p[:-1]
    if len(_p) < 3 or max(max(abs(a), abs(b)) for a, b in _p) > meta['near'] - 10: continue
    _A = np.array(_p, float)
    if _area(_A) < 0: _A = _A[::-1]
    _c = _A.mean(0)
    if KFr is not None and all(np.hypot(*q) < KFr[int((np.degrees(np.arctan2(q[1], q[0])) % 360) // 2)] + 2 for q in _A): continue   # wholly under the ground model
    _hs = height(_A[:, 0], _A[:, 1]); v, f, uv = _CP; o = len(v)
    v += [(x, y, float(z) + 0.08) for (x, y), z in zip(_A, _hs)]; f.append(tuple(range(o, o + len(_A)))); _E = np.diff(np.vstack([_A, _A[:1]]), axis=0); _e = _E[np.argmax(np.hypot(_E[:, 0], _E[:, 1]))]; _th = math.atan2(_e[1], _e[0]); _cs, _sn = math.cos(_th), math.sin(_th)
    uv += [((x * _cs + y * _sn) / 15.6, (-x * _sn + y * _cs) / 16.0) for x, y in _A]   # bay rows run along the lot's longest side
if _CP[1]:
    from mathutils import noise as _nz2
    _co = mk_obj('bg_carparks', _CP[0], _CP[1], mat_mul('park_bays', os.path.join(HERE, 'tex', 'mt', 'park_bays.png'), 0.92, 1.0))
    _lv = [i for q in _CP[1] for i in q]
    _nn = np.array([_nz2.noise(Vector((_CP[0][i][0] / 40.0, _CP[0][i][1] / 40.0, 0.5))) for i in _lv]); _m = 0.85 + 0.15 * np.clip(_nn * 0.5 + 0.5, 0, 1)
    set_corner_col(_co.data, np.stack([_m, _m, _m, np.ones_like(_m)], 1)); set_uv(_co.data, [_CP[2][i] for i in _lv]); print('car parks', len(_CP[1]))
