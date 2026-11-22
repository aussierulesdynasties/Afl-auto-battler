# exec'd from scene.py: the forecourt overlay (forecourt.png, 0.1 m/px, made by fc_overlay.py) on a 2 m grid draped 6 cm above the terrain.
_fj = os.path.join(D, 'forecourt.json')
if os.path.exists(_fj):
    _b = json.load(open(_fj))
    _nx = int((_b['x1'] - _b['x0']) / 2) + 1; _ny = int((_b['y1'] - _b['y0']) / 2) + 1
    _gx, _gy = np.meshgrid(np.linspace(_b['x0'], _b['x1'], _nx), np.linspace(_b['y0'], _b['y1'], _ny))
    _xy = np.column_stack([_gx.ravel(), _gy.ravel()])
    _z = drape(_xy) + 0.06
    _F = [(j * _nx + i, j * _nx + i + 1, (j + 1) * _nx + i + 1, (j + 1) * _nx + i) for j in range(_ny - 1) for i in range(_nx - 1)]
    _m = bpy.data.materials.new('forecourt'); _m.use_nodes = True; _nt = _m.node_tree; _bs = _nt.nodes['Principled BSDF']
    _t = _nt.nodes.new('ShaderNodeTexImage'); _t.image = bpy.data.images.load(os.path.join(D, 'forecourt.png')); _t.interpolation = 'Cubic'
    _nt.links.new(_t.outputs['Color'], _bs.inputs['Base Color']); _nt.links.new(_t.outputs['Alpha'], _bs.inputs['Alpha'])
    _bs.inputs['Roughness'].default_value = 0.85
    _o = mk_obj('forecourt', np.column_stack([_xy, _z]), _F, _m)
    _me = _o.data; _lv = np.empty(len(_me.loops), np.int32); _me.loops.foreach_get('vertex_index', _lv)
    _uv = np.column_stack([(_xy[:, 0] - _b['x0']) / (_b['x1'] - _b['x0']), (_xy[:, 1] - _b['y0']) / (_b['y1'] - _b['y0'])])[_lv]
    _me.uv_layers.new(name='UVMap').data.foreach_set('uv', _uv.astype(np.float32).ravel())
    print('forecourt overlay', _nx, _ny)

# plaza planters (hand trace): a 0.25 m wide, 0.45 m high off-white concrete rim round each bed, and a low lumpy shrub bed
_hj = os.path.join(HERE, 'spec', os.path.basename(SP).replace('.json', '_fc_hand.json'))
if os.path.exists(_hj):
    _V, _Fc, _PSV, _PSF = [], [], [], []
    for _p in json.load(open(_hj))['planters']:
        _P = np.array(_p['pts'], float); _c = _P.mean(0); _n = len(_P)
        _d = _P - _c; _r = np.linalg.norm(_d, axis=1, keepdims=True); _Pi = _c + _d * (1 - 0.25 / _r)
        _z = drape(_P) + 0.0; _zt = float(_z.max()) + 0.45
        o = len(_V)
        for i in range(_n): _V += [(*_P[i], _z[i] - 0.1), (*_P[i], _zt), (*_Pi[i], _zt), (*_Pi[i], _zt - 0.15)]
        for i in range(_n):
            j = (i + 1) % _n; a, b = o + 4 * i, o + 4 * j
            _Fc += [(a, b, b + 1, a + 1), (a + 1, b + 1, b + 2, a + 2), (a + 2, b + 2, b + 3, a + 3)]
        # shrub bed: centre raised 0.5 m above the soil line, edges at the rim, jittered
        o = len(_PSV); _PSV.append((*_c, _zt + 0.35))
        for i in range(_n):
            for t in (0.0, 0.5):
                q = _Pi[i] * (1 - t) + _Pi[(i + 1) % _n] * t
                _PSV.append((*q, _zt - 0.1 + rng.uniform(0, 0.2)))
        _m2 = 2 * _n
        _PSF += [(o, o + 1 + k, o + 1 + (k + 1) % _m2) for k in range(_m2)]
    _rm = mat_white('planter_rim', (205, 200, 190))
    mk_obj('plaza_planter_rims', _V, _Fc, _rm)
    _sm = mat_tint('planter_shrubs', os.path.join(HERE, 'tex', 'leaf_clumps.png'), tuple(srgb((78, 96, 58))), 0.9)
    _so = mk_obj('plaza_planter_shrubs', _PSV, _PSF, _sm); set_uv_box(_so.data, 2.8 / 8)
    print('plaza planters', len(json.load(open(_hj))['planters']))

# kiosks (Gates A/B ticket box, photo E37_017, scaled by a 1.75 m person at the gate: roof top 5.2 m, fascia 1.1 m) on
# warm-grey walls 2 m inside it; the dark rooftop unit is the LED screen (12 x 4.4 m, 2.7:1 in the photo) at the aerial's dark patch inside the slab (z19, reference only), 1.2 m tall
if os.path.exists(_hj):
    def _pip(P, X, Y):
        r = np.zeros(X.shape, bool); n = len(P)
        for i in range(n):
            (x1, y1), (x2, y2) = P[i], P[(i + 1) % n]
            c = ((y1 > Y) != (y2 > Y)) & (X < (x2 - x1) * (Y - y1) / ((y2 - y1) or 1e-9) + x1); r ^= c
        return r
    _im3 = bpy.data.images.load(os.path.join(HERE, 'data', 'optus', 'sat_hi_plaza.png')); _w3, _h3 = _im3.size
    _px3 = np.empty(_w3 * _h3 * 4, np.float32); _im3.pixels.foreach_get(_px3); _px3 = _px3.reshape(_h3, _w3, 4)[::-1]
    _Lk = (0.299 * _px3[..., 0] + 0.587 * _px3[..., 1] + 0.114 * _px3[..., 2]) * 100; bpy.data.images.remove(_im3)
    _KV, _KF, _WV, _WF, _UV, _UF = [], [], [], [], [], []
    def _prism(V, F, P, z0, z1):
        o = len(V); n = len(P)
        for x, y in P: V += [(x, y, z0), (x, y, z1)]
        for i in range(n): j = (i + 1) % n; F.append((o + 2 * i, o + 2 * j, o + 2 * j + 1, o + 2 * i + 1))
        F.append(tuple(o + 2 * i + 1 for i in range(n))); F.append(tuple(o + 2 * i for i in reversed(range(n))))
    for _b in [b for b in json.load(open(_hj))['bands'] if b.get('tone') == 3]:
        _P = np.array(_b['pts'], float); _c = _P.mean(0); _zg = float(drape(_P).min())
        _d = _P - _c; _r = np.linalg.norm(_d, axis=1, keepdims=True); _Pi = _c + _d * np.maximum(0.2, 1 - 2.0 / _r)
        _prism(_WV, _WF, _Pi, _zg - 0.2, _zg + 4.1); _prism(_KV, _KF, _P, _zg + 4.1, _zg + 5.2)
        _ys, _xs = np.mgrid[0:_Lk.shape[0], 0:_Lk.shape[1]]
        _X = 80 + _xs * 0.125; _Y = 135 - _ys * 0.125
        _in = _pip(_c + _d * np.maximum(0.1, 1 - 1.5 / _r), _X, _Y) & (_Lk < 25)
        if _in.sum() > 50:
            _ux, _uy = _X[_in], _Y[_in]; _cv2 = np.cov(np.vstack([_ux, _uy])); _ev, _evv = np.linalg.eigh(_cv2)
            _ax = _evv[:, 1]; _bx = _evv[:, 0]; _mc = np.array([_ux.mean(), _uy.mean()])
            _pr = np.column_stack([_ux - _mc[0], _uy - _mc[1]]); _a = _pr @ _ax; _bb = _pr @ _bx
            _hl, _hw = (np.percentile(_a, 98) - np.percentile(_a, 2)) / 2, (np.percentile(_bb, 98) - np.percentile(_bb, 2)) / 2
            _R = [_mc + sa * _hl * _ax + sb * _hw * _bx for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            _prism(_UV, _UF, _R, _zg + 5.2, _zg + 9.6); print('kiosk unit', [round(v, 1) for v in _mc], round(2 * _hl, 1), 'x', round(2 * _hw, 1))
    mk_obj('plaza_kiosk_roofs', _KV, _KF, mat_white('kiosk_roof', (226, 226, 222)))
    mk_obj('plaza_kiosk_walls', _WV, _WF, mat_white('kiosk_walls', (140, 132, 122)))
    if _UV: mk_obj('plaza_kiosk_units', _UV, _UF, mat_white('kiosk_unit', (30, 34, 40)))
