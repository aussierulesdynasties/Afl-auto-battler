s = open('pools.py', encoding='utf-8', newline='').read()
n0 = len(s)
s = s.replace("_flat('pool_water', [95, 195, 222], 0.08, 0.3)", "_flat('pool_water', [55, 160, 215], 0.08, 0.3)")
s = s.replace("_flat('pool_lane', [228, 234, 236], 0.6, 0.2)", "_flat('pool_lane', [165, 190, 220], 0.6, 0.2)")
s = s.replace("_W, _D, _C, _L = ([], []), ([], [], []), ([], []), ([], [])", "_W, _D, _C, _L = ([], []), ([], [], []), ([], []), ([], []); _FL = ([], [])")
a = "            f.append((o, o + 1, o + 2, o + 3))\n"
assert a in s
s = s.replace(a, a + "            q0 = _c + _vv * (off - 1.25) - _u * (_Ln / 2 - 2); q1 = _c + _vv * (off - 1.25) + _u * (_Ln / 2 - 2); g_ = _vv * 0.15   # dark floor line mid-lane (photos)\n"
              "            v, f = _FL; o = len(v); v += [(*(q0 - g_), _z + 0.005), (*(q1 - g_), _z + 0.005), (*(q1 + g_), _z + 0.005), (*(q0 + g_), _z + 0.005)]; f.append((o, o + 1, o + 2, o + 3))\n", 1)
b = "    print('pools', len(_W[1]), 'lane lines', len(_L[1]))"
assert b in s
s = s.replace(b, """    if _FL[1]: mk_obj('bg_pool_floorlines', _FL[0], _FL[1], _flat('pool_floorline', [28, 62, 120], 0.2, 0.1))
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
        _A = np.array(_p, float); _zz = float(height(_A[:, 0], _A[:, 1]).max()) + 0.04
        v, f, uv = _AQ; o = len(v); v += [(x, y, _zz) for x, y in _A]; f.append(tuple(range(o, o + len(_A)))); uv += [(x / 6.0, y / 6.0) for x, y in _A]
        _box = (_A.min(0), _A.max(0), _zz)
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
    print('aquatic concourse', len(_AQ[1]), 'lawns', len(_AG[1]))""")
open('pools.py', 'w', encoding='utf-8', newline='').write(s)
print('patched', n0, len(s))
