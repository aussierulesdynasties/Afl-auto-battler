# Hand-built landmarks, exec'd by scene.py before the generic buildings are built (shares its globals: BL, height, mk_obj,
# set_uv, HERE, spec, np, math, bpy). Each landmark sits on its OSM footprint (traced from the satellite) and copies a named
# reference photo in scratchpad/ref_landmarks (refs.json holds title, author, licence). Textures: tex/lm_*.png (hand-made).
LMS = json.load(open(os.path.join(HERE, 'tex', 'lm_sizes.json')))
def lm_mat(key, rough=0.5, alpha=False, metal=0.0):
    m = bpy.data.materials.new('lm_' + key); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(os.path.join(HERE, 'tex', 'lm_%s.png' % key))
    nt.links.new(t.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if alpha: nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
    return m
BK = {}   # material key -> [verts, faces, uvs]
def bk(key): return BK.setdefault(key, [[], [], []])
def wall_ring(key, P, z0, z1, v_off=0.0):
    """vertical walls round polygon P from z0 to z1; UVs in metres / the texture's tile size (v measured from v_off)."""
    tw, th = LMS['lm_%s.png' % key]; V, F, U = bk(key); per = 0.0; k = len(P)
    for i in range(k):
        a, b = P[i], P[(i + 1) % k]; L = math.hypot(b[0] - a[0], b[1] - a[1]); n = len(V)
        V += [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)]; F.append((n, n + 1, n + 2, n + 3))
        U += [(per / tw, (z0 - v_off) / th), ((per + L) / tw, (z0 - v_off) / th), ((per + L) / tw, (z1 - v_off) / th), (per / tw, (z1 - v_off) / th)]
        per += L
def cap(key, P, z, down=False):
    tw, th = LMS['lm_%s.png' % key] if key != 'roofcap' else (3.04, 3.04); V, F, U = bk(key); n = len(V)
    for x, y in P: V.append((x, y, z)); U.append((x / tw, y / th))
    F.append(tuple(range(n, n + len(P)))[::-1] if down else tuple(range(n, n + len(P))))
def quad(key, p0, u, w, h, z0, flip=False):
    """vertical rectangle: bottom-left p0, along unit u, width w, height h; full texture once."""
    V, F, U = bk(key); n = len(V)
    V += [(p0[0], p0[1], z0), (p0[0] + u[0] * w, p0[1] + u[1] * w, z0), (p0[0] + u[0] * w, p0[1] + u[1] * w, z0 + h), (p0[0], p0[1], z0 + h)]
    U += [(0, 0), (1, 0), (1, 1), (0, 1)]; F.append((n + 3, n + 2, n + 1, n) if flip else (n, n + 1, n + 2, n + 3))
def beam(key, a, b, w):
    """square-section member from point a to b (3D), width w."""
    a, b = np.array(a, float), np.array(b, float); d = b - a; L = np.linalg.norm(d)
    if L < 1e-6: return
    d /= L; up = np.array([0, 0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0, 0])
    s = np.cross(d, up); s /= np.linalg.norm(s); t = np.cross(d, s); h = w / 2
    C = [s * h + t * h, -s * h + t * h, -s * h - t * h, s * h - t * h]
    V, F, U = bk(key); n = len(V)
    for p in (a, b):
        for c in C: V.append(tuple(p + c))
    for i in range(4):
        F.append((n + i, n + (i + 1) % 4, n + 4 + (i + 1) % 4, n + 4 + i))
    for i in range(8): U.append(((i % 4) * 0.25, 0.0 if i < 4 else L / LMS['lm_%s.png' % key][1]))
def scaled(P, f):
    c = np.mean(P, 0); return [tuple(c + (np.array(p) - c) * f) for p in P]
def ccw(P):
    x, y = np.array(P)[:, 0], np.array(P)[:, 1]
    return P if np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)) > 0 else P[::-1]
def find(cx, cy, h=None, r=4.0):
    for i, b in enumerate(BL):
        P = np.array(b['p']); c = P.mean(0)
        if math.hypot(c[0] - cx, c[1] - cy) < r and (h is None or abs(b['h'] - h) < 0.6): return i
    raise SystemExit('landmark footprint not found %s %s %s' % (cx, cy, h))
def gz(P): c = np.mean(P, 0); return float(height(c[0], c[1])) - 1.0

LM = spec.get('landmarks', [])
drop = set()
# ---------- Collins St towers with their crowns (ref: towerref/c120.jpg, c101.jpg, nauru.jpg; heights: Wikipedia infobox roof/spire) ----------
def by_name(n_):
    for i, b in enumerate(BL):
        if n_ in b.get('name', ''): return i
def strip(key, a, u, nrm, w, z0, z1, off=0.15):
    """flat vertical band on a facade: centred at point a along unit u, width w, pushed out by off; texture tiled in metres."""
    tw, th = LMS['lm_%s.png' % key]; V, F, U = bk(key); n = len(V); p = np.array(a) - np.array(u) * w / 2 + np.array(nrm) * off; q = p + np.array(u) * w
    V += [(p[0], p[1], z0), (q[0], q[1], z0), (q[0], q[1], z1), (p[0], p[1], z1)]; F.append((n, n + 1, n + 2, n + 3))
    U += [(0, 0), (w / tw, 0), (w / tw, (z1 - z0) / th), (0, (z1 - z0) / th)]
def faces(P, minlen):
    for k in range(len(P)):
        a, b = np.array(P[k]), np.array(P[(k + 1) % len(P)]); L = np.linalg.norm(b - a)
        if L >= minlen: u = (b - a) / L; yield (a + b) / 2, u, np.array([u[1], -u[0]]), L
i = by_name('120 Collins')
if i is not None:   # 222 m roof; the top steps in twice (photo c120.jpg), mast to 265 m
    drop.add(i); P = ccw([tuple(p) for p in BL[i]['p']]); z = gz(P)
    wall_ring('c120', P, z, z + 200, z); cap('roofcap', P, z + 200)
    P2 = scaled(P, 0.82); wall_ring('c120', P2, z + 200, z + 212, z); cap('roofcap', P2, z + 212)
    P3 = scaled(P, 0.62); wall_ring('c120', P3, z + 212, z + 222, z); cap('roofcap', P3, z + 222)
    c = np.mean(P, 0); beam('white', (c[0], c[1], z + 222), (c[0], c[1], z + 265), 1.4); print('landmark 120 Collins')
i = by_name('101 Collins')
if i is not None:   # granite to 183 m, glazed crown to the 195 m roof, full-height glazed central strip on each long face, spire to 260 m
    drop.add(i); P = ccw([tuple(p) for p in BL[i]['p']]); z = gz(P)
    wall_ring('c101', P, z, z + 183, z); wall_ring('c101_glass', P, z + 183, z + 195, z); cap('roofcap', P, z + 195)
    for m_, u_, n_, L_ in faces(P, 20): strip('c101_glass', m_, u_, n_, 0.2 * L_, z, z + 183)
    c = np.mean(P, 0); beam('white', (c[0], c[1], z + 195), (c[0], c[1], z + 260), 1.0); print('landmark 101 Collins')
i = by_name('Nauru House')
if i is not None:   # finned concrete to 183 m, a dark recessed slot up the middle of each face (photo nauru.jpg), mast to 190 m
    drop.add(i); P = ccw([tuple(p) for p in BL[i]['p']]); z = gz(P)
    wall_ring('nauru', P, z, z + 183, z); cap('roofcap', P, z + 183)
    for m_, u_, n_, L_ in faces(P, 15): strip('slot', m_, u_, n_, 3.0, z, z + 183, 0.05)
    c = np.mean(P, 0); beam('white', (c[0], c[1], z + 183), (c[0], c[1], z + 190), 0.6); print('landmark Nauru House')
# ---------- Australia 108 (ref: a108_diagram.jpg profile; a108_in_2021.jpg, a108_southbank.jpg, Fed Square View 003) ----------
if 'a108' in LM:
    i_t, i_s = find(-1712, -347, 317), find(-1707, -345, 221); drop |= {i_t, i_s}
    T = ccw([tuple(p) for p in BL[i_t]['p']]); S = scaled(ccw([tuple(p) for p in BL[i_s]['p']]), 1.25); z = gz(T)   # photos: the starburst overhangs further than its OSM outline
    # diagram (576 px = 317 m): shaft to 210 m, starburst 210-222 m (its own wider outline), upper body to 269 m, crown at half width to 317 m
    wall_ring('a108_glass', T, z, z + 210, z); wall_ring('gold', S, z + 210, z + 222); cap('gold', S, z + 210, down=True); cap('gold', S, z + 222)
    wall_ring('a108_glass', T, z + 222, z + 269, z); cap('roofcap', T, z + 269)
    C = scaled(T, 0.5); wall_ring('a108_glass', C, z + 269, z + 317, z); cap('roofcap', C, z + 317)
    print('landmark a108 base', round(z, 1))
# ---------- Eureka (ref: Fed Square View 003; eureka.jpg): blue glass with white floor bands, top ten floors gold, red stripe ----------
if 'eureka' in LM:
    parts = [(-1662, -172, 290), (-1662, -174, 298), (-1648, -169, 207), (-1676, -180, 177)]
    for cx, cy, h in parts:
        i = find(cx, cy, h); drop.add(i); P = ccw([tuple(p) for p in BL[i]['p']]); z = gz(P)
        g0 = h - 32.6 if h > 280 else h
        wall_ring('eureka_glass', P, z, z + g0, z)
        if g0 < h: wall_ring('eureka_gold', P, z + g0, z + h, z)
        cap('roofcap', P, z + h)
        if h == 298:   # red stripe on the crown face that looks east (towards the MCG / Fed Square)
            best = max(range(len(P)), key=lambda k: ((P[(k + 1) % len(P)][1] - P[k][1]) * 1 - 0) / (math.hypot(P[(k + 1) % len(P)][0] - P[k][0], P[(k + 1) % len(P)][1] - P[k][1]) + 1e-6) if math.hypot(P[(k + 1) % len(P)][0] - P[k][0], P[(k + 1) % len(P)][1] - P[k][1]) > 6 else -9)
            a, b = np.array(P[best]), np.array(P[(best + 1) % len(P)]); u = (b - a) / np.linalg.norm(b - a); nrm = np.array([u[1], -u[0]])
            p0 = a + u * (np.linalg.norm(b - a) * 0.7) + nrm * 0.15
            V, F, U = bk('red'); n = len(V)
            for zz in (z + h - 56, z + h - 18):
                V += [(p0[0], p0[1], zz), (p0[0] + u[0] * 1.6, p0[1] + u[1] * 1.6, zz)]
            F.append((n, n + 1, n + 3, n + 2)); U += [(0, 0), (1, 0), (0, 1), (1, 1)]
    print('landmark eureka')
# ---------- Rialto (ref: rialto_1.jpg, rialto_2.jpg): two reflective blue towers, south 251 m, north 180 m ----------
if 'rialto' in LM:
    for cx, cy, h in [(-2256, 126, 251), (-2276, 153, 180)]:
        i = find(cx, cy, h); drop.add(i); P = ccw([tuple(p) for p in BL[i]['p']]); z = gz(P)
        wall_ring('rialto_glass', P, z, z + h, z); cap('roofcap', P, z + h)
    print('landmark rialto')
# ---------- Arts Centre spire (ref: arts_spire.jpg): white lattice, 162 m, splayed base with the gold mesh veil ----------
if 'spire' in LM:
    drop.add(find(-1320, -164, 162)); drop.add(find(-1320, -164, 50, r=8))
    cx, cy = -1320.0, -164.0; z = float(height(cx, cy))
    prof = [(0, 30), (10, 22), (21, 12), (35, 7), (55, 5), (110, 2.4), (150, 0.6), (162, 0.05)]   # (height m, leg radius m), measured off the photo
    def R(h): return float(np.interp(h, [p[0] for p in prof], [p[1] for p in prof]))
    NL = 6; zs = list(range(0, 150, 6)) + [150, 156, 162]
    for k in range(NL):
        a = 2 * math.pi * k / NL + 0.3
        pts = [(cx + R(h) * math.cos(a), cy + R(h) * math.sin(a), z + h) for h in zs]
        for p, q in zip(pts, pts[1:]): beam('white', p, q, 0.9 if p[2] - z < 40 else 0.55)
    for h0, h1 in zip(zs, zs[1:]):
        if h0 < 18: continue
        for k in range(NL):
            a0, a1 = 2 * math.pi * k / NL + 0.3, 2 * math.pi * (k + 1) / NL + 0.3
            P0 = (cx + R(h0) * math.cos(a0), cy + R(h0) * math.sin(a0), z + h0); P1 = (cx + R(h0) * math.cos(a1), cy + R(h0) * math.sin(a1), z + h0)
            Q1 = (cx + R(h1) * math.cos(a1), cy + R(h1) * math.sin(a1), z + h1)
            beam('white', P0, P1, 0.3); beam('white', P0, Q1, 0.25)
    beam('white', (cx, cy, z + 158), (cx, cy, z + 168), 0.25)   # mast tip
    # veil: 12-sided cone skirt between the splayed legs (photo: tan mesh from ~8 m to ~26 m)
    V, F, U = bk('veil'); n0 = len(V); NS_ = 24
    for h in (8.0, 26.0):
        r = R(h) + 0.5
        for k in range(NS_):
            a = 2 * math.pi * k / NS_; V.append((cx + r * math.cos(a), cy + r * math.sin(a), z + h)); U.append((k * 2 * math.pi * r / NS_ / 4, h / 4))
    for k in range(NS_): F.append((n0 + k, n0 + (k + 1) % NS_, n0 + NS_ + (k + 1) % NS_, n0 + NS_ + k))
    print('landmark spire')
# ---------- Shrine of Remembrance (ref: shrine.jpg): granite podium, porticos north and south, stepped pyramid roof ----------
if 'shrine' in LM:
    i = find(-879, -1163, 7, r=6); drop.add(i); P = np.array(BL[i]['p'], float); c = P.mean(0); z = float(height(c[0], c[1]))
    ev, evec = np.linalg.eigh(np.cov((P - c).T)); ax = evec[:, 1]; bx = np.array([-ax[1], ax[0]])   # ax = long axis (porticos at its ends)
    def sq(hu, hv): return ccw([tuple(c + ax * su * hu + bx * sv * hv) for su, sv in [(-1, -1), (1, -1), (1, 1), (-1, 1)]])
    plat = sq(21, 16); wall_ring('stone', plat, z - 1, z + 3, z); cap('stone', plat, z + 3)
    core = sq(13, 13); wall_ring('stone', core, z + 3, z + 19, z); cap('stone', core, z + 19)
    up = sq(10.5, 10.5); wall_ring('stone', up, z + 19, z + 23, z); cap('stone', up, z + 23)
    for s in range(12):   # stepped pyramid, 1.15 m steps (ref: roof about 0.7 of its base width tall)
        hw = 9.5 - s * 0.75; zz = z + 23 + s * 1.15; Q = sq(hw, hw); wall_ring("shrine_roof", Q, zz, zz + 1.15, zz); cap("shrine_roof", Q, zz + 1.15)
    beam('stone', tuple(c) + (z + 36.8,), tuple(c) + (z + 39.0,), 0.6)
    for sgn in (-1, 1):   # porticos: 8 columns, entablature, pediment
        f = c + ax * sgn * 16.5
        for k in range(8):
            p = f + bx * (-8.4 + k * 2.4); beam('stone', (p[0], p[1], z + 3), (p[0], p[1], z + 13), 1.1)
        E = ccw([tuple(f + ax * su * 3.0 + bx * sv * 9.4) for su, sv in [(-1, -1), (1, -1), (1, 1), (-1, 1)]])
        wall_ring('stone', E, z + 13, z + 15.5, z); cap('stone', E, z + 15.5); cap('stone', E, z + 13, down=True)
        V, F, U = bk('stone'); n = len(V); o = f + ax * sgn * 3.0
        for pb in (o - bx * 9.4, o + bx * 9.4, o):
            V.append((pb[0], pb[1], z + 15.5 if pb is not o else z + 18.5)); U.append((0, 0))
        V[-1] = (o[0], o[1], z + 18.5); F.append((n, n + 1, n + 2) if sgn > 0 else (n + 1, n, n + 2))
        for a_, b_ in [((o - bx * 9.4), o), (o, (o + bx * 9.4))]:   # pediment roof slopes back to the core
            n = len(V); ha = 15.5 if a_ is not o else 18.5; hb = 15.5 if b_ is not o else 18.5; back = -ax * sgn * 6.0
            V += [(a_[0], a_[1], z + ha), (b_[0], b_[1], z + hb), (b_[0] + back[0], b_[1] + back[1], z + hb), (a_[0] + back[0], a_[1] + back[1], z + ha)]
            U += [(0, 0), (1, 0), (1, 1), (0, 1)]; F.append((n, n + 1, n + 2, n + 3))
    print('landmark shrine axis', np.round(ax, 2))
# ---------- Skipping Girl sign (ref: skipping_1.jpg, skipping_2.jpg): on its building's roof, facing the city ----------
if 'skipping' in LM:
    i = find(2413, 983, 7, r=8); b = BL[i]; P = np.array(b['p'], float); c = np.array([2413.0, 983.0])
    top = float(height(*np.array(b['p']).mean(0))) - 1.0 + 1.0 + b['h']
    nv = -c / np.linalg.norm(c); u = np.array([-nv[1], nv[0]])   # faces the oval; u = viewer's right
    p0 = c - u * 5.0
    for s in (1.0, 9.0):
        q = p0 + u * s; beam('white', (q[0], q[1], top), (q[0], q[1], top + 13.5), 0.35)
    beam('white', (p0[0] + u[0] * 1.0, p0[1] + u[1] * 1.0, top + 1.2), (p0[0] + u[0] * 9.0, p0[1] + u[1] * 9.0, top + 1.2), 0.25)
    quad('vinegar', p0 + nv * 0.2, u, 10.0, 2.5, top + 2.5); quad('green', p0 + nv * 0.05, u, 10.0, 2.5, top + 2.5, flip=True)
    g0 = c - u * 1.5 + nv * 0.6; quad('girl', g0, u, 3.0, 5.0, top + 6.0); quad('girl', g0 - nv * 0.02, u, 3.0, 5.0, top + 6.0, flip=True)
    rc = c + nv * 0.6; rz = top + 8.6; ring = [(rc[0] + u[0] * 2.9 * math.cos(t), rc[1] + u[1] * 2.9 * math.cos(t), rz + 3.4 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 41)]
    for p, q in zip(ring, ring[1:]): beam('white', p, q, 0.12)
    print('landmark skipping girl, top', round(top, 1))

# ---------- Melbourne Park arenas (director 2026-11-20 "Yes, build all four"): OSM footprints, roofs copied from the aerial ----------
if 'arenas' in LM:
    AR = json.load(open(os.path.join(HERE, 'data', spec['name'], 'prep', 'arenas.json')))
    def gzm(P):   # walls start at the lowest ground round the footprint, so no side floats over a slope
        return float(np.min(height(np.array([q[0] for q in P]), np.array([q[1] for q in P])))) - 1.0
    def byname(nm):
        for i, b in enumerate(BL):
            if b.get('name') == nm: return i
        return None
    def dome(key, P, z0, rise, rings, f_top, uvmode='plan'):
        """roof rising from footprint P (at z0) to a smaller copy f_top of it; height follows a quarter sine; plan-mapped UVs."""
        tw, th = LMS['lm_%s.png' % key]; V, F, U = bk(key); k = len(P); c = np.mean(P, 0); n0 = len(V)
        for r in range(rings + 1):
            t = r / rings; f = 1 - (1 - f_top) * t; z = z0 + rise * math.sin(t * math.pi / 2)
            for x, y in P:
                q = c + (np.array((x, y)) - c) * f; V.append((q[0], q[1], z)); U.append((q[0] / tw, q[1] / th))
        for r in range(rings):
            for i in range(k):
                a = n0 + r * k + i; b = n0 + r * k + (i + 1) % k; F.append((a, b, b + k, a + k))
        return [tuple(np.array(V[n0 + rings * k + i][:2])) for i in range(k)], z0 + rise
    # Rod Laver: round ribbed white dome over white walls, glazed centre panel (aerial), 30 m
    i = byname('Rod Laver Arena'); P = ccw(AR['Rod Laver Arena']); z = gzm(P)
    if i is not None: drop.add(i)
    wall_ring('rla_wall', P, z, z + 12.5, z); top, zt = dome('ribwhite', P, z + 12.5, 15.5, 6, 0.55)   # glazed facade 12.5 m (photo 020); roof rise to 28 m unmeasured
    cap('ribwhite', scaled(top, 0.98), zt + 0.3); wall_ring('ribwhite', scaled(top, 0.98), zt - 0.5, zt + 0.3)
    c = np.mean(P, 0)
    cP = np.mean(P, 0); Pr = np.array(P) - cP; ax_, ay_ = np.abs(Pr[:, 0]).max(), np.abs(Pr[:, 1]).max()
    def dz(x_, y_):   # dome surface height at (x, y): same quarter-sine as dome(), radial fraction from the footprint's half-axes
        r_ = math.hypot((x_ - cP[0]) / ax_, (y_ - cP[1]) / ay_); t_ = min(1.0, max(0.0, (1 - r_) / 0.45)); return z + 12.5 + 15.5 * math.sin(t_ * math.pi / 2) + 1.0
    def hug(a2, b2, w_):
        pts = [np.array(a2) + (np.array(b2) - np.array(a2)) * s_ for s_ in np.linspace(0, 1, 11)]
        for p_, q_ in zip(pts, pts[1:]): beam('white', (p_[0], p_[1], dz(*p_)), (q_[0], q_[1], dz(*q_)), w_)
    for yb in (-146, -161, -176, -190, -205):   # opening-roof frame (aerial): 5 long E-W girders, 104 m, N-S ribs every 10.4 m, hugging the roof
        hug((-474, yb), (-370, yb), 0.9)
    for xb in np.linspace(-474, -370, 11): hug((xb, -146), (xb, -205), 0.5)
    print('landmark rod laver base', round(z, 1))
    # Margaret Court (OSM outline = the copper long-roof hall west of Rod Laver on the aerial): copper walls and roof, 16 m
    i = byname('Margaret Court Arena'); P = ccw(AR['Margaret Court Arena']); z = gzm(P)
    if i is not None: drop.add(i)
    wall_ring('mca_wall', P, z, z + 12, z); cap('copper', P, z + 12)   # glazed + diamond panels to a 12 m eave (photo 124)
    # folded-plate brown roof (aerial: lit/shaded stripe pairs, 8.75 m pitch, ridges ~15 deg west of north; photo 124 eave 12 m)
    def _inside(q, P=P):
        c_ = False; k_ = len(P)
        for i_ in range(k_):
            (x1_, y1_), (x2_, y2_) = P[i_], P[(i_ + 1) % k_]
            if (y1_ > q[1]) != (y2_ > q[1]) and q[0] < x1_ + (q[1] - y1_) * (x2_ - x1_) / (y2_ - y1_): c_ = not c_
        return c_
    d_ = np.array((-0.253, -0.967)); n_ = np.array((0.967, -0.253)); Pa = np.array(P)
    nn = Pa @ n_; dd = Pa @ d_; tw, th = LMS['lm_copper.png']; V, F, U = bk('copper')
    for s0 in np.arange(nn.min(), nn.max(), 8.75):
        s1_ = s0 + 8.75; ts = np.arange(dd.min(), dd.max() + 1, 1.0)
        ins = [_inside(n_ * (s0 + 0.6) + d_ * t) and _inside(n_ * (s1_ - 0.6) + d_ * t) for t in ts]
        runs = []; st = None
        for t, f in zip(ts, ins):
            if f and st is None: st = t
            if not f and st is not None: runs.append((st, t - 1)); st = None
        if st is not None: runs.append((st, ts[-1]))
        for a_, b_ in runs:
            if b_ - a_ < 4: continue
            sm = s0 + 4.375; pts6 = [(n_ * s0 + d_ * a_, z + 12), (n_ * sm + d_ * a_, z + 15), (n_ * s1_ + d_ * a_, z + 12),
                                    (n_ * s0 + d_ * b_, z + 12), (n_ * sm + d_ * b_, z + 15), (n_ * s1_ + d_ * b_, z + 12)]   # folded plate: ridge mid-bay, 3 m rise
            k0 = len(V)
            for q, zq in pts6: V.append((q[0], q[1], zq)); U.append((q[0] / tw, q[1] / th))
            F += [(k0, k0 + 3, k0 + 4, k0 + 1), (k0 + 1, k0 + 4, k0 + 5, k0 + 2), (k0, k0 + 1, k0 + 2), (k0 + 5, k0 + 4, k0 + 3)]
    print('landmark margaret court base', round(z, 1))
    # John Cain: traced on sat19 (0.25 m) in the arena's own frame, turned 5 deg clockwise from grid north about (-130, -305): u east, v north (out/mcg/qa/r5.png)
    # sat19 is not straight down: west and south wall faces show (2.0 m on the 12 m west wing, 2.5 m on the 15 m SW drum), so a roof at height h appears
    # 0.167 h north-east (u+, v+) of its footprint. Outlines below are the traced ROOF edges; each footprint is moved back by 0.167 h.
    i = byname('John Cain Arena'); P = ccw(AR['John Cain Arena']); z = gzm(P)
    if i is not None: drop.add(i)
    _c, _s, KL = math.cos(math.radians(5)), math.sin(math.radians(5)), 0.167
    def L(u_, v_, h_=0.0): return (-130 + (u_ - KL * h_) * _c + (v_ - KL * h_) * _s, -305 - (u_ - KL * h_) * _s + (v_ - KL * h_) * _c)
    def rect(u0_, v0_, u1_, v1_): return [(u0_, v0_), (u1_, v0_), (u1_, v1_), (u0_, v1_)]
    def quad(cu, cv, ru, rv, a0, a1, extra): return [(cu + ru * math.cos(t), cv + rv * math.sin(t)) for t in np.linspace(math.radians(a0), math.radians(a1), 10)] + extra
    eo = [(50.6, 30), (52, 30), (55, 27), (61, 21), (63, 10), (63, -38), (60, -46), (55, -52), (50.6, -55)]
    for R_, h_ in ((rect(-37.5, -28.75, 34.75, 35), 18), (rect(-66, -28, -37.5, 31), 12), (rect(34.75, -30.6, 50.6, 30), 16), (eo, 12),
                   (rect(-29, 35, 29, 55), 16), (rect(-26.5, 55, 26, 78), 10),
                   (quad(-34.4, 35, 17, 21, 90, 180, [(-34.4, 35)]), 15), (quad(34.75, 37, 15.25, 16.75, 0, 90, [(34.75, 30.6), (50, 30.6)]), 15),
                   (quad(-38.75, -30, 17, 20, 180, 270, [(-38.75, -28), (-55.75, -28)]), 15),
                   (rect(-38, -59, 30.6, -28.75), 15), (rect(-37, -82.5, 20, -59), 12)):   # heights: photos MCG OIC + Melbourne Park 011 (scaled off the 18 m parapet)
        P_ = ccw([L(u_, v_, h_) for u_, v_ in R_]); wall_ring('jca_wall', P_, z, z + h_, z); cap('ribwhite', P_, z + h_)
    D_ = ccw([L(u_, v_, 18) for u_, v_ in quad(30, -33, 16, 21, 270, 360, [(30, -33)])])   # SE signage drum facing Olympic Blvd (photo 011): glazed body to 14.5 m, grey crown with JOHN CAIN ARENA to 18 m
    # photo 2MCGG0C: ground storey set back behind round columns (to 5 m), silver panel band with a window strip to 14.5 m, grey sign crown to 18 m
    Di_ = ccw([L(u_, v_, 18) for u_, v_ in quad(30, -33, 13.5, 18.5, 270, 360, [(30, -33)])])
    wall_ring('glazed', Di_, z, z + 5, z); wall_ring('jca_wall', D_, z + 5, z + 14.5, z + 5); cap('ribwhite', D_, z + 5, down=True)
    wall_ring('jca_sign', D_, z + 14.5, z + 18, z + 14.5); cap('ribwhite', D_, z + 18)
    for t_ in np.linspace(math.radians(275), math.radians(355), 7):
        C_ = L(30 + 15 * math.cos(t_), -33 + 20 * math.sin(t_), 18); beam('white', (*C_, z), (*C_, z + 5), 0.7)
    wall_ring('jca_signq', ccw([L(u_, v_, 12) for u_, v_ in eo]), z + 9, z + 12.5, z + 9)   # east wing crown with sign facing the MCG (photo MCG OIC)
    for (ua, va), (ub, vb) in (((-31, 68), (-36.5, -68)), ((32.5, 68), (26.5, -68))):   # retractable-roof track girders, 19.5 m, ~3 deg off the hall axis on sat19
        A_, B_ = L(ua, va, 19.5), L(ub, vb, 19.5)
        beam('white', (*A_, z + 19.5), (*B_, z + 19.5), 1.2); beam('white', (*A_, z + 18), (*B_, z + 18), 0.6)
        for (ue, ve) in ((ua, va), (ub, vb)):   # photo 2MCGG0C: each end stands on a white lattice A-frame, legs splayed 8 m along the facade, ties and X-braces
            T_ = L(ue, ve, 19.5); F1, F2 = L(ue - 4, ve, 0), L(ue + 4, ve, 0)
            for F_ in (F1, F2): beam('white', (*F_, z), (*T_, z + 19.5), 0.7)
            for k3 in range(4):
                f0, f1 = k3 / 4, (k3 + 1) / 4
                P0 = [(F1[i] + (T_[i] - F1[i]) * f0, F2[i] + (T_[i] - F2[i]) * f0) for i in (0, 1)]; P1 = [(F1[i] + (T_[i] - F1[i]) * f1, F2[i] + (T_[i] - F2[i]) * f1) for i in (0, 1)]
                a0 = (P0[0][0], P0[1][0], z + 19.5 * f0); b0 = (P0[0][1], P0[1][1], z + 19.5 * f0); a1 = (P1[0][0], P1[1][0], z + 19.5 * f1); b1 = (P1[0][1], P1[1][1], z + 19.5 * f1)
                beam('white', a1, b1, 0.35); beam('white', a0, b1, 0.3); beam('white', b0, a1, 0.3)
    for vc in (20, -11.25):   # two E-W arched trusses, 27.5 m bands, X-braced in 5 bays (sat19)
        us = np.linspace(-34.4, 33, 11); ht_ = [19 + 5 * math.cos(u_ / 34 * math.pi / 2) for u_ in us]
        Q = lambda k2, sd: (*L(us[k2], vc + sd, ht_[k2]), z + ht_[k2])
        for side in (-13.75, 13.75):
            for k2 in range(10): beam('white', Q(k2, side), Q(k2 + 1, side), 0.6)
        for k2 in range(0, 10, 2):
            beam('white', Q(k2, -13.75), Q(k2 + 2, 13.75), 0.4); beam('white', Q(k2, 13.75), Q(k2 + 2, -13.75), 0.4)
        for k2 in range(0, 11, 2): beam('white', Q(k2, -13.75), Q(k2, 13.75), 0.4)
    print('landmark john cain base', round(z, 1))
    # AAMI Park: ring of white geodesic bubbles round a rectangular pitch (aerial: 6 lobes per long side, 4 per end), 30 m
    P = ccw(AR['AAMI Park']); z = gz(P); c = np.mean(P, 0)
    k = len(P)
    ang = np.arctan2(np.array(P)[:, 1] - c[1], np.array(P)[:, 0] - c[0])
    per = np.concatenate([[0], np.cumsum([math.hypot(P[(j + 1) % k][0] - P[j][0], P[(j + 1) % k][1] - P[j][1]) for j in range(k)])]); L = per[-1]
    NL = 20; tw, th = LMS['lm_bubble.png']; V, F, U = bk('bubble'); n0 = len(V); S = 16
    inner = scaled(P, 0.6)
    for s_ in range(S + 1):
        t = s_ / S
        for j in range(k):
            lob = 0.5 - 0.5 * math.cos(2 * math.pi * NL * per[j] / L)     # 0 at the valleys between bubbles, 1 at each crown
            o = np.array(P[j]); q = o + (np.array(inner[j]) - o) * t
            zz = z + 6 + (14 + 10 * math.sqrt(lob)) * math.sin(math.pi * t) ** 0.5
            q = q + (o - c) / np.linalg.norm(o - c) * 4 * lob * math.sin(math.pi * t)   # bubbles bulge outward
            V.append((q[0], q[1], zz)); U.append((per[j] / tw, t * 40 / th))
    for s_ in range(S):
        for j in range(k):
            a = n0 + s_ * k + j; b = n0 + s_ * k + (j + 1) % k; F.append((a, b, b + k, a + k))
    wall_ring('arena_wall', P, z, z + 6, z)
    T1 = scaled(P, 0.6); T2 = scaled(P, 0.48)    # empty seat bowl inside the shell, down to the pitch
    V, F, U = bk('tiers'); n0 = len(V); tw, th = LMS['lm_tiers.png']
    for j in range(k):
        V += [(T1[j][0], T1[j][1], z + 16), (T2[j][0], T2[j][1], z + 1)]; U += [(per[j] / tw, 18 / th), (per[j] / tw, 0)]
    for j in range(k):
        a, b = n0 + 2 * j, n0 + 2 * ((j + 1) % k); F.append((a + 1, b + 1, b, a))
    # pitch: 136 x 88 m rectangle (real dimensions incl. run-off) aligned with the shell's long axis
    Pa = np.array(P) - c; ev = np.linalg.eigh(Pa.T @ Pa)[1][:, 1]; ex = np.array([-ev[1], ev[0]])
    R = [tuple(c + ev * su * 68 + ex * sv * 44) for su, sv in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
    cap('pitch', ccw(R), z + 1.05)
    print('landmark aami park base', round(z, 1))

# build: one object per material; drop the generic boxes the landmarks replace
if BK:
    MAT = {'a108_glass': lm_mat('a108_glass', 0.15), 'gold': lm_mat('gold', 0.35, metal=0.6), 'eureka_glass': lm_mat('eureka_glass', 0.15),
           'eureka_gold': lm_mat('eureka_gold', 0.2, metal=0.5), 'rialto_glass': lm_mat('rialto_glass', 0.12), 'stone': lm_mat('stone', 0.85),
           'shrine_roof': lm_mat('shrine_roof', 0.8), 'white': lm_mat('white', 0.5), 'veil': lm_mat('veil', 0.6, alpha=True),
           'vinegar': lm_mat('vinegar', 0.5), 'girl': lm_mat('girl', 0.5, alpha=True), 'arena_wall': lm_mat('arena_wall', 0.6), 'copper': lm_mat('copper', 0.7, metal=0.05), 'ribwhite': lm_mat('ribwhite', 0.5), 'jca_wall': lm_mat('jca_wall', 0.5), 'rla_wall': lm_mat('rla_wall', 0.2), 'mca_wall': lm_mat('mca_wall', 0.3), 'jca_sign': lm_mat('jca_sign', 0.5), 'jca_signq': lm_mat('jca_signq', 0.5), 'glazed': lm_mat('glazed', 0.15), 'bubble': lm_mat('bubble', 0.4), 'tiers': lm_mat('tiers', 0.8), 'pitch': lm_mat('pitch', 0.9)}
    rc_ = mat_img('lm_roofcap', os.path.join(HERE, 'tex', 'roof_metal.png'), 0.6); MAT['roofcap'] = rc_
    red = bpy.data.materials.new('lm_red'); red.use_nodes = True; red.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.55, 0.03, 0.03, 1); MAT['red'] = red
    grn = bpy.data.materials.new('lm_green'); grn.use_nodes = True; grn.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.03, 0.22, 0.06, 1); MAT['green'] = grn
    MAT.update({k: lm_mat(k, r) for k, r in (('c120', 0.6), ('c101', 0.4), ('c101_glass', 0.12), ('nauru', 0.6), ('slot', 0.9)) if k not in MAT})
    for key, (V, F, U) in BK.items():
        ob = mk_obj('bg_lm_' + key, V, F, MAT[key]); set_uv(ob.data, [U[i] for f_ in F for i in f_])
        if key in ('bubble', 'ribwhite', 'copper'): ob.data.shade_smooth()
    BL[:] = [b for i, b in enumerate(BL) if i not in drop]
    print('landmarks built; generic boxes dropped', len(drop))
