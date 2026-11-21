# Photo pass 2026-11-21 (Dome 12, halls 10 photos):
#  - brick block south of The Dome (OSM 287001171, 3 levels): red-brick walls 14 m, grey flat roof, blue entry tower 24 m at the corner nearest the Dome.
#  - Home & Lifestyle Pavilion (OSM 35030128): grey roof at 14 m with 4 raised curved ribs running corner to corner.
def _accor_annex():
    import json as _j
    lat0, lon0 = -33.847086, 151.063400; KX = 111320 * math.cos(math.radians(lat0)); KY = 110540
    G = {e['id']: np.array([((g['lon'] - lon0) * KX, (g['lat'] - lat0) * KY) for g in e['geometry']])
         for e in _j.load(open(os.path.join(HERE, 'data', 'accor', 'osm.json'), encoding='utf-8'))['elements'] if e.get('id') in (287001171, 35030128) and 'geometry' in e}
    O = {}
    def q(key, a, b, c_, d, uv): V, F, U = O.setdefault(key, ([], [], [])); n = len(V); V += [a, b, c_, d]; F.append((n, n + 1, n + 2, n + 3)); U += uv
    def drop(c_):
        k = [i for i, b in enumerate(BL) if math.hypot(*(np.mean(b['p'], 0) - c_)) < 40]; BL[:] = [b for i, b in enumerate(BL) if i not in k]
    def extrude(P, z0, h, wall, roof):
        if np.allclose(P[0], P[-1]): P = P[:-1]
        per = 0.0
        for i in range(len(P)):
            a, b = P[i], P[(i + 1) % len(P)]; L = float(np.hypot(*(b - a)))
            q(wall, (*a, z0), (*b, z0), (*b, z0 + h), (*a, z0 + h), [(per / 6, 0), ((per + L) / 6, 0), ((per + L) / 6, h / 6), (per / 6, h / 6)]); per += L
        c_ = P.mean(0)
        for i in range(len(P)):
            a, b = P[i], P[(i + 1) % len(P)]
            q(roof, (*a, z0 + h), (*b, z0 + h), (*c_, z0 + h), (*c_, z0 + h), [(a[0] / 8, a[1] / 8), (b[0] / 8, b[1] / 8), (c_[0] / 8, c_[1] / 8), (c_[0] / 8, c_[1] / 8)])
        return P
    if 287001171 in G:
        P = G[287001171]; c_ = P.mean(0); drop(c_); z0 = float(height([c_[0]], [c_[1]])[0])
        P = extrude(P, z0, 14, 'brick', 'flat')
        extrude(P.mean(0) + (P - P.mean(0)) * 0.8, z0 + 14, 6, 'blue', 'flat')   # dome_02.jpg: blue-glass upper storey set back on the brick block
        v = P[np.argmin(np.hypot(*(P - (434, 148)).T))]; r = 3.5
        for k in range(16):   # blue entry tower
            a0, a1 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
            A = (v[0] + r * math.cos(a0), v[1] + r * math.sin(a0)); B = (v[0] + r * math.cos(a1), v[1] + r * math.sin(a1))
            q('blue', (*A, z0), (*B, z0), (*B, z0 + 24), (*A, z0 + 24), [(k / 4, 0), ((k + 1) / 4, 0), ((k + 1) / 4, 4), (k / 4, 4)])
        print('landmark annex brick', len(P))
    if 35030128 in G:
        P = G[35030128]; c_ = P.mean(0); drop(c_); z0 = float(height([c_[0]], [c_[1]])[0])
        P = extrude(P, z0, 14, 'hallwall', 'flat')
        lo, hi = P.min(0), P.max(0)
        for k in range(4):    # 4 curved ribs, 3 m wide, corner-to-corner diagonal, rising 6 m at mid-span
            off = (k - 1.5) * 18
            a = np.array([lo[0] + off, lo[1]]); b = np.array([hi[0] + off, hi[1]]); d = (b - a) / np.linalg.norm(b - a); nn = np.array([-d[1], d[0]]) * 1.5
            for j in range(12):
                t0, t1 = j / 12, (j + 1) / 12; p0, p1 = a + (b - a) * t0, a + (b - a) * t1
                z_0, z_1 = z0 + 14 + 6 * math.sin(math.pi * t0), z0 + 14 + 6 * math.sin(math.pi * t1)
                q('flat', (*(p0 - nn), z_0), (*(p0 + nn), z_0), (*(p1 + nn), z_1), (*(p1 - nn), z_1), [(0, t0 * 8), (0.5, t0 * 8), (0.5, t1 * 8), (0, t1 * 8)])
        print('landmark annex hall', len(P))
    M = {'brick': mat_img('acc_brick', os.path.join(HERE, 'tex', 'acc_brick.png'), 0.85),
         'flat': mat_img('acc_station2', os.path.join(HERE, 'tex', 'acc_station.png'), 0.4),
         'hallwall': mat_img('acc_hall_wall2', os.path.join(HERE, 'tex', 'acc_drum.png'), 0.4),
         'blue': mat_img('acc_bluetower', os.path.join(HERE, 'tex', 'acc_bluetower.png'), 0.4)}
    for k, (V, F, U) in O.items():
        o = mk_obj('bg_acc_lm_annex_' + k, V, F, M[k]); set_uv(o.data, [U[i] for f_ in F for i in f_])

_accor_annex()
