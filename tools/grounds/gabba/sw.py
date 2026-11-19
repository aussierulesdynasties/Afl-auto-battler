# ---- south-west corner buildings (photo g49 x 262-700, y 725-1000): measured on pixel grids, unprojected through camB
PT = mat('paletile', W1, 0.8, 'paletile.png'); GF = mat('gatefront', W1, 0.8, 'gatefront.png')
NW = mat('navywall', W1, 0.7, 'navywall.png'); N7F = mat('n7front', W1, 0.7, 'n7front.png'); N7R = mat('n7roof', W1, 0.8, 'n7roof.png')
WR = mat('whiterender', W1, 0.8, 'whiterender.png'); DD = mat('deckdots', W1, 0.9, 'deckdots.png'); SK = mat('skylight', W1, 0.4, 'skylight.png')
BOX.update({PT: 4.8, NW: 9.0, WR: 9.0, DD: 6.0, GF: 46.0, N7F: 8.5, N7R: 10.0, SK: 12.0})
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
def _slab(q, hs, m, capm, uw, vm):   # 4-sided block with a sloped top (heights per corner)
    vb = [bm.verts.new((x, y, 0)) for x, y in q]; vt = [bm.verts.new((x, y, h)) for (x, y), h in zip(q, hs)]
    L = 0.0
    for k in range(4):
        j = (k + 1) % 4; s = math.dist(q[k], q[j])
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
_slab(_q, [_h[p] for p in _q], PT, DK, 4.8, 4.8)
_skin(_F[0], _F[1], 0, 0, 24.0, 24.0, GF, _U[0], _U[1], 46.0, 24.0)
_skin(_F[1], _F[2], 0, 0, 21.0, 21.0, GF, _U[1], _U[2], 46.0, 24.0)
_skin(_F[2], _F[3], 0, 0, 17.3, 13.4, GF, _U[2], _U[3], 46.0, 24.0)

# navy Gate 7 block, 8.5 m: north of the white building's notch (OSM 483353591 vertices), north face from the current
# capture's navy roof (raw y 80, x 100) + lean (2.9, 1.5) at 8.5 m. The "7" face is the north face toward Vulture St.
_NV = [(102.8, 72.9), (108.7, 66.5), (114.4, 70.0), (111.5, 81.5), (103.0, 81.5)]
prism(_ccw(_NV), 0, 8.5, NW, True, 2, 9.0, 9.0, NW)
_skin(_NV[3], _NV[4], 0, 0, 8.5, 8.5, N7F, 0, 8.5, 8.5, 8.5)   # u from the east corner so the "7" reads from Vulture St
face([(x, y, 8.53) for x, y in _ccw(_NV)], N7R, [(0, 0), (1, 0), (1, 1), (0.5, 1), (0, 1)])

# white rendered building, 15 m: OSM part 483353591 east side, west side on the stadium facade (sat: its dark south deck runs to the facade)
_W = [(117.9, 31.1), (120.3, 44.4), (117.3, 49.3), (118.8, 50.2), (120.1, 48.1), (125.8, 51.6), (114.4, 70.0), (108.7, 66.5),
      (110.2, 64.0), (108.8, 63.1), (102.8, 72.9), (94.8, 68.0), (98.6, 64.2)]
_W += _arc(_ang(_W[-1]), _ang(_W[0]), 16)
prism(_ccw(_W), 0, 15.0, WR, True, 3, 9.0, 9.0, RD)
face([(x, y, 15.05) for x, y in _ccw([(95.6, 67.6), (102.6, 71.9), (107.9, 63.3), (98.9, 64.8)])], DD)   # terrace with tables (11135 + current)
face([(x, y, 15.05) for x, y in _ccw([(107.0, 38.0), (117.0, 33.0), (119.3, 44.0), (112.0, 45.0)])], DD)  # planted south deck (both captures)
_sk = [(103.0, 59.6), (110.2, 62.9), (117.5, 49.4), (112.0, 45.7)]                                       # skylight lantern (11135 trace + lean)
prism(_ccw(_sk), 15.0, 16.5, WR, True, 1, 9.0, 9.0, WR)
face([(x, y, 16.53) for x, y in _ccw(_sk)], SK, [(0, 0), (1, 0), (1, 1), (0, 1)])
for (px, py), r in (((116.0, 62.9), 3.1), ((119.2, 56.3), 2.6)):                                          # round plant screens (11135 + lean at 18.5 m)
    tube((px, py, 15.0), (px, py, 18.5), r, r, WR, 28)
    face([(px + (r - 0.2) * math.cos(t), py + (r - 0.2) * math.sin(t), 18.52) for t in [2 * math.pi * k / 28 for k in range(28)]], DK)

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
