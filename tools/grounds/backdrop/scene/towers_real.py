# Real-place towers (exec'd by scene.py when spec 'real'): no painted windows. Each tower is a glass core with a
# modelled floor slab every storey that stands 0.7 m proud of the core (balcony edges / spandrels read as real
# bands with depth), its roof capped in the aerial's roof colour. Shares scene.py's globals.
from shapely.geometry import Polygon as _Poly
def _ring(P, z0, z1, V, F, C, col):
    k = len(P)
    for i in range(k):
        a, b = P[i], P[(i + 1) % k]; n = len(V)
        V += [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)]; F.append((n, n + 1, n + 2, n + 3)); C += [col] * 4
def _capf(P, z, V, F, C, col, down=False):
    n = len(V)
    for x, y in P: V.append((x, y, z)); C.append(col)
    F.append(tuple(range(n, n + len(P)))[::-1] if down else tuple(range(n, n + len(P))))
_TV, _TF, _TC = [], [], []
_GV, _GF, _GC = [], [], []
_nt = 0
for b in BL:
    if b['c'] not in ('tower', 'tower_far'): continue
    P = np.array(b['p'], float)
    if len(P) > 3 and np.allclose(P[0], P[-1]): P = P[:-1]
    try:
        po = _Poly(P)
        if not po.is_valid: po = po.buffer(0)
        out = po.buffer(0.7, join_style=2)
        if out.geom_type != 'Polygon': continue
        O = np.array(out.exterior.coords)[:-1]
        if not _Poly(O).exterior.is_ccw: O = O[::-1]
        if not po.exterior.is_ccw: P = P[::-1]
    except Exception: continue
    cxy = P.mean(0); base = float(height(cxy[0], cxy[1])) - 1.0; top = base + 1.0 + b['h']
    _far = float(np.hypot(*cxy)) > 1000
    wc = lin(b['wall_rgb']) if b.get('wall_rgb') else lin(PAL['walls_tower'][b['wall'] % len(PAL['walls_tower'])]) * (1 + 0.06 * (rng.random() - 0.5))
    glass = np.array([0.035, 0.05, 0.065]) * (1 + 0.2 * (rng.random() - 0.5)) + wc * 0.08   # dark glass between the slabs
    rc = lin(b['roof_c']) if b.get('roof_c') else wc * 0.9
    g4 = (*glass, 1.0); w4 = (*wc, 1.0); r4 = (*rc, 1.0)
    _ring(P, base, top, _GV, _GF, _GC, g4)
    step = 6.8 if _far else 3.4; z = base + 1.0 + 4.5   # podium storey, then a slab every storey
    while z < top - 1.0:
        _ring(O, z, z + 0.55, _TV, _TF, _TC, w4); _capf(O, z + 0.55, _TV, _TF, _TC, w4); _capf(O, z, _TV, _TF, _TC, w4, True); z += step
    _ring(O, top - 1.2, top, _TV, _TF, _TC, w4)   # parapet band
    if not _far and float(np.hypot(*cxy)) < 800:
        # columns / balcony dividers: a modelled fin every ~4.5 m along each face, standing out as far as the slabs
        k = len(P)
        for i in range(k):
            a, c_ = P[i], P[(i + 1) % k]; L = float(np.hypot(*(c_ - a)))
            if L < 6: continue
            t_ = (c_ - a) / L; n_ = np.array([t_[1], -t_[0]])   # outward for a ccw ring
            nf = int(L // 4.5)
            for j in range(1, nf + 1):
                m_ = a + t_ * (L * j / (nf + 1))
                q = [m_ - t_ * 0.2, m_ + t_ * 0.2, m_ + t_ * 0.2 + n_ * 0.65, m_ - t_ * 0.2 + n_ * 0.65]
                _ring(q, base + 5.5, top - 1.2, _TV, _TF, _TC, w4)
    _capf(P, top - 0.05, _TV, _TF, _TC, r4); _nt += 1
    b['c'] = 'tower_done'
if _TV:
    for nm, (V_, F_, C_) in (('bg_bld_tower_slabs', (_TV, _TF, _TC)), ('bg_bld_tower_glass', (_GV, _GF, _GC))):
        o = mk_obj(nm, V_, F_, mat_vcol(nm, 0.35 if 'glass' in nm else 0.8))
        set_corner_col(o.data, np.array([C_[i] for f_ in F_ for i in f_]))
print('real towers', _nt, 'slab faces', len(_TF))
