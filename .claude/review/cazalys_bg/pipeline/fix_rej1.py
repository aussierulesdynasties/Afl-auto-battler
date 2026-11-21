s = open('scene.py', encoding='utf-8', newline='').read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:60], s.count(a)); s = s.replace(a, b)
# 1 roofs: big halls with solar arrays, other blocks ribbed sheet at 12 m; parapet 0.6 m on blocks
rep("""        top = base + 1.0 + h - rh
        k = len(P); s0 = len(verts)
        for x, y in P: verts.append((x, y, base))
        for x, y in P: verts.append((x, y, top))""",
"""        top = base + 1.0 + h - rh
        par = 0.6 if cls == 'block' else 0.0   # parapet lip round flat roofs, as on the aerial
        k = len(P); s0 = len(verts)
        for x, y in P: verts.append((x, y, base))
        for x, y in P: verts.append((x, y, top + par))""")
rep("            v0, v1 = -1.0 / th, (top - base - 1.0) / th", "            v0, v1 = -1.0 / th, (top + par - base - 1.0) / th")
rep("""        src = b.get('roof_c'); kind = 'tile' if""", """        src = b.get('roof_c'); kind = 'solar' if b.get('solar') else 'shed' if cls == 'block' else 'tile' if""")
rep("""        def ruv_(x, y): return ((x * ct + y * st) / 3.04, (-x * st + y * ct) / 3.04)""",
"""        RT = {'solar': 48.0, 'shed': 12.0}.get(kind, 3.04)
        def ruv_(x, y): return ((x * ct + y * st) / RT, (-x * st + y * ct) / RT)""")
rep("""    RF = {'metal': [[], [], [], []], 'tile': [[], [], [], []]}""", """    RF = {'metal': [[], [], [], []], 'tile': [[], [], [], []], 'shed': [[], [], [], []], 'solar': [[], [], [], []]}""")
rep("""for b in BL:
    P = np.array(b['p']); x, y = P[:, 0], P[:, 1]
    b['a'] = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))""",
"""for b in BL:
    P = np.array(b['p']); x, y = P[:, 0], P[:, 1]
    b['a'] = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
    c_ = P.mean(0)
    if any(math.hypot(c_[0] - sx, c_[1] - sy) < 25 for sx, sy in spec.get('solar_roofs', [])): b['solar'] = 1""")
# 2 paved: dark asphalt concourse, as the aerial
rep("""    m_pave = mat_img('plaza_pavers', _tint(None, 'pavers_paved.png'), 0.9); m_pave.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.3
    PF2 = _drape([np.array(p, float) for k, p in spec.get('paint_poly', []) if k == 'paved'], m_pave, 'bg_paved', 6.0, 0.03)""",
"""    PF2 = _drape([np.array(p, float) for k, p in spec.get('paint_poly', []) if k == 'paved'], m_road, 'bg_paved', TILE, 0.03)""")
rep("            if mat is m_park: _mottle(ob.data, co)", "            if mat in (m_park, m_road): _mottle(ob.data, co)")
# 3 car parks: bay texture along each car park's long side + parked cars; no service ribbons across them
rep("""    m_park = mat_img_vc('park_asphalt', _tint(PAL['parking'], 'road_asphalt_park.png'), 0.92)""",
"""    m_park = mat_img_vc('park_asphalt', os.path.join(HERE, 'tex', 'park_bays.png'), 0.92)
    def _inpoly(poly, px, py):
        ins = np.zeros(len(px), bool); j = len(poly) - 1
        for i in range(len(poly)):
            xi, yi = poly[i]; xj, yj = poly[j]
            ins ^= ((yi > py) != (yj > py)) & (px < (xj - xi) * (py - yi) / ((yj - yi) or 1e-9) + xi); j = i
        return ins
    def _ang(poly):
        E = np.diff(np.vstack([poly, poly[:1]]), axis=0); e = E[np.argmax(np.hypot(E[:, 0], E[:, 1]))]; return math.atan2(e[1], e[0])
    els_ = json.load(open(os.path.join(HERE, 'data', name, 'osm.json'), encoding='utf-8'))['elements']
    PPOL = [np.array([_xy(p) for p in (el.get('geometry') or []) if p]) for el in els_ if el.get('type') == 'way' and el.get('tags', {}).get('amenity') == 'parking' and el.get('tags', {}).get('parking', 'surface') == 'surface' and len(el.get('geometry') or []) > 3]
    PPOL += [np.array(p, float) for k, p in spec.get('paint_poly', []) if k == 'parking']""")
rep("""        if len(P) < 2: continue
        two = hw""", """        if len(P) < 2: continue
        if hw == 'service' and any(_inpoly(pp, P[:, 0], P[:, 1]).mean() > 0.5 for pp in PPOL): continue   # aisles: the bay texture draws them
        two = hw""")
rep("""    def _drape(polys, mat, nm, tile, lift):   # 1 m grid inside each outline; edge cells cut to the true outline
        PV, PF = [], []
        for poly in polys:""", """    def _drape(polys, mat, nm, tile, lift, bays=False):   # 1 m grid inside each outline; edge cells cut to the true outline
        PV, PF = [], []; AN = []
        for poly in polys:
            pv0 = len(PV)""")
rep("""                for tri in T: PF.append(tuple(s0 + t for t in tri))
        if PF:""", """                for tri in T: PF.append(tuple(s0 + t for t in tri))
            AN += [_ang(poly)] * (len(PV) - pv0)
        if PF:""")
rep("""            vi = np.zeros(len(ob.data.loops), int); ob.data.loops.foreach_get('vertex_index', vi); set_uv(ob.data, co[vi, :2] / tile)
            if mat""", """            vi = np.zeros(len(ob.data.loops), int); ob.data.loops.foreach_get('vertex_index', vi)
            if bays:   # u along the car park's long side (12 bays = 31.2 m), v across (two bay rows and an aisle = 34.8 m)
                A = np.array(AN)[vi]; X_, Y_ = co[vi, 0], co[vi, 1]
                set_uv(ob.data, np.stack([(X_ * np.cos(A) + Y_ * np.sin(A)) / 31.2, (-X_ * np.sin(A) + Y_ * np.cos(A)) / 34.8], 1))
            else: set_uv(ob.data, co[vi, :2] / tile)
            if mat""")
rep("""    PF = _drape(polys, m_park, 'bg_carparks', TILE, 0.02)   # 2 cm under the roads (0.04) so they never fight""",
"""    PF = _drape(polys, m_park, 'bg_carparks', TILE, 0.02, bays=True)   # 2 cm under the roads (0.04) so they never fight
    # parked cars in the bays, about half full as on the aerial; none within 3 m of a road edge or 4 m of the outline
    RS = np.vstack([Q for Q, w, _ in roads]); RW_ = np.concatenate([[w] * len(Q) for Q, w, _ in roads])
    CC = [(236, 236, 234)] * 5 + [(196, 198, 200)] * 3 + [(120, 122, 126), (34, 36, 40), (34, 36, 40), (60, 76, 120), (150, 40, 36)]
    CV, CF, CCol = [], [], []; crng = np.random.default_rng(11)
    for poly in polys:
        a = _ang(poly); ca, sa = math.cos(a), math.sin(a)
        R = np.stack([poly[:, 0] * ca + poly[:, 1] * sa, -poly[:, 0] * sa + poly[:, 1] * ca], 1)
        us = np.arange(math.floor(R[:, 0].min() / 2.6) * 2.6, R[:, 0].max(), 2.6)
        vs = [v for v0 in np.arange(math.floor(R[:, 1].min() / 34.8) * 34.8, R[:, 1].max(), 17.4) for v in (v0 + 2.7, v0 + 8.1)]
        GU, GV = np.meshgrid(us, vs); GU, GV = GU.ravel(), GV.ravel()
        X_ = GU * ca - GV * sa; Y_ = GU * sa + GV * ca
        ok = _inpoly(poly, X_, Y_) & (crng.random(len(X_)) < 0.55)
        for dx, dy in ((4, 0), (-4, 0), (0, 4), (0, -4)): ok &= _inpoly(poly, X_ + dx, Y_ + dy)
        for x, y in zip(X_[ok], Y_[ok]):
            d = np.hypot(RS[:, 0] - x, RS[:, 1] - y)
            if (d < RW_ / 2 + 3).any(): continue
            z = float(height(x, y)) + 0.02; col = list(lin(CC[crng.integers(len(CC))])) + [1.0]
            s0 = len(CV)
            for zz, hw, hl in ((z, 0.9, 2.25), (z + 0.75, 0.9, 2.25), (z + 1.45, 0.75, 1.3)):   # body to the shoulder, then the cabin
                for pw, pl in ((-hw, -hl), (hw, -hl), (hw, hl), (-hw, hl)):   # pl along the bay (across the car park's long side), pw across
                    CV.append((x + pw * ca - pl * sa, y + pw * sa + pl * ca, zz))
            for L0, L1 in ((0, 4), (4, 8)):
                for i in range(4): CF.append((s0 + L0 + i, s0 + L0 + (i + 1) % 4, s0 + L1 + (i + 1) % 4, s0 + L1 + i))
            CF.append((s0 + 8, s0 + 9, s0 + 10, s0 + 11))
            CCol += [col] * 36
    if CF:
        ob = mk_obj('bg_cars', CV, CF, mat_vcol('cars', 0.4)); set_corner_col(ob.data, np.array(CCol))
    print('cars', len(CF) // 9)""")
open('scene.py', 'w', encoding='utf-8', newline='').write(s); print('patched')
