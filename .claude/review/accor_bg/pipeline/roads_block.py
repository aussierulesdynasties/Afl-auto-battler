# ---------- roads and car parks: asphalt surfaces (road_asphalt.png, 512 px = 7.2 m) and white lines ----------
if spec.get('road_mesh'):
    from mathutils.geometry import tessellate_polygon
    from PIL import Image as _PI
    lat0, lon0 = spec['lat'], spec['lon']; KX = 111320 * math.cos(math.radians(lat0)); KY = 110540
    def _xy(p): return ((p['lon'] - lon0) * KX, (p['lat'] - lat0) * KY)
    _FP = np.array(json.load(open(os.path.join(D, 'footprint.json'))))
    def _outside(Q, pad=1.0):   # True where a point is clear of the ground model's footprint
        b = ((np.degrees(np.arctan2(Q[:, 1], Q[:, 0])) % 360) // (360 / len(_FP))).astype(int) % len(_FP)
        return np.hypot(Q[:, 0], Q[:, 1]) > _FP[b] + pad
    def _dens(P, step):
        Q = [P[0]]
        for p2 in P[1:]:
            k = max(1, int(math.ceil(np.hypot(*(p2 - Q[-1])) / step))); a = Q[-1]
            for j in range(1, k + 1): Q.append(a + (p2 - a) * (j / k))
        return np.array(Q)
    # one texture: the grey asphalt multiplier x the scene's road colour, every value <= 1
    ra = np.asarray(_PI.open(os.path.join(HERE, 'tex', 'road_asphalt.png')).convert('RGB'), np.float32)
    def _tint(rgb, fn):
        t = np.clip(ra / ra.mean() * np.array(rgb, np.float32), 0, 255).astype(np.uint8)
        p = os.path.join(HERE, 'tex', fn); _PI.fromarray(t).save(p); return p
    TILE = 7.2
    m_road = mat_img('road_asphalt', _tint(PAL['road'], 'road_asphalt_road.png'), 0.92)
    m_park = mat_img('park_asphalt', _tint(PAL['parking'], 'road_asphalt_park.png'), 0.92)
    m_line = mat_vcol('road_lines', 0.7); LC = list(lin((236, 236, 230))) + [1.0]
    WDR = {'motorway': 22, 'trunk': 18, 'primary': 16, 'secondary': 13, 'tertiary': 11, 'residential': 8, 'unclassified': 8, 'service': 5}
    TWO = ('secondary', 'tertiary', 'residential', 'unclassified')
    els = json.load(open(os.path.join(HERE, 'data', name, 'osm.json'), encoding='utf-8'))['elements']
    roads = []
    for el in els:
        t = el.get('tags', {}); hw = t.get('highway')
        if el.get('type') != 'way' or hw not in WDR: continue
        if t.get('tunnel', 'no') != 'no' or (t.get('bridge') and t.get('bridge') != 'no') or t.get('area') == 'yes': continue
        P = np.array([_xy(p) for p in (el.get('geometry') or []) if p], float)
        if len(P) < 2 or np.abs(P).max() > NE - 5: P = P[(np.abs(P) < NE - 5).all(1)] if len(P) else P
        if len(P) < 2: continue
        two = hw in TWO and t.get('oneway', 'no') == 'no' and t.get('lanes', '2') == '2'
        roads.append((_dens(P, 3.0), WDR[hw], two))
    # coverage hash: every road centreline sample, so lines stop where another road crosses (junctions)
    CELL = 12.0; H_ = {}
    for ri, (Q, w, _) in enumerate(roads):
        T = np.gradient(Q, axis=0); T = T / np.maximum(np.hypot(T[:, 0], T[:, 1]), 1e-6)[:, None]
        for q, tq in zip(Q, T): H_.setdefault((int(q[0] // CELL), int(q[1] // CELL)), []).append((ri, q[0], q[1], w, tq[0], tq[1]))
    def _clear(ri, x, y, tx, ty):   # a crossing road (more than 30 deg off this one's heading) blanks the lines near it
        cx, cy = int(x // CELL), int(y // CELL)
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for rj, qx, qy, w, ux, uy in H_.get((cx + i, cy + j), ()):
                    if rj != ri and abs(tx * ux + ty * uy) < 0.866 and math.hypot(x - qx, y - qy) < w / 2 + 1.5: return False
        return True
    def _ribbon(Q, off, w, lift, V, F, UV=None):
        n = len(Q); N_ = []
        for i in range(n):
            d_ = Q[min(i + 1, n - 1)] - Q[max(i - 1, 0)]; L = max(np.hypot(*d_), 1e-6); N_.append(np.array([-d_[1], d_[0]]) / L)
        N_ = np.array(N_); C = Q + N_ * off; A = C + N_ * w / 2; B = C - N_ * w / 2
        za = height(A[:, 0], A[:, 1]) + lift; zb = height(B[:, 0], B[:, 1]) + lift; s0 = len(V)
        for i in range(n):
            V.append((A[i, 0], A[i, 1], float(za[i]))); V.append((B[i, 0], B[i, 1], float(zb[i])))
        for i in range(n - 1):
            F.append((s0 + 2 * i, s0 + 2 * i + 1, s0 + 2 * i + 3, s0 + 2 * i + 2))
    def _runs(ok):
        return [r for r in np.split(np.arange(len(ok)), np.where(np.diff(ok.astype(int)) != 0)[0] + 1) if ok[r[0]] and len(r) > 1]
    RV, RF_, LV, LF = [], [], [], []
    for ri, (Q, w, two) in enumerate(roads):
        ok = _outside(Q)
        for r in _runs(ok): _ribbon(Q[r], 0, w, 0.08, RV, RF_)
        if not two: continue
        Ql = _dens(Q, 0.5); Tl = np.gradient(Ql, axis=0); Tl = Tl / np.maximum(np.hypot(Tl[:, 0], Tl[:, 1]), 1e-6)[:, None]
        okl = _outside(Ql, 2.0) & np.array([_clear(ri, x, y, a, b) for (x, y), (a, b) in zip(Ql, Tl)])
        for sd in (-1, 1):   # edge lines 0.1 m wide, 0.3 m inside each edge
            for r in _runs(okl): _ribbon(Ql[r], sd * (w / 2 - 0.35), 0.10, 0.10, LV, LF)
        s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(Ql, axis=0).T))])   # centre: 3 m dash, 9 m gap
        for r in _runs(okl & ((s % 12.0) < 3.0)): _ribbon(Ql[r], 0, 0.10, 0.10, LV, LF)
    if RF_:
        ob = mk_obj('bg_roads', RV, RF_, m_road); co = np.array(RV)
        vi = np.zeros(len(ob.data.loops), int); ob.data.loops.foreach_get('vertex_index', vi); set_uv(ob.data, co[vi, :2] / TILE)
    if LF:
        ob = mk_obj('bg_road_lines', LV, LF, m_line); set_corner_col(ob.data, np.tile(LC, (len(LF) * 4, 1)))
    # car parks: OSM amenity=parking plus the spec's traced parking, a 1 m grid inside each outline draped on the terrain
    polys = []
    for el in els:
        t = el.get('tags', {})
        if el.get('type') == 'way' and t.get('amenity') == 'parking' and t.get('parking', 'surface') == 'surface':
            g = [_xy(p) for p in (el.get('geometry') or []) if p]
            if len(g) > 3: polys.append(np.array(g))
    polys += [np.array(p, float) for k, p in spec.get('paint_poly', []) if k == 'parking']
    PV, PF = [], []
    for poly in polys:
        x0, y0 = np.floor(poly.min(0)); x1, y1 = np.ceil(poly.max(0))
        xs = np.arange(x0, x1 + 1); ys = np.arange(y0, y1 + 1); GX, GY = np.meshgrid(xs, ys)
        px, py = GX.ravel(), GY.ravel(); ins = np.zeros(len(px), bool); j = len(poly) - 1
        for i in range(len(poly)):   # even-odd ray test
            xi, yi = poly[i]; xj, yj = poly[j]
            ins ^= ((yi > py) != (yj > py)) & (px < (xj - xi) * (py - yi) / ((yj - yi) or 1e-9) + xi); j = i
        ins &= _outside(np.stack([px, py], 1), 1.0); ins = ins.reshape(GX.shape)
        q = ins[:-1, :-1] & ins[1:, :-1] & ins[:-1, 1:] & ins[1:, 1:]
        if not q.any(): continue
        Z = height(GX, GY) + 0.05; idx = -np.ones(GX.shape, int); used = np.zeros(GX.shape, bool)
        used[:-1, :-1] |= q; used[1:, :-1] |= q; used[:-1, 1:] |= q; used[1:, 1:] |= q
        s0 = len(PV); idx[used] = s0 + np.arange(used.sum())
        PV.extend(zip(GX[used], GY[used], Z[used]))
        jj, ii = np.nonzero(q)
        PF.extend(zip(idx[jj, ii], idx[jj, ii + 1], idx[jj + 1, ii + 1], idx[jj + 1, ii]))
    if PF:
        ob = mk_obj('bg_carparks', [tuple(map(float, v)) for v in PV], [tuple(map(int, f)) for f in PF], m_park); co = np.array(PV, float)
        vi = np.zeros(len(ob.data.loops), int); ob.data.loops.foreach_get('vertex_index', vi); set_uv(ob.data, co[vi, :2] / TILE)
    print('roads', len(roads), 'road faces', len(RF_), 'line faces', len(LF), 'car park faces', len(PF))

