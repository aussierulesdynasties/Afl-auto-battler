# Named Geelong CBD buildings (exec'd by scene.py before the generic towers when spec['towers_v2']). Each OSM-named tower
# whose facade the research confirmed gets its own hand-made facade (tex/fac/n_<key>.png, py_mk_tower22.py); the Old Post
# Office drops to its real two storeys plus the corner clock tower; St Mary of the Angels becomes a bluestone Gothic church
# (nave, transepts, slate roof, square tower and 46 m spire at the Yarra St end), laid out from the aerial.
NAMED = {  # centroid (local m), facade key, height override
 'pivot': ((218, 907), 'pivot', None), 'ryrie44': ((86, 1076), 'ryrie44', None), 'tac': ((520, 1405), 'tac', None),
 'barwon': ((115, 1149), 'barwon', None), 'oldpo': ((218, 1104), 'oldpo', 13.0),
 'gmhba': ((542, 1300), 'gmhba', None), 'worksafe': ((378, 1353), 'worksafe', None), 'holiday': ((49, 1100), 'holiday', None),
 'rhotel': ((985, 1150), 'rhotel', None), 'edgewater': ((739, 1468), 'edgewater', None), 'civic': ((938, 1287), 'civic', None),
 'rydges': ((184, 776), 'rydges', None)}   # second set: py_mk_tower25.py
for b in BL:
    if b['c'] != 'tower': continue
    c = np.array(b['p'], float).mean(0)
    if np.hypot(c[0] - 504, c[1] - 611) < 12: b['c'] = 'skip'; continue   # basilica: built below
    for k, (q, f, h) in NAMED.items():
        if np.hypot(c[0] - q[0], c[1] - q[1]) < 12:
            b['c'] = 'n_' + k; b['wall'] = 0
            if h: b['h'] = h
for k, (q, f, h) in NAMED.items():
    PAL['walls_n_' + k] = [[255, 255, 255]]; build_class('n_' + k, 'fac/n_%s.png' % f, 3.6, 3.2, None, 0.2)
def _box(V, F, U, c, u, v, L, W, z0, z1, T=(4.0, 6.0)):   # oriented box walls: centre c, unit axes u (length) v (width)
    P = [c - u * L / 2 - v * W / 2, c + u * L / 2 - v * W / 2, c + u * L / 2 + v * W / 2, c - u * L / 2 + v * W / 2]
    per = 0.0
    for i in range(4):
        a, b_ = P[i], P[(i + 1) % 4]; l = float(np.hypot(*(b_ - a))); o = len(V)
        V += [(a[0], a[1], z0), (b_[0], b_[1], z0), (b_[0], b_[1], z1), (a[0], a[1], z1)]; F.append((o, o + 1, o + 2, o + 3))
        U += [(per / T[0], 0), ((per + l) / T[0], 0), ((per + l) / T[0], (z1 - z0) / T[1]), (per / T[0], (z1 - z0) / T[1])]; per += l
    return P
def _gable(V, F, U, RV, RFc, P, u, v, L, W, z1, rh):   # pitched roof along u, gable end triangles in stone
    c = (P[0] + P[2]) / 2; r0, r1 = c - u * L / 2, c + u * L / 2; o = len(RV)
    RV += [(P[0][0], P[0][1], z1), (P[1][0], P[1][1], z1), (r1[0], r1[1], z1 + rh), (r0[0], r0[1], z1 + rh), (P[3][0], P[3][1], z1), (P[2][0], P[2][1], z1)]
    RFc += [(o, o + 1, o + 2, o + 3), (o + 5, o + 4, o + 3, o + 2)]
    for a, b_, r in ((P[1], P[2], r1), (P[3], P[0], r0)):
        o = len(V); V += [(a[0], a[1], z1), (b_[0], b_[1], z1), (r[0], r[1], z1 + rh)]; F.append((o, o + 1, o + 2)); U += [(0, 0), (W / 4.0, 0), (W / 8.0, rh / 6.0)]
_V, _F, _U, _RV, _RF = [], [], [], [], []
_e, _w = np.array([536.0, 605.5]), np.array([479.0, 626.0])   # Yarra St front (tower) and apse end, read off the aerial
_u = (_w - _e) / np.linalg.norm(_w - _e); _v = np.array([-_u[1], _u[0]]); _z = float(height(504, 611)) - 0.5
_nc = (_e + _w) / 2 + _u * 2; _NL = float(np.linalg.norm(_w - _e)) - 6
P = _box(_V, _F, _U, _nc, _u, _v, _NL, 15.0, _z, _z + 17); _gable(_V, _F, _U, _RV, _RF, P, _u, _v, _NL, 15.0, _z + 17, 8.5)   # nave
_tc = _e + _u * 0.62 * float(np.linalg.norm(_w - _e))
P = _box(_V, _F, _U, _tc, _v, _u, 40.0, 13.0, _z, _z + 16); _gable(_V, _F, _U, _RV, _RF, P, _v, _u, 40.0, 13.0, _z + 16, 7.5)   # transepts
_sc = _e + _u * 4.5; _box(_V, _F, _U, _sc, _u, _v, 9.0, 9.0, _z, _z + 18.0)   # square bell tower, 18 m
_o = len(_V); _ang = np.arange(8) * np.pi / 4 + np.pi / 8
for a in _ang: _V.append((_sc[0] + 5.0 * np.cos(a), _sc[1] + 5.0 * np.sin(a), _z + 18.0))
_V.append((_sc[0], _sc[1], _z + 64.0))   # 46 m octagonal bluestone spire to 64 m
for i in range(8): _F.append((_o + i, _o + (i + 1) % 8, _o + 8)); _U += [(0, 0), (1.0, 0), (0.5, 46.0 / 6.0)]
_ob = mk_obj('bg_basilica', _V, _F, mat_facade('basilica_stone', os.path.join(HERE, 'tex', 'fac', 'n_bluestone.png'), 0.85, 0.2))
set_corner_col(_ob.data, np.ones((sum(len(f) for f in _F), 4))); set_uv(_ob.data, _U)
_ro = mk_obj('bg_basilica_roof', _RV, _RF, mat_vcol('basilica_slate', 0.6))
set_corner_col(_ro.data, np.tile(np.array([*lin((66, 70, 76))[:3], 1.0]), (sum(len(f) for f in _RF), 1)))
_cv = []; _cf = []   # Old Post Office clock tower: 6 m square on the Ryrie / Gheringhap corner, to 36.8 m
_pc = np.array([229.0, 1084.0]); _zp = float(height(*_pc)) - 0.5; _cu = np.array([1.0, 0.0]); _cvv = np.array([0.0, 1.0]); _cu2 = []
_box(_cv, _cf, _cu2, _pc, _cu, _cvv, 6.0, 6.0, _zp, _zp + 31.0, (6.0, 6.0))
_o = len(_cv); _cv += [(_pc[0] + dx, _pc[1] + dy, _zp + 31.0) for dx, dy in ((-3, -3), (3, -3), (3, 3), (-3, 3))] + [(_pc[0], _pc[1], _zp + 36.8)]
for i in range(4): _cf.append((_o + i, _o + (i + 1) % 4, _o + 4)); _cu2 += [(0, 0), (1, 0), (0.5, 1)]
_co = mk_obj('bg_oldpo_tower', _cv, _cf, mat_facade('oldpo_tower', os.path.join(HERE, 'tex', 'fac', 'n_oldpo.png'), 0.8, 0.2))
set_corner_col(_co.data, np.ones((sum(len(f) for f in _cf), 4))); set_uv(_co.data, _cu2)
print('named towers', sum(1 for b in BL if b['c'].startswith('n_')), 'basilica faces', len(_F))
