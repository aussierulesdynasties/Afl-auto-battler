import shutil
shutil.copy('scene.py', 'scene.py.pre_pond2'); shutil.copy('surf.py', 'surf.py.pre_pond2')
p = 'scene.py'; s = open(p, encoding='utf-8').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a; s = s.replace(a, b)
rep("""    Z[_sel] = np.minimum(Z[_sel], _w['z'] - 0.15)   # only grid points inside the water, 15 cm under it: shallow banks
""", """    if not _w.get('still'):
        Z[_sel] = np.minimum(Z[_sel], _w['z'] - 0.15); continue
    # still pond: grade, don't sink (texture session 2026-11-20). Bed 0.15 under the water; a 10 m ring rises linearly
    # from water + 0.1 at the shore to the natural height at its outer edge
    _b = (X > _wv[:, 0].min() - 12) & (X < _wv[:, 0].max() + 12) & (Y > _wv[:, 1].min() - 12) & (Y < _wv[:, 1].max() + 12)
    _in = _b & (_gm[_iy, _ix, 1] > 0.5)
    if not _in.any(): continue
    _P = np.column_stack([X[_in], Y[_in]]); _out = _b & ~_in
    _Q = np.column_stack([X[_out], Y[_out]])
    _d = np.sqrt(((_Q[:, None, :] - _P[None, :, :]) ** 2).sum(-1)).min(1) - NS / 2   # metres from the shore
    _t = np.clip(_d / 10.0, 0, 1); _zs = _w['z'] + 0.1
    _zo = Z[_out]; _r = _d < 10.0
    _zo[_r] = (_zs + (_zo - _zs) * _t)[_r]; Z[_out] = _zo
    Z[_in] = _w['z'] - 0.15
    Z0[_b] = Z[_b]   # reeds and paths drape on the graded bank
""")
rep("""        bp = nt_.nodes.new('ShaderNodeBump')""", """        if nm == 'pond_water': return mm   # still ponds: no ripple bump
        bp = nt_.nodes.new('ShaderNodeBump')""")
rep("""_wp = mat_tint('pond_water', BGT + 'perth/perth_swan_water.png', (0.7, 0.7, 0.7), 0.15, 1.33)   # still ponds: base x 0.7""",
    """_wp = mat_tint('pond_water', BGT + 'perth/perth_swan_water.png', (1.334, 0.73, 0.267), 0.55, 1.33)   # still pond: texture tinted to mean albedo (48,70,62)""")
rep("""surf_obj('bg_reed', _SF['reed'], mat_tint""", """_ro = surf_obj('bg_reed', _SF['reed'], mat_tint""")
rep("""surf_obj('bg_path', _SF['path']""", """if _ro:   # reed clumps over the water sit just above it
    for _w in _SF['water']:
        if not _w.get('still'): continue
        _wv = np.array(_w['v'])
        for _v in _ro.data.vertices:
            if _wv[:, 0].min() - 3 < _v.co.x < _wv[:, 0].max() + 3 and _wv[:, 1].min() - 3 < _v.co.y < _wv[:, 1].max() + 3: _v.co.z = max(_v.co.z, _w['z'] + 0.04)
surf_obj('bg_path', _SF['path']""")
open(p, 'w', encoding='utf-8', newline='').write(s)
p = 'surf.py'; s = open(p, encoding='utf-8').read()
rep("""REED = WATER.buffer(1.5, quad_segs=3).difference(WATER).difference(ROAD).difference(PATH).intersection(CLIP)   # 1.5 m reed and grass fringe on every bank""",
"""import random as _rnd; _rnd.seed(7)
_cl = []   # irregular reed clumps reaching up to ~0.5 m (some 1 m) into the water, so the shoreline breaks up
for _wp in parts(WATER) if False else getattr(WATER, 'geoms', [WATER]):
    if _wp.is_empty or _wp.area >= 200000: continue
    _ring = _wp.exterior; _s = 0.0
    while _s < _ring.length:
        _pt = _ring.interpolate(_s); _cl.append(_pt.buffer(_rnd.uniform(0.3, 1.1), quad_segs=3)); _s += _rnd.uniform(1.0, 4.0)
_STILL = unary_union([g for g in getattr(WATER, 'geoms', [WATER]) if not g.is_empty and g.area < 200000]) if wpolys else Polygon()
REED = unary_union([WATER.buffer(1.5, quad_segs=3).difference(WATER), _STILL.difference(_STILL.buffer(-0.5)), unary_union(_cl).intersection(_STILL) if _cl else Polygon()]).difference(ROAD).difference(PATH).intersection(CLIP)   # 1.5 m fringe + 0.5 m overlap + clumps on still ponds""")
open(p, 'w', encoding='utf-8', newline='').write(s); print('ok')
