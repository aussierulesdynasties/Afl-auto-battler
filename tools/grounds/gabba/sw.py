# ---- south-west corner buildings (photo g49 x 262-700, y 725-1000): measured on pixel grids, unprojected through camB
PT = mat('paletile', W1, 0.8, 'paletile.png'); GF = mat('gatefront', W1, 0.8, 'gatefront.png')
NW = mat('navywall', W1, 0.7, 'navywall.png'); N7F = mat('n7front', W1, 0.7, 'n7front.png'); N7S = mat('n7strip', W1, 0.7, 'n7strip.png'); N7R = mat('n7roof', W1, 0.8, 'n7roof.png')
WR = mat('whiterender', W1, 0.8, 'whiterender.png'); DD = mat('deckdots', W1, 0.9, 'deckdots.png'); SK = mat('skylight', W1, 0.4, 'skylight.png')
GB = mat('glassblock', W1, 0.3, 'glassblock.png'); RG = mat('roundglass', W1, 0.2, 'roundglass.png'); DG = mat('darkglass', W1, 0.2, 'darkglass.png')
BOX.update({GB: 4.0, DG: 4.0, PT: 4.8, NW: 9.0, WR: 9.0, DD: 6.0, GF: 46.0, N7F: 8.5, N7S: 9.0, N7R: 10.0, SK: 12.0})
def _ccw(p):
    s = sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))
    return p if s > 0 else p[::-1]
def _ang(p): return math.atan2(p[1] - cy, p[0] - cx)
def _fac(a, d=0.5): return P(a, rF(a) - d, 0)[:2]
def _out(p, d=0.5):   # keep a roof point outside the facade line
    a = _ang(p); r = math.hypot(p[0] - cx, p[1] - cy); r = max(r, rF(a) - d); return (cx + r * math.cos(a), cy + r * math.sin(a))
def _arc(a0, a1, n=12, d=0.5): return [_fac(a0 + (a1 - a0) * k / n, d) for k in range(n + 1)]
def _skin(p0, p1, z00, z01, z10, z11, m, u0, u1, U, V, off=0.03):
    # one outward face from p0 to p1; z0x bottoms, z1x tops; uv = (u / U, z / V)
    nx, ny = p1[1] - p0[1], -(p1[0] - p0[0]); L = math.hypot(nx, ny); nx, ny = nx / L, ny / L
    mx, my = (p0[0] + p1[0]) / 2 - cx, (p0[1] + p1[1]) / 2 - cy
    if nx * mx + ny * my < 0: nx, ny = -nx, -ny
    q0 = (p0[0] + nx * off, p0[1] + ny * off); q1 = (p1[0] + nx * off, p1[1] + ny * off)
    vs = [(*q0, z00), (*q1, z01), (*q1, z11), (*q0, z10)]; uvs = [(u0 / U, z00 / V), (u1 / U, z01 / V), (u1 / U, z11 / V), (u0 / U, z10 / V)]
    e = (q1[0] - q0[0], q1[1] - q0[1]); n_ = (e[1], -e[0])          # (edge x up) for this vertex order
    if n_[0] * nx + n_[1] * ny < 0: vs, uvs = vs[::-1], uvs[::-1]
    face(vs, m, uvs)
def _slab(q, hs, m, capm, uw, vm, skip=()):   # 4-sided block with a sloped top (heights per corner); skip: a face's two corners
    vb = [bm.verts.new((x, y, 0)) for x, y in q]; vt = [bm.verts.new((x, y, h)) for (x, y), h in zip(q, hs)]
    L = 0.0
    for k in range(4):
        j = (k + 1) % 4; s = math.dist(q[k], q[j])
        if {q[k], q[j]} == set(skip): L += s; continue
        f = bm.faces.new((vb[k], vb[j], vt[j], vt[k])); f.material_index = m
        for l, t in zip(f.loops, [(L / uw, 0), ((L + s) / uw, 0), ((L + s) / uw, hs[j] / vm), (L / uw, hs[k] / vm)]): l[uv].uv = t
        L += s
    f = bm.faces.new(vt); f.material_index = capm; f = bm.faces.new(vb[::-1]); f.material_index = capm

# ---- NE corner (v6): plan from the top-down sources only (Esri 11135 + current capture, lean-corrected; OSM part 483353591),
# heights from photo g49. Satellite lean: tall points appear shifted (-0.117, -0.117) m per m of height in 11135.
def _pf(deg, off=1.0): a = math.radians(deg); return P(a, rF(a) + off, 0)[:2]
# pale gate block: face 1 m proud of the facade, under the roof overhang, palms on the footpath in front (sat palms at y 84-88).
# corners from photo columns 477/567/600/687, measured from the NE light tower (photo col 460, angle 40.4 deg) at 8.6 px per degree
_F = [_pf(42.4), _pf(52.8), _pf(56.7), _pf(66.8)]
# heights: photo (477,927)-(479,995) 23.6 m, (567,925) 24.7 m -> G1 24 m; G2 21 m; G3 slopes 17.3 m -> 13.4 m
_Bk = [_fac(_ang(p), 0.3) for p in _F]
_L = [math.dist(_F[i], _F[i + 1]) for i in range(3)]; _U = [0.0, _L[0], _L[0] + _L[1], sum(_L)]
prism(_ccw([_F[0], _F[1], _Bk[1], _Bk[0]]), 0, 24.0, PT, True, 4, 4.8, 4.8, DK)
prism(_ccw([_F[1], _F[2], _Bk[2], _Bk[1]]), 0, 21.0, PT, True, 4, 4.8, 4.8, DK)
_q = _ccw([_F[2], _F[3], _Bk[3], _Bk[2]]); _h = {_F[2]: 17.3, _F[3]: 13.4, _Bk[3]: 13.4, _Bk[2]: 17.3}
_slab(_q, [_h[p] for p in _q], PT, DK, 4.8, 4.8, skip={_F[2], _F[3]})   # its front is built round the gate opening below
_skin(_F[0], _F[1], 0, 0, 24.0, 24.0, GF, _U[0], _U[1], 46.0, 24.0)
_skin(_F[1], _F[2], 0, 0, 21.0, 21.0, GF, _U[1], _U[2], 46.0, 24.0)
# G3 front: the pale tiles round the gate's dark opening (u 34.6-43.3, 12 m tall, photo x 640-680), which is a real
# recess 1.1 m deep with its jambs, soffit and dark back wall; the tiled face (skin) and the block's own front are both
# built round it.
_UO0, _UO1, _ZO = 34.6, 43.3, 12.0
def _gp(u, d=0.0, z=0.0):   # a point on the gate front at u (metres along _U), d out from the _F line
    k = 0 if u <= _U[1] else 1 if u <= _U[2] else 2
    t = (u - _U[k]) / (_U[k + 1] - _U[k]); a_, b_ = _F[k], _F[k + 1]
    x_, y_ = a_[0] + (b_[0] - a_[0]) * t, a_[1] + (b_[1] - a_[1]) * t
    ex, ey = (b_[0] - a_[0]) / _L[k], (b_[1] - a_[1]) / _L[k]; nx, ny = ey, -ex
    if nx * (x_ - cx) + ny * (y_ - cy) < 0: nx, ny = -nx, -ny
    return (x_ + nx * d, y_ + ny * d, z)
_g3top = lambda u: 17.3 + (13.4 - 17.3) * (u - _U[2]) / (_U[3] - _U[2])
_Po0, _Po1 = (_gp(_UO0)[0], _gp(_UO0)[1]), (_gp(_UO1)[0], _gp(_UO1)[1])
for (a_, b_, ua, ub, za, zb) in ((_F[2], _Po0, _U[2], _UO0, 0.0, 0.0), (_Po1, _F[3], _UO1, _U[3], 0.0, 0.0), (_Po0, _Po1, _UO0, _UO1, _ZO, _ZO)):
    _skin(a_, b_, za, zb, _g3top(ua), _g3top(ub), GF, ua, ub, 46.0, 24.0)
    _skin(a_, b_, za, zb, _g3top(ua), _g3top(ub), PT, ua, ub, 4.8, 4.8, 0.0)       # the block's own front behind the skin
_RD_ = 1.1
face([_gp(_UO0, 0.03, 0), _gp(_UO0, -_RD_, 0), _gp(_UO0, -_RD_, _ZO), _gp(_UO0, 0.03, _ZO)], PT)        # jambs
face([_gp(_UO1, -_RD_, 0), _gp(_UO1, 0.03, 0), _gp(_UO1, 0.03, _ZO), _gp(_UO1, -_RD_, _ZO)], PT)
face([_gp(_UO0, 0.03, _ZO), _gp(_UO0, -_RD_, _ZO), _gp(_UO1, -_RD_, _ZO), _gp(_UO1, 0.03, _ZO)], PT)    # soffit
face([_gp(_UO0, -_RD_, 0), _gp(_UO1, -_RD_, 0), _gp(_UO1, -_RD_, _ZO), _gp(_UO0, -_RD_, _ZO)], DG)      # dark back: glazed doors
def _gbox(u0, u1, d0, d1, z0, z1, m):   # a box on the gate front (u along it, d out from the _F line)
    A_, B_, C_, D_ = _gp(u0, d1, z0), _gp(u1, d1, z0), _gp(u1, d1, z1), _gp(u0, d1, z1)
    face([A_, B_, C_, D_], m); face([_gp(u0, d0, z1), D_, C_, _gp(u1, d0, z1)], m); face([_gp(u0, d0, z0), _gp(u1, d0, z0), B_, A_], m)
    face([_gp(u0, d0, z0), A_, D_, _gp(u0, d0, z1)], m); face([B_, _gp(u1, d0, z0), _gp(u1, d0, z1), C_], m)
for _ux in (36.8, 39.0, 41.1): _gbox(_ux - 0.06, _ux + 0.06, -_RD_, -_RD_ + 0.1, 0.0, 3.2, GD)
_gbox(_UO0, _UO1, -_RD_, -_RD_ + 0.1, 3.1, 3.3, GD)                                                       # door head
_gbox(32.9, 34.1, 0.03, 0.13, 4.4, 5.6, DK); _gbox(43.6, 44.6, 0.03, 0.13, 4.0, 9.0, WR)                 # blank sign panels (no lettering)
# portholes (photo (622,962), (622,983)): round windows with a 0.3 m deep reveal ring standing out of the tiles
def _ring_win(u, z, w, h, m_glass, n=20, dep=0.3, t=0.25):
    for k in range(n):
        t0, t1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        o = lambda th, s_: (u + s_ * w / 2 * math.cos(th), z + s_ * h / 2 * math.sin(th))
        (ua, za), (ub, zb) = o(t0, 1.0), o(t1, 1.0); (uc, zc), (ud, zd) = o(t0, 1.0 + 2 * t / w), o(t1, 1.0 + 2 * t / w)
        face([_gp(ua, 0.03, za), _gp(ub, 0.03, zb), _gp(ub, dep, zb), _gp(ua, dep, za)], WR)                # reveal
        face([_gp(ua, dep, za), _gp(ub, dep, zb), _gp(ud, dep, zd), _gp(uc, dep, zc)], WR)                  # surround face
        face([_gp(uc, dep, zc), _gp(ud, dep, zd), _gp(ud, 0.03, zd), _gp(uc, 0.03, zc)], WR)                # outer edge
    g = face([_gp(u + w / 2 * math.cos(2 * math.pi * k / n), 0.05, z + h / 2 * math.sin(2 * math.pi * k / n)) for k in range(n)], m_glass,
             [(0.5 + 0.5 * math.cos(2 * math.pi * k / n), 0.5 + 0.5 * math.sin(2 * math.pi * k / n)) for k in range(n)])
    g.normal_update()
    if g.normal.dot(mu.Vector(_gp(u, 1.0, z)) - mu.Vector(_gp(u, 0.0, z))) < 0: g.normal_flip()
for _z in (12.0, 4.6): _ring_win(30.7, _z, 1.3, 1.4, DG, 16, 0.25, 0.18)
_ring_win(8.5, 19.5, 4.2, 5.7, RG, 32, 0.45, 0.35)                                                     # the big round window
# glass-block stair (photo (485,977)-(600,942)): a glazed volume 0.6 m proud of the tiles climbing across G1 and G2,
# with its white rail as a real tube on posts
_band = [(1.7, 6.2), (25.9, 18.6), (25.9, 12.4), (4.8, 0.0), (1.7, 0.0)]
def _clipu(pg, u0, u1):
    for lim, keep in ((u0, 1), (u1, -1)):
        out = []
        for i in range(len(pg)):
            P_, Q_ = pg[i - 1], pg[i]; pin, qin = (P_[0] - lim) * keep >= 0, (Q_[0] - lim) * keep >= 0
            if qin != pin: t = (lim - P_[0]) / (Q_[0] - P_[0]); out.append((lim, P_[1] + t * (Q_[1] - P_[1])))
            if qin: out.append(Q_)
        pg = out
    return pg
for (u0_, u1_) in ((_U[0], _U[1]), (_U[1], _U[2])):
    pg = _clipu(_band, u0_, u1_)
    if len(pg) < 3: continue
    f_ = face([_gp(u, 0.6, z) for u, z in pg], GB, [(u / 4.0, z / 4.0) for u, z in pg])
    f_.normal_update()
    if f_.normal.dot(mu.Vector(_gp(u0_ + 0.1, 1.0, 1)) - mu.Vector(_gp(u0_ + 0.1, 0.0, 1))) < 0: f_.normal_flip()
    for i in range(len(pg)):
        (ua, za), (ub, zb) = pg[i], pg[(i + 1) % len(pg)]
        if abs(ua - ub) < 1e-6 and abs(ua - u0_) < 1e-6 or abs(ua - ub) < 1e-6 and abs(ua - u1_) < 1e-6: continue   # the cut between faces
        if za == 0.0 and zb == 0.0: continue
        face([_gp(ua, 0.03, za), _gp(ub, 0.03, zb), _gp(ub, 0.6, zb), _gp(ua, 0.6, za)], PT)
_r0, _r1 = (4.8, 2.4), (25.9, 14.2)
tube(_gp(_r0[0], 0.75, _r0[1] + 1.0), _gp(_r1[0], 0.75, _r1[1] + 1.0), 0.06, 0.06, WR, 6)
for k in range(9):
    _t = k / 8; _u, _z = _r0[0] + (_r1[0] - _r0[0]) * _t, _r0[1] + (_r1[1] - _r0[1]) * _t
    tube(_gp(_u, 0.75, _z), _gp(_u, 0.75, _z + 1.0), 0.04, 0.04, WR, 5)

# navy Gate 7 block, 8.5 m: north of the white building's notch (OSM 483353591 vertices), north face from the current
# capture's navy roof (raw y 80, x 100) + lean (2.9, 1.5) at 8.5 m. The "7" face is the north face toward Vulture St.
_NV = [(102.8, 72.9), (108.7, 66.5), (114.4, 70.0), (111.5, 81.5), (103.0, 81.5)]
prism(_ccw(_NV), 0, 8.5, NW, True, 2, 9.0, 9.0, NW)
_skin(_NV[3], _NV[4], 0, 0, 8.5, 8.5, N7F, 0, 8.5, 8.5, 8.5)   # u from the east corner so the "7" reads from Vulture St
_skin(_NV[2], _NV[3], 0, 0, 8.5, 8.5, N7S, 0, 11.86, 9.0, 8.5)   # NE face: navy, maroon strip at the bottom (g49 left face)
face([(x, y, 8.53) for x, y in _ccw(_NV)], N7R, [(0, 0), (1, 0), (1, 1), (0.5, 1), (0, 1)])
def _inset(pg, d):   # the polygon moved d in from every edge (convex-ish footprints)
    pg = _ccw(pg); n_ = len(pg); out = []
    for i in range(n_):
        a_, b_, c_ = pg[i - 1], pg[i], pg[(i + 1) % n_]
        def off(p, q):
            ex, ey = q[0] - p[0], q[1] - p[1]; L_ = math.hypot(ex, ey); nx, ny = -ey / L_, ex / L_
            return (p[0] + nx * d, p[1] + ny * d), (q[0] + nx * d, q[1] + ny * d)
        (p1, p2), (p3, p4) = off(a_, b_), off(b_, c_)
        d1 = (p2[0] - p1[0], p2[1] - p1[1]); d2 = (p4[0] - p3[0], p4[1] - p3[1]); den = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(den) < 1e-9: out.append(p2); continue
        t = ((p3[0] - p1[0]) * d2[1] - (p3[1] - p1[1]) * d2[0]) / den; out.append((p1[0] + d1[0] * t, p1[1] + d1[1] * t))
    return out
def _curb(pg, z, h, w, m):   # a white upstand along the polygon's edges, w wide, h tall (modelled, not a painted line)
    n_ = len(pg)
    for i in range(n_):
        a_, b_ = pg[i], pg[(i + 1) % n_]; ex, ey = b_[0] - a_[0], b_[1] - a_[1]; L_ = math.hypot(ex, ey)
        if L_ < 0.2: continue
        nx, ny = -ey / L_ * w / 2, ex / L_ * w / 2
        q = [(a_[0] - nx, a_[1] - ny), (b_[0] - nx, b_[1] - ny), (b_[0] + nx, b_[1] + ny), (a_[0] + nx, a_[1] + ny)]
        prism(_ccw(q), z, z + h, m, True, 1, 4.0, None, m)
def _vent(px, py, z, r=0.18, h=0.45, m=None):
    tube((px, py, z), (px, py, z + h), r, r, m, 8)
_curb(_inset(_NV, 0.8), 8.5, 0.3, 0.15, WR)                       # the roof's upstand, 0.8 m in from the edge
_nc = (sum(x for x, y in _NV) / 5, sum(y for x, y in _NV) / 5)
for dx_, dy_ in ((-2.0, 1.5), (0.0, -1.8), (1.6, 2.4), (-2.8, -2.6)): _vent(_nc[0] + dx_, _nc[1] + dy_, 8.5, m=WR)   # roof vents

# white rendered building, 15 m: OSM part 483353591 east side, west side on the stadium facade (sat: its dark south deck runs to the facade)
_W = [(117.9, 31.1), (120.3, 44.4), (117.3, 49.3), (118.8, 50.2), (120.1, 48.1), (125.8, 51.6), (114.4, 70.0), (108.7, 66.5),
      (110.2, 64.0), (108.8, 63.1), (102.8, 72.9), (94.8, 68.0), (98.6, 64.2)]
_W += _arc(_ang(_W[-1]), _ang(_W[0]), 16)
prism(_ccw(_W), 0, 15.0, WR, True, 3, 9.0, 9.0, RD)
face([(x, y, 15.05) for x, y in _ccw([(95.6, 67.6), (102.6, 71.9), (107.9, 63.3), (98.9, 64.8)])], DD)   # terrace with tables (11135 + current)
face([(x, y, 15.05) for x, y in _ccw([(107.0, 38.0), (117.0, 33.0), (119.3, 44.0), (112.0, 45.0)])], DD)  # planted south deck (both captures)
# the terrace's white round tables and timber benches (the deck's 6 m pattern, every one inside the deck), modelled
def _inpoly(x, y, pg):
    c_ = False
    for i in range(len(pg)):
        (x1, y1), (x2, y2) = pg[i - 1], pg[i]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): c_ = not c_
    return c_
TB = mat('timber', W1, 0.8, 'timber.png'); BOX[TB] = 2.0
for _deck in ([(95.6, 67.6), (102.6, 71.9), (107.9, 63.3), (98.9, 64.8)], [(107.0, 38.0), (117.0, 33.0), (119.3, 44.0), (112.0, 45.0)]):
    _dk = _inset(_deck, 0.6); x0_ = min(x for x, y in _deck); y0_ = min(y for x, y in _deck)
    for gx in range(int(x0_ // 6) - 1, int(max(x for x, y in _deck) // 6) + 2):
        for gy in range(int(y0_ // 6) - 1, int(max(y for x, y in _deck) // 6) + 2):
            for u_, v_ in ((1.0, 1.2), (2.6, 4.4), (4.2, 1.8), (5.2, 4.9), (1.6, 3.4), (3.6, 2.9)):
                x_, y_ = gx * 6 + u_, gy * 6 + v_
                if _inpoly(x_, y_, _dk):
                    tube((x_, y_, 15.05), (x_, y_, 15.75), 0.05, 0.05, ST, 6); tube((x_, y_, 15.75), (x_, y_, 15.79), 0.4, 0.4, WR, 12)   # table
            for (ua, va), (ub, vb) in (((0.6, 5.0), (2.4, 5.35)), ((3.4, 0.4), (5.4, 0.75))):
                bx_ = [(gx * 6 + ua, gy * 6 + va), (gx * 6 + ub, gy * 6 + va), (gx * 6 + ub, gy * 6 + vb), (gx * 6 + ua, gy * 6 + vb)]
                if all(_inpoly(x, y, _dk) for x, y in bx_): prism(_ccw(bx_), 15.05, 15.5, TB, True, 1, 2.0, None, TB)      # bench
_sk = [(103.0, 59.6), (110.2, 62.9), (117.5, 49.4), (112.0, 45.7)]                                       # skylight lantern (11135 trace + lean)
prism(_ccw(_sk), 15.0, 16.5, WR, True, 1, 9.0, 9.0, WR)
face([(x, y, 16.53) for x, y in _ccw(_sk)], SK, [(0, 0), (1, 0), (1, 1), (0, 1)])
# the lantern's white frames: a bar round the edge and between the six panes, standing 0.15 m above the glass
_skq = _ccw(_sk)
def _bl(u, v):   # bilinear point on the lantern top
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = _skq
    return (x0 * (1 - u) * (1 - v) + x1 * u * (1 - v) + x2 * u * v + x3 * (1 - u) * v, y0 * (1 - u) * (1 - v) + y1 * u * (1 - v) + y2 * u * v + y3 * (1 - u) * v)
for u in (0.03, 0.35, 0.66, 0.97):
    tube((*_bl(u, 0.0), 16.6), (*_bl(u, 1.0), 16.6), 0.1, 0.1, WR, 4)
for v in (0.03, 0.5, 0.97):
    tube((*_bl(0.0, v), 16.6), (*_bl(1.0, v), 16.6), 0.1, 0.1, WR, 4)
# round fan drums (director 2026-11-19 gate: "shows a round tower on it. Build the round tower"): open-topped white drums
# on the roof, footprints from tile 11135 (+ lean), height 4.3 m from photo g49 (rim 33 px wide, 25 px deep, wall 15 px),
# a fan housing inside each and a steel frame across the top
DH = 4.3
def _drum(px, py, r, z0, z1, n=36):
    T = [2 * math.pi * k / n for k in range(n + 1)]
    ri = r - 0.25
    for k in range(n):
        a, b = T[k], T[k + 1]; u0, u1 = k * 2 * math.pi * r / n / 9.0, (k + 1) * 2 * math.pi * r / n / 9.0
        face([(px + r * math.cos(a), py + r * math.sin(a), z0), (px + r * math.cos(b), py + r * math.sin(b), z0),
              (px + r * math.cos(b), py + r * math.sin(b), z1), (px + r * math.cos(a), py + r * math.sin(a), z1)], WR,
             [(u0, z0 / 9.0), (u1, z0 / 9.0), (u1, z1 / 9.0), (u0, z1 / 9.0)])
        face([(px + ri * math.cos(b), py + ri * math.sin(b), z0 + 0.3), (px + ri * math.cos(a), py + ri * math.sin(a), z0 + 0.3),
              (px + ri * math.cos(a), py + ri * math.sin(a), z1), (px + ri * math.cos(b), py + ri * math.sin(b), z1)], DK,
             [(u1, 0), (u0, 0), (u0, (z1 - z0) / 6.0), (u1, (z1 - z0) / 6.0)])
        face([(px + ri * math.cos(a), py + ri * math.sin(a), z1), (px + r * math.cos(a), py + r * math.sin(a), z1),
              (px + r * math.cos(b), py + r * math.sin(b), z1), (px + ri * math.cos(b), py + ri * math.sin(b), z1)], WR,
             [(u0, 0), (u0, 0.03), (u1, 0.03), (u1, 0)])
    face([(px + ri * math.cos(t), py + ri * math.sin(t), z0 + 0.3) for t in T[:-1]], DK)
    hb = 0.42 * r                                                            # fan housing: white box with the dark fan on top
    prism(_ccw([(px - hb, py - hb), (px + hb, py - hb), (px + hb, py + hb), (px - hb, py + hb)]), z0 + 0.3, z1 - 1.2, WR, True, 1, 9.0, 9.0, WR)
    face([(px + 0.8 * hb * math.cos(t), py + 0.8 * hb * math.sin(t), z1 - 1.17) for t in T[:-1]], DK)
    for d in (-0.45 * r, 0.45 * r):                                          # steel frame across the rim, both ways
        tube((px - r, py + d, z1 + 0.1), (px + r, py + d, z1 + 0.1), 0.08, 0.08, ST, 6)
        tube((px + d, py - r, z1 + 0.1), (px + d, py + r, z1 + 0.1), 0.08, 0.08, ST, 6)
for (px, py), r in (((116.0, 62.9), 3.1), ((119.2, 56.3), 2.6)):
    _drum(px, py, r, 15.0, 15.0 + DH)

# dark navy face between the gate-7 block and the tiled gate face (photo 432-480 x 924-1000): skins 3 cm proud, away from each block's centre
def _dskin(p0, p1, h, ctr, m=NW):
    nx, ny = p1[1] - p0[1], -(p1[0] - p0[0]); L = math.hypot(nx, ny); nx, ny = nx / L, ny / L
    if nx * ((p0[0] + p1[0]) / 2 - ctr[0]) + ny * ((p0[1] + p1[1]) / 2 - ctr[1]) < 0: nx, ny = -nx, -ny
    q0 = (p0[0] + nx * 0.03, p0[1] + ny * 0.03); q1 = (p1[0] + nx * 0.03, p1[1] + ny * 0.03)
    vs = [(*q0, 0.0), (*q1, 0.0), (*q1, h), (*q0, h)]; e = (q1[0] - q0[0], q1[1] - q0[1])
    uvs = [(0, 0), (L / 9.0, 0), (L / 9.0, h / 9.0), (0, h / 9.0)]
    if e[1] * nx - e[0] * ny < 0: vs, uvs = vs[::-1], uvs[::-1]
    face(vs, m, uvs)
_wc = (sum(x for x, y in _W) / len(_W), sum(y for x, y in _W) / len(_W))
_gc = ((_F[0][0] + _F[1][0] + _Bk[0][0] + _Bk[1][0]) / 4, (_F[0][1] + _F[1][1] + _Bk[0][1] + _Bk[1][1]) / 4)
_dskin(_F[0], _Bk[0], 24.0, _gc)
